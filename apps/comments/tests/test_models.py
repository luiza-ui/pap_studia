from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.comments.models import Comment

User = get_user_model()

class CommentModelTests(TestCase):
    """Testes para a base de dados dos Comentários."""

    def setUp(self):
        # 1. Criar um utilizador
        self.user = User.objects.create_user(
            email='aluno@escola.pt', password='123', nome='Aluno Teste',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        
        # 2. Criar um recurso para ser comentado
        self.recurso = Resource.objects.create(
            usuario=self.user,
            nome='Apontamentos de Redes',
            curso='TGPSI',
            ano_letivo='12',
            disciplina='Redes',
            instituicao='Escola'
        )
        
        # 3. Criar o comentário base
        self.comentario = Comment.objects.create(
            usuario=self.user,
            recurso=self.recurso,
            texto='Muito obrigado por partilhares isto! Ajudou imenso.'
        )

    def test_comentario_criado_com_sucesso(self):
        """Testa se o comentário é gravado corretamente na base de dados."""
        self.assertTrue(Comment.objects.filter(texto__contains='Ajudou imenso').exists())

    def test_str_comentario(self):
        """Testa a representação em string do comentário (o def __str__)."""
        esperado = f"Comentário de {self.user} em {self.recurso}"
        self.assertEqual(str(self.comentario), esperado)

    def test_comentario_ativo_por_defeito(self):
        """Garante que um comentário recém-criado está ativo e visível no site."""
        self.assertTrue(self.comentario.ativo)

    def test_ordenacao_comentarios(self):
        """Testa se o comentário mais recente aparece em primeiro lugar (ordering)."""
        # Criamos um segundo comentário, que é mais recente que o do setUp
        comentario_novo = Comment.objects.create(
            usuario=self.user,
            recurso=self.recurso,
            texto='Só para acrescentar mais uma dúvida...'
        )
        
        # Vamos buscar todos os comentários daquele recurso
        comentarios = Comment.objects.filter(recurso=self.recurso)
        
        # O primeiro da lista (index 0) tem de ser o 'comentario_novo' 
        # devido à regra Meta: ordering = ['-criado_em']
        self.assertEqual(comentarios.first(), comentario_novo)