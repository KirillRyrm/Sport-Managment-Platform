# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages

from client_app.forms import ClientProgressForm
from client_app.models import ClientTrainingRegistration, ClientProgress
from .models import TrainingType, Trainers, TrainingSessions
from .forms import TrainingTypeForm, LocationRankingForm, TrainerForm, TrainingSessionForm, ClientAttendanceForm, TrainingTypeRankingForm
from gym_app.models import Gym, GymLocation
from django.db import IntegrityError, InternalError, transaction
from django.db.models import Avg, ProtectedError, RestrictedError
import logging
import os
from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db import models
from django.db import connection


class ClientAttendanceRecord(models.Model):
    id = models.AutoField(primary_key=True)
    rank = models.BigIntegerField()
    first_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birth = models.DateField()
    gender = models.CharField(max_length=50)
    visit_count = models.BigIntegerField()

    class Meta:
        managed = False





logger = logging.getLogger(__name__)

### training type ####

@login_required
@permission_required('auth_app.view_training_type', raise_exception=True)
def training_type_list(request):
    training_types = TrainingType.objects.all()
    return render(request, 'training_type/training_type_list.html', {'training_types': training_types})

@login_required
@permission_required('auth_app.add_training_type', raise_exception=True)
def add_training_type(request):
    if request.method == 'POST':
        form = TrainingTypeForm(request.POST)
        if form.is_valid():
            try:
                training_type = TrainingType.objects.create(
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description']
                )
                messages.success(request, 'Тип тренування успішно додано.')
                return redirect('training_type_list')
            except IntegrityError as e:
                messages.error(request, 'Помилка: не вдалося додати тип тренування. Перевірте унікальність назви.')
    else:
        form = TrainingTypeForm()
    return render(request, 'training_type/add_training_type.html', {'form': form})

@login_required
@permission_required('auth_app.change_training_type', raise_exception=True)
def edit_training_type(request, training_type_id):
    training_type = get_object_or_404(TrainingType, training_type_id=training_type_id)
    if request.method == 'POST':
        form = TrainingTypeForm(request.POST, instance=training_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Інформацію про тип тренування успішно оновлено.')
            return redirect('training_type_list')
    else:
        form = TrainingTypeForm(instance=training_type)
    return render(request, 'training_type/edit_training_type.html', {'form': form, 'training_type': training_type})

@login_required
@permission_required('auth_app.delete_training_type', raise_exception=True)
def delete_training_type(request, training_type_id):
    training_type = get_object_or_404(TrainingType, training_type_id=training_type_id)
    if request.method == 'POST':
        title = training_type.title
        training_type.delete()
        messages.success(request, f'Тип тренування "{title}" успішно видалено.')
        return redirect('training_type_list')
    return redirect('training_type_list')


### trainers ###
@login_required
def trainer_profile(request):
    try:
        trainer = Trainers.objects.get(user_credential=request.user)
    except Trainers.DoesNotExist:
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')

    if request.user.user_role != 'trainer':
        messages.error(request, 'Доступ до профілю тренера дозволено лише тренерам.')
        return redirect('home')

    if request.method == 'POST':
        form = TrainerForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Профіль успішно оновлено.')
                return redirect('trainer_profile')
            except IntegrityError as e:
                messages.error(request, 'Помилка: не вдалося оновити профіль. Перевірте унікальність телефону.')
    else:
        form = TrainerForm(instance=trainer)

    return render(request, 'trainers/trainer_profile.html', {
        'trainer': trainer,
        'form': form
    })

@login_required
@permission_required('auth_app.view_trainers', raise_exception=True)
def trainers_list(request):
    trainers = Trainers.objects.all().annotate(
        average_rating=Avg('feedbacks__rating')
    )
    return render(request, 'trainers/trainers_list.html', {
        'trainers': trainers,
        'is_admin': request.user.user_role == 'admin'
    })


@login_required
@permission_required('auth_app.delete_trainers', raise_exception=True)
def delete_trainer(request, trainer_id):
    trainer = get_object_or_404(Trainers, trainer_id=trainer_id)
    if request.method == 'POST':
        try:
            # Зберігаємо дані для логування та повідомлення
            full_name = f"{trainer.first_name} {trainer.last_name}"
            photo_path = trainer.photo.path if trainer.photo else None

            # Видаляємо тренера
            trainer.delete()

            # Видаляємо фото з медіа, якщо воно існує
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)

            messages.success(request, f'Тренера "{full_name}" успішно видалено.')
        except RestrictedError as e:
            messages.error(request, f'Тренер {full_name} на даний момент є активним (має тренувальні сесії).')
            return redirect('trainers_list')
        except Exception as e:
            messages.error(request, f'Помилка при видаленні тренера "{full_name}".')
        return redirect('trainers_list')
    return redirect('trainers_list')


