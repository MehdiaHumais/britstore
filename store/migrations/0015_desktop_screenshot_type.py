from django.db import migrations


def mobile_to_desktop(apps, schema_editor):
    Screenshot = apps.get_model('store', 'Screenshot')
    Screenshot.objects.filter(
        app__platform='desktop',
        type='mobile',
    ).update(type='desktop')


def desktop_to_mobile(apps, schema_editor):
    Screenshot = apps.get_model('store', 'Screenshot')
    Screenshot.objects.filter(
        app__platform='desktop',
        type='desktop',
    ).update(type='mobile')


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0014_alter_screenshot_type'),
    ]

    operations = [
        migrations.RunPython(mobile_to_desktop, desktop_to_mobile),
    ]
