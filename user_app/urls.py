from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),

    # Password Reset
    path("reset/", views.request_password_reset, name="reset"),
    path("reset-password/confirm/<str:token>/", views.reset_password_confirm, name="reset_confirm"),

    # Account Activation
    path("activate/<str:token>/", views.activate_account, name="activate"),
    path("resend-activation/", views.resend_activation, name="resend_activation"),

    # Account Settings
    path("account/", views.AccountSettingsView.as_view(), name="account_settings"),
    path("account/change-password/", views.change_password, name="change_password"),

    # Email Templates
    path("account/templates/new/", views.EmailTemplateCreateView.as_view(), name="template_create"),
    path("account/templates/<int:pk>/edit/", views.EmailTemplateUpdateView.as_view(), name="template_edit"),
    path("account/templates/<int:pk>/delete/", views.EmailTemplateDeleteView.as_view(), name="template_delete"),

    path("users/", views.UserListView.as_view(), name="user_list"),
    path("help/", views.HelpView.as_view(), name="help"),
]