from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
import pytz
import secrets
import hashlib
import re
from datetime import timedelta

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]


class User(AbstractUser):
    """Custom user model with activation support and profile info"""
    email = models.EmailField(unique=True)

    # Profile fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Name to display when sending emails. Falls back to username if empty.'
    )
    email_signature = models.TextField(
        blank=True,
        help_text='Your email signature. Will be inserted where %signature% appears in templates.'
    )

    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='America/New_York',
        help_text='User timezone for displaying dates'
    )
    is_activated = models.BooleanField(
        default=False,
        help_text='Designates whether this user has activated their account via email.'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user account is active. Unselect to disable the account.'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username

    def get_display_name(self):
        """Get the name to display for this user"""
        if self.display_name:
            return self.display_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return self.username

    def get_email_sender_name(self):
        """Get the name to use as email sender"""
        display = self.get_display_name()
        app_name = getattr(settings, 'EMAIL_SENDER_NAME', 'Order Form')
        return f"{display} via {app_name}"

    def can_resend_activation(self):
        """Check if enough time has passed to resend activation email"""
        cooldown = getattr(settings, 'ACTIVATION_RESEND_COOLDOWN_SECONDS', 60)
        latest_token = self.activation_tokens.order_by('-created_at').first()

        if not latest_token:
            return True

        elapsed = (timezone.now() - latest_token.created_at).total_seconds()
        return elapsed >= cooldown

    def get_resend_cooldown_remaining(self):
        """Get remaining seconds until user can resend activation"""
        cooldown = getattr(settings, 'ACTIVATION_RESEND_COOLDOWN_SECONDS', 60)
        latest_token = self.activation_tokens.order_by('-created_at').first()

        if not latest_token:
            return 0

        elapsed = (timezone.now() - latest_token.created_at).total_seconds()
        remaining = cooldown - elapsed
        return max(0, int(remaining))

    def get_default_template(self):
        """Get user's default email template or None"""
        return self.email_templates.filter(is_default=True).first()


class EmailTemplate(models.Model):
    """
    User-created email templates with variable support.

    Supported variables:
    - %company_name% - The recipient company's name
    - %order_id% - The order ID number
    - %order_date% - The order date formatted
    - %order_items% - Formatted list of order items
    - %total_items% - Total quantity of all items
    - %item_count% - Number of different products
    - %user_name% - The sender's display name
    - %user_email% - The sender's email address
    - %signature% - The user's email signature
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_templates'
    )
    name = models.CharField(
        max_length=100,
        help_text='A name to identify this template'
    )
    subject_template = models.CharField(
        max_length=255,
        default='Order Request for %company_name%',
        help_text='Email subject. Variables: %company_name%, %order_id%, %order_date%'
    )
    body_template = models.TextField(
        help_text='Email body. Use variables like %order_items%, %signature%, etc.'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Use this template by default when composing emails'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def save(self, *args, **kwargs):
        # If this template is set as default, unset others
        if self.is_default:
            EmailTemplate.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_available_variables(cls):
        """Return list of available template variables with descriptions"""
        return [
            {'var': '%company_name%', 'desc': "The recipient company's name"},
            {'var': '%order_id%', 'desc': 'The order ID number'},
            {'var': '%order_date%', 'desc': 'The order date (formatted)'},
            {'var': '%order_items%', 'desc': 'Formatted list of order items'},
            {'var': '%total_items%', 'desc': 'Total quantity of all items'},
            {'var': '%item_count%', 'desc': 'Number of different products'},
            {'var': '%user_name%', 'desc': "Your display name"},
            {'var': '%user_email%', 'desc': 'Your email address'},
            {'var': '%signature%', 'desc': 'Your email signature'},
        ]

    def render(self, context):
        """
        Render the template with the given context.

        Args:
            context: dict with keys matching variable names (without %)

        Returns:
            tuple: (rendered_subject, rendered_body)
        """
        subject = self.subject_template
        body = self.body_template

        for key, value in context.items():
            placeholder = f'%{key}%'
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))

        return subject, body

    @classmethod
    def create_default_template(cls, user):
        """Create a default template for a new user"""
        default_body = """Hello,

Here is my order:

%order_items%

%signature%"""

        return cls.objects.create(
            user=user,
            name='Default Template',
            subject_template='Order Request for %company_name%',
            body_template=default_body,
            is_default=True
        )


class PasswordResetToken(models.Model):
    """Stores password reset tokens with expiration and blacklist functionality."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_blacklisted = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_hash', 'is_blacklisted']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Password Reset for {self.user.username} - {'Used' if self.is_blacklisted else 'Active'}"

    @classmethod
    def generate_token(cls):
        return secrets.token_urlsafe(32)

    @classmethod
    def hash_token(cls, token):
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_for_user(cls, user, request=None):
        cls.objects.filter(user=user, is_blacklisted=False).update(is_blacklisted=True)

        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)

        expiry_minutes = getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES', 10)
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        ip_address = None
        user_agent = ''

        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        token_obj = cls.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return raw_token, token_obj

    @classmethod
    def get_client_ip(cls, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @classmethod
    def validate_token(cls, raw_token):
        token_hash = cls.hash_token(raw_token)

        try:
            token_obj = cls.objects.select_related('user').get(
                token_hash=token_hash,
                is_blacklisted=False
            )

            if timezone.now() > token_obj.expires_at:
                return None

            return token_obj
        except cls.DoesNotExist:
            return None

    def blacklist(self):
        self.is_blacklisted = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_blacklisted', 'used_at'])


class AccountActivationToken(models.Model):
    """Stores account activation tokens."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activation_tokens'
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Activation for {self.user.username} - {'Used' if self.is_used else 'Pending'}"

    @classmethod
    def generate_token(cls):
        return secrets.token_urlsafe(32)

    @classmethod
    def hash_token(cls, token):
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_for_user(cls, user):
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)

        expiry_minutes = getattr(settings, 'ACCOUNT_ACTIVATION_TOKEN_EXPIRY_MINUTES', 10)
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        token_obj = cls.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at
        )

        return raw_token, token_obj

    @classmethod
    def validate_token(cls, raw_token):
        token_hash = cls.hash_token(raw_token)

        try:
            token_obj = cls.objects.select_related('user').get(
                token_hash=token_hash,
                is_used=False
            )

            if timezone.now() > token_obj.expires_at:
                return None

            return token_obj
        except cls.DoesNotExist:
            return None

    def mark_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])