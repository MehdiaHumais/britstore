path = 'store/forms.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

# Update clean to handle platform-specific fields
old = '''    def clean(self):
        cleaned = super().clean()
        apk = cleaned.get('apk_file') or cleaned.get('exe_file')
        version = cleaned.get('version')
        platform = cleaned.get('platform', App.PLATFORM_ANDROID)
        if platform == App.PLATFORM_DESKTOP and not apk and cleaned.get('exe_file'):
            apk = cleaned.get('exe_file')
        if apk and version:
            try:
                validate_app_upload(apk, version, app=self.instance if self.instance.pk else None)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return cleaned'''

new = '''    def clean(self):
        cleaned = super().clean()
        apk = cleaned.get('apk_file') or cleaned.get('exe_file')
        version = cleaned.get('version')
        platform = cleaned.get('platform', App.PLATFORM_ANDROID)
        if platform == App.PLATFORM_DESKTOP:
            # Don't require android_version for desktop apps
            if 'android_version' in cleaned:
                cleaned.pop('android_version', None)
            if not cleaned.get('windows_version'):
                self.add_error('windows_version', 'Windows version is required for desktop apps.')
        else:
            # Android app
            if 'windows_version' in cleaned:
                cleaned.pop('windows_version', None)
        if platform == App.PLATFORM_DESKTOP and not apk and cleaned.get('exe_file'):
            apk = cleaned.get('exe_file')
        if apk and version:
            try:
                validate_app_upload(apk, version, app=self.instance if self.instance.pk else None)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return cleaned'''

if old not in content:
    print('not found')
else:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('ok')
