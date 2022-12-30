from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import User

# Create your views here.
def index(request):
    return render(request, "index.html")

def register(request):
    if request.method == "POST":
        # A.K.A. Process the registration data
        pass
    return render(request, "register.html")

def login(request):
    if request.method == "POST":
        # A.K.A. Process the login data
        pass
    return render(request, "login.html")

def reset_password(request):
    if request.method == "POST":
        # A.K.A. Process the password reset data
        pass
    return render(request, "reset_password.html")

def logout(request):
    for key in request.session.keys():
        del request.session[key]

    return redirect("/")

def dashboard(request):
    # if not "user_id" in request.session:
    #     return redirect("/")
    context = {
        # "logged_in_user": User.objects.get(id=request.session["user_id"]),
        "all_users": User.objects.all()
    }
    return render(request, "view_users.html", context)

def help(request):
    return render(request, "help.html")