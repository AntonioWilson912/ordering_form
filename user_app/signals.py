from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import User, EmailTemplate
from .services import EmailService


@receiver(post_save, sender=User)
def create_default_template_for_new_user(sender, instance, created, **kwargs):
    """
    When a new user is created, automatically create a default email template.
    This ensures every user has at least one template to work with.
    """
    if created:
        # Check if they don't already have a default template
        if not instance.email_templates.exists():
            EmailTemplate.create_default_template(instance)


@receiver(pre_save, sender=User)
def track_password_changes(sender, instance, **kwargs):
    """
    Detect when a user's password is changed and send them an email notification.
    This only works for password changes through the model, not through set_password().
    """
    if instance.pk:  # Only for existing users, not new ones
        try:
            old_instance = User.objects.get(pk=instance.pk)
            # Check if password has changed
            if old_instance.password != instance.password:
                # Mark that password was changed for post_save signal
                instance._password_was_changed = True
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def send_password_change_notification(sender, instance, created, **kwargs):
    """
    Send email notification after password is saved.
    Works in conjunction with pre_save signal above.
    """
    if not created and hasattr(instance, '_password_was_changed'):
        if instance._password_was_changed:
            EmailService.send_password_changed_notification(instance)
            # Clean up the marker
            delattr(instance, '_password_was_changed')


@receiver(user_logged_in)
def update_last_login_timezone(sender, request, user, **kwargs):
    """
    Update user's last login time in their own timezone.
    Could also be used for logging, analytics, etc.
    """
    # You could log this to a separate LoginHistory model
    # or update user preferences based on login patterns
    pass


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log when users log out - useful for security auditing.
    """
    # Could log to a separate audit table
    pass


# Example of custom signal
from django.dispatch import Signal

# Define custom signals
user_activated = Signal()  # No providing_args in Django 3.0+

@receiver(user_activated)
def welcome_activated_user(sender, user, **kwargs):
    """
    Send a welcome email when user activates their account.
    Triggered by custom signal in views.
    """
    # You could send a different welcome email here
    pass