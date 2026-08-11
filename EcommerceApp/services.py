import secrets

from datetime import timedelta
from django.utils import timezone

from .tasks import send_verification_email
from .models import EmailVerificationToken

def _create_and_send_token(user):
    """Issue a fresh verification token and queue the email."""
    token = secrets.token_urlsafe(32)
    EmailVerificationToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=24)
    )
    send_verification_email.delay(str(user.id), token)


def _resend_verification(user):
    """Invalidate old unused tokens, then issue a new one."""
    EmailVerificationToken.objects.filter(
        user=user, used_at__isnull=True
    ).update(used_at=timezone.now())
    _create_and_send_token(user)