import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not password:
            self.stdout.write("DJANGO_SUPERUSER_PASSWORD not set — skipping superuser creation.")
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' already exists — skipping.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(f"Superuser '{username}' created.")

        manager_group, _ = Group.objects.get_or_create(name="Manager")
        user = User.objects.get(username=username)
        user.groups.add(manager_group)
        self.stdout.write(f"Added '{username}' to Manager group.")