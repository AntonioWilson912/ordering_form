from django import template
from django.utils import timezone
import pytz

register = template.Library()


@register.filter
def user_timezone(value, user):
    """
    Convert datetime to user's timezone.

    Usage: {{ datetime_value|user_timezone:request.user }}
    """
    if not value:
        return value

    # Get user's timezone
    user_tz_name = "America/New_York"  # Default

    if user and hasattr(user, "timezone") and user.timezone:
        user_tz_name = user.timezone

    try:
        user_tz = pytz.timezone(user_tz_name)

        # Ensure value is timezone-aware
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_default_timezone())

        return timezone.localtime(value, user_tz)
    except Exception:
        return value


@register.filter
def format_datetime(value, format_string="M d, Y H:i"):
    """
    Format datetime with a specified format.

    Usage: {{ datetime_value|format_datetime:"F d, Y g:i A" }}
    """
    if not value:
        return ""

    try:
        from django.utils.dateformat import format

        return format(value, format_string)
    except Exception:
        return str(value)


@register.simple_tag
def user_datetime(value, user, format_string="M d, Y H:i"):
    """
    Convert to user timezone and format in one step.

    Usage: {% user_datetime order.date request.user "F d, Y g:i A" %}
    """
    if not value:
        return ""

    # Apply timezone conversion
    converted = user_timezone(value, user)

    # Apply formatting
    return format_datetime(converted, format_string)
