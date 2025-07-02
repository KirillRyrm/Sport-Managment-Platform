from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import Goal
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['goal_id', 'goal_name', 'description']

class GoalListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_goals'):
            logger.warning(f"User {request.user.username} attempted to access GoalListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        goals = Goal.objects.all().values('goal_id', 'goal_name', 'description')
        logger.debug(f"GoalListAPI accessed by user: {request.user.username}")
        return Response(list(goals))

    def post(self, request):
        if not request.user.has_perm('auth_app.add_goals'):
            logger.warning(f"User {request.user.username} attempted to create goal without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = GoalSerializer(data=request.data)
        if serializer.is_valid():
            try:
                goal = Goal.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created goal: {goal.goal_name}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create goal: {str(e)}")
                return Response({"error": "Goal with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create goal: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GoalDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, goal_id):
        if not request.user.has_perm('auth_app.view_goals'):
            logger.warning(f"User {request.user.username} attempted to access GoalDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            goal = Goal.objects.get(goal_id=goal_id)
            serializer = GoalSerializer(goal)
            logger.debug(f"GoalDetailAPI for goal_id {goal_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except Goal.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent goal_id: {goal_id}")
            return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, goal_id):
        if not request.user.has_perm('auth_app.change_goals'):
            logger.warning(f"User {request.user.username} attempted to update goal without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            goal = Goal.objects.get(goal_id=goal_id)
            serializer = GoalSerializer(goal, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated goal: {goal.goal_name}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update goal: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Goal.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent goal_id: {goal_id}")
            return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, goal_id):
        if not request.user.has_perm('auth_app.delete_goals'):
            logger.warning(f"User {request.user.username} attempted to delete goal without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            goal = Goal.objects.get(goal_id=goal_id)
            goal_name = goal.goal_name
            goal.delete()
            logger.info(f"User {request.user.username} deleted goal: {goal_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Goal.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent goal_id: {goal_id}")
            return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)