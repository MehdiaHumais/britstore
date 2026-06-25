import hashlib
import json
import logging

from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from store.forms import ApiUploadForm
from store.models import ApiToken, App, AppVersion, Notification, UploadAuditLog
from store.utils import get_client_ip

logger = logging.getLogger(__name__)


def _hash_token(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


def _auth_from_token(request):
    """Authenticate a CI/CD request via Bearer token in Authorization header.
    Returns (user, token) tuple or (None, None).
    """
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Bearer '):
        return None, None
    token_str = auth[7:]
    token_hash = _hash_token(token_str)
    try:
        token = ApiToken.objects.select_related('user').get(token_hash=token_hash, is_active=True)
        return token.user, token
    except ApiToken.DoesNotExist:
        return None, None


@require_GET
def check_update(request, package_name):
    """
    GET /api/apps/<package_name>/check-update/?current_version_code=<int>
    Returns the latest version info if a newer version exists.
    """
    app = get_object_or_404(App, package_name=package_name, published=True)
    current = request.GET.get('current_version_code')
    try:
        current_code = int(current) if current else 0
    except (TypeError, ValueError):
        current_code = 0

    latest = app.versions.filter(is_latest=True).first()
    if not latest:
        latest = app.versions.order_by('-version_code').first()

    if not latest or latest.version_code <= current_code:
        return JsonResponse({'update_available': False, 'message': 'Already up to date'})

    return JsonResponse({
        'update_available': True,
        'package_name': app.package_name,
        'app_name': app.name,
        'latest_version': latest.version,
        'latest_version_code': latest.version_code,
        'force_update': latest.force_update,
        'release_notes': latest.release_notes,
        'download_url': request.build_absolute_uri(f'/api/apps/{package_name}/download-latest/'),
        'file_size': latest.file_size,
    })


@require_GET
def download_latest(request, package_name):
    """
    GET /api/apps/<package_name>/download-latest/
    Returns the APK file of the latest version.
    """
    app = get_object_or_404(App, package_name=package_name, published=True)
    latest = app.versions.filter(is_latest=True).first()
    if not latest:
        latest = app.versions.order_by('-version_code').first()
    if not latest:
        raise Http404('No versions found')

    response = FileResponse(latest.apk_file.open('rb'), content_type='application/vnd.android.package-archive')
    response['Content-Disposition'] = f'attachment; filename="{app.slug}-v{latest.version}.apk"'
    return response


@require_GET
def release_notes(request, package_name):
    """
    GET /api/apps/<package_name>/release-notes/
    Returns release notes for all versions, newest first.
    """
    app = get_object_or_404(App, package_name=package_name, published=True)
    versions = app.versions.order_by('-version_code').values(
        'version', 'version_code', 'release_notes', 'force_update', 'created_at',
    )
    return JsonResponse({
        'package_name': app.package_name,
        'app_name': app.name,
        'versions': [
            {
                'version': v['version'],
                'version_code': v['version_code'],
                'release_notes': v['release_notes'],
                'force_update': v['force_update'],
                'published_at': v['created_at'].isoformat(),
            }
            for v in versions
        ],
    })


@csrf_exempt
@require_POST
def upload_release(request):
    """
    POST /api/upload-release/
    CI/CD endpoint. Authenticated via Bearer token (Authorization header).

    Accepts multipart form data:
      - package_name (required)
      - version (required, e.g. "1.2.3")
      - version_code (required, integer)
      - apk_file (required, file)
      - app_name (optional, used when creating a new app)
      - release_notes (optional)
      - force_update (optional, boolean, default false)

    Token scoping:
      If the token has a package_name restriction, it can only upload
      releases for that exact package name.

    force_update behavior:
      When true, the Android client should show only an "Update Now" button
      (no dismiss/skip option). When false, both "Update" and "Later" buttons
      should be shown.
    """
    user, token = _auth_from_token(request)
    if not user or not token:
        return JsonResponse({'error': 'Unauthorized. Provide a valid Bearer token.'}, status=401)

    form = ApiUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': 'Validation failed', 'details': form.errors}, status=400)

    cd = form.cleaned_data
    package_name = cd['package_name']
    version = cd['version']
    version_code = cd['version_code']
    apk_file = cd['apk_file']
    release_notes = cd.get('release_notes', '') or ''
    force_update = bool(cd.get('force_update', False))

    # Enforce package-name scoping if token is restricted
    if token.package_name and token.package_name != package_name:
        return JsonResponse({
            'error': f'This token is restricted to package "{token.package_name}". Cannot upload for "{package_name}".',
        }, status=403)

    app, created = App.objects.update_or_create(
        package_name=package_name,
        defaults={
            'name': cd.get('app_name', package_name),
            'version': version,
            'slug': package_name.replace('.', '-'),
        },
    )
    if created and cd.get('app_name'):
        app.name = cd['app_name']
    if created or cd.get('app_name'):
        app.slug = app.slug or package_name.replace('.', '-')
        app.save()

    existing = AppVersion.objects.filter(app=app, version=version).first()
    if existing:
        return JsonResponse({'error': f'Version {version} already exists for {package_name}'}, status=409)

    version_obj = AppVersion(
        app=app,
        version=version,
        version_code=version_code,
        apk_file=apk_file,
        release_notes=release_notes,
        force_update=force_update,
        is_latest=True,
    )
    version_obj.save()

    if hasattr(version_obj.apk_file, 'size'):
        app.file_size = version_obj.apk_file.size
    app.version = version
    app.release_notes = release_notes
    app.save()

    token.last_used = models.functions.Now()
    token.save(update_fields=['last_used'])

    # Create audit log
    UploadAuditLog.objects.create(
        token=token,
        token_name=token.name,
        uploader=user,
        package_name=package_name,
        version=version,
        version_code=version_code,
        force_update=force_update,
        apk_path=getattr(version_obj.apk_file, 'name', ''),
        ip_address=get_client_ip(request),
    )

    Notification.objects.create(
        type=Notification.TYPE_VERSION_UPLOAD,
        title=f'{app.name} v{version} uploaded via CI/CD',
        message=release_notes[:200] if release_notes else '',
        link=f'/dashboard/apps/{app.slug}/edit/',
    )

    return JsonResponse({
        'success': True,
        'package_name': package_name,
        'version': version,
        'version_code': version_code,
        'is_latest': True,
        'force_update': force_update,
        'download_url': request.build_absolute_uri(f'/api/apps/{package_name}/download-latest/'),
    }, status=201)
