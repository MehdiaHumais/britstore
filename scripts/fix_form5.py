path = 'store/forms.py'
with open(path, encoding='utf-8') as f:
    s = f.read()

# Override clean_errors or just handle in clean
# Add at end of clean
marker = '''        if apk and version:
            try:
                validate_app_upload(apk, version, app=self.instance if self.instance.pk else None)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return cleaned'''

if marker not in s:
    print('no')
else:
    replacement = '''        # Filter out platform-inconsistent errors
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
        return cleaned'''
    s = s.replace(marker, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('ok')
