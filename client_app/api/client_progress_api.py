from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import ClientProgress, Client
from training_app.models import TrainingSessions
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class ClientProgressSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    session = serializers.PrimaryKeyRelatedField(queryset=TrainingSessions.objects.all())

    class Meta:
        model = ClientProgress
        fields = ['progress_id', 'result', 'feedback', 'user', 'session']

class ClientProgressListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_client_progress'):
            logger.warning(f"User {request.user.username} attempted to access ClientProgressListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        progress = ClientProgress.objects.all()
        serializer = ClientProgressSerializer(progress, many=True)
        logger.debug(f"ClientProgressListAPI accessed by user: {request.user.username}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_client_progress'):
            logger.warning(f"User {request.user.username} attempted to create progress without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClientProgressSerializer(data=request.data)
        if serializer.is_valid():
            try:
                progress = ClientProgress.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created progress: {progress.progress_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create progress: {str(e)}")
                return Response({"error": "Progress for this user and session already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create progress: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientProgressDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, progress_id):
        if not request.user.has_perm('auth_app.view_client_progress'):
            logger.warning(f"User {request.user.username} attempted to access ClientProgressDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            progress = ClientProgress.objects.get(progress_id=progress_id)
            serializer = ClientProgressSerializer(progress)
            logger.debug(f"ClientProgressDetailAPI for progress_id {progress_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except ClientProgress.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent progress_id: {progress_id}")
            return Response({"error": "Progress not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, progress_id):
        if not request.user.has_perm('auth_app.change_client_progress'):
            logger.warning(f"User {request.user.username} attempted to update progress without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            progress = ClientProgress.objects.get(progress_id=progress_id)
            serializer = ClientProgressSerializer(progress, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated progress: {progress.progress_id}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update progress: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ClientProgress.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent progress_id: {progress_id}")
            return Response({"error": "Progress not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, progress_id):
        if not request.user.has_perm('auth_app.delete_client_progress'):
            logger.warning(f"User {request.user.username} attempted to delete progress without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            progress = ClientProgress.objects.get(progress_id=progress_id)
            progress_id = progress.progress_id
            progress.delete()
            logger.info(f"User {request.user.username} deleted progress: {progress_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClientProgress.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent progress_id: {progress_id}")
            return Response({"error": "Progress not found"}, status=status.HTTP_404_NOT_FOUND)