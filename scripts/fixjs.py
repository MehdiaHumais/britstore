path = 'templates/upload_app.html'
with open(path, encoding='utf-8', errors='replace') as f:
    s = f.read()

old_js = '''            var p = platform.value;
            var apkGroup = document.getElementById('field_apk_file');
            var exeGroup = document.getElementById('field_exe_file');
            var pkg = document.getElementById('field_package_name');
            var androidVer = document.getElementById('field_android_version');
            var winVer = document.getElementById('field_windows_version');
            if (apkGroup) apkGroup.style.display = (p === 'android') ? '' : 'none';
            if (exeGroup) exeGroup.style.display = (p === 'desktop') ? '' : 'none';
            if (androidVer) androidVer.style.display = (p === 'android') ? '' : 'none';
            if (winVer) winVer.style.display = (p === 'desktop') ? '' : 'none';'''

new_js = '''            var p = platform.value;
            var apkGroup = document.getElementById('field_apk_file');
            var exeGroup = document.getElementById('field_exe_file');
            var pkg = document.getElementById('field_package_name');
            var androidVer = document.getElementById('field_android_version');
            var winVer = document.getElementById('field_windows_version');
            if (apkGroup) apkGroup.style.display = (p === 'android') ? '' : 'none';
            if (exeGroup) exeGroup.style.display = (p === 'desktop') ? '' : 'none';
            if (androidVer) androidVer.style.display = (p === 'android') ? '' : 'none';
            if (winVer) winVer.style.display = (p === 'desktop') ? '' : 'none';
            var mobileGroup = document.getElementById('mobileScreenshotsGroup');
            var tabletGroup = document.getElementById('tabletScreenshotsGroup');
            var desktopGroup = document.getElementById('desktopScreenshotsGroup');
            var help = document.getElementById('screenshotHelp');
            if (p === 'desktop') {
                if (mobileGroup) mobileGroup.style.display = 'none';
                if (tabletGroup) tabletGroup.style.display = 'none';
                if (desktopGroup) desktopGroup.style.display = '';
                if (help) help.innerHTML = 'Upload at least <strong>5 screenshots</strong> for Desktop apps.';
            } else {
                if (mobileGroup) mobileGroup.style.display = '';
                if (tabletGroup) tabletGroup.style.display = '';
                if (desktopGroup) desktopGroup.style.display = 'none';
                if (help) help.innerHTML = 'Upload at least <strong>7 screenshots</strong> for Android apps.';
            }'''

if old_js not in s:
    print('no')
else:
    s = s.replace(old_js, new_js)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('ok')
