from django.db.models import RestrictedError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Gym, Equipment, GymLocation, GymEquipment, Subscription, Goal
from .forms import GymForm, EquipmentForm, LocationForm, GymEquipmentForm, SubscriptionForm, GoalForm
from django.db import IntegrityError

# Create your views here.


@login_required
@permission_required('auth_app.view_gyms', raise_exception=True)
def gym_list(request):
    gyms = Gym.objects.all()
    return render(request, 'gym_app/gym_list.html', {'gyms': gyms})


@login_required
@permission_required('auth_app.add_gyms', raise_exception=True)
def add_gym(request):
    if request.method == 'POST':
        form = GymForm(request.POST)
        if form.is_valid():
            Gym.objects.create(
                gym_name=form.cleaned_data['gym_name'],
                address=form.cleaned_data['address'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
            )
            messages.success(request, 'Спортивний зал успішно додано.')
            #logger.info(f"User {request.user.username} added gym: {form.cleaned_data['gym_name']}")
            return redirect('gym_list')
    else:
        form = GymForm()
    return render(request, 'gym_app/add_gym.html', {'form': form})

@login_required
@permission_required('auth_app.change_gyms', raise_exception=True)
def edit_gym(request, gym_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    if request.method == 'POST':
        form = GymForm(request.POST, instance=gym)
        if form.is_valid():
            form.save()
            messages.success(request, 'Інформацію про зал успішно оновлено.')
           # logger.info(f"User {request.user.username} updated gym: {gym.gym_name}")
            return redirect('gym_list')
    else:
        form = GymForm(instance=gym)
    return render(request, 'gym_app/edit_gym.html', {'form': form, 'gym': gym})

@login_required
@permission_required('auth_app.delete_gyms', raise_exception=True)
def delete_gym(request, gym_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    if request.method == 'POST':
        gym_name = gym.gym_name
        gym.delete()
        messages.success(request, f'Спортивний зал "{gym_name}" успішно видалено.')
        #logger.info(f"User {request.user.username} deleted gym: {gym_name}")
        return redirect('gym_list')
    return redirect('gym_list')



class GymListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        gyms = Gym.objects.all().values('gym_id', 'gym_name', 'address', 'phone', 'email')
        #logger.debug(f"API accessed by user: {request.user.username}")
        return Response(list(gyms))


################### equipment #####################

@login_required
@permission_required('auth_app.view_equipment', raise_exception=True)
def equipment_list(request):
    equipment = Equipment.objects.all()
    return render(request, 'equipment/equipment_list.html', {'equipment': equipment})

@login_required
@permission_required('auth_app.add_equipment', raise_exception=True)
def add_equipment(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            try:
                equipment = Equipment.objects.create(
                    equipment_name=form.cleaned_data['equipment_name'],
                    description=form.cleaned_data['description']
                )
                messages.success(request, 'Обладнання успішно додано.')
                return redirect('equipment_list')
            except IntegrityError as e:
                messages.error(request, 'Помилка: не вдалося додати обладнання. Перевірте унікальність назви.')
    else:
        form = EquipmentForm()
    return render(request, 'equipment/add_equipment.html', {'form': form})

@login_required
@permission_required('auth_app.change_equipment', raise_exception=True)
def edit_equipment(request, equipment_id):
    equipment = get_object_or_404(Equipment, equipment_id=equipment_id)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Інформацію про обладнання успішно оновлено.')
            return redirect('equipment_list')
    else:
        form = EquipmentForm(instance=equipment)
    return render(request, 'equipment/edit_equipment.html', {'form': form, 'equipment': equipment})

@login_required
@permission_required('auth_app.delete_equipment', raise_exception=True)
def delete_equipment(request, equipment_id):
    equipment = get_object_or_404(Equipment, equipment_id=equipment_id)
    if request.method == 'POST':
        equipment_name = equipment.equipment_name
        try:
            equipment.delete()
        except RestrictedError as e:
            messages.error(request, 'Обладнання видалити неможливо, оскільки воно використовується в спортивному залі')
            return redirect('equipment_list')
        messages.success(request, f'Обладнання "{equipment_name}" успішно видалено.')
        return redirect('equipment_list')
    return redirect('equipment_list')


class EquipmentListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm('auth_app.view_equipment'):
            return Response({"error": "Permission denied"}, status=403)
        equipment = Equipment.objects.all().values('equipment_id', 'equipment_name', 'description')
        return Response(list(equipment))


####### location #######
@login_required
@permission_required('auth_app.view_gym_locations', raise_exception=True)
def location_list(request, gym_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    locations = gym.locations.all()
    return render(request, 'locations/location_list.html', {'gym': gym, 'locations': locations})


@login_required
@permission_required('auth_app.add_gym_locations', raise_exception=True)
def add_location(request, gym_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            try:
                location = GymLocation.objects.create(
                    location_name=form.cleaned_data['location_name'],
                    capacity=form.cleaned_data['capacity'],
                    gym=gym
                )
                messages.success(request, 'Локацію успішно додано.')
                return redirect('location_list', gym_id=gym_id)
            except IntegrityError as e:
                messages.error(request, 'Помилка: не вдалося додати локацію. Перевірте унікальність назви.')
    else:
        form = LocationForm()
    return render(request, 'locations/add_location.html', {'form': form, 'gym': gym})

@login_required
@permission_required('auth_app.change_gym_locations', raise_exception=True)
def edit_location(request, gym_id, location_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    location = get_object_or_404(GymLocation, location_id=location_id, gym=gym)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, 'Інформацію про локацію успішно оновлено.')
            return redirect('location_list', gym_id=gym_id)
    else:
        form = LocationForm(instance=location)
    return render(request, 'locations/edit_location.html', {'form': form, 'gym': gym, 'location': location})

@login_required
@permission_required('auth_app.delete_gym_locations', raise_exception=True)
def delete_location(request, gym_id, location_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    location = get_object_or_404(GymLocation, location_id=location_id, gym=gym)
    if request.method == 'POST':
        location_name = location.location_name
        location.delete()
        messages.success(request, f'Локацію "{location_name}" успішно видалено.')
        return redirect('location_list', gym_id=gym_id)
    return redirect('location_list', gym_id=gym_id)


######## gym_equipment #############
@login_required
@permission_required('auth_app.add_gym_equipment', raise_exception=True)
def add_gym_equipment(request, gym_id, location_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    location = get_object_or_404(GymLocation, location_id=location_id, gym=gym)
    if request.method == 'POST':
        form = GymEquipmentForm(request.POST)
        if form.is_valid():
            try:
                gym_equipment = GymEquipment.objects.create(
                    equipment=form.cleaned_data['equipment'],
                    quantity=form.cleaned_data['quantity'],
                    location=location
                )
                messages.success(request, 'Обладнання успішно додано до локації.')
                return redirect('location_list', gym_id=gym_id)
            except IntegrityError as e:
                messages.error(request, 'Помилка: це обладнання вже є в цій локації.')
    else:
        form = GymEquipmentForm()
    return render(request, 'gym_equipment/add_gym_equipment.html', {'form': form, 'gym': gym, 'location': location})

@login_required
@permission_required('auth_app.change_gym_equipment', raise_exception=True)
def edit_gym_equipment(request, gym_id, location_id, gym_equipment_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    location = get_object_or_404(GymLocation, location_id=location_id, gym=gym)
    gym_equipment = get_object_or_404(GymEquipment, gym_equipment_id=gym_equipment_id, location=location)
    if request.method == 'POST':
        form = GymEquipmentForm(request.POST, instance=gym_equipment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Інформацію про обладнання в локації успішно оновлено.')
            return redirect('location_list', gym_id=gym_id)
    else:
        form = GymEquipmentForm(instance=gym_equipment)
    return render(request, 'gym_equipment/edit_gym_equipment.html', {'form': form, 'gym': gym, 'location': location, 'gym_equipment': gym_equipment})

@login_required
@permission_required('auth_app.delete_gym_equipment', raise_exception=True)
def delete_gym_equipment(request, gym_id, location_id, gym_equipment_id):
    gym = get_object_or_404(Gym, gym_id=gym_id)
    location = get_object_or_404(GymLocation, location_id=location_id, gym=gym)
    gym_equipment = get_object_or_404(GymEquipment, gym_equipment_id=gym_equipment_id, location=location)
    if request.method == 'POST':
        equipment_name = gym_equipment.equipment.equipment_name
        gym_equipment.delete()
        messages.success(request, f'Обладнання "{equipment_name}" успішно видалено з локації.')
        return redirect('location_list', gym_id=gym_id)
    return redirect('location_list', gym_id=gym_id)


##### subscription ######

@login_required
@permission_required('auth_app.view_subscriptions', raise_exception=True)
def subscription_list(request):
    subscriptions = Subscription.objects.all()
    return render(request, 'subscriptions/subscription_list.html', {'subscriptions': subscriptions})

@login_required
@permission_required('auth_app.add_subscriptions', raise_exception=True)
def add_subscription(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            try:
                subscription = Subscription.objects.create(
                    subscription_name=form.cleaned_data['subscription_name'],
                    price=form.cleaned_data['price'],
                    duration_days=form.cleaned_data['duration_days'],
                    description=form.cleaned_data['description']
                )
                messages.success(request, 'Підписку успішно додано.')
                return redirect('subscription_list')
            except IntegrityError as e:
                messages.error(request, 'Помилка: не вдалося додати підписку. Перевірте унікальність назви.')
    else:
        form = SubscriptionForm()
    return render(request, 'subscriptions/add_subscription.html', {'form': form})

@login_required
@permission_required('auth_app.change_subscriptions', raise_exception=True)
def edit_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, subscription_id=subscription_id)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Інформацію про підписку успішно оновлено.')
            return redirect('subscription_list')
    else:
        form = SubscriptionForm(instance=subscription)
    return render(request, 'subscriptions/edit_subscription.html', {'form': form, 'subscription': subscription})

@login_required
@permission_required('auth_app.delete_subscriptions', raise_exception=True)
def delete_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, subscription_id=subscription_id)
    if request.method == 'POST':
        subscription_name = subscription.subscription_name
        try:
            subscription.delete()
            messages.success(request, f'Підписку "{subscription_name}" успішно видалено.')
            return redirect('subscription_list')
        except RestrictedError:
            messages.error(request, f'Підписку "{subscription_name}" видалити неможливо, оскільки вона наявна у клієнтів.')
            return redirect('subscription_list')
    return redirect('subscription_list')


### goals ###

@login_required
@permission_required('auth_app.view_goals', raise_exception=True)
def goal_list(request):
    goals = Goal.objects.all()
    return render(request, 'goals/goal_list.html', {'goals': goals})

@login_required
@permission_required('auth_app.add_goals', raise_exception=True)
def add_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            try:
                goal = Goal.objects.create(
                    goal_name=form.cleaned_data['goal_name'],
                    description=form.cleaned_data['description']
                )
                messages.success(request, 'Ціль успішно додано.')
                return redirect('goal_list')
            except IntegrityError as e:
                messages.error(request, 'Помилка: не вдалося додати ціль. Перевірте унікальність назви.')
    else:
        form = GoalForm()
    return render(request, 'goals/add_goal.html', {'form': form})

@login_required
@permission_required('auth_app.change_goals', raise_exception=True)
def edit_goal(request, goal_id):
    goal = get_object_or_404(Goal, goal_id=goal_id)
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Інформацію про ціль успішно оновлено.')
            return redirect('goal_list')
    else:
        form = GoalForm(instance=goal)
    return render(request, 'goals/edit_goal.html', {'form': form, 'goal': goal})

@login_required
@permission_required('auth_app.delete_goals', raise_exception=True)
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, goal_id=goal_id)
    if request.method == 'POST':
        goal_name = goal.goal_name
        try:
            goal.delete()
        except RestrictedError as e:
            messages.error(request, "Неможливо видалити ціль, оскільки деякі клієнти поставили її для досягнення")
            return redirect('goal_list')
        messages.success(request, f'Ціль "{goal_name}" успішно видалено.')
        return redirect('goal_list')
    return redirect('goal_list')



