from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib import messages
from django.views.generic import ListView, TemplateView, UpdateView, CreateView, DeleteView, View
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.urls import reverse_lazy
from core.mixins import PageTitleMixin, LoginRequiredMixin
from .models import User, PasswordResetToken, AccountActivationToken, EmailTemplate
from .services import EmailService
from .forms import (
    ProfileSettingsForm, EmailSignatureForm, ChangePasswordForm, EmailTemplateForm
)


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, "user_app/index.html")


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        errors = []

        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long.")

        if User.objects.filter(username=username).exists():
            errors.append("Username already taken.")

        if not email or '@' not in email:
            errors.append("Valid email required.")

        if User.objects.filter(email=email).exists():
            errors.append("Email already registered.")

        if not password1 or len(password1) < 8:
            errors.append("Password must be at least 8 characters long.")

        if password1 != password2:
            errors.append("Passwords do not match.")

        if errors:
            return render(request, "user_app/register.html", {
                'errors': errors,
                'username': username,
                'email': email
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            is_activated=False
        )

        EmailTemplate.create_default_template(user)

        raw_token, token_obj = AccountActivationToken.create_for_user(user)
        EmailService.send_activation_email(user, raw_token)

        messages.success(
            request,
            "Registration successful! Please check your email to activate your account."
        )
        return redirect('users:login')

    return render(request, "user_app/register.html")


def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account has been deactivated. Please contact support.")
                return render(request, "user_app/login.html")

            if not user.is_activated:
                messages.error(
                    request,
                    "Your account is not activated. Please check your email for the activation link."
                )
                return render(request, "user_app/login.html", {
                    'show_resend': True,
                    'inactive_email': user.email
                })

            auth_login(request, user)
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "user_app/login.html")


def resend_activation(request):
    """Resend activation email"""
    if request.method == "POST":
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email, is_activated=False)

            if not user.can_resend_activation():
                remaining = user.get_resend_cooldown_remaining()
                messages.error(
                    request,
                    f"Please wait {remaining} seconds before requesting another activation email."
                )
            else:
                raw_token, token_obj = AccountActivationToken.create_for_user(user)
                EmailService.send_activation_email(user, raw_token)
                messages.success(
                    request,
                    "Activation email sent! Please check your inbox."
                )
        except User.DoesNotExist:
            messages.success(
                request,
                "If an account exists with this email, an activation link will be sent."
            )

        return redirect('users:login')

    return redirect('users:login')


def activate_account(request, token):
    """Activate user account via email link"""
    token_obj = AccountActivationToken.validate_token(token)

    if not token_obj:
        messages.error(
            request,
            "This activation link is invalid or has expired. Please request a new one."
        )
        return redirect('users:login')

    user = token_obj.user
    user.is_activated = True
    user.save(update_fields=['is_activated'])

    token_obj.mark_used()

    messages.success(
        request,
        "Your account has been activated! You can now log in."
    )
    return redirect('users:login')


def request_password_reset(request):
    """Request a password reset email"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == "POST":
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
            raw_token, token_obj = PasswordResetToken.create_for_user(user, request)
            EmailService.send_password_reset_email(user, raw_token, request)
        except User.DoesNotExist:
            pass

        messages.info(
            request,
            "If an account exists with this email, you will receive a password reset link."
        )
        return redirect('users:login')

    return render(request, "user_app/reset_password.html")


def reset_password_confirm(request, token):
    """Handle password reset confirmation"""
    token_obj = PasswordResetToken.validate_token(token)

    if not token_obj:
        messages.error(
            request,
            "This password reset link is invalid or has expired. Please request a new one."
        )
        return redirect('users:reset')

    if request.method == "POST":
        token_obj = PasswordResetToken.validate_token(token)

        if not token_obj:
            messages.error(
                request,
                "This password reset link has expired. Please request a new one."
            )
            return redirect('users:reset')

        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        errors = []

        if not password1 or len(password1) < 8:
            errors.append("Password must be at least 8 characters long.")

        if password1 != password2:
            errors.append("Passwords do not match.")

        if errors:
            return render(request, "user_app/reset_password_confirm.html", {
                'errors': errors,
                'token': token,
                'valid': True
            })

        user = token_obj.user
        user.set_password(password1)
        user.save()

        token_obj.blacklist()

        EmailService.send_password_changed_notification(user)

        messages.success(
            request,
            "Your password has been reset successfully! You can now log in."
        )
        return redirect('users:login')

    auto_show_form = request.session.session_key is not None

    return render(request, "user_app/reset_password_confirm.html", {
        'token': token,
        'valid': True,
        'auto_show_form': auto_show_form,
        'expiry_minutes': settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
    })


def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("users:login")


class AccountSettingsView(LoginRequiredMixin, PageTitleMixin, TemplateView):
    """View for account settings page"""
    template_name = 'user_app/account_settings.html'
    page_title = 'Account Settings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['profile_form'] = ProfileSettingsForm(instance=user)
        context['signature_form'] = EmailSignatureForm(instance=user)
        context['password_form'] = ChangePasswordForm(user=user)
        context['email_preview'] = user.get_email_sender_name()
        context['email_templates'] = user.email_templates.all()
        context['template_variables'] = EmailTemplate.get_available_variables()

        return context


def update_profile(request):
    """Handle profile information update"""
    if not request.user.is_authenticated:
        return redirect('users:login')

    if request.method == "POST":
        form = ProfileSettingsForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile information updated successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')

    return redirect('users:account_settings')


def update_signature(request):
    """Handle email signature update"""
    if not request.user.is_authenticated:
        return redirect('users:login')

    if request.method == "POST":
        form = EmailSignatureForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Email signature updated successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return redirect('users:account_settings')


def change_password(request):
    """Handle password change from account settings"""
    if not request.user.is_authenticated:
        return redirect('users:login')

    if request.method == "POST":
        form = ChangePasswordForm(user=request.user, data=request.POST)

        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.save()

            update_session_auth_hash(request, request.user)

            EmailService.send_password_changed_notification(request.user)

            messages.success(request, 'Your password has been changed successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return redirect('users:account_settings')


class EmailTemplateCreateView(LoginRequiredMixin, PageTitleMixin, CreateView):
    """Create a new email template"""
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'user_app/email_template_form.html'
    page_title = 'Create Email Template'
    success_url = reverse_lazy('users:account_settings')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Email template created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template_variables'] = EmailTemplate.get_available_variables()
        context['user_signature'] = self.request.user.email_signature
        return context


class EmailTemplateUpdateView(LoginRequiredMixin, PageTitleMixin, UpdateView):
    """Edit an email template"""
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'user_app/email_template_form.html'
    success_url = reverse_lazy('users:account_settings')

    def get_queryset(self):
        return EmailTemplate.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Template: {self.object.name}'
        context['is_update'] = True
        context['template_variables'] = EmailTemplate.get_available_variables()
        context['user_signature'] = self.request.user.email_signature
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Email template updated successfully!')
        return super().form_valid(form)


class EmailTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an email template"""
    model = EmailTemplate
    success_url = reverse_lazy('users:account_settings')

    def get_queryset(self):
        return EmailTemplate.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email template deleted successfully!')
        return super().delete(request, *args, **kwargs)


class UserListView(LoginRequiredMixin, PageTitleMixin, ListView):
    model = User
    template_name = 'user_app/user_list.html'
    context_object_name = 'users'
    page_title = 'All Users'

    def get_queryset(self):
        return User.objects.all().order_by('username')


class HelpView(LoginRequiredMixin, PageTitleMixin, TemplateView):
    template_name = 'user_app/help.html'
    page_title = 'Help'