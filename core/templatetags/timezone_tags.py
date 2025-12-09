from django import template
from django.utils import timezone
import pytz

register = template.Library()

@register.filter
def user_timezone(value, user):
    """Convert datetime to user's timezone"""
    if not value or not hasattr(user, 'timezone'):
        return value

    try:
        user_tz = pytz.timezone(user.timezone)
        return timezone.localtime(value, user_tz)
    except:
        return value