import hashlib
import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone


class User(AbstractUser):
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_APP_MANAGER = 'app_manager'
    ROLE_NORMAL_USER = 'normal_user'
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_APP_MANAGER, 'App Manager'),
        (ROLE_NORMAL_USER, 'Normal User'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_NORMAL_USER)
    is_fingerprint_user = models.BooleanField(default=False)
    has_upgraded = models.BooleanField(default=False)

    class Meta:
        ordering = ['username']

    @property
    def is_super_admin(self):
        return self.role == self.ROLE_SUPER_ADMIN or self.is_superuser

    @property
    def is_app_manager(self):
        return self.role == self.ROLE_APP_MANAGER

    @property
    def is_normal_user(self):
        return self.role == self.ROLE_NORMAL_USER

    @property
    def can_access_dashboard(self):
        return self.is_super_admin or self.is_app_manager or self.is_staff

    @property
    def avatar_letter(self):
        return self.username[0].upper() if self.username else '?'


class WebsiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='BritStore')
    tagline = models.CharField(max_length=200, default='Intelligent Apps for the AI Era')
    hero_title = models.CharField(max_length=200, default='Discover BritStore Apps')
    hero_subtitle = models.TextField(
        default='Explore our suite of AI-powered applications built to automate, educate, and innovate.',
    )
    about_title = models.CharField(max_length=200, default='About BritStore')
    about_content = models.TextField(default='')
    mission = models.TextField(default='')
    support_email = models.EmailField(default='britsyncuk@gmail.com')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Website Settings'
        verbose_name_plural = 'Website Settings'

    def __str__(self):
        return self.site_name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True)
    icon_emoji = models.CharField(max_length=10, blank=True, help_text='Fallback emoji if no icon image')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category', kwargs={'slug': self.slug})

    def published_app_count(self):
        return self.apps.filter(published=True).count()


def app_icon_path(instance, filename):
    return f'icons/{instance.slug or "app"}-{filename}'


def app_apk_path(instance, filename):
    return f'apk/{instance.slug or "app"}-{filename}'


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    app = models.ForeignKey('App', on_delete=models.CASCADE, related_name='ratings')
    score = models.PositiveSmallIntegerField(choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'app']

    def __str__(self):
        return f'{self.user.username} rated {self.app.name} {self.score}/5'


class App(models.Model):
    AGE_ALL = 'all'
    AGE_12 = '12+'
    AGE_16 = '16+'
    AGE_18 = '18+'
    AGE_CHOICES = [
        (AGE_ALL, 'All Ages'),
        (AGE_12, '12+'),
        (AGE_16, '16+'),
        (AGE_18, '18+'),
    ]
    PRICE_FREE = 'free'
    PRICE_PAID = 'paid'
    PRICE_CHOICES = [
        (PRICE_FREE, 'Free'),
        (PRICE_PAID, 'Paid'),
    ]
    CURRENCY_CHOICES = [
        ('USD', 'USD — US Dollar'),
        ('PKR', 'PKR — Pakistani Rupee'),
        ('EUR', 'EUR — Euro'),
        ('GBP', 'GBP — British Pound'),
        ('INR', 'INR — Indian Rupee'),
        ('AED', 'AED — UAE Dirham'),
        ('SAR', 'SAR — Saudi Riyal'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    full_description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='apps')
    version = models.CharField(max_length=50)
    package_name = models.CharField(max_length=200, unique=True, db_index=True)
    apk_file = models.FileField(upload_to=app_apk_path)
    icon = models.ImageField(upload_to=app_icon_path)
    file_size = models.PositiveBigIntegerField(default=0, help_text='Size in bytes')
    android_version = models.CharField(max_length=50, default='Android 8+')
    release_notes = models.TextField(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_apps',
    )
    age_rating = models.CharField(max_length=4, choices=AGE_CHOICES, default=AGE_ALL)
    price_type = models.CharField(max_length=4, choices=PRICE_CHOICES, default=PRICE_FREE)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Price (only for paid apps)')
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD', help_text='Currency for paid apps')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1
            while App.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        if self.apk_file and not self.file_size:
            try:
                self.file_size = self.apk_file.size
            except (OSError, ValueError):
                pass
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('app_detail', kwargs={'slug': self.slug})

    @property
    def file_size_display(self):
        size = self.file_size
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f'{size:.1f} {unit}' if unit != 'B' else f'{size} {unit}'
            size /= 1024
        return f'{size:.1f} TB'

    @property
    def avg_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return sum(r.score for r in ratings) / len(ratings)

    @property
    def rating_count(self):
        return self.ratings.count()

    @property
    def avg_rating_int(self):
        return int(round(self.avg_rating))


def screenshot_path(instance, filename):
    return f'screenshots/{instance.app.slug}-{filename}'


class Screenshot(models.Model):
    TYPE_MOBILE = 'mobile'
    TYPE_TABLET = 'tablet'
    TYPE_CHOICES = [
        (TYPE_MOBILE, 'Mobile'),
        (TYPE_TABLET, 'Tablet'),
    ]

    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to=screenshot_path)
    display_order = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_MOBILE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'created_at']

    def __str__(self):
        return f'{self.app.name} {self.type} screenshot #{self.display_order}'


