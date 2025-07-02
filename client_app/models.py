from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from auth_app.models import UserCredentials
from training_app.models import Trainers, TrainingSessions
from gym_app.models import Subscription, Goal
from django.core.exceptions import ValidationError
from datetime import datetime

class Client(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    email = models.CharField(
        max_length=100,
        null=False,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$',
                message='Невалідна email адреса.'
            )
        ]
    )
    phone = models.CharField(
        max_length=20,
        null=False,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9]{7,15}$',
                message='Номер телефону повинен містити від 7 до 15 цифр, можливо з + на початку.'
            )
        ]
    )
    birth = models.DateField(null=False)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, null=False)
    balance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=False,
        default=0.00,
        validators=[
            MinValueValidator(0.00, message='Баланс не може бути від’ємним.')
        ]
    )
    created_at = models.DateTimeField(null=False, auto_now_add=True)
    updated_at = models.DateTimeField(null=False, auto_now=True)
    user_credential = models.ForeignKey(
        UserCredentials,
        on_delete=models.CASCADE,
        related_name='client_profiles',
        db_column='user_credential_id',
        null=False
    )
    trainer = models.ForeignKey(
        Trainers,
        on_delete=models.SET_NULL,
        related_name='clients',
        db_column='trainer_id',
        null=True,
        blank=True
    )

    class Meta:
        db_table = '"client_scheme"."clients"'
        managed = False

    def clean(self):
        # Додаткові перевірки
        if self.email and not self.email:
            raise ValidationError({'email': 'Email не може бути порожнім.'})
        if self.phone and not self.phone:
            raise ValidationError({'phone': 'Телефон не може бути порожнім.'})
        if self.balance < 0:
            raise ValidationError({'balance': 'Баланс не може бути від’ємним.'})

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ClientTrainingRegistration(models.Model):
    registration_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='registrations',
        db_column='user_id',
        null=False
    )
    session = models.ForeignKey(
        TrainingSessions,
        on_delete=models.CASCADE,
        related_name='registrations',
        db_column='session_id',
        null=False
    )

    class Meta:
        db_table = '"client_scheme"."client_training_registrations"'
        managed = False
        unique_together = (('user', 'session'),)

    def __str__(self):
        return f"Registration {self.registration_id} for {self.user} on session {self.session}"


class ClientSubscription(models.Model):
    user_subscription_id = models.AutoField(primary_key=True)
    start_date = models.DateTimeField(null=False)
    end_date = models.DateTimeField(null=False)
    user = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        db_column='user_id',
        null=False
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.RESTRICT,
        related_name='client_subscriptions',
        db_column='subscription_id',
        null=False
    )

    class Meta:
        db_table = '"client_scheme"."client_subscriptions"'
        managed = False
        unique_together = (('user', 'subscription', 'start_date'),)

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError('Дата закінчення повинна бути пізніше дати початку.')

    def __str__(self):
        return f"Subscription {self.user_subscription_id} for {self.user}"


class ClientProgress(models.Model):
    progress_id = models.AutoField(primary_key=True)
    result = models.TextField(null=False)
    feedback = models.TextField(null=False)
    user = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='progress',
        db_column='user_id',
        null=False
    )
    session = models.ForeignKey(
        TrainingSessions,
        on_delete=models.RESTRICT,
        related_name='progress',
        db_column='session_id',
        null=False
    )

    class Meta:
        db_table = '"client_scheme"."client_progress"'
        managed = False
        unique_together = (('user', 'session'),)

    def __str__(self):
        return f"Progress {self.progress_id} for {self.user} on session {self.session}"


class ClientGoal(models.Model):
    client_goal_id = models.AutoField(primary_key=True)
    assigned_at = models.DateTimeField(null=False, default=datetime.now)
    is_achieved = models.BooleanField(null=False, default=False)
    description = models.TextField(null=False)
    user = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='goals',
        db_column='user_id',
        null=False
    )
    goal = models.ForeignKey(
        Goal,
        on_delete=models.RESTRICT,
        related_name='client_goals',
        db_column='goal_id',
        null=False
    )

    class Meta:
        db_table = '"client_scheme"."client_goals"'
        managed = False
        unique_together = (('user', 'goal', 'assigned_at'),)

    def __str__(self):
        return f"Goal {self.client_goal_id} for {self.user}"


class ClientFeedback(models.Model):
    RATING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    feedback_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, null=False)
    description = models.TextField(null=False)
    date = models.DateTimeField(null=False, default=datetime.now)
    rating = models.SmallIntegerField(
        null=False,
        choices=RATING_CHOICES,
        validators=[
            MinValueValidator(1, message='Рейтинг повинен бути від 1 до 5.'),
            MaxValueValidator(5, message='Рейтинг повинен бути від 1 до 5.')
        ]
    )
    user = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        db_column='user_id',
        null=False
    )
    trainer = models.ForeignKey(
        Trainers,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        db_column='trainer_id',
        null=False
    )

    class Meta:
        db_table = '"client_scheme"."client_feedbacks"'
        managed = False
        unique_together = (('user', 'trainer', 'date'),)

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({'rating': 'Рейтинг повинен бути від 1 до 5.'})

    def __str__(self):
        return f"Feedback {self.feedback_id} from {self.user} for {self.trainer}"