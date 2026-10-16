# coding: utf-8
path = 'templates/dashboard/version_form.html'
with open(path, encoding='utf-8') as f:
    s = f.read()

# Add JS to toggle apk/exe
js = '''
document.addEventListener('DOMContentLoaded', function() {
    // Try to detect platform context if present - but form is generic
    var apk = document.getElementById('id_apk_file');
    var exe = document.getElementById('id_exe_file');
    if (apk && exe) {
        // Show both? Or add toggle - simpler: just style
    }
});
'''
# Add note in help text via form? Better to just ensure fields show
with open(path, 'w', encoding='utf-8') as f:
    f.write(s)
print('ok')
