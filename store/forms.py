from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError

from store.models import App, AppVersion, Category, ContactMessage, Screenshot, User, WebsiteSettings
from store.services import validate_app_upload
from store.utils import validate_image_file, validate_upload_file


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                css = 'form-select'
            elif isinstance(field.widget, forms.Textarea):
                css = 'form-control'
            field.widget.attrs.setdefault('class', css)


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com', 'autofocus': True})
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def clean_username(self):
        email = self.cleaned_data.get('username', '').strip()
        if not email:
            raise forms.ValidationError('Email is required.')
        users = list(User.objects.filter(email__iexact=email).order_by('pk'))
        if not users:
            raise forms.ValidationError('No account found with this email address')
        for u in users:
            if u.is_active and u.is_super_admin:
                return u.username
        for u in users:
            if u.is_active:
                return u.username
        return users[0].username


class PasswordResetFormStyled(StyledFormMixin, PasswordResetForm):
    pass


class SetPasswordFormStyled(StyledFormMixin, SetPasswordForm):
    pass


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'icon_emoji']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['icon'].required = False
        self.fields['icon_emoji'].required = False


class AppForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = App
        fields = [
            'name', 'short_description', 'full_description', 'category',
            'version', 'package_name', 'platform', 'apk_file', 'exe_file', 'icon', 'android_version', 'windows_version',
            'release_notes', 'age_rating', 'price_type', 'price', 'currency', 'featured', 'published',
        ]
        widgets = {
            'short_description': forms.TextInput(),
            'release_notes': forms.Textarea(attrs={'rows': 4}),
            'full_description': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['apk_file'].required = False
            self.fields['exe_file'].required = False
            self.fields['icon'].required = False
        if self.user and not self.user.is_super_admin:
            self.fields.pop('featured', None)
            self.fields.pop('published', None)

    def _selected_platform(self):
        # 'platform' is cleaned AFTER 'package_name', so read the raw POST value first
        return self.data.get('platform') or self.cleaned_data.get('platform') or App.PLATFORM_ANDROID

    def clean_package_name(self):
        pn = self.cleaned_data.get('package_name', '') or ''
        platform = self._selected_platform()
        if platform == App.PLATFORM_DESKTOP and not pn:
            pn = ''
        if platform == App.PLATFORM_ANDROID and not pn:
            raise ValidationError('Package name (applicationId) is required for Android apps.')
        if pn:
            if App.objects.filter(package_name=pn).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
                raise ValidationError(f'An app with package name "{pn}" already exists.')
        return pn

    def clean_apk_file(self):
        apk = self.cleaned_data.get('apk_file')
        if apk:
            validate_upload_file(apk)
        elif not self.instance.pk and self._selected_platform() == App.PLATFORM_ANDROID:
            raise ValidationError('APK file is required for new Android apps.')
        return apk

    def clean_exe_file(self):
        exe = self.cleaned_data.get('exe_file')
        if exe:
            validate_upload_file(exe)
        elif not self.instance.pk and self._selected_platform() == App.PLATFORM_DESKTOP:
            raise ValidationError('.exe file is required for new Desktop apps.')
        return exe

    def clean_icon(self):
        icon = self.cleaned_data.get('icon')
        if icon:
            validate_image_file(icon)
        elif not self.instance.pk:
            raise ValidationError('App icon is required.')
        return icon

    def clean(self):
        cleaned = super().clean()
        apk = cleaned.get('apk_file') or cleaned.get('exe_file')
        version = cleaned.get('version')
        platform = cleaned.get('platform', App.PLATFORM_ANDROID)
        if platform == App.PLATFORM_DESKTOP:
            if 'android_version' in cleaned:
                cleaned.pop('android_version', None)
            if not cleaned.get('windows_version'):
                self.add_error('windows_version', 'Windows version is required for desktop apps.')
        else:
            if 'windows_version' in cleaned:
                cleaned.pop('windows_version', None)
            if not cleaned.get('android_version'):
                self.add_error('android_version', 'Android version is required for Android apps.')
        if platform == App.PLATFORM_DESKTOP and not apk and cleaned.get('exe_file'):
            apk = cleaned.get('exe_file')
        # Filter out platform-inconsistent errors
        if platform == App.PLATFORM_DESKTOP:
            if 'android_version' in self.errors:
                del self.errors['android_version']
        else:
            if 'windows_version' in self.errors:
                del self.errors['windows_version']

        if apk and version:
            try:
                validate_app_upload(apk, version, app=self.instance if self.instance.pk else None)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return cleaned


class ScreenshotForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Screenshot
        fields = ['image', 'type', 'display_order']

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            validate_image_file(image)
        return image

    def clean(self):
        cleaned = super().clean()
        image = cleaned.get('image')
        img_type = cleaned.get('type')
        if image and img_type:
            from store.utils import validate_screenshot_file
            validate_screenshot_file(image, img_type)
        return cleaned


class AppVersionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AppVersion
        fields = ['version', 'version_code', 'apk_file', 'exe_file', 'release_notes', 'force_update', 'is_latest']
        widgets = {'release_notes': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        self.app = kwargs.pop('app')
        super().__init__(*args, **kwargs)
        self.fields['apk_file'].required = False
        self.fields['exe_file'].required = False

    def clean_apk_file(self):
        apk = self.cleaned_data.get('apk_file')
        if apk:
            validate_upload_file(apk)
        return apk

    def clean_exe_file(self):
        exe = self.cleaned_data.get('exe_file')
        if exe:
            validate_upload_file(exe)
        return exe

    def clean(self):
        cleaned = super().clean()
        file = cleaned.get('apk_file') or cleaned.get('exe_file')
        version = cleaned.get('version')
        if file and version:
            try:
                validate_app_upload(file, version, app=self.app, is_new_version=True)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return cleaned


class WebsiteSettingsForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = WebsiteSettings
        fields = [
            'site_name', 'tagline', 'hero_title', 'hero_subtitle',
            'about_title', 'about_content', 'mission', 'support_email',
        ]
        widgets = {
            'hero_subtitle': forms.Textarea(attrs={'rows': 3}),
            'about_content': forms.Textarea(attrs={'rows': 8}),
            'mission': forms.Textarea(attrs={'rows': 4}),
        }


class ApiUploadForm(forms.Form):
    package_name = forms.CharField(max_length=200)
    app_name = forms.CharField(max_length=200, required=False)
    version = forms.CharField(max_length=50)
    version_code = forms.IntegerField(min_value=1)
    apk_file = forms.FileField()
    release_notes = forms.CharField(widget=forms.Textarea, required=False)
    force_update = forms.BooleanField(required=False)

    def clean_apk_file(self):
        apk = self.cleaned_data.get('apk_file')
        if apk:
            from store.services import validate_app_upload
            try:
                validate_app_upload(apk, self.cleaned_data.get('version', ''))
            except Exception as e:
                raise forms.ValidationError(str(e))
        return apk


class SignUpForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = User.ROLE_NORMAL_USER
        if commit:
            user.save()
        return user


class AdminUserForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.is_staff = user.role in (User.ROLE_SUPER_ADMIN, User.ROLE_APP_MANAGER)
        if commit:
            user.save()
        return user


class AdminUserEditForm(StyledFormMixin, forms.ModelForm):
    role = forms.ChoiceField(choices=[
        (User.ROLE_SUPER_ADMIN, 'Super Admin'),
        (User.ROLE_APP_MANAGER, 'App Manager'),
        (User.ROLE_NORMAL_USER, 'Normal User'),
    ])

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_active']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = user.role in (User.ROLE_SUPER_ADMIN, User.ROLE_APP_MANAGER)
        if commit:
            user.save()
        return user
