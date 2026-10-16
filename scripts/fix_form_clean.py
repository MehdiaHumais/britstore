path = 'store/forms.py'
with open(path, encoding='utf-8') as f:
    s = f.read()

# Clean up android_version validation - should be conditional
# But we already pop it for desktop; maybe just don't add error for android if not present?
old = '''        if platform == App.PLATFORM_DESKTOP:
            # Don't require android_version for desktop apps
            if 'android_version' in cleaned:
                cleaned.pop('android_version', None)
            if not cleaned.get('windows_version'):
                self.add_error('windows_version', 'Windows version is required for desktop apps.')
        else:
            # Android app
            if 'windows_version' in cleaned:
                cleaned.pop('windows_version', None)'''

new = '''        if platform == App.PLATFORM_DESKTOP:
            if 'android_version' in cleaned:
                cleaned.pop('android_version', None)
            if not cleaned.get('windows_version'):
                self.add_error('windows_version', 'Windows version is required for desktop apps.')
        else:
            if 'windows_version' in cleaned:
                cleaned.pop('windows_version', None)
            if not cleaned.get('android_version'):
                self.add_error('android_version', 'Android version is required for Android apps.')'''

if old in s:
    s = s.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('ok1')
else:
    print('no1')
