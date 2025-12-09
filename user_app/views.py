from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.views.generic import ListView, TemplateView
from django.contrib.auth.decorators import login_required
from core.mixins import PageTitleMixin, LoginRequiredMixin
from .models import User

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

        # Basic validation
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

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # Log the user in
        auth_login(request, user)
        messages.success(request, "Registration successful!")
        return redirect('dashboard:home')

    return render(request, "user_app/register.html")

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "user_app/login.html")

def reset_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        # TODO: Implement password reset logic
        messages.info(request, "If an account exists with this email, you will receive a password reset link.")

    return render(request, "user_app/reset_password.html")

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