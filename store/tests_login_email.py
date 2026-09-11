from django.contrib.auth import authenticate
from django.test import TestCase

from store.forms import LoginForm
from store.models import User


class EmailLoginTests(TestCase):
    def test_duplicate_email_login_uses_super_admin(self):
        admin = User.objects.create_user(username='admin', email='britsyncuk@gmail.com', password='admin123', role=User.ROLE_SUPER_ADMIN, is_staff=True)
        manager = User.objects.create_user(username='manager', email='britsyncuk@gmail.com', password='managerpass', role=User.ROLE_APP_MANAGER, is_staff=True)

        user = authenticate(request=None, username='britsyncuk@gmail.com', password='admin123')
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, admin.pk)

    def test_login_form_resolves_email(self):
        admin = User.objects.create_user(username='admin', email='britsyncuk@gmail.com', password='admin123', role=User.ROLE_SUPER_ADMIN, is_staff=True)
        form = LoginForm(data={'username': 'BRITSYNCUK@gmail.com', 'password': 'admin123'})
        self.assertTrue(form.is_valid(), dict(form.errors))
        self.assertEqual(form.get_user().pk, admin.pk)

    def test_unknown_email_error(self):
        form = LoginForm(data={'username': 'nobody@nowhere.com', 'password': 'whatever123'})
        self.assertFalse(form.is_valid())
        self.assertIn('No account found with this email address', form.errors['username'])

    def test_login_view_post_no_crash(self):
        admin = User.objects.create_user(username='admin', email='britsyncuk@gmail.com', password='admin123', role=User.ROLE_SUPER_ADMIN, is_staff=True)
        User.objects.create_user(username='manager', email='britsyncuk@gmail.com', password='managerpass', role=User.ROLE_APP_MANAGER, is_staff=True)
        resp = self.client.post('/login/', {'username': 'britsyncuk@gmail.com', 'password': 'admin123'})
        self.assertEqual(resp.status_code, 302)

    def test_email_login_success(self):
        User.objects.create_user(username='admin', email='britsyncuk@gmail.com', password='admin123', role=User.ROLE_SUPER_ADMIN, is_staff=True)
        resp = self.client.post('/login/', {'username': 'britsyncuk@gmail.com', 'password': 'admin123'}, follow=True)
        self.assertEqual(resp.status_code, 200)