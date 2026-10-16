# coding: utf-8
path = 'store/views.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

# Replace the upload_app view logic for screenshots
old = '''            mobile_files = request.FILES.getlist('mobile_screenshots')
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
                    form.add_error(None, str(e))'''

new = '''            platform = form.cleaned_data.get('platform', 'android')
            mobile_files = request.FILES.getlist('mobile_screenshots')
            tablet_files = request.FILES.getlist('tablet_screenshots')
            desktop_files = request.FILES.getlist('desktop_screenshots')

            if platform == 'desktop':
                if len(desktop_files) < 5:
                    form.add_error(None, f'Please upload at least 5 desktop screenshots (got {len(desktop_files)}).')
            else:
                if len(mobile_files) < 7:
                    form.add_error(None, f'Please upload at least 7 mobile screenshots (got {len(mobile_files)}).')

            if form.is_valid():
                try:
                    for f in mobile_files:
                        validate_screenshot_file(f, 'mobile')
                    for f in tablet_files:
                        validate_screenshot_file(f, 'tablet')
                    for f in desktop_files:
                        validate_screenshot_file(f, 'mobile')  # use same validation for desktop
                except Exception as e:
                    form.add_error(None, str(e))'''

if old not in content:
    print('not found')
else:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('ok')
