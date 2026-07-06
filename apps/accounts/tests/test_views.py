from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class LoginLogoutTests(TestCase):

    def setUp(self):
        self.email = 'teste@login.com'
        self.password = 'senhaSegura123'
        self.user = User.objects.create_user(
            email=self.email, password=self.password, nome="User Teste",
            curso='TGPSI', ano_letivo=12, instituicao='Escola X'
        )
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')

    def test_pagina_login_carrega_corretamente(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_sucesso(self):
        response = self.client.post(self.login_url, {
            'email': self.email,
            'password': self.password
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_senha_errada(self):
        response = self.client.post(self.login_url, {
            'email': self.email,
            'password': 'senhaErrada'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requer_post(self):
        """Logout por GET deve ser rejeitado com 405 Method Not Allowed."""
        self.client.login(email=self.email, password=self.password)
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 405)
        # Sessão mantida — o GET não fez logout
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_sucesso_via_post(self):
        """Logout por POST deve encerrar a sessão."""
        self.client.login(email=self.email, password=self.password)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_utilizador_ja_logado(self):
        self.client.login(email=self.email, password=self.password)
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)


class RegistoViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.registo_url = reverse('accounts:registo')

    def test_pagina_registo_carrega(self):
        response = self.client.get(self.registo_url)
        self.assertEqual(response.status_code, 200)

    def test_registo_utilizador_sucesso(self):
        dados = {
            'nome': 'Novo Aluno',
            'curso': 'TGPSI',
            'ano_letivo': 10,
            'instituicao': 'Escola Secundária',
            'email': 'novo.aluno@escola.pt',
            'password1': 'senhaSegura123',
            'password2': 'senhaSegura123'
        }
        response = self.client.post(self.registo_url, dados)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='novo.aluno@escola.pt').exists())

    def test_registo_utilizador_ja_logado(self):
        User.objects.create_user(
            email='logado@escola.pt', password='123', nome='Logado',
            curso='TGPSI', ano_letivo=10, instituicao='Escola'
        )
        self.client.login(email='logado@escola.pt', password='123')
        response = self.client.get(self.registo_url)
        self.assertEqual(response.status_code, 302)


class PerfilViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.perfil_url = reverse('accounts:perfil')
        self.editar_url = reverse('accounts:editar_perfil')
        self.apagar_url = reverse('accounts:apagar_conta')
        self.user = User.objects.create_user(
            email='aluno@perfil.com', password='senha123', nome='Aluno',
            curso='TGPSI', ano_letivo=12, instituicao='Escola'
        )

    def test_acesso_perfil_anonimo_rejeitado(self):
        response = self.client.get(self.perfil_url)
        self.assertEqual(response.status_code, 302)

    def test_acesso_perfil_logado_permitido(self):
        self.client.login(email='aluno@perfil.com', password='senha123')
        response = self.client.get(self.perfil_url)
        self.assertEqual(response.status_code, 200)

    def test_editar_perfil_sucesso(self):
        self.client.login(email='aluno@perfil.com', password='senha123')
        dados = {
            'nome': 'Nome Alterado',
            'curso': 'TGPSI', 'ano_letivo': 12, 'instituicao': 'Escola'
        }
        self.client.post(self.editar_url, dados)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nome, 'Nome Alterado')

    def test_apagar_conta_requer_senha_correta(self):
        """Apagar conta com senha errada deve falhar e manter a conta."""
        self.client.login(email='aluno@perfil.com', password='senha123')
        response = self.client.post(self.apagar_url, {'senha': 'senhaErrada'})
        # Fica na mesma página (200) com mensagem de erro
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='aluno@perfil.com').exists())

    def test_apagar_conta_sucesso_com_senha_correta(self):
        """Apagar conta com senha correta deve eliminar a conta."""
        self.client.login(email='aluno@perfil.com', password='senha123')
        response = self.client.post(self.apagar_url, {'senha': 'senha123'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(email='aluno@perfil.com').exists())
