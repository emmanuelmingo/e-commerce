from rest_framework import serializers
from .models import User

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length= 8)
    class Meta:
        model = User
        fields = ['email','first_name', 'last_name', 'password']
        extra_kwargs = {
            'password':{'min_length': 8}
        }

    def create(self, validated_data):
        # create_user() hashes the password for you
        return User.objects.create_user(**validated_data)

class LoginDeserializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
        