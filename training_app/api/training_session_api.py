from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from training_app.models import TrainingSessions, Trainers
from .serializers import TrainingSessionsSerializer

from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class TrainingSessionsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = TrainingSessions.objects.all()
        serializer = TrainingSessionsSerializer(sessions, many=True)
        logger.debug(f"User {request.user.username} viewed training sessions: {[s.session_id for s in sessions]}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('training_app.add_training_session'):
            logger.warning(f"User {request.user.username} attempted to create training session without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TrainingSessionsSerializer(data=request.data)
        if serializer.is_valid():
            try:
                trainer = Trainers.objects.get(user_credential=request.user)
                serializer.save(trainer=trainer)
                logger.info(f"User {request.user.username} created training session: {serializer.data['session_id']}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Trainers.DoesNotExist:
                logger.error(f"User {request.user.username} has no trainer profile")
                return Response({'error': 'Trainer profile not found'}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create training session: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingSessionsDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return TrainingSessions.objects.get(pk=pk)
        except TrainingSessions.DoesNotExist:
            logger.error(f"Training session {pk} not found")
            return None

    def get(self, request, pk):
        session = self.get_object(pk)
        if not session:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TrainingSessionsSerializer(session)
        logger.debug(f"User {request.user.username} viewed training session: {pk}")
        return Response(serializer.data)

    def put(self, request, pk):
        session = self.get_object(pk)
        if not session:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.has_perm('auth_app.change_training_sessions'):
            logger.warning(f"User {request.user.username} attempted to update training session {pk} without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TrainingSessionsSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated training session: {pk}")
            return Response(serializer.data)
        logger.warning(f"User {request.user.username} failed to update training session {pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        session = self.get_object(pk)
        if not session:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.has_perm('auth_app.delete_training_sessions'):
            logger.warning(f"User {request.user.username} attempted to delete training session {pk} without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        session.delete()
        logger.info(f"User {request.user.username} deleted training session: {pk}")
        return Response(status=status.HTTP_204_NO_CONTENT)