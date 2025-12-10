from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.views.generic import ListView, TemplateView, View
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from core.mixins import PageTitleMixin, LoginRequiredMixin
from .models import User, PasswordResetToken, AccountActivationToken
from .services import EmailService


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

        # Create user (inactive until email verification)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            is_activated=False
        )

        # Generate activation token and send email
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
            # Check if account is activated
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
                cooldown = settings.ACTIVATION_RESEND_COOLDOWN_SECONDS
                messages.error(
                    request,
                    f"Please wait {cooldown} seconds before requesting another activation email."
                )
            else:
                raw_token, token_obj = AccountActivationToken.create_for_user(user)
                EmailService.send_activation_email(user, raw_token)
                messages.success(
                    request,
                    "Activation email sent! Please check your inbox."
                )
        except User.DoesNotExist:
            # Don't reveal if email exists or not
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

    # Activate the user
    user = token_obj.user
    user.is_activated = True
    user.save(update_fields=['is_activated'])

    # Mark token as used
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

        # Always show the same message regardless of whether email exists
        # This prevents email enumeration attacks
        try:
            user = User.objects.get(email=email)

            # Generate token and send email
            raw_token, token_obj = PasswordResetToken.create_for_user(user, request)
            EmailService.send_password_reset_email(user, raw_token, request)

        except User.DoesNotExist:
            # Do nothing, but show same message
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
        # Re-validate token at submission time
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

        # Update password
        user = token_obj.user
        user.set_password(password1)
        user.save()

        # Blacklist the token
        token_obj.blacklist()

        # Send notification email
        EmailService.send_password_changed_notification(user)

        messages.success(
            request,
            "Your password has been reset successfully! You can now log in."
        )
        return redirect('users:login')

    # Check if within same browser context (has session)
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