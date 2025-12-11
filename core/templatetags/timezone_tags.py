from django import template
from django.utils import timezone
from django.utils.dateformat import format as date_format
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
    user_tz_name = 'America/New_York'  # Default

    if user and hasattr(user, 'timezone') and user.timezone:
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
def format_datetime(value, format_string='M d, Y H:i'):
    """
    Format datetime with a specified format.

    Usage: {{ datetime_value|format_datetime:"F d, Y g:i A" }}
    """
    if not value:
        return ''

    try:
        return date_format(value, format_string)
    except Exception:
        return str(value)


@register.simple_tag
def user_datetime(value, user, format_string='M d, Y H:i'):
    """
    Convert to user timezone and format in one step.

    Usage: {% user_datetime order.date request.user "F d, Y g:i A" %}

    Common format strings:
    - "M d, Y" = "Jan 01, 2024"
    - "F d, Y" = "January 01, 2024"
    - "m/d/Y" = "01/01/2024"
    - "Y-m-d" = "2024-01-01"
    - "g:i A" = "1:30 PM"
    - "H:i" = "13:30"
    - "F d, Y g:i A" = "January 01, 2024 1:30 PM"
    """
    if not value:
        return ''

    try:
        # Get user's timezone
        user_tz_name = 'America/New_York'  # Default

        if user and hasattr(user, 'timezone') and user.timezone:
            user_tz_name = user.timezone

        user_tz = pytz.timezone(user_tz_name)

        # Ensure value is timezone-aware
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_default_timezone())

        # Convert to user's timezone
        converted = timezone.localtime(value, user_tz)

        # Format the datetime
        return date_format(converted, format_string)
    except Exception as e:
        return str(value)


@register.simple_tag
def user_timezone_name(user):
    """
    Get the user's timezone name.

    Usage: {% user_timezone_name request.user %}
    """
    if user and hasattr(user, 'timezone') and user.timezone:
        return user.timezone
    return 'America/New_York'


@register.simple_tag
def current_time_in_user_tz(user, format_string='g:i A'):
    """
    Get the current time in user's timezone.

    Usage: {% current_time_in_user_tz request.user "g:i A" %}
    """
    try:
        user_tz_name = 'America/New_York'

        if user and hasattr(user, 'timezone') and user.timezone:
            user_tz_name = user.timezone

        user_tz = pytz.timezone(user_tz_name)
        now = timezone.localtime(timezone.now(), user_tz)

        return date_format(now, format_string)
    except Exception:
        return ''