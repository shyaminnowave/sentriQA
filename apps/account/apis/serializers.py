from rest_framework import serializers
from apps.account.models import Account
from apps.account.utils import generate_user



class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True, max_length=100,
                                   write_only=True,
                                   style={
                                       "input_type": "email",
                                   })
    password = serializers.CharField(required=True, max_length=100,
                                     write_only=True,
                                     style={
                                         "input_type": "password",
                                     })


class AccountSerializer(serializers.Serializer):

    email = serializers.EmailField(
        required=True,
        max_length=255,
        style={
            "input_type": "email",
        }
    )
    first_name = serializers.CharField(
        required=True,
        max_length=255,
        style={
            "input_type": "first_name",
        }
    )
    last_name = serializers.CharField(
        required=True,
        max_length=255,
        style={
            "input_type": "last_name",
        }
    )
    password = serializers.CharField(
        required=True,
        max_length=255,
        style={
            "input_type": "password",
        }
    )
    confirm_password = serializers.CharField(
        required=True,
        max_length=255,
        style={
            "input_type": "password",
        }
    )

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError('Passwords must match')
        if Account.objects.filter(email=attrs.get('email')).exists():
            raise serializers.ValidationError('Email already registered')
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = Account.objects.create_user(username=generate_user()
            **validated_data)
        return user