from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import UserCredentials
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserCredentialsSerializer

def register(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Валідація
        if not username or not password or not password_confirm:
            messages.error(request, 'All fields are required')
        elif len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
        elif password != password_confirm:
            messages.error(request, 'Passwords do not match')
        elif UserCredentials.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            # Створення користувача
            user = UserCredentials(
                username=username,
                password=make_password(password),
                user_role='client'
            )
            user.save()

            # Додавання до групи client
            try:
                client_group = Group.objects.get(name='client')
                user.groups.add(client_group)
                messages.success(request, 'Регістрація успішна!')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('create_profile')
            except Group.DoesNotExist:
                messages.error(request, 'Error: Client group not found. Contact admin.')
                user.delete()
    return render(request, 'auth_app/register.html')

def login_view(request):
    if request.user.is_authenticated:
        messages.info(request, 'Ви вже війшли в систему.')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Валідація
        if not username or not password:
            messages.error(request, 'Username and password are required')
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Ласкаво просимо, {user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password')
    return render(request, 'auth_app/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Ви вийшли з системи.')
    return redirect('login')

@login_required
def home(request):
    return render(request, 'auth_app/home.html', {
        'user_role': request.user.user_role,
        'username': request.user.username
    })



# API-ендпоінти для мікросервісів
def api_register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        if not username or not password or not password_confirm:
            return JsonResponse({'error': 'All fields are required'}, status=400)
        if len(username) < 3:
            return JsonResponse({'error': 'Username must be at least 3 characters long'}, status=400)
        if len(password) < 6:
            return JsonResponse({'error': 'Password must be at least 6 characters long'}, status=400)
        if password != password_confirm:
            return JsonResponse({'error': 'Passwords do not match'}, status=400)
        if UserCredentials.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        user = UserCredentials(
            username=username,
            password=make_password(password),
            user_role='client'
        )
        user.save()
        try:
            client_group = Group.objects.get(name='client')
            user.groups.add(client_group)
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
            return JsonResponse({
                'message': 'Registration successful',
                'username': username,
                'role': 'client',
                'sessionid': request.session.session_key
            }, status=201)
        except Group.DoesNotExist:
            user.delete()
            return JsonResponse({'error': 'Client group not found'}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def api_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                'message': 'Login successful',
                'username': user.username,
                'role': user.user_role,
                'sessionid': request.session.session_key
            }, status=200)
        return JsonResponse({'error': 'Invalid username or password'}, status=401)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def api_user_info(request):
    if request.method == 'GET':
        return JsonResponse({
            'username': request.user.username,
            'role': request.user.user_role,
            'permissions': list(request.user.get_group_permissions())
        }, status=200)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def api_check_user(request):
    if request.method == 'GET':
        username = request.GET.get('username', '').strip()
        if not username:
            return JsonResponse({'error': 'Username is required'}, status=400)
        exists = UserCredentials.objects.filter(username=username).exists()
        return JsonResponse({
            'username': username,
            'exists': exists
        }, status=200)
    return JsonResponse({'error': 'Method not allowed'}, status=405)



class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            serializer = UserCredentialsSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class UserPermissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserCredentialsSerializer(request.user)
        return Response(serializer.data)