# coding: utf-8
import sys

path = 'templates/upload_app.html'
with open(path, encoding='utf-8') as f:
    s = f.read()

# Add JavaScript to handle platform change - show/hide apk/exe fields
js_add = '''
document.addEventListener('DOMContentLoaded', function() {
    var priceType = document.getElementById('id_price_type');
    if (priceType) {
        priceType.addEventListener('change', function() {
            var show = this.value === 'paid';
            document.querySelectorAll('.paid-only').forEach(function(el) {
                el.style.display = show ? '' : 'none';
            });
        });
    }
    var platform = document.getElementById('id_platform');
    if (platform) {
        function togglePlatform() {
            var p = platform.value;
            var apkGroup = document.getElementById('field_apk_file');
            var exeGroup = document.getElementById('field_exe_file');
            var pkg = document.getElementById('field_package_name');
            var androidVer = document.getElementById('field_android_version');
            var winVer = document.getElementById('field_windows_version');
            if (apkGroup) apkGroup.style.display = (p === 'android') ? '' : 'none';
            if (exeGroup) exeGroup.style.display = (p === 'desktop') ? '' : 'none';
            if (androidVer) androidVer.style.display = (p === 'android') ? '' : 'none';
            if (winVer) winVer.style.display = (p === 'desktop') ? '' : 'none';
        }
        platform.addEventListener('change', togglePlatform);
        togglePlatform();
    }
});
'''

s = s.replace('''document.addEventListener('DOMContentLoaded', function() {
    var priceType = document.getElementById('id_price_type');
    if (priceType) {
        priceType.addEventListener('change', function() {
            var show = this.value === 'paid';
            document.querySelectorAll('.paid-only').forEach(function(el) {
                el.style.display = show ? '' : 'none';
            });
        });
    }
});
''', js_add)

with open(path, 'w', encoding='utf-8') as f:
    f.write(s)
print('ok')
