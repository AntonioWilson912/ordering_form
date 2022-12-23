from django.shortcuts import render, redirect

# Create your views here.
def index(request):
    return render(request, "index.html")

def register(request):
    return render(request, "register.html")

def login(request):
    return render(request, "login.html")

def reset_password(request):
    return render(request, "reset_password.html")

def logout(request):
    for key in request.session.keys():
        del request.session[key]

    return redirect("/")


def dashboard(request):
    return render(request, "view_users.html")

def help(request):
    return render(request, "help.html")