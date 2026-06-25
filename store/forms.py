from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
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
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


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
            'version', 'package_name', 'apk_file', 'icon', 'android_version',
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
            self.fields['icon'].required = False
        if self.user and not self.user.is_super_admin:
            self.fields.pop('featured', None)
            self.fields.pop('published', None)

    def clean_package_name(self):
        pn = self.cleaned_data.get('package_name', '')
        if not pn:
            raise ValidationError('Package name (applicationId) is required.')
        if App.objects.filter(package_name=pn).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
            raise ValidationError(f'An app with package name "{pn}" already exists.')
        return pn

    def clean_apk_file(self):
        apk = self.cleaned_data.get('apk_file')
        if apk:
            validate_upload_file(apk)
        elif not self.instance.pk:
            raise ValidationError('APK file is required for new apps.')
        return apk

    def clean_icon(self):
        icon = self.cleaned_data.get('icon')
        if icon:
            validate_image_file(icon)
        elif not self.instance.pk:
            raise ValidationError('App icon is required.')
        return icon

    def clean(self):
        cleaned = super().clean()
        apk = cleaned.get('apk_file')
        version = cleaned.get('version')
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
        fields = ['version', 'version_code', 'apk_file', 'release_notes', 'force_update', 'is_latest']
        widgets = {'release_notes': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        self.app = kwargs.pop('app')
        super().__init__(*args, **kwargs)

    def clean_apk_file(self):
        apk = self.cleaned_data.get('apk_file')
        if apk:
            validate_upload_file(apk)
        return apk

    def clean(self):
        cleaned = super().clean()
        apk = cleaned.get('apk_file')
        version = cleaned.get('version')
        if apk and version:
            try:
                validate_app_upload(apk, version, app=self.app, is_new_version=True)
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
