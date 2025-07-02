from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import ClientSubscription, Client
from gym_app.models import Subscription
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class ClientSubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    subscription = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.all())

    class Meta:
        model = ClientSubscription
        fields = ['user_subscription_id', 'start_date', 'end_date', 'user', 'subscription']

class ClientSubscriptionListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_client_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to access ClientSubscriptionListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        subscriptions = ClientSubscription.objects.all()
        serializer = ClientSubscriptionSerializer(subscriptions, many=True)
        logger.debug(f"ClientSubscriptionListAPI accessed by user: {request.user.username}")
        return Response(serializer.data)

    def post(self, request):
        if not request.user.has_perm('auth_app.add_client_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to create subscription without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClientSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                subscription = ClientSubscription.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created subscription: {subscription.user_subscription_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create subscription: {str(e)}")
                return Response({"error": "Subscription for this user and start date already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create subscription: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientSubscriptionDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_subscription_id):
        if not request.user.has_perm('auth_app.view_client_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to access ClientSubscriptionDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            subscription = ClientSubscription.objects.get(user_subscription_id=user_subscription_id)
            serializer = ClientSubscriptionSerializer(subscription)
            logger.debug(f"ClientSubscriptionDetailAPI for user_subscription_id {user_subscription_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except ClientSubscription.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent user_subscription_id: {user_subscription_id}")
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, user_subscription_id):
        if not request.user.has_perm('auth_app.change_client_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to update subscription without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            subscription = ClientSubscription.objects.get(user_subscription_id=user_subscription_id)
            serializer = ClientSubscriptionSerializer(subscription, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated subscription: {subscription.user_subscription_id}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update subscription: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ClientSubscription.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent user_subscription_id: {user_subscription_id}")
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, user_subscription_id):
        if not request.user.has_perm('auth_app.delete_client_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to delete subscription without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            subscription = ClientSubscription.objects.get(user_subscription_id=user_subscription_id)
            subscription_id = subscription.user_subscription_id
            subscription.delete()
            logger.info(f"User {request.user.username} deleted subscription: {subscription_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClientSubscription.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent user_subscription_id: {user_subscription_id}")
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)