import logging

from django.conf import settings
from django.core.exceptions import ValidationError

from store.utils import validate_upload_file

logger = logging.getLogger(__name__)


def validate_app_upload(apk_file, version, app=None, is_new_version=False):
    """
    Validate uploaded APK/XAPK files.
    Hook point for future virus scanning integration.
    """
    validate_upload_file(apk_file)

    if is_new_version and app:
        from store.models import AppVersion
        if AppVersion.objects.filter(app=app, version=version).exists():
            raise ValidationError(f'Version {version} already exists for this app.')

    if app and not is_new_version:
        from store.models import AppVersion
        if app.version == version:
            existing_versions = AppVersion.objects.filter(app=app, version=version)
            if not existing_versions.exists() and app.apk_file:
                logger.info('Updating app %s to same version %s', app.slug, version)

    logger.info('Upload validated: %s (%s bytes)', apk_file.name, apk_file.size)
    return True


def scan_file_for_malware(file):
    """
    Placeholder for future ClamAV or third-party virus scanning.
    Returns True if file passes scan.
    """
    return True


def send_email_resend(to_email, subject, text_body):
    """Send email via Resend API. Falls back to console log on failure."""
    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        params = {
            'from': settings.DEFAULT_FROM_EMAIL,
            'to': [to_email],
            'subject': subject,
            'text': text_body,
        }
        response = resend.Emails.send(params)
        logger.info('Email sent to %s via Resend: %s', to_email, response)
        return True
    except Exception as e:
        logger.warning('Resend email failed to %s: %s', to_email, e)
        # Fallback: log to console
        print(f'--- EMAIL TO {to_email} (Resend failed: {e}) ---')
        print(f'Subject: {subject}')
        print(text_body)
        print('--- END EMAIL (console fallback) ---')
        return False
