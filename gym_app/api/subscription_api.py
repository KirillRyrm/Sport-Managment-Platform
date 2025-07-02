from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import IntegrityError
from ..models import Subscription
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['subscription_id', 'subscription_name', 'price', 'duration_days', 'description']

class SubscriptionListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to access SubscriptionListAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        subscriptions = Subscription.objects.all().values('subscription_id', 'subscription_name', 'price', 'duration_days', 'description')
        logger.debug(f"SubscriptionListAPI accessed by user: {request.user.username}")
        return Response(list(subscriptions))

    def post(self, request):
        if not request.user.has_perm('auth_app.add_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to create subscription without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = SubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                subscription = Subscription.objects.create(**serializer.validated_data)
                logger.info(f"User {request.user.username} created subscription: {subscription.subscription_name}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to create subscription: {str(e)}")
                return Response({"error": "Subscription with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"User {request.user.username} failed to create subscription: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubscriptionDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subscription_id):
        if not request.user.has_perm('auth_app.view_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to access SubscriptionDetailAPI without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            subscription = Subscription.objects.get(subscription_id=subscription_id)
            serializer = SubscriptionSerializer(subscription)
            logger.debug(f"SubscriptionDetailAPI for subscription_id {subscription_id} accessed by user: {request.user.username}")
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to access non-existent subscription_id: {subscription_id}")
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, subscription_id):
        if not request.user.has_perm('auth_app.change_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to update subscription without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            subscription = Subscription.objects.get(subscription_id=subscription_id)
            serializer = SubscriptionSerializer(subscription, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.username} updated subscription: {subscription.subscription_name}")
                return Response(serializer.data)
            logger.warning(f"User {request.user.username} failed to update subscription: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Subscription.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to update non-existent subscription_id: {subscription_id}")
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, subscription_id):
        if not request.user.has_perm('auth_app.delete_subscriptions'):
            logger.warning(f"User {request.user.username} attempted to delete subscription without permission")
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        try:
            subscription = Subscription.objects.get(subscription_id=subscription_id)
            subscription_name = subscription.subscription_name
            subscription.delete()
            logger.info(f"User {request.user.username} deleted subscription: {subscription_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            logger.error(f"User {request.user.username} attempted to delete non-existent subscription_id: {subscription_id}")
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)