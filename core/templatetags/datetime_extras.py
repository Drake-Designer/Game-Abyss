from django import template

register = template.Library()


@register.filter
def rfc3339_seconds(value):
    """
    Return datetime in RFC3339/ISO8601 without fractional seconds.
    Example: 2025-10-29T15:12:44+00:00
    """
    if not value:
        return ""
    # Usa timespec='seconds' per togliere i microsecondi
    try:
        return value.isoformat(timespec="seconds")
    except TypeError:
        # Fallback se necessario
        return value.strftime("%Y-%m-%dT%H:%M:%S%z").replace("+0000", "+00:00")
