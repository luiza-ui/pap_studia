from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.favorites.models import Favorite
from apps.favorites.services import adicionar_favorito, remover_favorito, is_favorito

User = get_user_model()


class FavoriteServicesTests(TestCase):
    """Testes para a camada de serviços dos Favoritos."""

    def setUp(self):
        self.dono = User.objects.create_user(
            email='dono@escola.pt', password='123', nome='Dono',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )

        self.aluno = User.objects.create_user(
            email='aluno@escola.pt', password='123', nome='Aluno',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )

        self.recurso = Resource.objects.create(
            usuario=self.dono,
            nome='Manual de Redes',
            curso='TGPSI',
            ano_letivo='12',
            disciplina='Redes',
            instituicao='Escola'
        )

    # ----------------------
    # is_favorito
    # ----------------------

    def test_is_favorito_retorna_false_quando_nao_existe(self):
        """is_favorito deve retornar False quando o aluno ainda não favoritou."""
        self.assertFalse(is_favorito(self.aluno, self.recurso))

    def test_is_favorito_retorna_true_quando_existe(self):
        """is_favorito deve retornar True quando o favorito já existe na BD."""
        Favorite.objects.create(usuario=self.aluno, recurso=self.recurso)
        self.assertTrue(is_favorito(self.aluno, self.recurso))

    def test_is_favorito_e_especifico_ao_utilizador(self):
        """is_favorito deve ser específico ao utilizador — outro aluno não interfere."""
        outro_aluno = User.objects.create_user(
            email='outro@escola.pt', password='123', nome='Outro',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        # Outro aluno favorita, não o aluno principal
        Favorite.objects.create(usuario=outro_aluno, recurso=self.recurso)

        # O aluno principal não deve aparecer como tendo favoritado
        self.assertFalse(is_favorito(self.aluno, self.recurso))

    # ----------------------
    # adicionar_favorito
    # ----------------------

    def test_adicionar_favorito_sucesso(self):
        """adicionar_favorito deve criar o favorito e retorná-lo."""
        favorito = adicionar_favorito(self.aluno, self.recurso)

        self.assertIsNotNone(favorito)
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(favorito.usuario, self.aluno)
        self.assertEqual(favorito.recurso, self.recurso)

    def test_adicionar_favorito_duplicado_lanca_erro(self):
        """adicionar_favorito deve lançar ValidationError se já existir."""
        Favorite.objects.create(usuario=self.aluno, recurso=self.recurso)

        with self.assertRaises(ValidationError):
            adicionar_favorito(self.aluno, self.recurso)

    # ----------------------
    # remover_favorito
    # ----------------------

    def test_remover_favorito_sucesso(self):
        """remover_favorito deve apagar o favorito da BD."""
        Favorite.objects.create(usuario=self.aluno, recurso=self.recurso)

        resultado = remover_favorito(self.aluno, self.recurso)

        self.assertTrue(resultado)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_remover_favorito_inexistente_lanca_erro(self):
        """remover_favorito deve lançar ValidationError se o favorito não existir."""
        with self.assertRaises(ValidationError):
            remover_favorito(self.aluno, self.recurso)