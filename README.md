# BritStore Company App Store

Internal app store for **BritStore** — browse, search, and download company Android apps. Public browsing with login-required downloads.

## Stack

- **Backend:** Django 5.2 + Gunicorn
- **Database:** SQLite (upgrade to PostgreSQL later)
- **Storage:** Local `/media/` directory
- **Web server:** Nginx (production)

## Quick Start

```bash
# Install dependencies
py -m pip install -r requirements.txt

# Run migrations
py manage.py migrate

# Seed default categories & website content
py manage.py seed_data

# Create Super Admin (default: admin / admin123)
py manage.py create_super_admin

# Start development server
py manage.py runserver
```

Open **http://127.0.0.1:8000/** for the public store.  
Dashboard: **http://127.0.0.1:8000/dashboard/**

## User Roles

| Role | Access |
|------|--------|
| **Super Admin** | Full control — apps, users, categories, settings, analytics, publish/unpublish |
| **App Manager** | Upload/edit own apps, screenshots, versions |

## Upload Rules

- Allowed extensions: `.apk`, `.xapk`
- Maximum file size: **500 MB**
- Extension, size, and MIME validation on upload
- Virus scan hook ready for future ClamAV integration

## Project Structure

```
├── config/          # Django settings & URLs
├── store/           # Main app (models, views, forms)
├── templates/       # HTML templates
├── static/          # CSS & JS
├── media/           # Uploaded APKs, icons, screenshots
└── logs/            # Application logs
```

## Production Notes

1. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and `DJANGO_ALLOWED_HOSTS`
2. Run `py manage.py collectstatic`
3. Serve with Nginx + Gunicorn
4. Switch database to PostgreSQL when scaling

## Default Categories

AI Tools · Business · Education · Automation · Productivity · Utilities
