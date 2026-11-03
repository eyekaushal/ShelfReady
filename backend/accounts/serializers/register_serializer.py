from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates sign-up data and creates the user.

    Django's built-in User doesn't force unique emails, so we check that here.
    """

    email = serializers.EmailField(required=True, max_length=254)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, attrs):
        # Run Django's password rules (too common, too similar to username, all numbers...).
        # We build an unsaved User so the "similar to username/email" rule can compare.
        candidate = User(username=attrs.get("username"), email=attrs.get("email"))
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:  # Django's error type → DRF error under "password"
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        # create_user hashes the password. Never save the raw password.
        return User.objects.create_user(**validated_data)
