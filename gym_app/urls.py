from django.urls import path
from . import views
from .api import gym_api, equipment_api, location_api, gym_equipment_api, subscription_api, goal_api

urlpatterns = [
   #path('login/', views.auth_login, name='auth_login'),
   path('gym_list/', views.gym_list, name='gym_list'),
   path('gym_list/add/', views.add_gym, name='add_gym'),
   path('gym_list/edit/<int:gym_id>/', views.edit_gym, name='edit_gym'),
   path('gym_list/delete/<int:gym_id>/', views.delete_gym, name='delete_gym'),
   path('api/gym_list/', views.GymListAPI.as_view(), name='gym_list_api'),
   path('api/gym_list/<int:gym_id>/', gym_api.GymDetailAPI.as_view(), name='gym_detail_api'),

   path('equipment/', views.equipment_list, name='equipment_list'),
   path('equipment/add/', views.add_equipment, name='add_equipment'),
   path('equipment/edit/<int:equipment_id>/', views.edit_equipment, name='edit_equipment'),
   path('equipment/delete/<int:equipment_id>/', views.delete_equipment, name='delete_equipment'),
   path('api/equipment/', views.EquipmentListAPI.as_view(), name='equipment_list_api'),
   path('api/equipment/<int:equipment_id>/', equipment_api.EquipmentDetailAPI.as_view(), name='equipment_detail_api'),

   path('gym_list/<int:gym_id>/locations/', views.location_list, name='location_list'),
   path('gym_list/<int:gym_id>/locations/add/', views.add_location, name='add_location'),
   path('gym_list/<int:gym_id>/locations/edit/<int:location_id>/', views.edit_location, name='edit_location'),
   path('gym_list/<int:gym_id>/locations/delete/<int:location_id>/', views.delete_location, name='delete_location'),
   path('api/locations/', location_api.GymLocationListAPI.as_view(), name='location_list_api'),
   path('api/locations/<int:location_id>/', location_api.GymLocationDetailAPI.as_view(), name='location_detail_api'),
   path('api/gym_list/<int:gym_id>/locations/', location_api.GymLocationListAPI.as_view(), name='gym_location_list_api'),

   path('gym_list/<int:gym_id>/locations/<int:location_id>/equipment/add/', views.add_gym_equipment, name='add_gym_equipment'),
   path('gym_list/<int:gym_id>/locations/<int:location_id>/equipment/edit/<int:gym_equipment_id>/', views.edit_gym_equipment, name='edit_gym_equipment'),
   path('gym_list/<int:gym_id>/locations/<int:location_id>/equipment/delete/<int:gym_equipment_id>/', views.delete_gym_equipment, name='delete_gym_equipment'),
   path('api/gym_equipment/', gym_equipment_api.GymEquipmentListAPI.as_view(), name='gym_equipment_list_api'),
   path('api/gym_equipment/<int:gym_equipment_id>/', gym_equipment_api.GymEquipmentDetailAPI.as_view(), name='gym_equipment_detail_api'),
   path('api/locations/<int:location_id>/gym_equipment/', gym_equipment_api.GymEquipmentListAPI.as_view(), name='location_gym_equipment_list_api'),


   path('subscriptions/', views.subscription_list, name='subscription_list'),
   path('subscriptions/add/', views.add_subscription, name='add_subscription'),
   path('subscriptions/edit/<int:subscription_id>/', views.edit_subscription, name='edit_subscription'),
   path('subscriptions/delete/<int:subscription_id>/', views.delete_subscription, name='delete_subscription'),
   path('api/subscriptions/', subscription_api.SubscriptionListAPI.as_view(), name='subscription_list_api'),
   path('api/subscriptions/<int:subscription_id>/', subscription_api.SubscriptionDetailAPI.as_view(), name='subscription_detail_api'),

   path('goals/', views.goal_list, name='goal_list'),
   path('goals/add/', views.add_goal, name='add_goal'),
   path('goals/edit/<int:goal_id>/', views.edit_goal, name='edit_goal'),
   path('goals/delete/<int:goal_id>/', views.delete_goal, name='delete_goal'),
   path('api/goals/', goal_api.GoalListAPI.as_view(), name='goal_list_api'),
   path('api/goals/<int:goal_id>/', goal_api.GoalDetailAPI.as_view(), name='goal_detail_api'),


]
