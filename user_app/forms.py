from django import forms

class RegisterUserForm(forms.Form):
    username = forms.CharField(label="Username:", max_length=255)
    password = forms.CharField(label="Password:", max_length=255, widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirm Password:", max_length=255, widget=forms.PasswordInput)

class LoginUserForm(forms.Form):
    username = forms.CharField(label="Username:", max_length=255)
    password = forms.CharField(label="Password:", max_length=255, widget=forms.PasswordInput)

class ResetPasswordForm(forms.Form):
    username = forms.CharField(label="Username:", max_length=255)
    password = forms.CharField(label="Password:", max_length=255, widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirm Password:", max_length=255, widget=forms.PasswordInput)