
from .models import Gym, Equipment, GymLocation, GymEquipment, Subscription, Goal
from django import forms


class GymForm(forms.ModelForm):
    class Meta:
        model = Gym
        fields = ['gym_name', 'address', 'phone', 'email']

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not phone.startswith('+') or not phone[1:].isdigit():
            raise forms.ValidationError('Телефон повинен починатися з "+" і містити лише цифри.')
        return phone

    def clean_email(self):
        email = self.cleaned_data['email']
        if '@' not in email:
            raise forms.ValidationError('Введіть коректну email-адресу.')
        return email

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['equipment_name', 'description']

    def clean_equipment_name(self):
        equipment_name = self.cleaned_data['equipment_name']
        if len(equipment_name) < 3:
            raise forms.ValidationError('Назва обладнання повинна містити щонайменше 3 символи.')
        return equipment_name


class LocationForm(forms.ModelForm):
    class Meta:
        model = GymLocation
        fields = ['location_name', 'capacity']

    def clean_location_name(self):
        location_name = self.cleaned_data['location_name']
        if len(location_name) < 3:
            raise forms.ValidationError('Назва локації повинна містити щонайменше 3 символи.')
        return location_name

    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']
        if capacity < 1:
            raise forms.ValidationError('Місткість повинна бути більше 0.')
        return capacity


class GymEquipmentForm(forms.ModelForm):
    class Meta:
        model = GymEquipment
        fields = ['equipment', 'quantity']

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 0:
            raise forms.ValidationError('Кількість не може бути від’ємною.')
        return quantity


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['subscription_name', 'price', 'duration_days', 'description']

    def clean_subscription_name(self):
        subscription_name = self.cleaned_data['subscription_name']
        if len(subscription_name) < 3:
            raise forms.ValidationError('Назва підписки повинна містити щонайменше 3 символи.')
        return subscription_name

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0.01:
            raise forms.ValidationError('Ціна повинна бути більше 0.00.')
        return price

    def clean_duration_days(self):
        duration_days = self.cleaned_data['duration_days']
        if duration_days < 1:
            raise forms.ValidationError('Тривалість повинна бути більше 0 днів.')
        return duration_days


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['goal_name', 'description']

    def clean_goal_name(self):
        goal_name = self.cleaned_data['goal_name']
        if len(goal_name) < 3:
            raise forms.ValidationError('Назва цілі повинна містити щонайменше 3 символи.')
        return goal_name



