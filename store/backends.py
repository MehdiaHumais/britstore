from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


UserModel = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            if '@' in username:
                users = list(UserModel.objects.filter(email__iexact=username, is_active=True).order_by('pk'))
                if not users:
                    try:
                        users = list(UserModel.objects.filter(email__iexact=username).order_by('pk'))
                    except Exception:
                        users = []
                for u in users:
                    if u.check_password(password) and self.user_can_authenticate(u):
                        if u.is_super_admin:
                            return u
                for u in users:
                    if u.check_password(password) and self.user_can_authenticate(u):
                        return u
                return None
            user = UserModel.objects.get(username=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except UserModel.DoesNotExist:
            try:
                user = UserModel.objects.filter(email__iexact=username).order_by('pk').first()
                if user and user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except Exception:
                pass
            return None
        except Exception:
            return None
        return None
