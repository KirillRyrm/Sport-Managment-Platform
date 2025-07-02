from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.decorators import permission_required
from django.db import IntegrityError
from ..models import Gym
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ['gym_id', 'gym_name', 'address', 'phone', 'email']

class GymListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_gyms'):
            logger.warning(f"User {request.user.username} attempted to access GymListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        gyms = Gym.objects.all().values('gym_id', 'gym_name', 'address', 'phone', 'email')
        logger.debug(f"GymListAPI accessed by user: {request.user.username}")
        return Response(list(gyms))

    def post(self, request):
        if not request.user.has_perm('auth_app.add_gyms'):
            logger.warning(f"User {request.user.username} attempted to create gym without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = GymSerializer(data=request.data)
        if serializer.is_valid():
            try:
                gym = Gym.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created gym: {gym.gym_name}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create gym: {str(e)}")
                return Response({"error": "Gym with this name, phone, or email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create gym: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GymDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id):
        if not request.user.has_perm('auth_app.view_gyms'):
            logger.warning(f"User {request.user.username} attempted to access GymDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            gym = Gym.objects.get(gym_id=gym_id)
            serializer = GymSerializer(gym)
            logger.debug(f"GymDetailAPI for gym_id {gym_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except Gym.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent gym_id: {gym_id}")
            return Response({"error": "Gym not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, gym_id):
        if not request.user.has_perm('auth_app.change_gyms'):
            logger.warning(f"User {request.user.username} attempted to update gym without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            gym = Gym.objects.get(gym_id=gym_id)
            serializer = GymSerializer(gym, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated gym: {gym.gym_name}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update gym: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Gym.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent gym_id: {gym_id}")
            return Response({"error": "Gym not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, gym_id):
        if not request.user.has_perm('auth_app.delete_gyms'):
            logger.warning(f"User {request.user.username} attempted to delete gym without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            gym = Gym.objects.get(gym_id=gym_id)
            gym_name = gym.gym_name
            gym.delete()
            logger.info(f"User {request.user.username} deleted gym: {gym_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Gym.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent gym_id: {gym_id}")
            return Response({"error": "Gym not found"}, status=status.HTTP_404_NOT_FOUND)