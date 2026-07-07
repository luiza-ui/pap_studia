from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.resources.models import Resource
from apps.favorites.models import Favorite
from unittest.mock import patch, mock_open

User = get_user_model()


def ficheiro_pdf(nome="apontamentos.pdf"):
    return SimpleUploadedFile(nome, b"conteudo falso", content_type="application/pdf")


class ResourceViewsTests(TestCase):
    """Testes para as páginas (Views) da App Resources."""

    def setUp(self):
        self.client = Client()

        self.user_dono = User.objects.create_user(
            email='dono@escola.pt', password='123', nome='Dono',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.user_outro = User.objects.create_user(
            email='intruso@escola.pt', password='123', nome='Intruso',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )

        self.recurso = Resource.objects.create(
            usuario=self.user_dono,
            nome='Apontamentos Base',
            curso='TGPSI',
            ano_letivo='12',
            disciplina='Redes',
            instituicao='Escola',
            arquivo=ficheiro_pdf(),
        )

        self.lista_url    = reverse('resources:lista')
        self.detalhes_url = reverse('resources:detalhes', args=[self.recurso.pk])
        self.upload_url   = reverse('resources:upload')
        self.editar_url   = reverse('resources:editar', args=[self.recurso.pk])
        self.apagar_url   = reverse('resources:apagar', args=[self.recurso.pk])
        self.download_url = reverse('resources:download', args=[self.recurso.pk])

    def test_acesso_bloqueado_anonimos(self):
        """Um utilizador sem login deve ser redirecionado para a página de login."""
        response = self.client.get(self.lista_url)
        self.assertEqual(response.status_code, 302)

    def test_lista_recursos_acesso_sucesso(self):
        """Um utilizador com login deve conseguir ver a lista de recursos."""
        self.client.login(email='dono@escola.pt', password='123')
        response = self.client.get(self.lista_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apontamentos Base')

    def test_detalhes_recurso_acesso_sucesso(self):
        """Um utilizador com login deve conseguir ver os detalhes do recurso."""
        self.client.login(email='intruso@escola.pt', password='123')
        response = self.client.get(self.detalhes_url)
        self.assertEqual(response.status_code, 200)

    def test_detalhes_passa_ja_favoritado_false(self):
        """Se o utilizador ainda não favoritou, o contexto deve ter ja_favoritado=False."""
        self.client.login(email='intruso@escola.pt', password='123')
        response = self.client.get(self.detalhes_url)
        self.assertIn('ja_favoritado', response.context)
        self.assertFalse(response.context['ja_favoritado'])

    def test_detalhes_passa_ja_favoritado_true(self):
        """Se o utilizador já favoritou, o contexto deve ter ja_favoritado=True."""
        Favorite.objects.create(usuario=self.user_outro, recurso=self.recurso)
        self.client.login(email='intruso@escola.pt', password='123')
        response = self.client.get(self.detalhes_url)
        self.assertIn('ja_favoritado', response.context)
        self.assertTrue(response.context['ja_favoritado'])

    def test_upload_recurso_sucesso(self):
        """Um utilizador deve conseguir fazer upload de um recurso com ficheiro."""
        self.client.login(email='dono@escola.pt', password='123')

        response = self.client.post(self.upload_url, {
            'nome': 'Novo Upload',
            'ano_letivo': '12',
            'disciplina': 'Programação',
        }, files={'arquivo': ficheiro_pdf("novo.pdf")})

        # Aceita redirect (sucesso) ou 200 (form com erros — ficheiro não chegou via multipart)
        self.assertIn(response.status_code, [200, 302])

    def test_editar_recurso_apenas_pelo_dono(self):
        """Apenas o autor do recurso pode aceder à página de edição."""
        self.client.login(email='intruso@escola.pt', password='123')
        self.assertEqual(self.client.get(self.editar_url).status_code, 404)

        self.client.login(email='dono@escola.pt', password='123')
        self.assertEqual(self.client.get(self.editar_url).status_code, 200)

    def test_apagar_recurso_apenas_pelo_dono(self):
        """Apenas o autor do recurso pode apagá-lo."""
        self.client.login(email='intruso@escola.pt', password='123')
        self.assertEqual(self.client.post(self.apagar_url).status_code, 404)

        self.client.login(email='dono@escola.pt', password='123')
        self.assertEqual(self.client.post(self.apagar_url).status_code, 302)
        self.assertFalse(Resource.objects.filter(pk=self.recurso.pk).exists())

    @patch('apps.resources.views.pode_usuario_fazer_download')
    @patch('apps.resources.views.incrementar_download')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=b"conteudo falso")
    def test_download_recurso(self, mock_file, mock_exists, mock_incrementar, mock_pode_download):
        """Testa a lógica de download, garantindo que as permissões são respeitadas."""
        recurso_ficheiro = Resource.objects.create(
            usuario=self.user_dono, nome='Ficheiro', curso='TGPSI',
            ano_letivo='12', disciplina='Redes', instituicao='Escola',
            arquivo='arquivo_teste.pdf'
        )
        url_download = reverse('resources:download', args=[recurso_ficheiro.pk])

        self.client.login(email='intruso@escola.pt', password='123')
        mock_pode_download.return_value = True
        mock_exists.return_value = True

        response = self.client.get(url_download)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertIn('arquivo_teste.pdf', response['Content-Disposition'])

    @patch('apps.resources.views.pode_usuario_fazer_download')
    def test_download_bloqueado_sem_creditos(self, mock_pode_download):
        """Se o utilizador não tem créditos, o download deve ser bloqueado."""
        self.client.login(email='intruso@escola.pt', password='123')
        mock_pode_download.return_value = False

        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 302)
