with open('store/models.py', 'r', encoding='utf-8') as f:
    s = f.read()

old = '''    PRICE_FREE = 'free'
    PRICE_PAID = 'paid'
    PRICE_CHOICES = [
        (PRICE_FREE, 'Free'),
        (PRICE_PAID, 'Paid'),
    ]
    CURRENCY_CHOICES = [
        ('USD', 'USD — US Dollar'),
        ('PKR', 'PKR — Pakistani Rupee'),
        ('EUR', 'EUR — Euro'),
        ('GBP', 'GBP — British Pound'),
        ('INR', 'INR — Indian Rupee'),
        ('AED', 'AED — UAE Dirham'),
        ('SAR', 'SAR — Saudi Riyal'),
    ]'''

new = '''    PLATFORM_ANDROID = 'android'
    PLATFORM_DESKTOP = 'desktop'
    PLATFORM_CHOICES = [
        (PLATFORM_ANDROID, 'Android'),
        (PLATFORM_DESKTOP, 'Desktop (Windows)'),
    ]
    PRICE_FREE = 'free'
    PRICE_PAID = 'paid'
    PRICE_CHOICES = [
        (PRICE_FREE, 'Free'),
        (PRICE_PAID, 'Paid'),
    ]
    CURRENCY_CHOICES = [
        ('USD', 'USD - US Dollar'),
        ('PKR', 'PKR - Pakistani Rupee'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('INR', 'INR - Indian Rupee'),
        ('AED', 'AED - UAE Dirham'),
        ('SAR', 'SAR - Saudi Riyal'),
    ]'''

if old not in s:
    print('not found')
else:
    s = s.replace(old, new)
    with open('store/models.py', 'w', encoding='utf-8') as f:
        f.write(s)
    print('ok')