@login_required
@permission_required('auth_app.view_training_sessions', raise_exception=True)
def training_sessions(request):
    try:

        trainer = Trainers.objects.get(user_credential=request.user)
        sessions = TrainingSessions.objects.filter(trainer=trainer).order_by('session_date', 'start_time')

        current_time = timezone.now()

        # Проходим по каждой сессии и проверяем время её завершения
        for session in sessions:

            #session_start = datetime.combine(session.session_date, session.start_time)
            session_end = datetime.combine(session.session_date, session.end_time)



            # Если сессия завершилась, но статус ещё не установлен как 'завершено'
            if session_end < current_time and session.status != 'завершено':
                session.status = 'завершено'
                session.save(update_fields=['status'])
        return render(request, 'training_sessions/training_sessions_list.html', {
            'sessions': sessions,
            'trainer': trainer
        })
    except Trainers.DoesNotExist:
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')


@login_required
@permission_required('auth_app.add_training_sessions', raise_exception=True)
def add_training_session(request):
    try:
        trainer = Trainers.objects.get(user_credential=request.user)
    except Trainers.DoesNotExist:
        logger.error(f"User {request.user.username} (role: {request.user.user_role}) attempted to add training session but no matching Trainers record found.")
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')

    if request.method == 'POST':
        form = TrainingSessionForm(request.POST)
        if form.is_valid():
            try:
                session = form.save(commit=False)
                session.trainer = trainer
                session.save()
                messages.success(request, 'Тренувальну сесію успішно додано.')
                logger.info(f"User {request.user.username} added training session: {session.session_id} on {session.session_date}")
                return redirect('training_sessions')

            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to add training session: {str(e)}")
                messages.error(request, 'Помилка: сесія на цей час для цього тренера вже існує.')

            except InternalError as e:
                logger.error(
                    f"User {request.user.username} failed to add training session due to InternalError: {str(e)}")
                if 'зайнятий у цей час' in str(e):
                    messages.error(request, f'Помилка: Ви вже маєте заняття у цей час.')
                elif 'уже має заняття на іншій локації' in str(e):
                    messages.error(request, f'Помилка: Ви вже маєте заняття у іншій локації в цей день.')
                else:
                    messages.error(request, 'Сталася внутрішня помилка бази даних. Зверніться до адміністратора.')

        else:
            logger.warning(f"User {request.user.username} failed to add training session: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Помилка: {error}')
    else:
        form = TrainingSessionForm()


    gyms = Gym.objects.all()
    gym_locations = {
        gym.gym_id: [
            {'location_id': loc.location_id, 'location_name': loc.location_name}
            for loc in GymLocation.objects.filter(gym=gym)
        ]
        for gym in gyms
    }
    return render(request, 'training_sessions/add_training_session.html', {
        'form': form,
        'trainer': trainer,
        'gyms': gyms,
        'gym_locations': gym_locations
    })


@login_required
@permission_required('auth_app.change_training_sessions', raise_exception=True)
def edit_training_session(request, session_id):
    try:
        trainer = Trainers.objects.get(user_credential=request.user)
    except Trainers.DoesNotExist:
        logger.error(f"User {request.user.username} (role: {request.user.user_role}) attempted to edit training session but no matching Trainers record found.")
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')

    session = get_object_or_404(TrainingSessions, session_id=session_id, trainer=trainer)

    if request.method == 'POST':
        form = TrainingSessionForm(request.POST, instance=session)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Тренувальну сесію успішно оновлено.')
                logger.info(f"User {request.user.username} updated training session: {session.session_id} on {session.session_date}")
                return redirect('training_sessions')
            except IntegrityError as e:
                logger.error(f"User {request.user.username} failed to update training session: {str(e)}")
                messages.error(request, 'Помилка: сесія на цей час для цього тренера вже існує.')
        else:
            logger.warning(f"User {request.user.username} failed to update training session: {form.errors}")
    else:
        form = TrainingSessionForm(instance=session)

    gyms = Gym.objects.all()
    gym_locations = {
        gym.gym_id: [
            {'location_id': loc.location_id, 'location_name': loc.location_name}
            for loc in GymLocation.objects.filter(gym=gym)
        ]
        for gym in gyms
    }
    return render(request, 'training_sessions/edit_training_session.html', {
        'form': form,
        'trainer': trainer,
        'gyms': gyms,
        'gym_locations': gym_locations,
        'session': session
    })

@login_required
@permission_required('auth_app.delete_training_sessions', raise_exception=True)
def delete_training_session(request, session_id):
    try:
        trainer = Trainers.objects.get(user_credential=request.user)
    except Trainers.DoesNotExist:
        logger.error(f"User {request.user.username} (role: {request.user.user_role}) attempted to delete training session but no matching Trainers record found.")
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')

    session = get_object_or_404(TrainingSessions, session_id=session_id, trainer=trainer)

    if request.method == 'POST':
        try:
            session_date = session.session_date
            session.delete()
            messages.success(request, 'Тренувальну сесію успішно видалено.')
            logger.info(f"User {request.user.username} deleted training session: {session_id} on {session_date}")
            return redirect('training_sessions')
        except RestrictedError as e:
            logger.warning(f"User {request.user.username} attempted to delete session {session_id} but it is protected: {e}")
            messages.error(request,'Не можна видалити це тренування, оскільки є записаний прогрес клієнтів, пов’язаний із ним.')
        except Exception as e:
            logger.exception(f"Unexpected error when deleting session {session_id}: {e}")
            messages.error(request, 'Виникла помилка під час видалення тренування.')
    return redirect('training_sessions')


@login_required
@permission_required('auth_app.view_training_sessions', raise_exception=True)
def view_session_registrations(request, session_id):
    try:
        trainer = Trainers.objects.get(user_credential=request.user)
        try:
            session = TrainingSessions.objects.get(session_id=session_id, trainer=trainer)
        except TrainingSessions.DoesNotExist:
            logger.warning(f"Session {session_id} not found or not owned by trainer {request.user.username}")
            messages.error(request, 'Сесію не знайдено або вона не належить вам.')
            return redirect('training_sessions')
        # Получаем клиентов, зарегистрированных на сессию
        registrations = ClientTrainingRegistration.objects.filter(session=session).select_related('user')
        clients = [registration.user for registration in registrations]
        logger.info(f"Trainer {request.user.username} viewed registrations for session {session_id} (count: {len(clients)})")
        return render(request, 'training_sessions/registered_clients.html', {
            'session': session,
            'clients': clients,
            'trainer': trainer
        })
    except Trainers.DoesNotExist:
        logger.warning(f"User {request.user.username} has no trainer profile")
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error accessing registrations for session {session_id} by user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('training_sessions')


@login_required
@permission_required('auth_app.view_client_progress', raise_exception=True)
def my_client_progress(request):
    try:
        trainer = Trainers.objects.get(user_credential=request.user)
        # Получаем прогресс клиентов тренера
        progress_records = ClientProgress.objects.filter(
            user__trainer=trainer
        ).select_related('user', 'session', 'session__training_type').order_by('-session__session_date')
        logger.info(f"Trainer {request.user.username} viewed client progress records (count: {progress_records.count()})")
        return render(request, 'training_sessions/my_client_progress.html', {
            'progress_records': progress_records,
            'trainer': trainer
        })
    except Trainers.DoesNotExist:
        logger.warning(f"User {request.user.username} has no trainer profile")
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error accessing my_client_progress for user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('home')


@login_required
@permission_required('auth_app.change_client_progress', raise_exception=True)
def edit_client_progress(request, progress_id):
    try:
        trainer = Trainers.objects.get(user_credential=request.user)
        try:
            progress = ClientProgress.objects.get(
                progress_id=progress_id,
                user__trainer=trainer
            )
        except ClientProgress.DoesNotExist:
            logger.warning(f"Progress {progress_id} not found or not owned by trainer {request.user.username}")
            messages.error(request, 'Запис прогресу не знайдено або не належить вам.')
            return redirect('my_client_progress')

        if request.method == 'POST':
            form = ClientProgressForm(request.POST, instance=progress)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        form.save()
                        logger.info(f"Trainer {request.user.username} edited progress {progress_id}")
                        messages.success(request, f'Прогрес для {progress.user.first_name} {progress.user.last_name} відредаговано!')
                        return redirect('my_client_progress')
                except Exception as e:
                    logger.error(f"Error saving progress {progress_id} by user {request.user.username}: {str(e)}")
                    messages.error(request, 'Сталася помилка при збереженні змін.')
            else:
                messages.error(request, 'Будь ласка, заповніть усі поля коректно.')
        else:
            form = ClientProgressForm(instance=progress)

        return render(request, 'training_sessions/edit_client_progress.html', {
            'form': form,
            'progress': progress,
            'trainer': trainer
        })
    except Trainers.DoesNotExist:
        logger.warning(f"User {request.user.username} has no trainer profile")
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error accessing edit_client_progress for progress {progress_id}: {str(e)}")
        messages.error(request, 'Сталася помилка при завантаженні сторінки.')
        return redirect('my_client_progress')

@login_required
@permission_required('auth_app.change_client_progress', raise_exception=True)
def delete_client_progress(request, progress_id):
    if request.method != 'POST':
        logger.warning(f"Invalid method for delete_client_progress {progress_id} by user {request.user.username}")
        messages.error(request, 'Неправильний метод запиту.')
        return redirect('my_client_progress')

    try:
        trainer = Trainers.objects.get(user_credential=request.user)
        try:
            progress = ClientProgress.objects.get(
                progress_id=progress_id,
                user__trainer=trainer
            )
        except ClientProgress.DoesNotExist:
            logger.warning(f"Progress {progress_id} not found or not owned by trainer {request.user.username}")
            messages.error(request, 'Запис прогресу не знайдено або не належить вам.')
            return redirect('my_client_progress')

        progress.delete()
        logger.info(f"Trainer {request.user.username} deleted progress {progress_id}")
        messages.success(request, f'Прогрес для {progress.user.first_name} {progress.user.last_name} видалено!')
        return redirect('my_client_progress')
    except Trainers.DoesNotExist:
        logger.warning(f"User {request.user.username} has no trainer profile")
        messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error deleting progress {progress_id} by user {request.user.username}: {str(e)}")
        messages.error(request, 'Сталася помилка при видаленні прогресу.')
        return redirect('my_client_progress')



### analytics ###
@login_required
def analytics_page(request):
    if request.user.user_role != 'admin':
        messages.error(request, 'Вам не доступно мати змогу займатися аналітикою.')
        return redirect('home')
    return render(request, 'analytics/analytics.html')


@login_required
@permission_required(('auth_app.view_clients', 'auth_app.view_user_credentials',
                      'auth_app.view_training_sessions',
                      ), raise_exception=True)
def client_attendance(request):
    if request.user.user_role != 'admin':
        logger.warning(f"User {request.user.username} attempted to access client attendance without admin role")
        messages.error(request, 'Вам не доступно мати змогу займатися аналітикою.')
        return redirect('home')

    form = ClientAttendanceForm(request.GET or None)
    attendance_records = []

    if form.is_valid():
        try:
            trainer_id = form.cleaned_data['trainer'].trainer_id if form.cleaned_data['trainer'] else None
            training_type_id = form.cleaned_data['training_type'].training_type_id if form.cleaned_data['training_type'] else None
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM training_scheme.get_client_attendance_ranking(%s, %s, %s, %s)
                """, [trainer_id, training_type_id, start_date, end_date])
                columns = [col[0] for col in cursor.description]
                attendance_records = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]

            logger.info(f"Admin {request.user.username} viewed client attendance (records: {len(list(attendance_records))})")
        except Exception as e:
            logger.error(f"Error fetching client attendance for user {request.user.username}: {str(e)}")
            messages.error(request, 'Сталася помилка при отриманні даних аналітики.')

    return render(request, 'analytics/client_attendance.html', {
        'form': form,
        'attendance_records': attendance_records
    })


@login_required
@permission_required(('auth_app.view_training_sessions', 'auth_app.view_training_type'), raise_exception=True)
def training_type_ranking(request):
    if request.user.user_role != 'admin':
        logger.warning(f"User {request.user.username} attempted to access training type ranking without admin role")
        messages.error(request, 'Вам не доступно мати змогу займатися аналітикою.')
        return redirect('home')

    form = TrainingTypeRankingForm(request.GET or None)
    ranking_records = []

    if form.is_valid():
        try:
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM training_scheme.get_training_type_ranking(%s, %s)
                """, [start_date, end_date])
                columns = [col[0] for col in cursor.description]
                ranking_records = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]

            logger.info(f"Admin {request.user.username} viewed training type ranking (records: {len(ranking_records)})")
        except Exception as e:
            logger.error(f"Error fetching training type ranking for user {request.user.username}: {str(e)}")
            messages.error(request, 'Сталася помилка при отриманні даних аналітики.')

    return render(request, 'analytics/training_type_ranking.html', {
        'form': form,
        'ranking_records': ranking_records
    })


