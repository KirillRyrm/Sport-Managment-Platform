from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Setup initial roles and permissions based on role-table access matrix'

    def handle(self, *args, **kwargs):
        # Створюємо групи
        admin_group, _ = Group.objects.get_or_create(name='admin')
        trainer_group, _ = Group.objects.get_or_create(name='trainer')
        client_group, _ = Group.objects.get_or_create(name='client')

        # Список таблиць і моделей (вказуємо ContentType вручну, бо моделі розкидані по сервісах)
        tables = [
            'clients', 'user_credentials', 'trainers', 'client_goals', 'goals',
            'client_subscriptions', 'subscriptions', 'client_progress', 'client_feedbacks',
            'client_training_registrations', 'training_sessions', 'training_type',
            'gyms', 'gym_locations', 'gym_equipment', 'equipment'
        ]

        # Словник прав доступу
        permissions_matrix = {
            'clients': {'admin': 'CRUD', 'trainer': 'R', 'client': 'RU'},
            'user_credentials': {'admin': 'CRUD', 'trainer': 'RU', 'client': 'RU'},
            'trainers': {'admin': 'CRUD', 'trainer': 'RU', 'client': 'R'},
            'client_goals': {'admin': '', 'trainer': 'R', 'client': 'CRUD'},
            'goals': {'admin': 'CRUD', 'trainer': '', 'client': 'R'},
            'client_subscriptions': {'admin': '', 'trainer': '', 'client': 'CRUD'},
            'subscriptions': {'admin': 'CRUD', 'trainer': 'R', 'client': 'R'},
            'client_progress': {'admin': '', 'trainer': 'CRU', 'client': 'CRUD'},
            'client_feedbacks': {'admin': 'RD', 'trainer': 'R', 'client': 'CRUD'},
            'client_training_registrations': {'admin': '', 'trainer': '', 'client': 'CRUD'},
            'training_sessions': {'admin': 'RUD', 'trainer': 'CRUD', 'client': 'R'},
            'training_type': {'admin': 'CRUD', 'trainer': 'R', 'client': 'R'},
            'gyms': {'admin': 'CRUD', 'trainer': 'R', 'client': 'R'},
            'gym_locations': {'admin': 'CRUD', 'trainer': 'R', 'client': 'R'},
            'gym_equipment': {'admin': 'CRUD', 'trainer': 'R', 'client': 'R'},
            'equipment': {'admin': 'CRUD', 'trainer': 'R', 'client': 'R'},
        }

        # Створюємо дозволи для кожної таблиці
        for table in tables:
            content_type = ContentType.objects.get_or_create(
                app_label='auth_app',  # Тимчасово, можеш змінити на відповідний сервіс
                model=table
            )[0]

            # CRUD дозволи
            perms = {
                'view': Permission.objects.get_or_create(
                    codename=f'view_{table}', name=f'Can view {table}', content_type=content_type
                )[0],
                'add': Permission.objects.get_or_create(
                    codename=f'add_{table}', name=f'Can add {table}', content_type=content_type
                )[0],
                'change': Permission.objects.get_or_create(
                    codename=f'change_{table}', name=f'Can change {table}', content_type=content_type
                )[0],
                'delete': Permission.objects.get_or_create(
                    codename=f'delete_{table}', name=f'Can delete {table}', content_type=content_type
                )[0],
            }

            # Призначаємо дозволи групам
            for group_name, group in [('admin', admin_group), ('trainer', trainer_group), ('client', client_group)]:
                access = permissions_matrix[table][group_name]
                group_perms = []
                if 'R' in access:
                    group_perms.append(perms['view'])
                if 'C' in access:
                    group_perms.append(perms['add'])
                if 'U' in access:
                    group_perms.append(perms['change'])
                if 'D' in access:
                    group_perms.append(perms['delete'])
                group.permissions.add(*group_perms)

        self.stdout.write(self.style.SUCCESS('Roles and permissions setup completed'))