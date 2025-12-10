from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone


class EmailService:
    """Service for sending authentication-related emails"""

    @staticmethod
    def send_password_reset_email(user, raw_token, request=None):
        """Send password reset email with security notices"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password/confirm/{raw_token}/"

        # Get request info for security notice
        ip_address = 'Unknown'
        location = 'Unknown location'

        if request:
            ip_address = PasswordResetToken.get_client_ip(request)

        context = {
            'user': user,
            'reset_url': reset_url,
            'expiry_minutes': settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
            'ip_address': ip_address,
            'timestamp': timezone.now().strftime('%B %d, %Y at %I:%M %p %Z'),
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }

        html_content = render_to_string('emails/password_reset.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject='Password Reset Request - Order Form',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    @staticmethod
    def send_activation_email(user, raw_token):
        """Send account activation email with CTA button"""
        activation_url = f"{settings.FRONTEND_URL}/activate/{raw_token}/"

        context = {
            'user': user,
            'activation_url': activation_url,
            'expiry_hours': settings.ACCOUNT_ACTIVATION_TOKEN_EXPIRY_HOURS,
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }

        html_content = render_to_string('emails/account_activation.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject='Activate Your Account - Order Form',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    @staticmethod
    def send_password_changed_notification(user):
        """Send notification that password was changed"""
        context = {
            'user': user,
            'timestamp': timezone.now().strftime('%B %d, %Y at %I:%M %p %Z'),
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }

        html_content = render_to_string('emails/password_changed.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject='Your Password Was Changed - Order Form',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)


# Import for convenience
from .models import PasswordResetToken