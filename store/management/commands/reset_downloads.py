from django.core.management.base import BaseCommand

from store.models import App, Download


class Command(BaseCommand):
    help = 'Reset download counts to match actual download records'

    def handle(self, *args, **options):
        total_downloads = Download.objects.count()
        self.stdout.write(f'Total Download records: {total_downloads}')

        for app in App.objects.all():
            actual = app.downloads.count()
            if app.download_count != actual:
                self.stdout.write(f'  {app.name}: download_count was {app.download_count}, reset to {actual}')
                app.download_count = actual
                app.save(update_fields=['download_count'])
            else:
                self.stdout.write(f'  {app.name}: download_count {app.download_count} OK')

        self.stdout.write(self.style.SUCCESS('Download counts synced.'))
