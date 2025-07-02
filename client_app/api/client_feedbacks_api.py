from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import ClientFeedback, Client
from training_app.models import Trainers
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class ClientFeedbackSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    trainer = serializers.PrimaryKeyRelatedField(queryset=Trainers.objects.all())

    class Meta:
        model = ClientFeedback
        fields = ['feedback_id', 'title', 'description', 'date', 'rating', 'user', 'trainer']

class ClientFeedbackListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_client_feedbacks'):
            logger.warning(f"User {request.user.username} attempted to access ClientFeedbackListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        feedbacks = ClientFeedback.objects.all()
        serializer = ClientFeedbackSerializer(feedbacks, many=True)
        logger.debug(f"ClientFeedbackListAPI accessed by user: {request.user.username}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_client_feedbacks'):
            logger.warning(f"User {request.user.username} attempted to create feedback without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClientFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            try:
                feedback = ClientFeedback.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created feedback: {feedback.feedback_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create feedback: {str(e)}")
                return Response({"error": "Feedback for this user, trainer, and date already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create feedback: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientFeedbackDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, feedback_id):
        if not request.user.has_perm('auth_app.view_client_feedbacks'):
            logger.warning(f"User {request.user.username} attempted to access ClientFeedbackDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            feedback = ClientFeedback.objects.get(feedback_id=feedback_id)
            serializer = ClientFeedbackSerializer(feedback)
            logger.debug(f"ClientFeedbackDetailAPI for feedback_id {feedback_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except ClientFeedback.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent feedback_id: {feedback_id}")
            return Response({"error": "Feedback not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, feedback_id):
        if not request.user.has_perm('auth_app.change_client_feedbacks'):
            logger.warning(f"User {request.user.username} attempted to update feedback without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            feedback = ClientFeedback.objects.get(feedback_id=feedback_id)
            serializer = ClientFeedbackSerializer(feedback, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated feedback: {feedback.feedback_id}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update feedback: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ClientFeedback.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent feedback_id: {feedback_id}")
            return Response({"error": "Feedback not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, feedback_id):
        if not request.user.has_perm('auth_app.delete_client_feedbacks'):
            logger.warning(f"User {request.user.username} attempted to delete feedback without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            feedback = ClientFeedback.objects.get(feedback_id=feedback_id)
            feedback_id = feedback.feedback_id
            feedback.delete()
            logger.info(f"User {request.user.username} deleted feedback: {feedback_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClientFeedback.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent feedback_id: {feedback_id}")
            return Response({"error": "Feedback not found"}, status=status.HTTP_404_NOT_FOUND)