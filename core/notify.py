"""Notifications: email through Django's backend; SMS only if a backend is plugged in."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils.module_loading import import_string

log = logging.getLogger(__name__)


def send_email(to, subject, body):
    recipients = [to] if isinstance(to, str) else [r for r in to if r]
    if not recipients:
        return 0
    try:
        return send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
    except Exception:  # never break a citizen's request because email failed
        log.exception("Email to %s failed", recipients)
        return 0


def send_sms(phone, message):
    """Off by default. Set SMS_BACKEND to a dotted path of a callable(phone, message)."""
    if not settings.SMS_BACKEND or not phone:
        return False
    try:
        import_string(settings.SMS_BACKEND)(phone, message)
        return True
    except Exception:
        log.exception("SMS to %s failed", phone)
        return False


def console_sms_backend(phone, message):
    """Free stand-in for testing the SMS hook: prints instead of sending."""
    print(f"[SMS to {phone}] {message}")
