from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import PasswordResetToken


class EmailService:
    """Service for sending authentication-related emails"""

    @staticmethod
    def send_password_reset_email(user, raw_token, request=None):
        """Send password reset email with security notices"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password/confirm/{raw_token}/"

        ip_address = "Unknown"

        if request:
            ip_address = PasswordResetToken.get_client_ip(request)

        context = {
            "user": user,
            "reset_url": reset_url,
            "expiry_minutes": settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
            "ip_address": ip_address,
            "timestamp": timezone.now().strftime("%B %d, %Y at %I:%M %p %Z"),
            "support_email": settings.DEFAULT_FROM_EMAIL,
        }

        html_content = render_to_string("emails/password_reset.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject="Password Reset Request - Order Form",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    @staticmethod
    def send_activation_email(user, raw_token):
        """Send account activation email with CTA button"""
        activation_url = f"{settings.FRONTEND_URL}/activate/{raw_token}/"

        # Use minutes now instead of hours
        expiry_minutes = getattr(
            settings, "ACCOUNT_ACTIVATION_TOKEN_EXPIRY_MINUTES", 10
        )

        context = {
            "user": user,
            "activation_url": activation_url,
            "expiry_minutes": expiry_minutes,
            "support_email": settings.DEFAULT_FROM_EMAIL,
        }

        html_content = render_to_string("emails/account_activation.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject="Activate Your Account - Order Form",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    @staticmethod
    def send_password_changed_notification(user):
        """Send notification that password was changed"""
        context = {
            "user": user,
            "timestamp": timezone.now().strftime("%B %d, %Y at %I:%M %p %Z"),
            "support_email": settings.DEFAULT_FROM_EMAIL,
        }

        html_content = render_to_string("emails/password_changed.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject="Your Password Was Changed - Order Form",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    @staticmethod
    def send_order_email(user, to_email, subject, content):
        """
        Send order email with user's name as sender and their email as Reply-To.

        Args:
            user: The User object sending the email
            to_email: Recipient email address
            subject: Email subject
            content: Email body content
        """
        # Build the "From" address with user's display name
        sender_name = user.get_email_sender_name()
        from_email = f'"{sender_name}" <{settings.DEFAULT_FROM_EMAIL}>'

        # User's email will be the Reply-To
        reply_to = [user.email]

        email = EmailMultiAlternatives(
            subject=subject,
            body=content,
            from_email=from_email,
            to=[to_email],
            reply_to=reply_to,
        )
        email.send(fail_silently=False)

        return True
