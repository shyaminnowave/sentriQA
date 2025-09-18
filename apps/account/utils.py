import string
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


def generate_user():
    try:
        letters = string.ascii_letters
    except AttributeError:
        letters = string.letters
    allowed_char = letters + string.digits + '_'
    username = get_random_string(length=15, allowed_chars=allowed_char)
    try:
        User.objects.get(username=username)
        return generate_user()
    except User.DoesNotExist:
        return username


def get_token_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }

