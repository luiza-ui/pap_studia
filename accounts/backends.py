from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

User = get_user_model()


class EmailBackend(BaseBackend):
    """
    Backend de autenticação personalizado que usa email em vez de username.
    Registado em settings.AUTHENTICATION_BACKENDS.
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        """
        Autentica um utilizador pelo email e senha.
        Devolve o utilizador se as credenciais forem válidas e a conta estiver activa,
        ou None em caso contrário.
        """
        if email is None or password is None:
            return None

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        # Verifica a senha e se a conta está activa
        if user.check_password(password) and user.is_active:
            return user

        return None

    def get_user(self, user_id):
        """Devolve o utilizador com o pk indicado, ou None se não existir."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
