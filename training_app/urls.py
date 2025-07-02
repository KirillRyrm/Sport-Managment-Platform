from django.urls import path
from .api import trainer_api, training_type_api, training_session_api
from . import views
#from client_app.views import add_client_progress

urlpatterns = [
    path('training_types/', views.training_type_list, name='training_type_list'),
    path('training_types/add/', views.add_training_type, name='add_training_type'),
    path('training_types/edit/<int:training_type_id>/', views.edit_training_type, name='edit_training_type'),
    path('training_types/delete/<int:training_type_id>/', views.delete_training_type, name='delete_training_type'),


    path('trainer_profile/', views.trainer_profile, name='trainer_profile'),
    path('trainers/', views.trainers_list, name='trainers_list'),
    path('trainers/delete_trainer/<int:trainer_id>/', views.delete_trainer, name='delete_trainer'),

    path('training_sessions/', views.training_sessions, name='training_sessions'),
    path('training_sessions/add/', views.add_training_session, name='add_training_session'),
    path('training_sessions/edit/<int:session_id>/', views.edit_training_session, name='edit_training_session'),
    path('training_sessions/delete/<int:session_id>/', views.delete_training_session, name='delete_training_session'),


    path('training_sessions/<int:session_id>/registrations/', views.view_session_registrations, name='view_session_registrations'),
    path('my_client_progress/', views.my_client_progress, name='my_client_progress'),
    path('training_sessions/progress/edit/<int:progress_id>/', views.edit_client_progress, name='edit_client_progress'),
    path('training_sessions/progress/delete/<int:progress_id>/', views.delete_client_progress, name='delete_client_progress'),



    path('api/training_types/', training_type_api.TrainingTypeListView.as_view(), name='api_training_type_list'),
    path('api/training_types/<int:pk>/', training_type_api.TrainingTypeDetailView.as_view(), name='api_training_type_detail'),
    path('api/trainers/', trainer_api.TrainersListView.as_view(), name='api_trainer_list'),
    path('api/trainers/<int:pk>/', trainer_api.TrainersDetailView.as_view(), name='api_trainer_detail'),
    path('api/training_sessions/', training_session_api.TrainingSessionsListView.as_view(), name='api_training_session_list'),
    path('api/training_sessions/<int:pk>/', training_session_api.TrainingSessionsDetailView.as_view(), name='api_training_session_detail'),

    path('analytics/', views.analytics_page, name='analytics'),
    path('analytics/client_attendance/', views.client_attendance, name='client_attendance'),
    path('analytics/training_type_ranking/', views.training_type_ranking, name='training_type_ranking'),
    path('analytics/location_ranking/', views.location_ranking, name='location_ranking'),

]
