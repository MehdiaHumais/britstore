from django.core.management.base import BaseCommand

from store.models import Category, WebsiteSettings
from store.signals import DEFAULT_ABOUT, DEFAULT_MISSION


class Command(BaseCommand):
    help = 'Seed default categories and website settings for BritStore App Store'

    def handle(self, *args, **options):
        categories = [
            ('AI Tools', '🤖', 'Intelligent AI-powered applications and agents'),
            ('Business', '💼', 'Apps for business operations and enterprise workflows'),
            ('Education', '📚', 'Learning tools and educational resources'),
            ('Automation', '⚙️', 'Workflow automation and productivity bots'),
            ('Productivity', '📈', 'Tools to boost efficiency and organization'),
            ('Utilities', '🔧', 'Essential utility apps and helpers'),
        ]
        for name, icon_emoji, description in categories:
            obj, created = Category.objects.get_or_create(
                name=name,
                defaults={'icon_emoji': icon_emoji, 'description': description},
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {name}')

        settings_obj, created = WebsiteSettings.objects.get_or_create(pk=1)
        if not settings_obj.about_content:
            settings_obj.about_content = DEFAULT_ABOUT
        if not settings_obj.mission:
            settings_obj.mission = DEFAULT_MISSION
        settings_obj.save()

        self.stdout.write(self.style.SUCCESS('Seed data applied successfully.'))
