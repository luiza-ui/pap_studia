from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.favorites.models import Favorite
from unittest.mock import patch

User = get_user_model()


class FavoriteModelTests(TestCase):
    """Testes para as regras de negócio dos Favoritos."""

    def setUp(self):
        # 1. Criar o Dono do Recurso
        self.dono = User.objects.create_user(
            email='dono@escola.pt', password='123', nome='Dono',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )

        # 2. Criar outro Aluno (que vai adicionar aos favoritos)
        self.outro_aluno = User.objects.create_user(
            email='aluno@escola.pt', password='123', nome='Aluno',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )

        # 3. Criar o Recurso pertencente ao Dono
        self.recurso = Resource.objects.create(
            usuario=self.dono,
            nome='Manual de Python',
            curso='TGPSI',
            ano_letivo='12',
            disciplina='Programação',
            instituicao='Escola'
        )

    def test_adicionar_favorito_sucesso(self):
        """Testa se um aluno consegue favoritar o recurso de outra pessoa."""
        favorito = Favorite.objects.create(usuario=self.outro_aluno, recurso=self.recurso)

        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(favorito.usuario, self.outro_aluno)

    def test_str_favorito(self):
        """Testa se o texto de representação do favorito está correto."""
        favorito = Favorite.objects.create(usuario=self.outro_aluno, recurso=self.recurso)
        esperado = f"{self.outro_aluno} favoritou {self.recurso.nome}"

        self.assertEqual(str(favorito), esperado)

    def test_nao_pode_favoritar_proprio_recurso(self):
        """Garante que o ValidationError bloqueia quem tenta favoritar o seu próprio recurso."""
        favorito_ilegal = Favorite(usuario=self.dono, recurso=self.recurso)

        with self.assertRaisesMessage(ValidationError, "Não podes adicionar os teus próprios recursos aos favoritos."):
            favorito_ilegal.save()

    def test_nao_pode_favoritar_duas_vezes(self):
        """Garante que o unique_together impede favoritos duplicados do mesmo utilizador."""
        # 1ª vez (sucesso)
        Favorite.objects.create(usuario=self.outro_aluno, recurso=self.recurso)

        # 2ª vez (tem de dar erro de integridade da BD)
        favorito_duplicado = Favorite(usuario=self.outro_aluno, recurso=self.recurso)

        with self.assertRaises(Exception):
            favorito_duplicado.save()

    def test_incrementa_contador_ao_salvar_novo(self):
        """Verifica se o contador total_salvos do Recurso sobe quando criamos o favorito."""
        # O contador começa em 0
        self.assertEqual(self.recurso.total_salvos, 0)

        # Criamos o favorito
        Favorite.objects.create(usuario=self.outro_aluno, recurso=self.recurso)

        # Recarregamos o recurso da BD para ver o valor atualizado
        self.recurso.refresh_from_db()

        # O contador tem de ter subido para 1
        self.assertEqual(self.recurso.total_salvos, 1)