from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import Equipment
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['equipment_id', 'equipment_name', 'description']

class EquipmentListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_equipment'):
            logger.warning(f"User {request.user.username} attempted to access EquipmentListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        equipment = Equipment.objects.all().values('equipment_id', 'equipment_name', 'description')
        logger.debug(f"EquipmentListAPI accessed by user: {request.user.username}")
        return Response(list(equipment))

    def post(self, request):
        if not request.user.has_perm('auth_app.add_equipment'):
            logger.warning(f"User {request.user.username} attempted to create equipment without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = EquipmentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                equipment = Equipment.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created equipment: {equipment.equipment_name}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create equipment: {str(e)}")
                return Response({"error": "Equipment with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create equipment: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EquipmentDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, equipment_id):
        if not request.user.has_perm('auth_app.view_equipment'):
            logger.warning(f"User {request.user.username} attempted to access EquipmentDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
            serializer = EquipmentSerializer(equipment)
            logger.debug(f"EquipmentDetailAPI for equipment_id {equipment_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except Equipment.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent equipment_id: {equipment_id}")
            return Response({"error": "Equipment not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, equipment_id):
        if not request.user.has_perm('auth_app.change_equipment'):
            logger.warning(f"User {request.user.username} attempted to update equipment without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
            serializer = EquipmentSerializer(equipment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated equipment: {equipment.equipment_name}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update equipment: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Equipment.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent equipment_id: {equipment_id}")
            return Response({"error": "Equipment not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, equipment_id):
        if not request.user.has_perm('auth_app.delete_equipment'):
            logger.warning(f"User {request.user.username} attempted to delete equipment without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
            equipment_name = equipment.equipment_name
            equipment.delete()
            logger.info(f"User {request.user.username} deleted equipment: {equipment_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Equipment.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent equipment_id: {equipment_id}")
            return Response({"error": "Equipment not found"}, status=status.HTTP_404_NOT_FOUND)