from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import User, EmailVerificationToken
from .serializers import UserSerializers

from .services  import _resend_verification, _create_and_send_token

class SignupThrottle(AnonRateThrottle):
    scope = 'signup'
    rate = '5/hour'
    
@api_view(['POST'])
@throttle_classes([SignupThrottle])
def signup(request):
    email = request.data.get('email')
    existing_user = User.objects.filter(email=email).first()

    # Same response regardless of outcome  prevents email enumeration.
    generic_response = Response(
        {"message": "If this email can be used, we've sent instructions to it."},
        status=200
    )

    if existing_user:
        if not existing_user.is_active:
            _resend_verification(existing_user)
        return generic_response

    serializer = UserSerializers(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    with transaction.atomic():
        user = serializer.save()
        _create_and_send_token(user)

    return generic_response


@api_view(['GET'])
def verify_email(request, token):
    try:
        record = EmailVerificationToken.objects.get(token=token)
    except EmailVerificationToken.DoesNotExist:
        return HttpResponse("<h2>Invalid verification link.</h2>", status=400)

    if record.used_at is not None:
        return HttpResponse("<h2>This link has already been used.</h2>", status=400)

    if record.expires_at < timezone.now():
        return HttpResponse("<h2>This link has expired.</h2>", status=400)

    user = record.user
    user.is_active = True
    user.email_verified = True
    user.save()

    record.used_at = timezone.now()
    record.save()

    return HttpResponse("<h2>Your email has been verified. You can now log in.</h2>", status=200)