class Download(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='downloads')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, default='Unknown')
    device_type = models.CharField(max_length=50, default='Unknown')
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-downloaded_at']

    def __str__(self):
        return f'{self.app.name} - {self.downloaded_at:%Y-%m-%d}'


def version_apk_path(instance, filename):
    return f'apk/{instance.app.slug}-v{instance.version}-{filename}'


class AppVersion(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=50)
    version_code = models.IntegerField(default=1, help_text='Numeric version code for comparison (e.g. 3 for v1.0.3)')
    apk_file = models.FileField(upload_to=version_apk_path)
    release_notes = models.TextField(blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    force_update = models.BooleanField(default=False, help_text='Force users to update to this version')
    is_latest = models.BooleanField(default=False, help_text='Currently the latest published version')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['app', 'version']]

    def __str__(self):
        return f'{self.app.name} v{self.version}'

    def save(self, *args, **kwargs):
        if self.apk_file and not self.file_size:
            try:
                self.file_size = self.apk_file.size
            except (OSError, ValueError):
                pass
        if self.is_latest:
            AppVersion.objects.filter(app=self.app).exclude(pk=self.pk).update(is_latest=False)
        super().save(*args, **kwargs)

    @property
    def file_size_display(self):
        size = self.file_size
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f'{size:.1f} {unit}' if unit != 'B' else f'{size} {unit}'
            size /= 1024
        return f'{size:.1f} TB'


def _raw_token():
    """Generate a cryptographically random 48-char hex token."""
    return hashlib.sha256(os.urandom(64)).hexdigest()[:48]

def _hash_token(raw):
    """Return the SHA-256 hash of a raw token (stored in DB)."""
    return hashlib.sha256(raw.encode()).hexdigest()


class ApiToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    name = models.CharField(max_length=100, help_text='Label for this token (e.g. "GitHub Actions - MyApp")')
    package_name = models.CharField(
        max_length=200, blank=True, default='',
        help_text='If set, this token can only upload releases for this package name (e.g. com.ascentra.crm). Leave empty for unrestricted access.',
    )
    token_hash = models.CharField(max_length=64, unique=True, editable=False, db_index=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    _raw_cache = None  # holds the raw token between generate and save

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        restricted = f' [{self.package_name}]' if self.package_name else ''
        return f'{self.name}{restricted} ({self.user.username})'

    def generate_raw(self):
        """Generate a new raw token, hash it, and cache the raw value for one-time display."""
        raw = _raw_token()
        self.token_hash = _hash_token(raw)
        self._raw_cache = raw
        return raw

    def regenerate(self):
        raw = self.generate_raw()
        self.save(update_fields=['token_hash'])
        return raw

    def get_raw_once(self):
        """Return and clear the cached raw token (for one-time display)."""
        raw = self._raw_cache
        self._raw_cache = None
        return raw


class UploadAuditLog(models.Model):
    token = models.ForeignKey(ApiToken, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    token_name = models.CharField(max_length=100, blank=True, default='')
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='upload_audit_logs')
    package_name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    version_code = models.IntegerField(default=1)
    force_update = models.BooleanField(default=False)
    apk_path = models.CharField(max_length=500, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Upload Audit Log'
        verbose_name_plural = 'Upload Audit Logs'

    def __str__(self):
        return f'{self.package_name} v{self.version} by {self.token_name or "?"}'


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} from {self.name}'


class Notification(models.Model):
    TYPE_CONTACT = 'contact'
    TYPE_APP_UPLOAD = 'app_upload'
    TYPE_APP_PUBLISHED = 'app_published'
    TYPE_VERSION_UPLOAD = 'version_upload'
    TYPE_CHOICES = [
        (TYPE_CONTACT, 'New Contact Message'),
        (TYPE_APP_UPLOAD, 'App Uploaded'),
        (TYPE_APP_PUBLISHED, 'App Published'),
        (TYPE_VERSION_UPLOAD, 'Version Uploaded'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class FingerprintCredential(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='fingerprint_credential',
    )
    credential_id = models.TextField(unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    device_info = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Fingerprint credential for {self.user.username}'
