from django.urls import path
from . import views
from .api import client_api, client_training_registration_api, client_subscriptions_api, client_progress_api, client_goal_api, client_feedbacks_api

urlpatterns = [
    path('client_profile/', views.client_profile, name='client_profile'),
    path('clients/', views.clients_list, name='clients_list'),
    path('create_profile/', views.create_profile, name='create_profile'),
    path('clients/delete/<int:user_id>/', views.delete_client, name='delete_client'),


    path('client_subscriptions/', views.client_subscriptions_list, name='client_subscriptions_list'),
    path('client_subscriptions/purchase/', views.purchase_subscription, name='purchase_subscription'),
    path('client_subscriptions/delete/<int:user_subscription_id>/', views.delete_client_subscription, name='delete_client_subscription'),


    path('client_goals/', views.client_goals_list, name='client_goals_list'),
    path('client_goals/add/', views.add_client_goal, name='add_client_goal'),
    path('client_goals/edit/<int:client_goal_id>/', views.edit_client_goal, name='edit_client_goal'),
    path('client_goals/delete/<int:client_goal_id>/', views.delete_client_goal, name='delete_client_goal'),

    path('client_feedbacks/', views.client_feedbacks_list, name='client_feedbacks_list'),
    path('client_feedbacks/add/', views.add_client_feedback, name='add_client_feedback'),
    path('client_feedbacks/edit/<int:feedback_id>/', views.edit_client_feedback, name='edit_client_feedback'),
    path('client_feedbacks/delete/<int:feedback_id>/', views.delete_client_feedback, name='delete_client_feedback'),

    path('assign_trainer/<int:trainer_id>/', views.assign_trainer, name='assign_trainer'),
    path('trainer_feedbacks/', views.trainer_feedbacks, name='trainer_feedbacks'),

    path('client_trainings/', views.client_training_registrations, name='client_trainings'),
    path('register_for_session/<int:session_id>/', views.register_for_session, name='register_for_session'),
    path('cancel_registration/<int:session_id>/', views.cancel_registration, name='cancel_registration'),

    path('training_sessions/<int:session_id>/progress/add/<int:client_id>/', views.add_client_progress, name='add_client_progress'),
    path('progress/', views.client_progress, name='client_progress'),


    # API endpoints
    path('api/clients/', client_api.ClientListAPI.as_view(), name='api_client_list'),
    path('api/clients/<int:user_id>/', client_api.ClientDetailAPI.as_view(), name='api_client_detail'),
    path('api/training_registrations/', client_training_registration_api.ClientTrainingRegistrationListAPI.as_view(), name='api_training_registration_list'),
    path('api/training_registrations/<int:registration_id>/', client_training_registration_api.ClientTrainingRegistrationDetailAPI.as_view(), name='api_training_registration_detail'),
    path('api/subscriptions/', client_subscriptions_api.ClientSubscriptionListAPI.as_view(), name='api_subscription_list'),
    path('api/subscriptions/<int:user_subscription_id>/', client_subscriptions_api.ClientSubscriptionDetailAPI.as_view(), name='api_subscription_detail'),
    path('api/progress/', client_progress_api.ClientProgressListAPI.as_view(), name='api_progress_list'),
    path('api/progress/<int:progress_id>/', client_progress_api.ClientProgressDetailAPI.as_view(), name='api_progress_detail'),
    path('api/goals/', client_goal_api.ClientGoalListAPI.as_view(), name='api_goal_list'),
    path('api/goals/<int:client_goal_id>/', client_goal_api.ClientGoalDetailAPI.as_view(), name='api_goal_detail'),
    path('api/feedbacks/', client_feedbacks_api.ClientFeedbackListAPI.as_view(), name='api_feedback_list'),
    path('api/feedbacks/<int:feedback_id>/', client_feedbacks_api.ClientFeedbackDetailAPI.as_view(), name='api_feedback_detail'),
]