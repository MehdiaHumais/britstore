from django.db.models import Count, Q

from store.models import WebsiteSettings


def site_context(request):
    settings_obj = WebsiteSettings.get_solo()
    from store.models import Category, Notification
    nav_categories = Category.objects.annotate(
        published_count=Count('apps', filter=Q(apps__published=True)),
    ).filter(published_count__gt=0)[:8]
    notifications = []
    unread_notifications = 0
    if request.user.is_authenticated and request.user.is_super_admin:
        notifications = Notification.objects.all()[:10]
        unread_notifications = Notification.objects.filter(is_read=False).count()
    return {
        'site_settings': settings_obj,
        'nav_categories': nav_categories,
        'notifications': notifications,
        'unread_notifications': unread_notifications,
    }
