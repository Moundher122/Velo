import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser if one does not already exist."

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@velo.com")
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"Superuser '{email}' already exists. Skipping."))
            return

        User.objects.create_superuser(email=email, username=username, password=password)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{email}' created successfully."))
