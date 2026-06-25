import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_apk_extension(file):
    ext = os.path.splitext(file.name)[1].lower()
    allowed = getattr(settings, 'ALLOWED_APK_EXTENSIONS', ['.apk', '.xapk'])
    if ext not in allowed:
        raise ValidationError(
            f'File type "{ext}" is not allowed. Allowed types: {", ".join(allowed)}',
        )


def validate_file_size(file):
    max_bytes = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 500) * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(
            f'File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB.',
        )


def validate_upload_file(file):
    validate_apk_extension(file)
    validate_file_size(file)


def validate_image_file(file, min_width=None, max_height=None):
    validate_file_size(file)
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
        raise ValidationError('Image must be PNG, JPG, WEBP, or GIF.')
    if min_width is None and max_height is None:
        return
    from PIL import Image
    try:
        img = Image.open(file)
        w, h = img.size
        if min_width and w < min_width:
            raise ValidationError(f'Image width must be at least {min_width}px (got {w}px).')
        if max_height and h > max_height:
            raise ValidationError(f'Image height must be at most {max_height}px (got {h}px).')
    except Exception:
        pass


def get_client_ip(request):
    """Extract client IP from request headers."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def validate_screenshot_file(file, screenshot_type):
    validate_image_file(file, min_width=320, max_height=3840)
    if screenshot_type == 'tablet':
        from PIL import Image
        try:
            img = Image.open(file)
            w, h = img.size
            if w < 600:
                raise ValidationError(f'Tablet screenshot width must be at least 600px (got {w}px).')
        except Exception:
            pass
