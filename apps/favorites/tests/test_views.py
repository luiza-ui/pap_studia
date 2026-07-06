from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.favorites.models import Favorite

User = get_user_model()


class FavoriteViewsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.dono = User.objects.create_user(
            email='dono@escola.pt', password='123', nome='Dono',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.aluno = User.objects.create_user(
            email='aluno@escola.pt', password='123', nome='Aluno',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.recurso = Resource.objects.create(
            usuario=self.dono, nome='Manual de Redes', curso='TGPSI',
            ano_letivo='12', disciplina='Redes', instituicao='Escola',
            link='https://manual.com', total_salvos=0
        )
        self.toggle_url = reverse('favorites:toggle', args=[self.recurso.pk])
        self.remover_url = reverse('favorites:remover', args=[self.recurso.pk])
        self.detalhes_url = reverse('resources:detalhes', args=[self.recurso.pk])

    def test_toggle_adicionar_favorito(self):
        """Toggle via POST deve criar o favorito."""
        self.client.login(email='aluno@escola.pt', password='123')
        response = self.client.post(self.toggle_url)
        self.assertRedirects(response, self.detalhes_url)
        self.assertEqual(Favorite.objects.count(), 1)
        self.recurso.refresh_from_db()
        self.assertGreater(self.recurso.total_salvos, 0)

    def test_toggle_remover_favorito(self):
        """Toggle via POST quando favorito já existe deve removê-lo."""
        self.client.login(email='aluno@escola.pt', password='123')
        Favorite.objects.create(usuario=self.aluno, recurso=self.recurso)
        Resource.objects.filter(pk=self.recurso.pk).update(total_salvos=1)
        response = self.client.post(self.toggle_url)
        self.assertRedirects(response, self.detalhes_url)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_toggle_rejeita_get(self):
        """Toggle via GET deve ser rejeitado com 405."""
        self.client.login(email='aluno@escola.pt', password='123')
        response = self.client.get(self.toggle_url)
        self.assertEqual(response.status_code, 405)

    def test_remover_favorito_view_redireciona_para_perfil(self):
        """Remover favorito da página de perfil deve redirecionar para o perfil."""
        self.client.login(email='aluno@escola.pt', password='123')
        Favorite.objects.create(usuario=self.aluno, recurso=self.recurso)
        response = self.client.post(self.remover_url)
        self.assertRedirects(response, reverse('accounts:perfil'))
        self.assertEqual(Favorite.objects.count(), 0)

    def test_remover_rejeita_get(self):
        """Remover via GET deve ser rejeitado com 405."""
        self.client.login(email='aluno@escola.pt', password='123')
        response = self.client.get(self.remover_url)
        self.assertEqual(response.status_code, 405)

    def test_views_protegidas_por_login(self):
        """Sem login, as views devem redirecionar para o login."""
        self.assertEqual(self.client.post(self.toggle_url).status_code, 302)
        self.assertEqual(self.client.post(self.remover_url).status_code, 302)
