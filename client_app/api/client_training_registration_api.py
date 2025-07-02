from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import ClientTrainingRegistration, Client
from training_app.models import TrainingSessions
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class ClientTrainingRegistrationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    session = serializers.PrimaryKeyRelatedField(queryset=TrainingSessions.objects.all())

    class Meta:
        model = ClientTrainingRegistration
        fields = ['registration_id', 'user', 'session']

class ClientTrainingRegistrationListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_client_training_registrations'):
            logger.warning(f"User {request.user.username} attempted to access ClientTrainingRegistrationListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        registrations = ClientTrainingRegistration.objects.all()
        serializer = ClientTrainingRegistrationSerializer(registrations, many=True)
        logger.debug(f"ClientTrainingRegistrationListAPI accessed by user: {request.user.username}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_client_training_registrations'):
            logger.warning(f"User {request.user.username} attempted to create registration without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClientTrainingRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                registration = ClientTrainingRegistration.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created registration: {registration.registration_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create registration: {str(e)}")
                return Response({"error": "Registration for this user and session already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create registration: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientTrainingRegistrationDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, registration_id):
        if not request.user.has_perm('auth_app.view_client_training_registrations'):
            logger.warning(f"User {request.user.username} attempted to access ClientTrainingRegistrationDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            registration = ClientTrainingRegistration.objects.get(registration_id=registration_id)
            serializer = ClientTrainingRegistrationSerializer(registration)
            logger.debug(f"ClientTrainingRegistrationDetailAPI for registration_id {registration_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except ClientTrainingRegistration.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent registration_id: {registration_id}")
            return Response({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, registration_id):
        if not request.user.has_perm('auth_app.change_client_training_registrations'):
            logger.warning(f"User {request.user.username} attempted to update registration without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            registration = ClientTrainingRegistration.objects.get(registration_id=registration_id)
            serializer = ClientTrainingRegistrationSerializer(registration, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated registration: {registration.registration_id}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update registration: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ClientTrainingRegistration.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent registration_id: {registration_id}")
            return Response({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, registration_id):
        if not request.user.has_perm('auth_app.delete_client_training_registrations'):
            logger.warning(f"User {request.user.username} attempted to delete registration without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            registration = ClientTrainingRegistration.objects.get(registration_id=registration_id)
            registration_id = registration.registration_id
            registration.delete()
            logger.info(f"User {request.user.username} deleted registration: {registration_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClientTrainingRegistration.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent registration_id: {registration_id}")
            return Response({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)