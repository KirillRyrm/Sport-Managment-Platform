from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.home, name='home'),            # Головна сторінка
    path('register/', views.register, name='register'),  # Реєстрація
    path('login/', views.login_view, name='login'),      # Логін
    path('logout/', views.logout_view, name='logout'),   # Логаут
    #path('home/', views.home, name='home'),
    #path('gyms/', RedirectView.as_view(url='http://127.0.0.1:8000/gyms', permanent=False), name='gym_redirect'),

    #path('gyms/<path:path>', RedirectView.as_view(url='http://127.0.0.1:8001/%(path)s', permanent=False), name='gym_redirect'),

    # API-ендпоінти
    path('auth/api/register/', views.api_register, name='api_register'),
    #path('api/login/', views.api_login, name='api_login'),
    path('auth/api/user-info/', views.api_user_info, name='api_user_info'),
    path('auth/api/check-user/', views.api_check_user, name='api_check_user'),
    path('auth/api/login/', views.LoginView.as_view(), name='api_login'),
    path('auth/api/user/permissions/', views.UserPermissionsView.as_view(), name='user_permissions'),
]