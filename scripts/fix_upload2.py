# coding: utf-8
path = 'store/views.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

old = '''                for i, f in enumerate(mobile_files):
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
                return redirect('dashboard_edit_app', slug=app.slug)'''

new = '''                for i, f in enumerate(mobile_files):
                    Screenshot.objects.create(app=app, image=f, type=Screenshot.TYPE_MOBILE, display_order=i + 1)
                for i, f in enumerate(tablet_files):
                    Screenshot.objects.create(app=app, image=f, type=Screenshot.TYPE_TABLET, display_order=i + 1)
                for i, f in enumerate(desktop_files):
                    Screenshot.objects.create(app=app, image=f, type=Screenshot.TYPE_MOBILE, display_order=i + 1)

                if not request.user.is_super_admin:
                    Notification.objects.create(
                        type=Notification.TYPE_APP_UPLOAD,
                        title=f'New app uploaded by {request.user.username}',
                        message=app.name,
                        link='/dashboard/apps/',
                    )

                total_screens = len(mobile_files) + len(tablet_files) + len(desktop_files)
                messages.success(request, f'App "{app.name}" uploaded successfully with {total_screens} screenshots.')
                return redirect('dashboard_edit_app', slug=app.slug)'''

if old not in content:
    print('not found')
else:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('ok')
