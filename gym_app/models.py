from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator

class Gym(models.Model):
    gym_id = models.AutoField(primary_key=True)
    gym_name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^\+?[0-9]{7,15}$', 'Телефон має містити цифри в кількості 7-15, бажано починаючи з +')]
    )
    email = models.CharField(
        max_length=100,
        unique=True,
        validators=[RegexValidator(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', 'Некореткний формат email адреси')]
    )

    def __str__(self):
        return self.gym_name

    class Meta:
        managed = False
        db_table = '"gym_scheme"."gyms"'

class GymLocation(models.Model):
    location_id = models.AutoField(primary_key=True)
    location_name = models.CharField(max_length=255, unique=True)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    gym = models.ForeignKey(
        'Gym',
        on_delete=models.CASCADE,
        db_column='gym_id',
        related_name='locations'
    )

    def __str__(self):
        return f"{self.location_name} ({self.gym.gym_name})"

    class Meta:
        managed = False
        db_table = '"gym_scheme"."gym_locations"'

class Equipment(models.Model):
    equipment_id = models.AutoField(primary_key=True)
    equipment_name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.equipment_name

    class Meta:
        managed = False
        db_table = '"gym_scheme"."equipment"'

class GymEquipment(models.Model):
    gym_equipment_id = models.AutoField(primary_key=True)
    quantity = models.SmallIntegerField(validators=[MinValueValidator(0)])
    location = models.ForeignKey(
        'GymLocation',
        on_delete=models.CASCADE,
        db_column='location_id',
        related_name='equipment'
    )
    equipment = models.ForeignKey(
        'Equipment',
        on_delete=models.RESTRICT,
        db_column='equipment_id',
        related_name='gym_equipment'
    )

    def __str__(self):
        return f"{self.equipment.equipment_name} in {self.location.location_name}"

    class Meta:
        managed = False
        db_table = '"gym_scheme"."gym_equipment"'
        unique_together = ('location_id', 'equipment_id')

class Subscription(models.Model):
    subscription_id = models.AutoField(primary_key=True)
    subscription_name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    duration_days = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField()

    def __str__(self):
        return self.subscription_name

    class Meta:
        managed = False
        db_table = '"gym_scheme"."subscriptions"'

class Goal(models.Model):
    goal_id = models.AutoField(primary_key=True)
    goal_name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.goal_name

    class Meta:
        managed = False
        db_table = '"gym_scheme"."goals"'