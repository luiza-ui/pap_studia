"""Testes para o fluxo de confirmação de email por token."""

import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


def _criar_user_inactivo(email='novo@escola.pt'):
    """Cria utilizador inactivo directamente (sem passar pelo formulário)."""
    user = User.objects.create_user(
        email=email, password='SenhaSegura123!',
        nome='Novo', curso='CT', ano_letivo='12',
        instituicao='Escola Teste',
    )
    User.objects.filter(pk=user.pk).update(is_active=False)
    user.refresh_from_db()
    return user


class EmailActivationTokenModelTestes(TestCase):

    def test_token_criado_com_uuid_unico(self):
        """Cada token tem um UUID diferente."""
        from apps.accounts.models import EmailActivationToken
        user = _criar_user_inactivo()
        t1 = EmailActivationToken.objects.create(user=user)
        t2 = EmailActivationToken.objects.create(user=user)
        self.assertNotEqual(t1.token, t2.token)

    def test_token_nao_expirado_dentro_de_24h(self):
        """Token criado agora não está expirado."""
        from apps.accounts.models import EmailActivationToken
        user = _criar_user_inactivo()
        token = EmailActivationToken.objects.create(user=user)
        self.assertFalse(token.esta_expirado())

    def test_token_expirado_apos_24h(self):
        """Token com criado_em há mais de 24h está expirado."""
        from apps.accounts.models import EmailActivationToken
        user = _criar_user_inactivo()
        token = EmailActivationToken.objects.create(user=user)
        EmailActivationToken.objects.filter(pk=token.pk).update(
            criado_em=timezone.now() - timedelta(hours=25)
        )
        token.refresh_from_db()
        self.assertTrue(token.esta_expirado())


class ActivarContaViewTestes(TestCase):

    def _criar_token(self, email='activar@escola.pt'):
        from apps.accounts.models import EmailActivationToken
        user = _criar_user_inactivo(email)
        token = EmailActivationToken.objects.create(user=user)
        return user, token

    def test_activacao_com_token_valido(self):
        """Token válido activa a conta e marca o token como utilizado."""
        from apps.accounts.models import EmailActivationToken
        user, token = self._criar_token()

        url = reverse('accounts:activar_conta', kwargs={'token': str(token.token)})
        resposta = self.client.get(url)

        user.refresh_from_db()
        token.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(token.utilizado)
        self.assertRedirects(resposta, reverse('accounts:login'))

    def test_activacao_com_token_invalido(self):
        """UUID inválido redireciona para login com mensagem de erro."""
        url = reverse('accounts:activar_conta', kwargs={'token': str(uuid.uuid4())})
        resposta = self.client.get(url)
        self.assertRedirects(resposta, reverse('accounts:login'))

    def test_activacao_com_token_ja_utilizado(self):
        """Token já utilizado não reactiva conta (não causa erro)."""
        from apps.accounts.models import EmailActivationToken
        user, token = self._criar_token()
        token.utilizado = True
        token.save()

        url = reverse('accounts:activar_conta', kwargs={'token': str(token.token)})
        self.client.get(url)  # não deve levantar excepção

    def test_activacao_com_token_expirado(self):
        """Token expirado não activa a conta."""
        from apps.accounts.models import EmailActivationToken
        user, token = self._criar_token()
        EmailActivationToken.objects.filter(pk=token.pk).update(
            criado_em=timezone.now() - timedelta(hours=25)
        )

        url = reverse('accounts:activar_conta', kwargs={'token': str(token.token)})
        self.client.get(url)

        user.refresh_from_db()
        self.assertFalse(user.is_active)


class RegistoComEmailTestes(TestCase):

    def test_registo_cria_conta_inactiva(self):
        """Após registo, conta fica inactiva até confirmar email."""
        dados = {
            'nome': 'Ana Teste',
            'curso': 'CT',
            'ano_letivo': '12',
            'instituicao': 'Escola Teste',
            'email': 'ana@escola.pt',
            'password1': 'SenhaSegura123!',
            'password2': 'SenhaSegura123!',
        }
        self.client.post(reverse('accounts:registo'), dados)
        user = User.objects.get(email='ana@escola.pt')
        self.assertFalse(user.is_active)

    def test_registo_envia_email_de_activacao(self):
        """Após registo, é enviado um email de activação."""
        dados = {
            'nome': 'Ana Teste',
            'curso': 'CT',
            'ano_letivo': '12',
            'instituicao': 'Escola Teste',
            'email': 'ana@escola.pt',
            'password1': 'SenhaSegura123!',
            'password2': 'SenhaSegura123!',
        }
        self.client.post(reverse('accounts:registo'), dados)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('ana@escola.pt', mail.outbox[0].to)

    def test_login_com_conta_inactiva_mostra_mensagem(self):
        """Tentativa de login com conta não confirmada mostra mensagem útil."""
        _criar_user_inactivo('bloqueado@escola.pt')
        dados = {'email': 'bloqueado@escola.pt', 'password': 'SenhaSegura123!'}
        resposta = self.client.post(reverse('accounts:login'), dados)
        self.assertContains(resposta, 'activ', status_code=200)
