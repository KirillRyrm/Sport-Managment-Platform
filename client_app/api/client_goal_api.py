from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import ClientGoal, Client
from gym_app.models import Goal
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class ClientGoalSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    goal = serializers.PrimaryKeyRelatedField(queryset=Goal.objects.all())

    class Meta:
        model = ClientGoal
        fields = ['client_goal_id', 'assigned_at', 'is_achieved', 'description', 'user', 'goal']

class ClientGoalListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_client_goals'):
            logger.warning(f"User {request.user.username} attempted to access ClientGoalListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        goals = ClientGoal.objects.all()
        serializer = ClientGoalSerializer(goals, many=True)
        logger.debug(f"ClientGoalListAPI accessed by user: {request.user.username}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_client_goals'):
            logger.warning(f"User {request.user.username} attempted to create goal without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClientGoalSerializer(data=request.data)
        if serializer.is_valid():
            try:
                goal = ClientGoal.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created goal: {goal.client_goal_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create goal: {str(e)}")
                return Response({"error": "Goal for this user and assigned date already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create goal: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientGoalDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_goal_id):
        if not request.user.has_perm('auth_app.view_client_goals'):
            logger.warning(f"User {request.user.username} attempted to access ClientGoalDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            goal = ClientGoal.objects.get(client_goal_id=client_goal_id)
            serializer = ClientGoalSerializer(goal)
            logger.debug(f"ClientGoalDetailAPI for client_goal_id {client_goal_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except ClientGoal.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent client_goal_id: {client_goal_id}")
            return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, client_goal_id):
        if not request.user.has_perm('auth_app.change_client_goals'):
            logger.warning(f"User {request.user.username} attempted to update goal without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            goal = ClientGoal.objects.get(client_goal_id=client_goal_id)
            serializer = ClientGoalSerializer(goal, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated goal: {goal.client_goal_id}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update goal: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ClientGoal.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent client_goal_id: {client_goal_id}")
            return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, client_goal_id):
        if not request.user.has_perm('auth_app.delete_client_goals'):
            logger.warning(f"User {request.user.username} attempted to delete goal without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            goal = ClientGoal.objects.get(client_goal_id=client_goal_id)
            goal_id = goal.client_goal_id
            goal.delete()
            logger.info(f"User {request.user.username} deleted goal: {goal_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClientGoal.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent client_goal_id: {client_goal_id}")
            return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)