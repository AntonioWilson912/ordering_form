from django import forms
from .models import User


class RegisterUserForm(forms.Form):
    username = forms.CharField(label="Username:", max_length=255)
    email = forms.EmailField(label="Email:")
    password = forms.CharField(label="Password:", max_length=255, widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirm Password:", max_length=255, widget=forms.PasswordInput)


class LoginUserForm(forms.Form):
    username = forms.CharField(label="Username:", max_length=255)
    password = forms.CharField(label="Password:", max_length=255, widget=forms.PasswordInput)


class ResetPasswordForm(forms.Form):
    email = forms.EmailField(label="Email:")


class AccountSettingsForm(forms.ModelForm):
    """Form for updating account settings"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'display_name', 'email', 'timezone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name shown when sending emails'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'timezone': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        help_texts = {
            'display_name': 'This name will appear when you send order emails. If empty, your username will be used.',
            'email': 'Replies to order emails will be sent to this address.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email read-only if user is editing their own profile
        # (email changes might require re-verification)
        if self.instance and self.instance.pk:
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].help_text = 'Contact support to change your email address.'


class ChangePasswordForm(forms.Form):
    """Form for changing password"""
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
    )
    new_password = forms.CharField(
        label="New Password",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password (min 8 characters)'
        })
    )
    confirm_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("New passwords do not match.")

        return cleaned_data