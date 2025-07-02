from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from training_app.models import Trainers, TrainingSessions
from .models import Client, ClientSubscription, ClientGoal, ClientFeedback, ClientProgress, ClientTrainingRegistration
from .forms import ClientForm, BalanceTopUpForm, PurchaseSubscriptionForm, ClientGoalForm, ClientFeedbackForm, \
    ClientProgressForm
from auth_app.models import UserCredentials
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef, Case, When, Value, BooleanField
import logging
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, date
from django.db.utils import DatabaseError, InternalError

logger = logging.getLogger(__name__)

@login_required
@permission_required(('auth_app.view_clients', 'auth_app.change_clients'), raise_exception=True)
def client_profile(request):
    try:
        # Отримуємо профіль клієнта
        client = Client.objects.get(user_credential=request.user)

        # Перевіряємо роль
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to access client profile")
            messages.error(request, 'Доступ до профілю клієнта дозволено лише клієнтам.')
            return redirect('home')

        # Ініціалізація форм
        client_form = ClientForm(instance=client)
        balance_form = BalanceTopUpForm()

        # Обробка POST-запитів
        if request.method == 'POST':
            if 'update_profile' in request.POST:
                # Оновлення профілю
                client_form = ClientForm(request.POST, instance=client)
                if client_form.is_valid():
                    try:
                        client_form.save()
                        logger.info(f"User {request.user.username} updated client profile: {client.user_id}")
                        messages.success(request, 'Профіль успішно оновлено.')
                        return redirect('client_profile')
                    except IntegrityError:
                        logger.warning(f"User {request.user.username} failed to update profile due to unique constraint")
                        messages.error(request, 'Помилка: email або телефон уже використовуються.')
            elif 'top_up_balance' in request.POST:
                # Поповнення балансу
                balance_form = BalanceTopUpForm(request.POST)
                if balance_form.is_valid():
                    amount = balance_form.cleaned_data['amount']
                    try:
                        client.balance += amount
                        client.save()
                        logger.info(f"User {request.user.username} topped up balance by {amount} for client: {client.user_id}")
                        messages.success(request, f'Баланс поповнено на {amount} грн.')
                        return redirect('client_profile')
                    except Exception as e:
                        logger.error(f"Error topping up balance for user {request.user.username}: {str(e)}")
                        messages.error(request, 'Помилка при поповненні балансу.')
                else:
                    logger.warning(f"User {request.user.username} submitted invalid balance top-up data")
                    messages.error(request, 'Помилка: введіть коректну суму.')

        # Логуємо успішний перегляд
        logger.info(f"User {request.user.username} viewed client profile: {client.user_id}")

        context = {
            'client': client,
            'trainer': client.trainer if client.trainer else None,
            'client_form': client_form,
            'balance_form': balance_form,
        }
        return render(request, 'clients/client_profile.html', context)

    except Client.DoesNotExist:
        #messages.error(request, 'Профіль клієнта не знайдено. Зверніться до адміністратора.')
        return redirect('create_profile')
    except Exception as e:
        logger.error(f"Error viewing client profile for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні профілю.')
        return redirect('home')


@login_required
@permission_required('auth_app.change_clients', raise_exception=True)
def create_profile(request):
    try:
        # Перевіряємо, чи профіль уже існує
        if Client.objects.filter(user_credential=request.user).exists():
            logger.info(f"User {request.user.username} already has a client profile, redirecting to client_profile")
            messages.info(request, 'Ваш профіль уже створено.')
            return redirect('client_profile')

        # Перевіряємо роль
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to create client profile")
            messages.error(request, 'Створення профілю дозволено лише клієнтам.')
            return redirect('home')

        if request.method == 'POST':
            form = ClientForm(request.POST)
            if form.is_valid():
                try:
                    client = form.save(commit=False)
                    client.user_credential = request.user
                    client.save()
                    logger.info(f"User {request.user.username} created client profile: {client.user_id}")
                    messages.success(request, 'Профіль успішно створено!')
                    return redirect('client_profile')
                except IntegrityError:
                    logger.warning(f"User {request.user.username} failed to create profile due to unique constraint")
                    messages.error(request, 'Помилка: email або телефон уже використовуються.')
                except Exception as e:
                    logger.error(f"Error creating client profile for user {request.user.username}: {str(e)}")
                    messages.error(request, 'Сталася помилка при створенні профілю.')
            else:
                logger.warning(f"User {request.user.username} submitted invalid form data")
                messages.error(request, 'Помилка: перевірте правильність даних.')
        else:
            form = ClientForm()

        context = {
            'form': form,
        }
        return render(request, 'clients/create_profile.html', context)

    except Exception as e:
        logger.error(f"Error accessing create profile for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('home')

@login_required
@permission_required('auth_app.view_clients', raise_exception=True)
def clients_list(request):
    try:
        clients_data = []

        if request.user.user_role == 'trainer':
            try:
                trainer = Trainers.objects.get(user_credential=request.user)
                clients = (Client.objects.filter(trainer=trainer)
                .select_related('user_credential')
                .prefetch_related('goals__goal'))
                #clients = Client.objects.filter(trainer=trainer)
                # Для тренеров показываем только клиентов с профилем Client
                for client in clients:
                    goals = [
                        {
                            'title': client_goal.goal.goal_name,
                            'description': client_goal.description,
                            'is_achieved': client_goal.is_achieved
                        }
                        for client_goal in client.goals.all()
                    ]
                    clients_data.append({
                        'user': client.user_credential,
                        'client': client,
                        'goals': goals
                    })
                logger.info(f"Trainer {request.user.username} viewed their clients list")
            except Trainers.DoesNotExist:
                logger.warning(f"User {request.user.username} has no trainer profile")
                messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
                return redirect('home')
        elif request.user.user_role == 'admin':
            # Для админов показываем всех пользователей с user_role='client'
            users = UserCredentials.objects.filter(user_role='client')
            for user in users:
                client = Client.objects.filter(user_credential=user).first()
                clients_data.append({
                    'user': user,
                    'client': client
                })
            logger.info(f"Admin {request.user.username} viewed all clients list")
        else:
            logger.warning(
                f"User {request.user.username} (role: {request.user.user_role}) attempted to access clients list")
            messages.error(request, 'Доступ до списку клієнтів дозволено лише тренерам або адміністраторам.')
            return redirect('home')

        context = {
            'clients_data': clients_data,
            'user_role': request.user.user_role,
        }
        return render(request, 'clients/clients_list.html', context)

    except Exception as e:
        logger.error(f"Error viewing clients list for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні списку клієнтів.')
        return redirect('home')



@login_required
@permission_required('auth_app.delete_clients', raise_exception=True)
def delete_client(request, user_id):
    try:
        # Перевіряємо роль
        if request.user.user_role != 'admin':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to delete client {user_id}")
            messages.error(request, 'Видалення клієнтів дозволено лише адміністраторам.')
            return redirect('clients_list')

        if request.method == 'POST':
            try:
                user = UserCredentials.objects.get(user_credential_id=user_id)
                # Проверяем наличие профиля Client для получения имени
                try:
                    client_info = Client.objects.get(user_credential=user)
                    client_name = f"{client_info.first_name} {client_info.last_name}"
                except Client.DoesNotExist:
                    client_name = user.username  # Используем username, если нет профиля Client

                user.delete()  # Видаляє UserCredentials і пов'язаний Client через CASCADE
                logger.info(f"Admin {request.user.username} deleted client: {user_id} ({client_name})")
                messages.success(request, f'Клієнт {client_name} успішно видалений.')
                return redirect('clients_list')
            except UserCredentials.DoesNotExist:
                logger.warning(f"User {user_id} not found for deletion by user {request.user.username}")
                messages.error(request, 'Клієнт не знайдений.')
                return redirect('clients_list')
        else:
            logger.warning(f"Invalid request method for delete_client by user {request.user.username}")
            messages.error(request, 'Невалідний запит для видалення.')
            return redirect('clients_list')

    except Exception as e:
        logger.error(f"Error deleting client {user_id} by user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при видаленні клієнта.')
        return redirect('clients_list')


### client_subscriptions ###
@login_required
@permission_required('auth_app.view_client_subscriptions', raise_exception=True)
def client_subscriptions_list(request):
    try:
        subscriptions = []

        if request.user.user_role == 'client':
            try:
                client = Client.objects.get(user_credential=request.user)
                subscriptions = ClientSubscription.objects.filter(user=client).select_related('user', 'subscription')
                logger.info(f"Client {request.user.username} viewed their subscriptions list")
            except Client.DoesNotExist:
                logger.warning(f"User {request.user.username} has no client profile")
                messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
                return redirect('create_profile')
        elif request.user.user_role == 'trainer':
            try:
                trainer = Trainers.objects.get(user_credential=request.user)
                subscriptions = ClientSubscription.objects.filter(user__trainer=trainer).select_related('user', 'subscription')
                logger.info(f"Trainer {request.user.username} viewed their clients' subscriptions list")
            except Trainers.DoesNotExist:
                logger.warning(f"User {request.user.username} has no trainer profile")
                messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
                return redirect('home')
        elif request.user.user_role == 'admin':
            subscriptions = ClientSubscription.objects.all().select_related('user', 'subscription')
            logger.info(f"Admin {request.user.username} viewed all client subscriptions list")
        else:
            logger.warning(
                f"User {request.user.username} (role: {request.user.user_role}) attempted to access client subscriptions list")
            messages.error(request, 'Доступ до списку абонементів не дозволено.')
            return redirect('home')

        context = {
            'subscriptions': subscriptions,
            'user_role': request.user.user_role,
        }
        return render(request, 'client_subscriptions/client_subscriptions_list.html', context)

    except Exception as e:
        logger.error(f"Error viewing client subscriptions list for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні списку абонементів.')
        return redirect('home')


@login_required
@permission_required('auth_app.add_client_subscriptions', raise_exception=True)
def purchase_subscription(request):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to purchase subscription")
            messages.error(request, 'Покупка абонемента дозволена лише клієнтам.')
            return redirect('home')
        try:
            client = Client.objects.get(user_credential=request.user)
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        if request.method == 'POST':
            form = PurchaseSubscriptionForm(request.POST)
            if form.is_valid():
                subscription = form.cleaned_data['subscription']
                try:
                    with transaction.atomic():
                        if client.balance < subscription.price:
                            logger.warning(f"User {request.user.username} has insufficient balance for subscription {subscription.subscription_id}")
                            messages.error(request, 'Недостатньо коштів на балансі.')
                            return redirect('client_profile')
                        start_date = datetime.now()
                        end_date = start_date + timedelta(days=subscription.duration_days)
                        client_subscription = ClientSubscription(
                            user=client,
                            subscription=subscription,
                            start_date=start_date,
                            end_date=end_date
                        )
                        client_subscription.clean()
                        client_subscription.save()
                        client.balance -= subscription.price
                        client.save()
                        logger.info(f"User {request.user.username} purchased subscription {subscription.subscription_id} for client {client.user_id}")
                        messages.success(request, f'Абонемент "{subscription.subscription_name}" успішно придбано!')
                        return redirect('client_subscriptions_list')
                except ValidationError as e:
                    logger.warning(f"Validation error for user {request.user.username} purchasing subscription: {str(e)}")
                    messages.error(request, f'Помилка: {str(e)}')
                except Exception as e:
                    logger.error(f"Error purchasing subscription for user {request.user.username}: {str(e)}")
                    messages.error(request, 'Сталася помилка при покупці абонемента.')
            else:
                logger.warning(f"User {request.user.username} submitted invalid subscription purchase form")
                messages.error(request, 'Помилка: виберіть коректний абонемент.')
        else:
            form = PurchaseSubscriptionForm()
        context = {
            'form': form,
            'client': client,
        }
        return render(request, 'client_subscriptions/purchase_subscription.html', context)
    except Exception as e:
        logger.error(f"Error accessing purchase subscription for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки покупки.')
        return redirect('home')


@login_required
@permission_required('auth_app.delete_client_subscriptions', raise_exception=True)
def delete_client_subscription(request, user_subscription_id):
    try:
        if request.method == 'POST':
            try:
                subscription = ClientSubscription.objects.get(user_subscription_id=user_subscription_id)
                subscription_name = subscription.subscription.subscription_name
                client_name = f"{subscription.user.first_name} {subscription.user.last_name}"
                subscription.delete()
                messages.success(request, f'Абонемент "{subscription_name}" для клієнта {client_name} успішно видалено.')
                return redirect('client_subscriptions_list')
            except ClientSubscription.DoesNotExist:
                messages.error(request, 'Абонемент не знайдено.')
                return redirect('client_subscriptions_list')
        else:
            messages.error(request, 'Невалідний запит для видалення.')
            return redirect('client_subscriptions_list')
    except Exception as e:
        messages.error(request, 'Сталася помилка при видаленні абонемента.')
        return redirect('client_subscriptions_list')


### client_goals ###
@login_required
@permission_required('auth_app.view_client_goals', raise_exception=True)
def client_goals_list(request):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to access client goals list")
            messages.error(request, 'Доступ до списку цілей дозволено лише клієнтам.')
            return redirect('home')
        try:
            client = Client.objects.get(user_credential=request.user)
            goals = ClientGoal.objects.filter(user=client).select_related('user', 'goal')
            context = {
                'goals': goals,
            }
            return render(request, 'client_goals/client_goals_list.html', context)
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
    except Exception as e:
        logger.error(f"Error viewing client goals list for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні списку цілей.')
        return redirect('home')


@login_required
@permission_required('auth_app.add_client_goals', raise_exception=True)
def add_client_goal(request):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to add client goal")
            messages.error(request, 'Додавання цілей дозволено лише клієнтам.')
            return redirect('home')
        try:
            client = Client.objects.get(user_credential=request.user)
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        if request.method == 'POST':
            form = ClientGoalForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        client_goal = form.save(commit=False)
                        client_goal.user = client
                        client_goal.assigned_at = datetime.now()
                        client_goal.is_achieved = False
                        client_goal.save()
                        logger.info(f"User {request.user.username} added goal {client_goal.client_goal_id} for client {client.user_id}")
                        messages.success(request, f'Ціль "{client_goal.goal.goal_name}" успішно додано!')
                        return redirect('client_goals_list')
                except IntegrityError:
                    logger.warning(f"User {request.user.username} failed to add goal due to unique constraint")
                    messages.error(request, 'Помилка: ця ціль уже додана на цю дату.')
                except Exception as e:
                    logger.error(f"Error adding goal for user {request.user.username}: {str(e)}")
                    messages.error(request, 'Сталася помилка при додаванні цілі.')
            else:
                logger.warning(f"User {request.user.username} submitted invalid goal form")
                messages.error(request, 'Помилка: перевірте правильність даних.')
        else:
            form = ClientGoalForm()
        context = {
            'form': form,
        }
        return render(request, 'client_goals/add_client_goal.html', context)
    except Exception as e:
        logger.error(f"Error accessing add client goal for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('home')


@login_required
@permission_required('auth_app.change_client_goals', raise_exception=True)
def edit_client_goal(request, client_goal_id):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to edit client goal {client_goal_id}")
            messages.error(request, 'Редагування цілей дозволено лише клієнтам.')
            return redirect('client_goals_list')
        try:
            client = Client.objects.get(user_credential=request.user)
            goal = ClientGoal.objects.get(client_goal_id=client_goal_id, user=client)
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        except ClientGoal.DoesNotExist:
            logger.warning(f"Goal {client_goal_id} not found or not owned by user {request.user.username}")
            messages.error(request, 'Ціль не знайдено.')
            return redirect('client_goals_list')
        if request.method == 'POST':
            form = ClientGoalForm(request.POST, instance=goal)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        client_goal = form.save()
                        logger.info(f"User {request.user.username} updated goal {client_goal_id} for client {client.user_id}")
                        messages.success(request, f'Ціль "{client_goal.goal.goal_name}" успішно оновлено!')
                        return redirect('client_goals_list')
                except IntegrityError:
                    logger.warning(f"User {request.user.username} failed to update goal due to unique constraint")
                    messages.error(request, 'Помилка: ціль із такими даними вже існує.')
                except Exception as e:
                    logger.error(f"Error updating goal {client_goal_id} for user {request.user.username}: {str(e)}")
                    messages.error(request, 'Сталася помилка при оновленні цілі.')
            else:
                logger.warning(f"User {request.user.username} submitted invalid goal form: {form.errors}")
                messages.error(request, 'Помилка: перевірте правильність даних.')
        else:
            form = ClientGoalForm(instance=goal)
        context = {
            'form': form,
            'goal': goal,
        }
        return render(request, 'client_goals/edit_client_goal.html', context)
    except Exception as e:
        logger.error(f"Error accessing edit client goal {client_goal_id} for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('client_goals_list')

@login_required
@permission_required('auth_app.delete_client_goals', raise_exception=True)
def delete_client_goal(request, client_goal_id):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to delete client goal {client_goal_id}")
            messages.error(request, 'Видалення цілей дозволено лише клієнтам.')
            return redirect('client_goals_list')
        if request.method == 'POST':
            try:
                client = Client.objects.get(user_credential=request.user)
                goal = ClientGoal.objects.get(client_goal_id=client_goal_id, user=client)
                goal_name = goal.goal.goal_name
                goal.delete()
                logger.info(f"User {request.user.username} deleted goal {client_goal_id} for client {client.user_id}")
                messages.success(request, f'Ціль "{goal_name}" успішно видалено.')
                return redirect('client_goals_list')
            except Client.DoesNotExist:
                logger.warning(f"User {request.user.username} has no client profile")
                messages.error(request, 'Профіль клієнта не знайдено.')
                return redirect('client_goals_list')
            except ClientGoal.DoesNotExist:
                logger.warning(f"Goal {client_goal_id} not found or not owned by user {request.user.username}")
                messages.error(request, 'Ціль не знайдено.')
                return redirect('client_goals_list')
        else:
            logger.warning(f"Invalid request method for delete_client_goal by user {request.user.username}")
            messages.error(request, 'Невалідний запит для видалення.')
            return redirect('client_goals_list')
    except Exception as e:
        logger.error(f"Error deleting client goal {client_goal_id} by user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при видаленні цілі.')
        return redirect('client_goals_list')


### client_feedbacks ###
@login_required
@permission_required('auth_app.view_client_feedbacks', raise_exception=True)
def client_feedbacks_list(request):
    try:
        if request.user.user_role == 'admin':
            feedbacks = ClientFeedback.objects.all()
            return render(request, 'client_feedbacks/client_feedbacks_list.html', {'feedbacks': feedbacks})
        # if request.user.user_role == 'trainer':
        #     trainer = Trainers.objects.get(user_credential=request.user)
        #     feedbacks = ClientFeedback.objects.filter(trainer=trainer).select_related('user', 'trainer')
        #     #logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to access client feedbacks list")
        #     messages.error(request, 'Доступ до списку відгуків дозволено лише клієнтам.')
        #     return redirect('home')
        try:
            client = Client.objects.get(user_credential=request.user)
            feedbacks = ClientFeedback.objects.filter(user=client).select_related('user', 'trainer')
            logger.info(f"Client {request.user.username} viewed their feedbacks list")
            context = {
                'feedbacks': feedbacks,
            }
            return render(request, 'client_feedbacks/client_feedbacks_list.html', context)
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
    except Exception as e:
        logger.error(f"Error viewing client feedbacks list for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні списку відгуків.')
        return redirect('home')


@login_required
@permission_required('auth_app.add_client_feedbacks', raise_exception=True)
def add_client_feedback(request):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to add client feedback")
            messages.error(request, 'Додавання відгуків дозволено лише клієнтам.')
            return redirect('client_feedbacks_list')
        try:
            client = Client.objects.get(user_credential=request.user)
            if not client.trainer:
                logger.warning(f"User {request.user.username} has no assigned trainer")
                messages.error(request, 'У вас немає призначеного тренера для залишення відгуку.')
                return redirect('client_feedbacks_list')
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        if request.method == 'POST':
            form = ClientFeedbackForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        feedback = form.save(commit=False)
                        feedback.user = client
                        feedback.trainer = client.trainer
                        feedback.date = datetime.now()
                        feedback.clean()
                        feedback.save()
                        logger.info(f"User {request.user.username} added feedback {feedback.feedback_id} for trainer {client.trainer.user_credential.username}")
                        messages.success(request, f'Відгук "{feedback.title}" успішно додано!')
                        return redirect('client_feedbacks_list')
                except IntegrityError:
                    logger.warning(f"User {request.user.username} failed to add feedback due to unique constraint")
                    messages.error(request, 'Помилка: відгук для цього тренера на цю дату вже існує.')
                except ValidationError as e:
                    logger.warning(f"Validation error for user {request.user.username} adding feedback: {str(e)}")
                    messages.error(request, f'Помилка: {str(e)}')
                except Exception as e:
                    logger.error(f"Error adding feedback for user {request.user.username}: {str(e)}")
                    messages.error(request, 'Сталася помилка при додаванні відгуку.')
            else:
                logger.warning(f"User {request.user.username} submitted invalid feedback form: {form.errors}")
                messages.error(request, 'Помилка: перевірте правильність даних.')
        else:
            form = ClientFeedbackForm()
        context = {
            'form': form,
            'client': client,
        }
        return render(request, 'client_feedbacks/add_client_feedback.html', context)
    except Exception as e:
        logger.error(f"Error accessing add client feedback for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('client_feedbacks_list')


@login_required
@permission_required('auth_app.change_client_feedbacks', raise_exception=True)
def edit_client_feedback(request, feedback_id):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} attempted to edit client feedback {feedback_id}")
            messages.error(request, 'Редагування відгуків дозволено лише клієнтам.')
            return redirect('client_feedbacks_list')
        try:
            client = Client.objects.get(user_credential=request.user)
            feedback = ClientFeedback.objects.get(feedback_id=feedback_id, user=client)
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        except ClientFeedback.DoesNotExist:
            logger.warning(f"Feedback {feedback_id} not found or not owned by user {request.user.username}")
            messages.error(request, 'Відгук не знайдено.')
            return redirect('client_feedbacks_list')
        if request.method == 'POST':
            form = ClientFeedbackForm(request.POST, instance=feedback)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        feedback = form.save(commit=False)
                        feedback.clean()
                        feedback.save()
                        logger.info(f"User {request.user.username} updated feedback {feedback_id} for trainer {feedback.trainer.user_credential.username}")
                        messages.success(request, f'Відгук "{feedback.title}" успішно оновлено!')
                        return redirect('client_feedbacks_list')
                except IntegrityError:
                    logger.warning(f"User {request.user.username} failed to update feedback due to unique constraint")
                    messages.error(request, 'Помилка: відгук із такими даними вже існує.')
                except ValidationError as e:
                    logger.warning(f"Validation error for user {request.user.username} updating feedback: {str(e)}")
                    messages.error(request, f'Помилка: {str(e)}')
                except Exception as e:
                    logger.error(f"Error updating feedback {feedback_id} for user {request.user.username}: {str(e)}")
                    messages.error(request, 'Сталася помилка при оновленні відгуку.')
            else:
                logger.warning(f"User {request.user.username} submitted invalid feedback form: {form.errors}")
                messages.error(request, 'Помилка: перевірте правильність даних.')
        else:
            form = ClientFeedbackForm(instance=feedback)
        context = {
            'form': form,
            'feedback': feedback,
        }
        return render(request, 'client_feedbacks/edit_client_feedback.html', context)
    except Exception as e:
        logger.error(f"Error accessing edit client feedback {feedback_id} for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('client_feedbacks_list')

@login_required
@permission_required('auth_app.delete_client_feedbacks', raise_exception=True)
def delete_client_feedback(request, feedback_id):
    try:
        if request.user.user_role == 'admin':
            feedback = ClientFeedback.objects.get(feedback_id=feedback_id)
            feedback_title = feedback.title
            feedback.delete()
            messages.success(request, f'Відгук "{feedback_title}" успішно видалено.')
            #logger.warning(f"User {request.user.username} attempted to delete client feedback {feedback_id}")
            #messages.error(request, 'Видалення відгуків дозволено лише клієнтам або адміністраторам')
            return redirect('client_feedbacks_list')
        if request.method == 'POST':
            try:
                client = Client.objects.get(user_credential=request.user)
                feedback = ClientFeedback.objects.get(feedback_id=feedback_id, user=client)
                feedback_title = feedback.title
                feedback.delete()
                messages.success(request, f'Відгук "{feedback_title}" успішно видалено.')
                return redirect('client_feedbacks_list')
            except Client.DoesNotExist:
                messages.error(request, 'Профіль клієнта не знайдено.')
                return redirect('client_feedbacks_list')
            except ClientFeedback.DoesNotExist:
                messages.error(request, 'Відгук не знайдено.')
                return redirect('client_feedbacks_list')
        else:
            messages.error(request, 'Невалідний запит для видалення.')
            return redirect('client_feedbacks_list')
    except Exception as e:
        messages.error(request, 'Сталася помилка при видаленні відгуку.')
        return redirect('client_feedbacks_list')



@login_required
@permission_required('auth_app.view_trainers', raise_exception=True)
def assign_trainer(request, trainer_id):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to assign trainer {trainer_id}")
            messages.error(request, 'Призначення тренера дозволено лише клієнтам.')
            return redirect('trainers_list')
        if request.method != 'POST':
            logger.warning(f"Invalid request method for assign_trainer by user {request.user.username}")
            messages.error(request, 'Невалідний запит.')
            return redirect('trainers_list')
        try:
            client = Client.objects.get(user_credential=request.user)
            trainer = Trainers.objects.get(trainer_id=trainer_id)
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        except Trainers.DoesNotExist:
            logger.warning(f"Trainer {trainer_id} not found for user {request.user.username}")
            messages.error(request, 'Тренера не знайдено.')
            return redirect('trainers_list')
        try:
            with transaction.atomic():
                try:
                    client.trainer = trainer
                    client.save()
                except InternalError as e:
                    if 'вже досягнув максимальної' in str(e):
                        messages.error(request, f'Помилка: У тренера {trainer.first_name} {trainer.last_name} немає вільних місць для запису до нього.')
                        return redirect('trainers_list')
                logger.info(f"User {request.user.username} assigned trainer {trainer.user_credential.username} (trainer_id: {trainer_id})")
                messages.success(request, f'Ви успішно записалися до тренера {trainer.first_name} {trainer.last_name}!')
                return redirect('trainers_list')
        except DatabaseError as e:
            logger.warning(f"User {request.user.username} failed to assign trainer {trainer_id} due to database error: {str(e)}")
            if 'Неможливо призначити тренера без активного абонемента' in str(e):
                messages.error(request, 'Помилка: для призначення тренера потрібен активний абонемент.')
            else:
                messages.error(request, 'Сталася помилка при призначенні тренера.')
            return redirect('client_subscriptions_list')
        except Exception as e:
            logger.error(f"Error assigning trainer {trainer_id} for user {request.user.username}: {str(e)}")
            messages.error(request, 'Сталася помилка при призначенні тренера.')
            return redirect('trainers_list')
    except Exception as e:
        logger.error(f"Error accessing assign_trainer for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('trainers_list')


@login_required
@permission_required('auth_app.view_client_feedbacks', raise_exception=True)
def trainer_feedbacks(request):
    try:
        if request.user.user_role != 'trainer':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to view trainer feedbacks")
            messages.error(request, 'Перегляд відгуків дозволено лише тренерам.')
            return redirect('home')
        try:
            trainer = Trainers.objects.get(user_credential=request.user)
        except Trainers.DoesNotExist:
            logger.warning(f"User {request.user.username} has no trainer profile")
            messages.error(request, 'Профіль тренера не знайдено.')
            return redirect('home')
        feedbacks = ClientFeedback.objects.filter(trainer=trainer).order_by('-date')
        logger.info(f"User {request.user.username} viewed their feedbacks (count: {feedbacks.count()})")
        return render(request, 'client_feedbacks/trainer_feedbacks.html', {
            'feedbacks': feedbacks,
            'trainer': trainer,
        })
    except Exception as e:
        logger.error(f"Error accessing trainer feedbacks for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні відгуків.')
        return redirect('home')


### client_training_registrations ###

@login_required
@permission_required('auth_app.view_client_training_registrations', raise_exception=True)
def client_training_registrations(request):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to view client trainings")
            messages.error(request, 'Перегляд тренувальних сесій дозволено лише клієнтам.')
            return redirect('home')
        try:
            client = Client.objects.get(user_credential=request.user)
            if client.subscriptions.count() == 0:
                messages.error(request, 'Необхідно мати активний абонемент для перегляду тренувальних сесій.')
                return redirect('client_subscriptions_list')
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        if not client.trainer:
            logger.info(f"User {request.user.username} has no assigned trainer")
            messages.error(request, 'У вас немає призначеного тренера.')
            sessions = []
        else:
            # Аннотируем сессии флагом is_registered
            sessions = TrainingSessions.objects.filter(
                trainer=client.trainer,
                status='заплановано'
            ).annotate(
                is_registered=Exists(
                    ClientTrainingRegistration.objects.filter(
                        session=OuterRef('pk'),
                        user=client
                    )
                )
            ).annotate(
                is_finished=Case(
                    When(
                        session_date__lt=datetime.now().date(),
                        then=Value(True)
                    ),
                    When(
                        session_date=datetime.now().date(),
                        end_time__lt=datetime.now().time(),
                        then=Value(True)
                    ),
                    default=Value(False),
                    output_field=BooleanField()
            )).order_by('session_date', 'start_time')
            logger.info(f"User {request.user.username} viewed training sessions (count: {sessions.count()})")
        return render(request, 'client_trainings/client_trainings.html', {
            'sessions': sessions,
            'client': client,
            'today': date.today(),
            'now_time': datetime.now().time(),
        })
    except Exception as e:
        logger.error(f"Error accessing client trainings for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('home')


@login_required
@permission_required('auth_app.add_client_training_registrations', raise_exception=True)
def register_for_session(request, session_id):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to register for session {session_id}")
            messages.error(request, 'Реєстрація на тренування дозволена лише клієнтам.')
            return redirect('client_trainings')
        if request.method != 'POST':
            logger.warning(f"Invalid request method for register_for_session by user {request.user.username}")
            messages.error(request, 'Невалідний запит.')
            return redirect('client_trainings')
        try:
            client = Client.objects.get(user_credential=request.user)
            session = TrainingSessions.objects.get(session_id=session_id, status='заплановано')
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        except TrainingSessions.DoesNotExist:
            logger.warning(f"Session {session_id} not found or not planned for user {request.user.username}")
            messages.error(request, 'Сесію не знайдено або вона не запланована.')
            return redirect('client_trainings')
        if session.trainer != client.trainer:
            logger.warning(f"User {request.user.username} attempted to register for session {session_id} not belonging to their trainer")
            messages.error(request, 'Ви можете реєструватися лише на сесії вашого тренера.')
            return redirect('client_trainings')
        current_participants = ClientTrainingRegistration.objects.filter(session=session).count()
        if current_participants >= session.max_participants:
            logger.warning(f"User {request.user.username} failed to register for session {session_id}: session is full")
            messages.error(request, 'Сесія заповнена. Оберіть іншу.')
            return redirect('client_trainings')
        try:
            with transaction.atomic():
                registration = ClientTrainingRegistration.objects.create(
                    user=client,
                    session=session
                )
                logger.info(f"User {request.user.username} registered for session {session_id}")
                messages.success(request, f'Ви успішно зареєструвалися на сесію {session.session_date.strftime("%d.%m.%Y")} {session.start_time.strftime("%H:%M")}!')
                return redirect('client_trainings')
        except IntegrityError:
            logger.warning(f"User {request.user.username} already registered for session {session_id}")
            messages.error(request, 'Ви вже зареєстровані на цю сесію.')
            return redirect('client_trainings')
        except Exception as e:
            logger.error(f"Error registering user {request.user.username} for session {session_id}: {str(e)}")
            messages.error(request, 'Сталася помилка при реєстрації.')
            return redirect('client_trainings')
    except Exception as e:
        logger.error(f"Error accessing register_for_session for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('client_trainings')


@login_required
@permission_required('auth_app.delete_client_training_registrations', raise_exception=True)
def cancel_registration(request, session_id):
    try:
        if request.user.user_role != 'client':
            logger.warning(f"User {request.user.username} (role: {request.user.user_role}) attempted to cancel registration for session {session_id}")
            messages.error(request, 'Скасування реєстрації дозволено лише клієнтам.')
            return redirect('client_trainings')
        if request.method != 'POST':
            logger.warning(f"Invalid request method for cancel_registration by user {request.user.username}")
            messages.error(request, 'Невалідний запит.')
            return redirect('client_trainings')
        try:
            client = Client.objects.get(user_credential=request.user)
            session = TrainingSessions.objects.get(session_id=session_id, status='заплановано')
            registration = ClientTrainingRegistration.objects.get(user=client, session=session)
        except Client.DoesNotExist:
            logger.warning(f"User {request.user.username} has no client profile")
            messages.error(request, 'Профіль клієнта не знайдено. Створіть профіль.')
            return redirect('create_profile')
        except TrainingSessions.DoesNotExist:
            logger.warning(f"Session {session_id} not found or not planned for user {request.user.username}")
            messages.error(request, 'Сесію не знайдено або вона не запланована.')
            return redirect('client_trainings')
        except ClientTrainingRegistration.DoesNotExist:
            logger.warning(f"Registration for session {session_id} not found for user {request.user.username}")
            messages.error(request, 'Реєстрація на цю сесію не знайдена.')
            return redirect('client_trainings')
        try:
            with transaction.atomic():
                registration.delete()
                logger.info(f"User {request.user.username} cancelled registration for session {session_id}")
                messages.success(request, f'Реєстрацію на сесію {session.session_date.strftime("%d.%m.%Y")} {session.start_time.strftime("%H:%M")} скасовано!')
                return redirect('client_trainings')
        except Exception as e:
            logger.error(f"Error cancelling registration for user {request.user.username} for session {session_id}: {str(e)}")
            messages.error(request, 'Сталася помилка при скасуванні реєстрації.')
            return redirect('client_trainings')
    except Exception as e:
        logger.error(f"Error accessing cancel_registration for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('client_trainings')



### client_progress ###
@login_required
@permission_required('auth_app.view_client_progress', raise_exception=True)
def client_progress(request):
    try:
        client = Client.objects.get(user_credential=request.user)
        progress_records = ClientProgress.objects.filter(
            user=client
        ).select_related('session', 'session__training_type').order_by('-session__session_date')
        logger.info(f"Client {request.user.username} viewed their progress records (count: {progress_records.count()})")
        return render(request, 'client_progress/client_progress_list.html', {
            'progress_records': progress_records,
            'client': client
        })
    except Client.DoesNotExist:
        logger.warning(f"User {request.user.username} has no client profile")
        messages.error(request, 'Профіль клієнта не знайдено. Зверніться до адміністратора.')
        return redirect('create_profile')
    except Exception as e:
        logger.error(f"Error accessing client_progress for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('home')

@login_required
@permission_required('auth_app.add_client_progress', raise_exception=True)
def add_client_progress(request, session_id, client_id):
    try:
        trainer = Trainers.objects.get(user_credential=request.user)
        try:
            session = TrainingSessions.objects.get(session_id=session_id, trainer=trainer, status='завершено')
            client = Client.objects.get(user_id=client_id)
            # Проверяем, что клиент зарегистрирован на сессию
            ClientTrainingRegistration.objects.get(user=client, session=session)
        except TrainingSessions.DoesNotExist:
            logger.warning(f"Session {session_id} not found, not completed, or not owned by trainer {request.user.username}")
            messages.error(request, 'Сесію не знайдено, вона не завершена або не належить вам.')
            return redirect('view_session_registrations', session_id=session_id)
        except Client.DoesNotExist:
            logger.warning(f"Client {client_id} not found for session {session_id}")
            messages.error(request, 'Клієнта не знайдено.')
            return redirect('view_session_registrations', session_id=session_id)
        except ClientTrainingRegistration.DoesNotExist:
            logger.warning(f"Client {client_id} not registered for session {session_id}")
            messages.error(request, 'Клієнт не зареєстрований на цю сесію.')
            return redirect('view_session_registrations', session_id=session_id)

        # Проверяем, не существует ли уже прогресс
        if ClientProgress.objects.filter(user=client, session=session).exists():
            logger.warning(f"Progress already exists for client {client_id} in session {session_id}")
            messages.error(request, 'Відгук про прогрес для цього клієнта вже існує.')
            return redirect('view_session_registrations', session_id=session_id)

        if request.method == 'POST':
            form = ClientProgressForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        progress = form.save(commit=False)
                        progress.user = client
                        progress.session = session
                        progress.save()
                        logger.info(f"Trainer {request.user.username} added progress for client {client_id} in session {session_id}")
                        messages.success(request, f'Відгук про прогрес для {client.first_name} {client.last_name} додано!')
                        return redirect('view_session_registrations', session_id=session_id)
                except Exception as e:
                    logger.error(f"Error saving progress for client {client_id} in session {session_id}: {str(e)}")
                    messages.error(request, 'Сталася помилка при збереженні відгуку.')
            else:
                messages.error(request, 'Будь ласка, заповніть усі поля коректно.')
        else:
            form = ClientProgressForm()

        return render(request, 'client_progress/add_client_progress.html', {
            'form': form,
            'session': session,
            'client': client,
            'trainer': trainer
        })
    except Trainers.DoesNotExist:
        logger.warning(f"User {request.user.username} has no trainer profile")
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('training_sessions')
    except Exception as e:
        logger.error(f"Error accessing add_client_progress for session {session_id}, client {client_id}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('view_session_registrations', session_id=session_id)