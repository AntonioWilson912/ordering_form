from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
import pytz
import secrets
import hashlib
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


class PasswordResetToken(models.Model):
    """
    Stores password reset tokens with expiration and blacklist functionality.
    """
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
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(32)

    @classmethod
    def hash_token(cls, token):
        """Hash the token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_for_user(cls, user, request=None):
        """Create a new password reset token for a user"""
        # Invalidate any existing unused tokens
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
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @classmethod
    def validate_token(cls, raw_token):
        """
        Validate a token and return the token object if valid.
        Returns None if invalid, expired, or blacklisted.
        """
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
        """Blacklist this token so it can never be used again"""
        self.is_blacklisted = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_blacklisted', 'used_at'])


class AccountActivationToken(models.Model):
    """
    Stores account activation tokens.
    """
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
        """Create a new activation token for a user"""
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)

        # Use minutes like password reset
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
        """Validate an activation token"""
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
        """Mark this token as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])