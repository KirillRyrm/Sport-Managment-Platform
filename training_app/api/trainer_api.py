from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from training_app.models import Trainers
from .serializers import TrainersSerializer
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class TrainersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trainers = Trainers.objects.all()
        serializer = TrainersSerializer(trainers, many=True)
        logger.debug(f"User {request.user.username} viewed trainers: {[t.trainer_id for t in trainers]}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_trainers'):
            logger.warning(f"User {request.user.username} attempted to create trainer without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TrainersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} created trainer: {serializer.data['full_name']}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"User {request.user.username} failed to create trainer: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainersDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Trainers.objects.get(pk=pk)
        except Trainers.DoesNotExist:
            logger.error(f"Trainer {pk} not found")
            return None

    def get(self, request, pk):
        trainer = self.get_object(pk)
        if not trainer:
            return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TrainersSerializer(trainer)
        logger.debug(f"User {request.user.username} viewed trainer: {pk}")
        return Response(serializer.data)

    def put(self, request, pk):
        trainer = self.get_object(pk)
        if not trainer:
            return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.has_perm('auth_app.change_trainers'):
            logger.warning(f"User {request.user.username} attempted to update trainer {pk} without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TrainersSerializer(trainer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated trainer: {pk}")
            return Response(serializer.data)
        logger.warning(f"User {request.user.username} failed to update trainer {pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.has_perm('auth_app.delete_trainers'):
            logger.warning(f"User {request.user.username} attempted to delete trainer {pk} without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        trainer = self.get_object(pk)
        if not trainer:
            return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)

        trainer.delete()
        logger.info(f"User {request.user.username} deleted trainer: {pk}")
        return Response(status=status.HTTP_204_NO_CONTENT)