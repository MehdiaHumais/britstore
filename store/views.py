import hashlib
import json
import logging
import uuid
from datetime import timedelta
from enum import Enum

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Max, Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from user_agents import parse
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
    UserVerificationRequirement,
)

from store.forms import (
    AdminUserEditForm,
    AdminUserForm,
    AppForm,
    AppVersionForm,
    CategoryForm,
    ContactForm,
    LoginForm,
    ScreenshotForm,
    SignUpForm,
    WebsiteSettingsForm,
)
from store.models import (
    AndroidFingerprintDevice,
    App,
    AppVersion,
    ApiToken,
    Category,
    ContactMessage,
    Download,
    FingerprintCredential,
    Notification,
    Rating,
    Screenshot,
    UploadAuditLog,
    User,
    WebsiteSettings,
)
from store.permissions import (
    app_edit_required,
    dashboard_required,
    super_admin_required,
    user_can_delete_app,
    user_can_edit_app,
)
from store.services import scan_file_for_malware, send_email_resend
from store.utils import validate_screenshot_file

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_country(request):
    return request.META.get('HTTP_CF_IPCOUNTRY', 'Unknown') or 'Unknown'


def get_device_type(request):
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    ua = parse(ua_string)
    if ua.is_mobile:
        return 'Mobile'
    if ua.is_tablet:
        return 'Tablet'
    if ua.is_pc:
        return 'Desktop'
    return 'Unknown'


def _published_apps():
    return App.objects.filter(published=True).select_related('category', 'uploaded_by').prefetch_related('ratings')


# ── Public views ──────────────────────────────────────────────────────────────

def home(request):
    apps = _published_apps()
    return render(request, 'home.html', {
        'featured_apps': apps.filter(featured=True)[:6],
        'latest_apps': apps[:8],
        'popular_apps': apps.order_by('-download_count')[:8],
        'categories': Category.objects.annotate(
            app_count=Count('apps', filter=Q(apps__published=True)),
        ).filter(app_count__gt=0),
    })


def app_detail(request, slug):
    app = get_object_or_404(_published_apps(), slug=slug)
    versions = app.versions.all()
    all_shots = app.screenshots.all()
    mobile_shots = [s for s in all_shots if s.type == Screenshot.TYPE_MOBILE]
    tablet_shots = [s for s in all_shots if s.type == Screenshot.TYPE_TABLET]
    similar_apps = _published_apps().filter(category=app.category).exclude(pk=app.pk)[:8]
    return render(request, 'app_detail.html', {
        'app': app,
        'versions': versions,
        'screenshots': all_shots,
        'mobile_screenshots': mobile_shots,
        'tablet_screenshots': tablet_shots,
        'similar_apps': similar_apps,
    })


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    apps = _published_apps().filter(category=category)
    return render(request, 'category.html', {'category': category, 'apps': apps})


def search_view(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    apps = _published_apps()
    if query:
        apps = apps.filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(full_description__icontains=query)
            | Q(package_name__icontains=query),
        )
    if category_slug:
        apps = apps.filter(category__slug=category_slug)
    categories = Category.objects.all()
    return render(request, 'search.html', {
        'apps': apps,
        'query': query,
        'category_slug': category_slug,
        'categories': categories,
    })


def downloads_view(request):
    apps = _published_apps().order_by('-updated_at')
    q = request.GET.get('q', '').strip()
    if q:
        apps = apps.filter(name__icontains=q)
    return render(request, 'downloads.html', {'apps': apps, 'query': q})


