from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import UserCredentials

class UserCredentialsBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserCredentials.objects.get(username=username)
            if check_password(password, user.password):
                return user
        except UserCredentials.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return UserCredentials.objects.get(pk=user_id)
        except UserCredentials.DoesNotExist:
            return None