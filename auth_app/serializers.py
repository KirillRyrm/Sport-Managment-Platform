from rest_framework import serializers
from .models import UserCredentials

class UserCredentialsSerializer(serializers.ModelSerializer):
   permissions = serializers.SerializerMethodField()

   class Meta:
       model = UserCredentials
       fields = ['username', 'user_role', 'permissions']

   def get_permissions(self, obj):
       return list(obj.get_all_permissions())