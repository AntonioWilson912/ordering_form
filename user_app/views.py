from django.shortcuts import render

# Create your views here.
def index(request):
    return render("index.html")

def register(request):
    return render("register.html")

def login(request):
    return render("login.html")

def reset_password(request):
    return render("reset_password.html")