from rest_framework import serializers
from training_app.models import TrainingType, Trainers, TrainingSessions
from gym_app.models import GymLocation
from auth_app.models import UserCredentials
from datetime import datetime
from django.core.validators import RegexValidator
from django.db.models import Q

class TrainingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingType
        fields = ['training_type_id', 'title', 'description']

    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError('Назва типу тренування повинна містити щонайменше 3 символи.')
        return value

    def validate_description(self, value):
        if len(value) < 10:
            raise serializers.ValidationError('Опис повинен містити щонайменше 10 символів.')
        return value


class TrainersSerializer(serializers.ModelSerializer):
    user_credential_id = serializers.PrimaryKeyRelatedField(
        queryset=UserCredentials.objects.all(), source='user_credential', write_only=True
    )
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Trainers
        fields = [
            'trainer_id', 'first_name', 'last_name', 'full_name', 'birth', 'gender', 'phone',
            'qualification', 'specialization', 'bio', 'photo', 'client_qty_constraint',
            'user_credential_id'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def validate_phone(self, value):
        phone_validator = RegexValidator(
            regex=r'^\+?[0-9]{7,15}$',
            message='Номер телефону повинен містити від 7 до 15 цифр, можливо з + на початку.'
        )
        phone_validator(value)
        if Trainers.objects.filter(phone=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError('Цей номер телефону вже використовується.')
        return value

    def validate_birth(self, value):
        today = datetime.now().date()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError('Тренер повинен бути старше 18 років.')
        return value

    def validate_client_qty_constraint(self, value):
        if value < 0:
            raise serializers.ValidationError('Кількість клієнтів не може бути від’ємною.')
        return value

    def validate_photo(self, value):
        if value:
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError('Розмір фото не повинен перевищувати 5 МБ.')
        return value


class TrainingSessionsSerializer(serializers.ModelSerializer):
    training_type = TrainingTypeSerializer(read_only=True)
    training_type_id = serializers.PrimaryKeyRelatedField(
        queryset=TrainingType.objects.all(), source='training_type', write_only=True, allow_null=True
    )
    trainer = TrainersSerializer(read_only=True)
    trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=Trainers.objects.all(), source='trainer', write_only=True
    )
    location = serializers.SlugRelatedField(
        slug_field='location_name', queryset=GymLocation.objects.all()
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=GymLocation.objects.all(), source='location', write_only=True
    )

    class Meta:
        model = TrainingSessions
        fields = [
            'session_id', 'session_date', 'start_time', 'end_time', 'max_participants',
            'training_type', 'training_type_id', 'trainer', 'trainer_id', 'location',
            'location_id', 'status'
        ]

    def validate_session_date(self, value):
        today = datetime.now().date()
        if value.date() < today:
            raise serializers.ValidationError('Дата сесії не може бути в минулому.')
        return value

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        session_date = data.get('session_date')
        trainer = data.get('trainer')

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError('Час початку повинен бути раніше часу закінчення.')

        # Перевірка унікальності (session_date, start_time, trainer)
        if session_date and start_time and trainer:
            existing_session = TrainingSessions.objects.filter(
                session_date=session_date,
                start_time=start_time,
                trainer=trainer
            ).exclude(pk=self.instance.pk if self.instance else None)
            if existing_session.exists():
                raise serializers.ValidationError('Сесія на цей час для цього тренера вже існує.')

        return data