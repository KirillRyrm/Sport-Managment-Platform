from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import Client
from auth_app.models import UserCredentials
from training_app.models import Trainers
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class ClientSerializer(serializers.ModelSerializer):
    user_credential = serializers.PrimaryKeyRelatedField(queryset=UserCredentials.objects.all())
    trainer = serializers.PrimaryKeyRelatedField(queryset=Trainers.objects.all(), allow_null=True)

    class Meta:
        model = Client
        fields = ['user_id', 'first_name', 'last_name', 'email', 'phone', 'birth', 'gender', 'balance', 'created_at', 'updated_at', 'user_credential', 'trainer']

class ClientListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_clients'):
            logger.warning(f"User {request.user.username} attempted to access ClientListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        clients = Client.objects.all()
        serializer = ClientSerializer(clients, many=True)
        logger.debug(f"ClientListAPI accessed by user: {request.user.username}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_clients'):
            logger.warning(f"User {request.user.username} attempted to create client without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            try:
                client = Client.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created client: {client.first_name} {client.last_name}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create client: {str(e)}")
                return Response({"error": "Client with this email or phone already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create client: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if not request.user.has_perm('auth_app.view_clients'):
            logger.warning(f"User {request.user.username} attempted to access ClientDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            client = Client.objects.get(user_id=user_id)
            serializer = ClientSerializer(client)
            logger.debug(f"ClientDetailAPI for user_id {user_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except Client.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent user_id: {user_id}")
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, user_id):
        if not request.user.has_perm('auth_app.change_clients'):
            logger.warning(f"User {request.user.username} attempted to update client without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            client = Client.objects.get(user_id=user_id)
            serializer = ClientSerializer(client, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated client: {client.first_name} {client.last_name}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update client: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Client.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent user_id: {user_id}")
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, user_id):
        if not request.user.has_perm('auth_app.delete_clients'):
            logger.warning(f"User {request.user.username} attempted to delete client without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            client = Client.objects.get(user_id=user_id)
            client_name = f"{client.first_name} {client.last_name}"
            client.delete()
            logger.info(f"User {request.user.username} deleted client: {client_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Client.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent user_id: {user_id}")
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)