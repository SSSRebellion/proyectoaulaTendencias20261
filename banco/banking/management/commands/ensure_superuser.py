import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea o actualiza el administrador desde variables de entorno (sin Shell).'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '').strip()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip() or f'{username}@banco.local'

        if not username or not password:
            self.stdout.write(
                'Omitido: defina DJANGO_SUPERUSER_USERNAME y DJANGO_SUPERUSER_PASSWORD en Render.'
            )
            return

        grupo_admin, _ = Group.objects.get_or_create(name='administrador_bancario')

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.email = email
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            user.groups.add(grupo_admin)
            self.stdout.write(self.style.SUCCESS(f'Administrador "{username}" actualizado.'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        user.groups.add(grupo_admin)
        self.stdout.write(self.style.SUCCESS(f'Administrador "{username}" creado.'))
