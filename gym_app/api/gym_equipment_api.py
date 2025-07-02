from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import GymEquipment, Equipment, GymLocation
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class GymEquipmentSerializer(serializers.ModelSerializer):
    equipment_id = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all(), source='equipment')
    location_id = serializers.PrimaryKeyRelatedField(queryset=GymLocation.objects.all(), source='location')

    class Meta:
        model = GymEquipment
        fields = ['gym_equipment_id', 'equipment_id', 'location_id', 'quantity']

class GymEquipmentListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, location_id=None):
        if not request.user.has_perm('auth_app.view_gym_equipment'):
            logger.warning(f"User {request.user.username} attempted to access GymEquipmentListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        if location_id:
            equipment = GymEquipment.objects.filter(location_id=location_id)
        else:
            equipment = GymEquipment.objects.all()
        serializer = GymEquipmentSerializer(equipment, many=True)
        logger.debug(f"GymEquipmentListAPI accessed by user: {request.user.username}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_gym_equipment'):
            logger.warning(f"User {request.user.username} attempted to create gym equipment without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = GymEquipmentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                gym_equipment = GymEquipment.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created gym equipment: {gym_equipment.equipment.equipment_name}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create gym equipment: {str(e)}")
                return Response({"error": "Equipment already exists in this location"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create gym equipment: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GymEquipmentDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_equipment_id):
        if not request.user.has_perm('auth_app.view_gym_equipment'):
            logger.warning(f"User {request.user.username} attempted to access GymEquipmentDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            gym_equipment = GymEquipment.objects.get(gym_equipment_id=gym_equipment_id)
            serializer = GymEquipmentSerializer(gym_equipment)
            logger.debug(f"GymEquipmentDetailAPI for gym_equipment_id {gym_equipment_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except GymEquipment.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent gym_equipment_id: {gym_equipment_id}")
            return Response({"error": "Gym equipment not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, gym_equipment_id):
        if not request.user.has_perm('auth_app.change_gym_equipment'):
            logger.warning(f"User {request.user.username} attempted to update gym equipment without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            gym_equipment = GymEquipment.objects.get(gym_equipment_id=gym_equipment_id)
            serializer = GymEquipmentSerializer(gym_equipment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated gym equipment: {gym_equipment.equipment.equipment_name}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update gym equipment: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except GymEquipment.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent gym_equipment_id: {gym_equipment_id}")
            return Response({"error": "Gym equipment not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, gym_equipment_id):
        if not request.user.has_perm('auth_app.delete_gym_equipment'):
            logger.warning(f"User {request.user.username} attempted to delete gym equipment without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            gym_equipment = GymEquipment.objects.get(gym_equipment_id=gym_equipment_id)
            equipment_name = gym_equipment.equipment.equipment_name
            gym_equipment.delete()
            logger.info(f"User {request.user.username} deleted gym equipment: {equipment_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except GymEquipment.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent gym_equipment_id: {gym_equipment_id}")
            return Response({"error": "Gym equipment not found"}, status=status.HTTP_404_NOT_FOUND)