from celery import shared_task
from django.conf import settings
import resend

resend.api_key = settings.EMAIL_API_KEY


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_verification_email(self, user_id, token):
    from .models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    verify_link = f"{settings.FRONTEND_VERIFY_URL}/{token}/"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Verify your email</h2>
        <p>Hi {user.first_name},</p>
        <p>Click the button below to verify your email address. This link expires in 24 hours.</p>
        <p style="text-align: center; margin: 32px 0;">
            <a href="{verify_link}"
               style="background:#4f46e5;color:#fff;padding:12px 24px;
                      border-radius:6px;text-decoration:none;font-weight:bold;">
                Verify Email
            </a>
        </p>
        <p style="color:#888;font-size:12px;">
            If the button doesn't work, copy this link into your browser:<br>{verify_link}
        </p>
    </div>
    """

    params = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [user.email],
        "subject": "Verify your email",
        "html": html_body,
    }

    try:
        result = resend.Emails.send(params)
        return result.get("id")
    except Exception as exc:
        raise self.retry(exc=exc)
    