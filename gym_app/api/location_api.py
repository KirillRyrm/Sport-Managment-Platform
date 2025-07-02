from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import GymLocation, Gym
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class GymLocationSerializer(serializers.ModelSerializer):
    gym_id = serializers.PrimaryKeyRelatedField(queryset=Gym.objects.all(), source='gym')

    class Meta:
        model = GymLocation
        fields = ['location_id', 'location_name', 'capacity', 'gym_id']

class GymLocationListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id=None):
        if not request.user.has_perm('auth_app.view_gym_locations'):
            logger.warning(f"User {request.user.username} attempted to access GymLocationListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        if gym_id:
            locations = GymLocation.objects.filter(gym_id=gym_id)
        else:
            locations = GymLocation.objects.all()
        serializer = GymLocationSerializer(locations, many=True)
        logger.debug(f"GymLocationListAPI accessed by user: {request.user.username}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_gym_locations'):
            logger.warning(f"User {request.user.username} attempted to create location without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = GymLocationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                location = GymLocation.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created location: {location.location_name}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create location: {str(e)}")
                return Response({"error": "Location with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create location: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GymLocationDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, location_id):
        if not request.user.has_perm('auth_app.view_gym_locations'):
            logger.warning(f"User {request.user.username} attempted to access GymLocationDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            location = GymLocation.objects.get(location_id=location_id)
            serializer = GymLocationSerializer(location)
            logger.debug(f"GymLocationDetailAPI for location_id {location_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except GymLocation.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent location_id: {location_id}")
            return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, location_id):
        if not request.user.has_perm('auth_app.change_gym_locations'):
            logger.warning(f"User {request.user.username} attempted to update location without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            location = GymLocation.objects.get(location_id=location_id)
            serializer = GymLocationSerializer(location, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated location: {location.location_name}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update location: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except GymLocation.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent location_id: {location_id}")
            return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, location_id):
        if not request.user.has_perm('auth_app.delete_gym_locations'):
            logger.warning(f"User {request.user.username} attempted to delete location without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            location = GymLocation.objects.get(location_id=location_id)
            location_name = location.location_name
            location.delete()
            logger.info(f"User {request.user.username} deleted location: {location_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except GymLocation.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent location_id: {location_id}")
            return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)