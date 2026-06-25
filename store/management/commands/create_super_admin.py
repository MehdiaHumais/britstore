from django.core.management.base import BaseCommand

from store.models import User


class Command(BaseCommand):
    help = 'Create a Super Admin user for BritStore App Store'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--email', default='britsyncuk@gmail.com')
        parser.add_argument('--password', default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists.'))
            return
        user = User.objects.create_user(
            username=username,
            email=options['email'],
            password=options['password'],
            role=User.ROLE_SUPER_ADMIN,
            is_staff=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f'Super Admin created: {username} / {options["password"]}',
        ))
