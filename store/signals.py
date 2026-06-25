from django.db.models.signals import post_migrate
from django.dispatch import receiver

from store.models import WebsiteSettings

DEFAULT_ABOUT = """BritStore is an AI innovation company dedicated to building intelligent agents and \
automation tools that help businesses and individuals work smarter.

Founded with a vision to democratize artificial intelligence, we create practical, \
production-ready applications that solve real-world problems — from intelligent assistants \
and workflow automation to educational tools and productivity enhancers.

Our team of AI engineers, researchers, and product designers work together to deliver \
software that is powerful yet accessible, secure yet easy to use."""

DEFAULT_MISSION = """To empower organizations and individuals with cutting-edge AI applications \
that automate complexity, unlock creativity, and drive meaningful progress — one app at a time."""


@receiver(post_migrate)
def seed_initial_data(sender, **kwargs):
    if sender.name != 'store':
        return

    from django.apps import apps
    Category = apps.get_model('store', 'Category')
    WebsiteSettings = apps.get_model('store', 'WebsiteSettings')

    categories = [
        ('AI Tools', '🤖', 'Intelligent AI-powered applications and agents'),
        ('Business', '💼', 'Apps for business operations and enterprise workflows'),
        ('Education', '📚', 'Learning tools and educational resources'),
        ('Automation', '⚙️', 'Workflow automation and productivity bots'),
        ('Productivity', '📈', 'Tools to boost efficiency and organization'),
        ('Utilities', '🔧', 'Essential utility apps and helpers'),
    ]
    for name, icon, description in categories:
        Category.objects.get_or_create(name=name, defaults={'icon': icon, 'description': description})

    settings_obj, created = WebsiteSettings.objects.get_or_create(pk=1)
    if created or not settings_obj.about_content:
        settings_obj.about_content = DEFAULT_ABOUT
        settings_obj.mission = DEFAULT_MISSION
    if settings_obj.support_email == 'support@britsync.com':
        settings_obj.support_email = 'britsyncuk@gmail.com'
    settings_obj.save()
