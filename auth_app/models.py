from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import Group

# Create your models here.
class UserCredentials(models.Model):
    user_credential_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=64, unique=True)
    user_role = models.CharField(max_length=32, default='client')
    password = models.CharField(max_length=255)
    groups = models.ManyToManyField(Group,
                                    related_name='user_credentials',
                                    blank=True,
                                    through='UserCredentialsGroups'
                                    )
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'user_credentials'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        return self.user_role == 'admin'

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return self.username

    def get_user_permissions(self, obj=None):
        """
        Повертає набір дозволів, призначених безпосередньо користувачу.
        У нашому випадку прямих дозволів немає, тому повертаємо порожній набір.
        """
        return set()

    def get_group_permissions(self, obj=None):
        """
        Повертає набір дозволів, отриманих через групи користувача.
        """
        permissions = set()
        for group in self.groups.all():
            for perm in group.permissions.select_related('content_type').all():
                permissions.add(f"{perm.content_type.app_label}.{perm.codename}")
        return permissions

    def get_all_permissions(self, obj=None):
        """
        Повертає всі дозволи користувача (прямі + групові).
        """
        return self.get_group_permissions(obj)

    def has_perm(self, perm, obj=None):
        """
        Перевіряє, чи має користувач вказаний дозвіл.
        Наприклад, perm = 'auth_app.view_gyms'.
        """
        if not self.is_active:
            return False
        return perm in self.get_all_permissions(obj)

    def has_perms(self, perm_list, obj=None):
        """
        Перевіряє, чи має користувач усі дозволи зі списку.
        """
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        """
        Перевіряє, чи має користувач будь-які дозволи для вказаного додатку.
        """
        if not self.is_active:
            return False
        for perm in self.get_all_permissions():
            if perm.startswith(f"{app_label}."):
                return True
        return False


class UserCredentialsGroups(models.Model):
    user_credentials = models.ForeignKey(
        'UserCredentials',
        on_delete=models.CASCADE,
        db_column='usercredentials_id'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column='group_id'
    )

    class Meta:
        managed = False
        db_table = 'auth_app_usercredentials_groups'