from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from training_app.models import TrainingType
from .serializers import TrainingTypeSerializer
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class TrainingTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        training_types = TrainingType.objects.all()
        serializer = TrainingTypeSerializer(training_types, many=True)
        logger.debug(
            f"User {request.user.username} viewed training types: {[t.training_type_id for t in training_types]}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_training_type'):
            logger.warning(f"User {request.user.username} attempted to create training type without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TrainingTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} created training type: {serializer.data['title']}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"User {request.user.username} failed to create training type: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingTypeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return TrainingType.objects.get(pk=pk)
        except TrainingType.DoesNotExist:
            logger.error(f"Training type {pk} not found")
            return None

    def get(self, request, pk):
        training_type = self.get_object(pk)
        if not training_type:
            return Response({'error': 'Training type not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TrainingTypeSerializer(training_type)
        logger.debug(f"User {request.user.username} viewed training type: {pk}")
        return Response(serializer.data)

    def put(self, request, pk):
        if not request.user.has_perm('auth_app.change_training_type'):
            logger.warning(f"User {request.user.username} attempted to update training type {pk} without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        training_type = self.get_object(pk)
        if not training_type:
            return Response({'error': 'Training type not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TrainingTypeSerializer(training_type, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated training type: {pk}")
            return Response(serializer.data)
        logger.warning(f"User {request.user.username} failed to update training type {pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.has_perm('auth_app.delete_training_type'):
            logger.warning(f"User {request.user.username} attempted to delete training type {pk} without permission")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        training_type = self.get_object(pk)
        if not training_type:
            return Response({'error': 'Training type not found'}, status=status.HTTP_404_NOT_FOUND)

        training_type.delete()
        logger.info(f"User {request.user.username} deleted training type: {pk}")
        return Response(status=status.HTTP_204_NO_CONTENT)