from django import forms
from .models import User, EmailTemplate


class RegisterUserForm(forms.Form):
    username = forms.CharField(label="Username:", max_length=255)
    email = forms.EmailField(label="Email:")
    password = forms.CharField(
        label="Password:", max_length=255, widget=forms.PasswordInput
    )
    confirm_password = forms.CharField(
        label="Confirm Password:", max_length=255, widget=forms.PasswordInput
    )


class LoginUserForm(forms.Form):
    username = forms.CharField(label="Username:", max_length=255)
    password = forms.CharField(
        label="Password:", max_length=255, widget=forms.PasswordInput
    )


class ResetPasswordForm(forms.Form):
    email = forms.EmailField(label="Email:")


class AccountSettingsForm(forms.ModelForm):
    """Form for updating account settings"""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "display_name",
            "email",
            "email_signature",
            "timezone",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter your first name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter your last name"}
            ),
            "display_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Name shown when sending emails",
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "your@email.com"}
            ),
            "email_signature": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Thank you,\nYour Name",
                }
            ),
            "timezone": forms.Select(attrs={"class": "form-control"}),
        }
        help_texts = {
            "display_name": "This name will appear when you send order emails. If empty, your username will be used.",
            "email": "Replies to order emails will be sent to this address.",
            "email_signature": "Your signature will appear where %signature% is used in email templates.",
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if (
            email
            and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists()
        ):
            raise forms.ValidationError("This email address is already in use.")
        return email


class ChangePasswordForm(forms.Form):
    """Form for changing password"""

    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your current password",
            }
        ),
    )
    new_password = forms.CharField(
        label="New Password",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new password (min 8 characters)",
            }
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm your new password"}
        ),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get("current_password")
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Your current password is incorrect.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError(
                    {
                        "confirm_password": "The new passwords don't match. Please try again."
                    }
                )

        return cleaned_data


class EmailTemplateForm(forms.ModelForm):
    """Form for creating/editing email templates"""

    class Meta:
        model = EmailTemplate
        fields = ["name", "subject_template", "body_template", "is_default"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Standard Order, Rush Order",
                }
            ),
            "subject_template": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Order Request for %company_name%",
                }
            ),
            "body_template": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": "Hello,\n\nHere is my order:\n\n%order_items%\n\n%signature%",
                }
            ),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "is_default": "Set as default template",
        }
