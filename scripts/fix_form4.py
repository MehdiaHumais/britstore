path = 'store/forms.py'
with open(path, encoding='utf-8') as f:
    s = f.read()

# When platform is desktop, remove android_version error if it was added? Or better fix field requirement
# Also in clean, we should not let form think it's required? Or pop from errors
pass
