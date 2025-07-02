from django.db import models

# Create your models here.
from django.db import models
from auth_app.models import UserCredentials
from django.core.validators import RegexValidator, MinValueValidator
from gym_app.models import GymLocation

class TrainingType(models.Model):
    training_type_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False)
    description = models.TextField(null=False)

    class Meta:
        db_table = '"training_scheme"."training_type"'
        managed = False

    def __str__(self):
        return self.title


class Trainers(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    trainer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    birth = models.DateField(null=False)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, null=False)
    phone = models.CharField(
        max_length=32,
        null=False,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9]{7,15}$',
                message='Phone number must be 7 to 15 digits, optionally starting with +'
            )
        ]
    )
    qualification = models.CharField(max_length=255, null=False)
    specialization = models.CharField(max_length=255, null=False)
    bio = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='photos/')
    #photo = models.CharField(max_length=255, null=False)
    client_qty_constraint = models.IntegerField(
        null=False,
        validators=[MinValueValidator(0, message='Client quantity cannot be negative')]
    )
    user_credential = models.ForeignKey(
        UserCredentials,
        on_delete=models.CASCADE,
        related_name='trainer_profiles',
        db_column='user_credential_id'
    )

    class Meta:
        db_table = '"training_scheme"."trainers"'
        managed = False

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TrainingSessions(models.Model):
    STATUS_CHOICES = [
        ('заплановано', 'Заплановано'),
        ('скасовано', 'Скасовано'),
        ('завершено', 'Завершено'),
    ]

    session_id = models.AutoField(primary_key=True)
    session_date = models.DateTimeField(null=False)
    start_time = models.TimeField(null=False)
    end_time = models.TimeField(null=False)
    max_participants = models.IntegerField(
        null=False,
        validators=[MinValueValidator(1, message='Max participants must be greater than 0')]
    )
    training_type = models.ForeignKey(
        TrainingType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        db_column='training_type_id'
    )
    trainer = models.ForeignKey(
        Trainers,
        on_delete=models.RESTRICT,
        related_name='sessions',
        db_column='trainer_id'
    )
    location = models.ForeignKey(
        GymLocation,
        on_delete=models.CASCADE,
        related_name='sessions',
        db_column='location_id'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='заплановано',
        null=False
    )

    class Meta:
        db_table = '"training_scheme"."training_sessions"'
        managed = False
        unique_together = (('session_date', 'start_time', 'trainer'),)

    def __str__(self):
        return f"Session {self.session_id} on {self.session_date}"