def about_view(request):
    settings_obj = WebsiteSettings.get_solo()
    return render(request, 'about.html', {'settings': settings_obj})


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save()
            Notification.objects.create(
                type=Notification.TYPE_CONTACT,
                title=f'New message from {msg.name}',
                message=msg.subject,
                link='/dashboard/messages/',
            )
            send_email_resend(
                to_email=WebsiteSettings.get_solo().support_email,
                subject=f'[BritStore Contact] {msg.subject}',
                text_body=f'From: {msg.name} ({msg.email})\n\n{msg.message}',
            )
            messages.success(request, 'Thank you! Your message has been sent.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        if request.user.can_access_dashboard and request.GET.get('next', '').startswith('/dashboard'):
            return redirect(request.GET['next'])
        return redirect('home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get('next', 'home')
        messages.success(request, f'Welcome back, {request.user.username}!')
        return redirect(next_url)
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome to {WebsiteSettings.get_solo().site_name}, {user.username}!')
        return redirect('home')
    return render(request, 'signup.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        email = request.POST.get('email', '').strip()
        current_password = request.POST.get('current_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, 'Email already in use.')
            else:
                user.email = email

        if current_password and new_password1:
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password1 != new_password2:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password1) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                user.set_password(new_password1)
                messages.success(request, 'Password updated. Please sign in again.')
                logout(request)
                return redirect('login')

        user.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')

    return render(request, 'profile.html')


# ── WebAuthn Fingerprint Auth ─────────────────────────────────────────────────

def _get_origin(request):
    return f"{request.scheme}://{request.get_host()}"

def _get_rp_id(request):
    return request.get_host().split(':')[0]

def _make_username():
    return f'fp_{uuid.uuid4().hex[:12]}'

def _snake_to_camel(name):
    parts = name.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])

def _webauthn_options_to_dict(obj):
    if obj is None:
        return None
    if isinstance(obj, bytes):
        import base64
        return base64.urlsafe_b64encode(obj).rstrip(b'=').decode()
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for field_name in obj.__dataclass_fields__:
            val = getattr(obj, field_name)
            if val is not None:
                result[_snake_to_camel(field_name)] = _webauthn_options_to_dict(val)
        return result
    if isinstance(obj, list):
        return [_webauthn_options_to_dict(item) for item in obj]
    return obj


def webauthn_register_begin(request):
    rp_id = _get_rp_id(request)
    origin = _get_origin(request)
    challenge = uuid.uuid4().bytes
    request.session['webauthn_challenge'] = challenge.hex()
    request.session['webauthn_origin'] = origin

    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_name=_make_username(),
        challenge=challenge,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    return JsonResponse(_webauthn_options_to_dict(options), safe=False)


@csrf_exempt
def webauthn_register_complete(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    challenge_hex = request.session.pop('webauthn_challenge', None)
    expected_origin = request.session.pop('webauthn_origin', None)
    if not challenge_hex or not expected_origin:
        return JsonResponse({'error': 'No registration in progress'}, status=400)

    try:
        verified = verify_registration_response(
            credential=body,
            expected_challenge=bytes.fromhex(challenge_hex),
            expected_rp_id=_get_rp_id(request),
            expected_origin=expected_origin,
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    cred_id_b64 = verified.credential_id.hex()
    if FingerprintCredential.objects.filter(credential_id=cred_id_b64).exists():
        return JsonResponse({'error': 'This device is already registered'}, status=409)

    user = User.objects.create_user(
        username=_make_username(),
        is_fingerprint_user=True,
    )

    FingerprintCredential.objects.create(
        user=user,
        credential_id=cred_id_b64,
        public_key=verified.credential_public_key.hex(),
        sign_count=verified.sign_count,
        device_info=request.META.get('HTTP_USER_AGENT', '')[:500],
    )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    return JsonResponse({
        'status': 'ok',
        'user_id': user.pk,
        'credential_id': cred_id_b64,
    })


def webauthn_login_begin(request):
    credential_id = request.GET.get('credential_id', '')
    if not credential_id:
        return JsonResponse({'error': 'credential_id required'}, status=400)

    try:
        cred = FingerprintCredential.objects.get(credential_id=credential_id)
    except FingerprintCredential.DoesNotExist:
        return JsonResponse({'error': 'Credential not found'}, status=404)

    rp_id = _get_rp_id(request)
    origin = _get_origin(request)
    challenge = uuid.uuid4().bytes
    request.session['webauthn_challenge'] = challenge.hex()
    request.session['webauthn_origin'] = origin
    request.session['webauthn_user_id'] = cred.user_id

    options = generate_authentication_options(
        rp_id=rp_id,
        challenge=challenge,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=bytes.fromhex(cred.credential_id)),
        ],
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    return JsonResponse(_webauthn_options_to_dict(options), safe=False)


@csrf_exempt
def webauthn_login_complete(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    challenge_hex = request.session.pop('webauthn_challenge', None)
    expected_origin = request.session.pop('webauthn_origin', None)
    user_id = request.session.pop('webauthn_user_id', None)
    if not challenge_hex or not expected_origin or not user_id:
        return JsonResponse({'error': 'No login in progress'}, status=400)

    cred_id = body.get('id', '')
    try:
        cred = FingerprintCredential.objects.get(credential_id=cred_id)
    except FingerprintCredential.DoesNotExist:
        return JsonResponse({'error': 'Credential not found'}, status=404)

    if cred.user_id != user_id:
        return JsonResponse({'error': 'Credential does not match user'}, status=403)

    try:
        verified = verify_authentication_response(
            credential=body,
            expected_challenge=bytes.fromhex(challenge_hex),
            expected_rp_id=_get_rp_id(request),
            expected_origin=expected_origin,
            credential_public_key=bytes.fromhex(cred.public_key),
            credential_current_sign_count=cred.sign_count,
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    cred.sign_count = verified.new_sign_count
    cred.save(update_fields=['sign_count'])

    login(request, cred.user, backend='django.contrib.auth.backends.ModelBackend')

    return JsonResponse({'status': 'ok', 'user_id': cred.user_id})


def fingerprint_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({'is_fingerprint_user': False})
    return JsonResponse({
        'is_fingerprint_user': request.user.is_fingerprint_user,
        'has_upgraded': request.user.has_upgraded,
        'has_credential': hasattr(request.user, 'fingerprint_credential'),
        'credential_id': request.user.fingerprint_credential.credential_id if hasattr(request.user, 'fingerprint_credential') else None,
    })


@login_required
def attach_email_password(request):
    user = request.user
    if not user.is_fingerprint_user:
        messages.error(request, 'This account does not use fingerprint authentication.')
        return redirect('profile')
    if user.has_upgraded:
        messages.info(request, 'You already have an email and password attached.')
        return redirect('profile')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exclude(pk=user.pk).exists():
            errors.append('Email already in use.')
        if not password1 or len(password1) < 8:
            errors.append('Password must be at least 8 characters.')
        elif password1 != password2:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            user.email = email
            user.set_password(password1)
            user.has_upgraded = True
            user.username = email.split('@')[0]
            user.save(update_fields=['email', 'password', 'has_upgraded', 'username'])
            messages.success(request, 'Email and password attached! You can now log in with either method.')
            return redirect('profile')

    return render(request, 'attach_email.html', {'user': user})


# ── Android Fingerprint API ────────────────────────────────────────────────────

@csrf_exempt
def android_fingerprint_signup(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    device_token = data.get('device_token')
    if not device_token:
        return JsonResponse({'status': 'error', 'message': 'Missing device_token'}, status=400)
    hashed = hashlib.sha256(device_token.encode()).hexdigest()
    if AndroidFingerprintDevice.objects.filter(device_id=hashed).exists():
        device = AndroidFingerprintDevice.objects.get(device_id=hashed)
        if device.user:
            login(request, device.user)
            return JsonResponse({'status': 'ok', 'username': device.user.username})
        return JsonResponse({'status': 'error', 'message': 'Already registered'}, status=400)
    username = 'fp_' + uuid.uuid4().hex[:12]
    user = User.objects.create_user(username=username, is_fingerprint_user=True)
    AndroidFingerprintDevice.objects.create(user=user, device_id=hashed)
    login(request, user)
    return JsonResponse({'status': 'ok', 'username': username, 'is_new': True})


@csrf_exempt
def android_fingerprint_login(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    device_token = data.get('device_token')
    if not device_token:
        return JsonResponse({'status': 'error', 'message': 'Missing device_token'}, status=400)
    hashed = hashlib.sha256(device_token.encode()).hexdigest()
    try:
        device = AndroidFingerprintDevice.objects.get(device_id=hashed)
    except AndroidFingerprintDevice.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'No fingerprint registered'}, status=404)
    if not device.user:
        return JsonResponse({'status': 'error', 'message': 'No user linked'}, status=404)
    login(request, device.user)
    return JsonResponse({'status': 'ok', 'username': device.user.username})


@login_required
@csrf_exempt
def android_fingerprint_register(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    device_token = data.get('device_token')
    if not device_token:
        return JsonResponse({'status': 'error', 'message': 'Missing device_token'}, status=400)
    hashed = hashlib.sha256(device_token.encode()).hexdigest()
    if AndroidFingerprintDevice.objects.filter(device_id=hashed).exists():
        return JsonResponse({'status': 'error', 'message': 'Already registered'}, status=400)
    request.user.is_fingerprint_user = True
    request.user.save(update_fields=['is_fingerprint_user'])
    AndroidFingerprintDevice.objects.create(user=request.user, device_id=hashed)
    return JsonResponse({'status': 'ok'})


def android_fingerprint_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({'has_fingerprint': False})
    has_device = AndroidFingerprintDevice.objects.filter(user=request.user).exists()
    return JsonResponse({
        'is_fingerprint_user': request.user.is_fingerprint_user,
        'has_upgraded': request.user.has_upgraded,
        'has_android_fingerprint': has_device,
    })


# ── Download (login required) ─────────────────────────────────────────────────

def _track_download(app, request):
    session_key = f'dl_{app.pk}'
    if request.session.get(session_key):
        return
    request.session[session_key] = True
    request.session.set_expiry(300)
    Download.objects.create(
        app=app,
        user=request.user if request.user.is_authenticated else None,
        ip_address=get_client_ip(request),
        country=get_country(request),
        device_type=get_device_type(request),
    )
    App.objects.filter(pk=app.pk).update(download_count=F('download_count') + 1)


@login_required
def download_app(request, slug):
    app = get_object_or_404(_published_apps(), slug=slug)
    if not app.apk_file:
        raise Http404('APK file not found.')
    scan_file_for_malware(app.apk_file)
    _track_download(app, request)
    app.refresh_from_db()
    response = FileResponse(app.apk_file.open('rb'), as_attachment=True, filename=app.apk_file.name.split('/')[-1])
    return response


@login_required
def download_version(request, slug, version):
    app = get_object_or_404(_published_apps(), slug=slug)
    app_version = get_object_or_404(AppVersion, app=app, version=version)
    scan_file_for_malware(app_version.apk_file)
    _track_download(app, request)
    app.refresh_from_db()
    filename = app_version.apk_file.name.split('/')[-1]
    return FileResponse(app_version.apk_file.open('rb'), as_attachment=True, filename=filename)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@dashboard_required
def dashboard_home(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    downloads_qs = Download.objects.all()
    apps_qs = App.objects.all()

    total_downloads = downloads_qs.count()
    downloads_today = downloads_qs.filter(downloaded_at__gte=today_start).count()
    downloads_month = downloads_qs.filter(downloaded_at__gte=month_start).count()
    most_downloaded = apps_qs.order_by('-download_count').first()
    latest_uploads = apps_qs.order_by('-created_at')[:5]
    recent_downloads = downloads_qs.select_related('app')[:10]
    recent_versions = AppVersion.objects.filter(created_at__gte=week_ago).select_related('app')[:5]
    unread_messages = ContactMessage.objects.filter(is_read=False)[:5]

    return render(request, 'admin_dashboard.html', {
        'total_downloads': total_downloads,
        'downloads_today': downloads_today,
        'downloads_month': downloads_month,
        'most_downloaded': most_downloaded,
        'latest_uploads': latest_uploads,
        'recent_downloads': recent_downloads,
        'recent_versions': recent_versions,
        'unread_messages': unread_messages,
        'total_apps': apps_qs.count(),
        'published_apps': apps_qs.filter(published=True).count(),
    })


@dashboard_required
def dashboard_apps(request):
    apps = App.objects.select_related('category', 'uploaded_by')
    return render(request, 'dashboard/apps_list.html', {'apps': apps})


@dashboard_required
def upload_app(request):
    if request.method == 'POST':
        form = AppForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            mobile_files = request.FILES.getlist('mobile_screenshots')
            tablet_files = request.FILES.getlist('tablet_screenshots')

            if len(mobile_files) < 7:
                form.add_error(None, f'Please upload at least 7 mobile screenshots (got {len(mobile_files)}).')

            if form.is_valid():
                try:
                    for f in mobile_files:
                        validate_screenshot_file(f, 'mobile')
                    for f in tablet_files:
                        validate_screenshot_file(f, 'tablet')
                except Exception as e:
                    form.add_error(None, str(e))

            if form.is_valid():
                app = form.save(commit=False)
                app.uploaded_by = request.user
                if request.user.is_super_admin:
                    app.published = True
                else:
                    app.published = False
                    app.featured = False
                app.save()

                for i, f in enumerate(mobile_files):
                    Screenshot.objects.create(app=app, image=f, type=Screenshot.TYPE_MOBILE, display_order=i + 1)
                for i, f in enumerate(tablet_files):
                    Screenshot.objects.create(app=app, image=f, type=Screenshot.TYPE_TABLET, display_order=i + 1)

                if not request.user.is_super_admin:
                    Notification.objects.create(
                        type=Notification.TYPE_APP_UPLOAD,
                        title=f'New app uploaded by {request.user.username}',
                        message=app.name,
                        link='/dashboard/apps/',
                    )

                messages.success(request, f'App "{app.name}" uploaded successfully with {len(mobile_files) + len(tablet_files)} screenshots.')
                return redirect('dashboard_edit_app', slug=app.slug)
    else:
        form = AppForm(user=request.user)
    return render(request, 'upload_app.html', {'form': form, 'is_edit': False})


@app_edit_required
def edit_app(request, slug, app=None):
    if request.method == 'POST':
        form = AppForm(request.POST, request.FILES, instance=app, user=request.user)
        if form.is_valid():
            updated = form.save(commit=False)
            if request.user.is_app_manager and not request.user.is_super_admin:
                updated.featured = app.featured
                updated.published = app.published
            updated.save()
            messages.success(request, f'App "{app.name}" updated successfully.')
            return redirect('dashboard_edit_app', slug=app.slug)
    else:
        form = AppForm(instance=app, user=request.user)
    screenshots_qs = app.screenshots.all()
    mobile_count = screenshots_qs.filter(type=Screenshot.TYPE_MOBILE).count()
    tablet_count = screenshots_qs.filter(type=Screenshot.TYPE_TABLET).count()
    return render(request, 'upload_app.html', {
        'form': form,
        'app': app,
        'is_edit': True,
        'screenshots': screenshots_qs,
        'versions': app.versions.all(),
        'mobile_count': mobile_count,
        'tablet_count': tablet_count,
    })


@dashboard_required
def delete_app(request, slug):
    app = get_object_or_404(App, slug=slug)
    if not user_can_delete_app(request.user, app):
        messages.error(request, 'Only Super Admins can delete apps.')
        return redirect('dashboard_apps')
    if request.method == 'POST':
        name = app.name
        app.delete()
        Notification.objects.create(
            type=Notification.TYPE_APP_PUBLISHED,
            title=f'App "{name}" deleted',
            message=f'Deleted by {request.user.username}',
        )
        messages.success(request, f'App "{name}" deleted.')
        return redirect('dashboard_apps')
    messages.warning(request, f'Are you sure you want to delete "{app.name}"? Click Delete again to confirm.')
    return redirect('dashboard_apps')


@app_edit_required
def add_screenshot(request, slug, app=None):
    if request.method == 'POST':
        form = ScreenshotForm(request.POST, request.FILES)
        if form.is_valid():
            screenshot = form.save(commit=False)
            screenshot.app = app
            if not screenshot.display_order:
                next_order = (app.screenshots.aggregate(m=models.Max('display_order'))['m'] or 0) + 1
                screenshot.display_order = next_order
            screenshot.save()
            messages.success(request, 'Screenshot added.')
            return redirect('dashboard_edit_app', slug=app.slug)
    else:
        next_order = (app.screenshots.aggregate(m=models.Max('display_order'))['m'] or 0) + 1
        form = ScreenshotForm(initial={'display_order': next_order})
    return render(request, 'dashboard/screenshot_form.html', {'form': form, 'app': app})


@app_edit_required
def delete_screenshot(request, slug, pk, app=None):
    screenshot = get_object_or_404(Screenshot, pk=pk, app=app)
    if request.method == 'POST':
        screenshot.delete()
        messages.success(request, 'Screenshot removed.')
    return redirect('dashboard_edit_app', slug=app.slug)


@app_edit_required
def add_version(request, slug, app=None):
    if request.method == 'POST':
        form = AppVersionForm(request.POST, request.FILES, app=app)
        if form.is_valid():
            version_obj = form.save()
            app.version = version_obj.version
            if hasattr(version_obj.apk_file, 'size') and version_obj.apk_file.size:
                app.file_size = version_obj.apk_file.size
            app.release_notes = version_obj.release_notes
            app.save()
            messages.success(request, f'Version {form.cleaned_data["version"]} added.')
            return redirect('dashboard_edit_app', slug=app.slug)
    else:
        form = AppVersionForm(app=app)
    return render(request, 'dashboard/version_form.html', {'form': form, 'app': app})


@app_edit_required
def delete_version(request, slug, pk, app=None):
    version = get_object_or_404(AppVersion, pk=pk, app=app)
    if request.method == 'POST':
        version.delete()
        messages.success(request, 'Version removed.')
    return redirect('dashboard_edit_app', slug=app.slug)


@dashboard_required
def analytics_view(request):
    now = timezone.now()
    downloads_qs = Download.objects.select_related('app')
    apps_qs = App.objects.all()

    daily = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = downloads_qs.filter(downloaded_at__date=day).count()
        daily.append({'date': day.strftime('%a %d'), 'count': count})

    by_device = list(
        downloads_qs.values('device_type').annotate(count=Count('id')).order_by('-count'),
    )
    by_country = list(
        downloads_qs.values('country').annotate(count=Count('id')).order_by('-count')[:10],
    )
    top_apps = apps_qs.order_by('-download_count')[:10]

    return render(request, 'analytics.html', {
        'daily_downloads': daily,
        'by_device': by_device,
        'by_country': by_country,
        'top_apps': top_apps,
        'total_downloads': downloads_qs.count(),
    })


@super_admin_required
def manage_categories(request):
    categories = Category.objects.annotate(app_count=Count('apps'))
    return render(request, 'dashboard/categories.html', {'categories': categories})


@super_admin_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect('dashboard_categories')
    else:
        form = CategoryForm()
    return render(request, 'dashboard/category_form.html', {'form': form, 'is_edit': False})


@super_admin_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('dashboard_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'dashboard/category_form.html', {
        'form': form,
        'category': category,
        'is_edit': True,
    })


@super_admin_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.apps.exists():
        messages.error(request, 'Cannot delete a category that has apps. Reassign apps first.')
        return redirect('dashboard_categories')
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
    return redirect('dashboard_categories')


@super_admin_required
def manage_users(request):
    users = User.objects.annotate(download_count=Count('downloads'))
    return render(request, 'dashboard/users.html', {'users': users})


@super_admin_required
def user_create(request):
    if request.method == 'POST':
        form = AdminUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Admin user created.')
            return redirect('dashboard_users')
    else:
        form = AdminUserForm()
    return render(request, 'dashboard/user_form.html', {'form': form, 'is_edit': False})


@super_admin_required
def user_edit(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated.')
            return redirect('dashboard_users')
    else:
        form = AdminUserEditForm(instance=user_obj)
    return render(request, 'dashboard/user_form.html', {'form': form, 'user_obj': user_obj, 'is_edit': True})


@super_admin_required
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('dashboard_users')
    if request.method == 'POST':
        user_obj.delete()
        messages.success(request, 'User deleted.')
    return redirect('dashboard_users')


@super_admin_required
def website_settings(request):
    settings_obj = WebsiteSettings.get_solo()
    if request.method == 'POST':
        form = WebsiteSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Website settings updated.')
            return redirect('dashboard_settings')
    else:
        form = WebsiteSettingsForm(instance=settings_obj)
    return render(request, 'dashboard/settings.html', {'form': form})


@super_admin_required
def contact_messages(request):
    unread_count = ContactMessage.objects.filter(is_read=False).count()
    if request.method == 'POST':
        msg_id = request.POST.get('mark_read')
        if msg_id:
            ContactMessage.objects.filter(pk=msg_id).update(is_read=True)
            messages.success(request, 'Message marked as read.')
            return redirect('dashboard_messages')
        reply_id = request.POST.get('reply_id')
        reply_text = request.POST.get('reply_text', '').strip()
        if reply_id and reply_text:
            msg = get_object_or_404(ContactMessage, pk=reply_id)
            msg.is_read = True
            msg.save()
            sent = send_email_resend(
                to_email=msg.email,
                subject=f'Re: {msg.subject} — BritStore',
                text_body=f'Dear {msg.name},\n\n{reply_text}\n\n— BritStore Support\n{WebsiteSettings.get_solo().support_email}',
            )
            if sent:
                messages.success(request, f'Reply sent to {msg.email}')
            else:
                messages.warning(request, f'Reply saved but email failed to send. Check Resend dashboard or server logs.')
            return redirect('dashboard_messages')
    msgs = ContactMessage.objects.all()
    return render(request, 'dashboard/messages.html', {
        'messages_list': msgs,
        'unread_count': unread_count,
    })


@super_admin_required
def mark_notification_read(request, pk):
    Notification.objects.filter(pk=pk).update(is_read=True)
    return HttpResponse('ok')


@super_admin_required
def toggle_publish(request, slug):
    app = get_object_or_404(App, slug=slug)
    app.published = not app.published
    app.save(update_fields=['published'])
    status = 'published' if app.published else 'unpublished'
    messages.success(request, f'App "{app.name}" {status}.')
    return redirect('dashboard_apps')


@login_required
def rate_app(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    app_id = request.POST.get('app_id')
    score = request.POST.get('score')
    if not app_id or not score:
        return JsonResponse({'error': 'Missing app_id or score'}, status=400)
    try:
        score = int(score)
        if score < 1 or score > 5:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Score must be 1-5'}, status=400)
    app = get_object_or_404(App, pk=app_id, published=True)
    Rating.objects.update_or_create(
        user=request.user,
        app=app,
        defaults={'score': score},
    )
    return JsonResponse({
        'status': 'ok',
        'avg': app.avg_rating,
        'count': app.rating_count,
    })


@super_admin_required
def manage_api_tokens(request):
    tokens = ApiToken.objects.select_related('user').all()
    ctx = {
        'tokens': tokens,
        'audit_logs': UploadAuditLog.objects.select_related('token', 'uploader').all()[:50],
    }
    # Carry over one-time token display data from session (set by create/regenerate views)
    for k in ('new_api_token', 'new_api_token_name', 'new_api_token_package'):
        val = request.session.pop(k, None)
        if val:
            ctx[k] = val
    return render(request, 'dashboard/api_tokens.html', ctx)


@super_admin_required
def create_api_token(request):
    if request.method == 'POST':
        if request.POST.get('clear_token'):
            request.session.pop('new_api_token', None)
            request.session.pop('new_api_token_name', None)
            return redirect('dashboard_api_tokens')
        name = request.POST.get('name', '').strip()
        user_id = request.POST.get('user_id')
        package_name = request.POST.get('package_name', '').strip()
        if not name:
            messages.error(request, 'Token name is required.')
            return redirect('dashboard_api_tokens')
        user = get_object_or_404(User, pk=user_id) if user_id else request.user
        token = ApiToken(user=user, name=name, package_name=package_name)
        raw = token.generate_raw()
        token.save()
        messages.success(request, 'API token created successfully!')
        request.session['new_api_token'] = raw
        request.session['new_api_token_name'] = token.name
        request.session['new_api_token_package'] = token.package_name or '(any package)'
        request.session.modified = True
        request.session.save()
        return redirect('dashboard_api_tokens')
    users = User.objects.filter(is_active=True)
    return render(request, 'dashboard/api_token_form.html', {'users': users})


@super_admin_required
def revoke_api_token(request, pk):
    token = get_object_or_404(ApiToken, pk=pk)
    if request.method == 'POST':
        token.is_active = False
        token.save()
        messages.success(request, f'Token "{token.name}" revoked.')
    return redirect('dashboard_api_tokens')


@super_admin_required
def regenerate_api_token(request, pk):
    token = get_object_or_404(ApiToken, pk=pk)
    if request.method == 'POST':
        raw = token.regenerate()
        request.session['new_api_token'] = raw
        request.session['new_api_token_name'] = token.name
        request.session['new_api_token_package'] = token.package_name or '(any package)'
        request.session.modified = True
        request.session.save()
        messages.success(request, 'Token regenerated!')
    return redirect('dashboard_api_tokens')


def search_ajax(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    apps = _published_apps().filter(
        Q(name__icontains=query) | Q(short_description__icontains=query),
    )[:10]
    results = []
    for app in apps:
        results.append({
            'name': app.name,
            'url': app.get_absolute_url(),
            'category': app.category.name,
            'icon': app.icon.url if app.icon else '',
        })
    return JsonResponse({'results': results})
