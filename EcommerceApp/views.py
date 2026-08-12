from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import User, EmailVerificationToken
from .serializers import SignUpSerializer, LoginDeserializer
from .services  import _resend_verification, _create_and_send_token

class SignupThrottle(AnonRateThrottle):
    scope = 'signup'
    rate = '5/hour'
    
@api_view(['POST'])
@throttle_classes([SignupThrottle])
def signup(request):

    # Same response regardless of outcome  prevents email enumeration.
    generic_response = Response(
        {"message": "User has been created, verify email address"},
        status=201
    )

    

    serializer = SignUpSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    # If one fails everything fails
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

@api_view(['POST'])
def login(request):
    deserializer= LoginDeserializer(data=request.data)
    if not deserializer.is_valid():
        return Response(deserializer.errors, status= 400)

    email = deserializer.validated_data["email"]
    password = deserializer.validated_data["password"]
    existing_user = User.objects.filter(email=email).first()
    email_verification = EmailVerificationToken.objects.filter(user_id=existing_user.id).first()
    if existing_user:
            if not existing_user.email_verified:
                if timezone.now() < email_verification.expires_at:
                    return Response({"message": "Verify your email, a mail was sent to your email"}, status= 200)
                else:
                    if email_verification:
                        email_verification.delete()
                    _resend_verification(existing_user)
                    return Response({"message": "Verify your email, a mail has been sent to your email"}, status= 200)

            if not existing_user.check_password(password):
                return Response({"message": "Invalid Credentials"}, status= 401)
        
            return Response({"message": "Login Successful"}, status= 200)
            
    else:
        return Response({"message": "User doesn't exist. SignUp"}, status= 401)