from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("reset", views.reset_password, name="reset"),
    path("logout", views.logout, name="logout"),

    path("users/all", views.dashboard, name="dashboard"),
    path("help", views.help, name="help")
]