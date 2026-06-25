from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def dashboard_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.can_access_dashboard:
            messages.error(request, 'You do not have permission to access the dashboard.')
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def super_admin_required(view_func):
    @dashboard_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_super_admin:
            messages.error(request, 'Super Admin access required.')
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def user_can_edit_app(user, app):
    if user.is_super_admin:
        return True
    if user.is_app_manager and app.uploaded_by_id == user.id:
        return True
    return False


def user_can_delete_app(user, app):
    return user.is_super_admin


def app_edit_required(view_func):
    @dashboard_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from store.models import App
        slug = kwargs.get('slug') or kwargs.get('app_slug')
        app = App.objects.filter(slug=slug).first()
        if not app:
            messages.error(request, 'App not found.')
            return redirect('dashboard_apps')
        if not user_can_edit_app(request.user, app):
            messages.error(request, 'You can only edit apps you uploaded.')
            raise PermissionDenied
        kwargs['app'] = app
        return view_func(request, *args, **kwargs)
    return wrapper
