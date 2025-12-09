from django.contrib.auth.models import AbstractUser
from django.db import models
import pytz

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]

class User(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    email = models.EmailField(unique=True)
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='America/New_York',
        help_text='User timezone for displaying dates'
    )

    # Add any additional fields here
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username