@login_required
@permission_required(('auth_app.view_gym_locations', 'auth_app.view_training_sessions'), raise_exception=True)
def location_ranking(request):
    if request.user.user_role != 'admin':
        logger.warning(f"User {request.user.username} attempted to access location ranking without admin role")
        messages.error(request, 'Вам не доступно мати змогу займатися аналітикою.')
        return redirect('home')

    form = LocationRankingForm(request.GET or None)
    ranking_records = []

    if form.is_valid():
        try:
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM training_scheme.get_location_ranking(%s, %s)
                """, [start_date, end_date])
                columns = [col[0] for col in cursor.description]
                ranking_records = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]

            logger.info(f"Admin {request.user.username} viewed location ranking (records: {len(ranking_records)})")
        except Exception as e:
            logger.error(f"Error fetching location ranking for user {request.user.username}: {str(e)}")
            messages.error(request, 'Сталася помилка при отриманні даних аналітики.')

    return render(request, 'analytics/location_ranking.html', {
        'form': form,
        'ranking_records': ranking_records
    })

### api requests ###
# @login_required
# @permission_required('training_app.view_training_sessions', raise_exception=True)
# def training_sessions_api(request):
#     try:
#         trainer = Trainers.objects.get(user_credential=request.user)
#
#         api_url = "127.0.0.1:8000/api/locations/"
#         response = requests.get(api_url)
#
#         locations = []
#         if response.status_code == 200:
#             locations = response.json()
#         else:
#             messages.error(request, 'Не вдалося отримати список локацій. Спробуйте пізніше.')
#
#         # Фільтрація сесій
#         location_id = request.GET.get('location_id')
#         sessions = TrainingSessions.objects.filter(trainer=trainer)
#         if location_id:
#             try:
#                 sessions = sessions.filter(location_id=int(location_id))
#             except ValueError:
#                 messages.error(request, 'Невалідний ідентифікатор локації.')
#
#         sessions = sessions.order_by('session_date', 'start_time')
#
#         return render(request, 'training_app/training_sessions_list.html', {
#             'sessions': sessions,
#             'trainer': trainer,
#             'locations': locations
#         })
#     except Trainers.DoesNotExist:
#         messages.error(request, 'Профіль тренера не знайдено. Зверніться до адміністратора.')
#         return redirect('home')

