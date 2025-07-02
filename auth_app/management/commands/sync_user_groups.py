from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from auth_app.models import UserCredentials

class Command(BaseCommand):
    help = 'Sync user_credentials with groups based on user_role'

    def handle(self, *args, **kwargs):
        # Отримуємо всі групи
        groups = {group.name: group for group in Group.objects.all()}
        users = UserCredentials.objects.all()
        synced = 0
        errors = 0

        for user in users:
            group_name = user.user_role
            if group_name in groups:
                # Очищаємо старі групи (якщо є)
                user.groups.clear()
                # Додаємо до відповідної групи
                user.groups.add(groups[group_name])
                self.stdout.write(self.style.SUCCESS(f'Synced user {user.username} to group {group_name}'))
                synced += 1
            else:
                self.stdout.write(self.style.ERROR(f'Group {group_name} not found for user {user.username}'))
                errors += 1

        self.stdout.write(self.style.SUCCESS(f'Synced {synced} users, {errors} errors'))