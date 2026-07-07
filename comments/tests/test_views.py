from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.comments.models import Comment

User = get_user_model()

class CommentViewsTests(TestCase):
    """Testes para as páginas e ações (Views) da App Comments."""

    def setUp(self):
        self.client = Client()
        
        # 1. Criar o Dono do Comentário
        self.aluno_dono = User.objects.create_user(
            email='dono@escola.pt', password='123', nome='Dono',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        
        # 2. Criar um Intruso
        self.aluno_intruso = User.objects.create_user(
            email='intruso@escola.pt', password='123', nome='Intruso',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        
        # 3. Criar um Administrador (Staff)
        self.admin_user = User.objects.create_user(
            email='admin@escola.pt', password='123', nome='Admin',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.admin_user.is_staff = True
        self.admin_user.save()
        
        # 4. Criar um Recurso
        self.recurso = Resource.objects.create(
            usuario=self.aluno_dono, nome='Recurso Teste', curso='TGPSI',
            ano_letivo='12', disciplina='Redes', instituicao='Escola'
        )
        
        # 5. Criar um Comentário Inicial (pertence ao Dono)
        self.comentario = Comment.objects.create(
            usuario=self.aluno_dono,
            recurso=self.recurso,
            texto='Comentário original para ser apagado.'
        )
        
        # URLs - Parto do princípio que no teu urls.py desta app tens app_name='comments'
        self.adicionar_url = reverse('comments:adicionar_comentario', args=[self.recurso.pk])
        self.apagar_url = reverse('comments:apagar_comentario', args=[self.comentario.pk])
        self.detalhes_recurso_url = reverse('resources:detalhes', args=[self.recurso.pk])

    def test_adicionar_comentario_bloqueia_get(self):
        """Garante que o @require_POST bloqueia acessos via GET."""
        self.client.login(email='dono@escola.pt', password='123')
        response = self.client.get(self.adicionar_url)
        
        # 405 significa "Method Not Allowed" (Método não permitido)
        self.assertEqual(response.status_code, 405)

    def test_adicionar_comentario_sucesso(self):
        """Testa se um utilizador consegue adicionar um comentário com sucesso via POST."""
        self.client.login(email='intruso@escola.pt', password='123')
        dados = {'texto': 'Este é um comentário novo!'}
        
        response = self.client.post(self.adicionar_url, dados)
        
        # Verifica se redirecionou para os detalhes do recurso
        self.assertRedirects(response, self.detalhes_recurso_url)
        # Confirma que o comentário foi criado na BD
        self.assertTrue(Comment.objects.filter(texto='Este é um comentário novo!').exists())

    def test_adicionar_comentario_vazio_falha(self):
        """Testa se o sistema rejeita um comentário sem texto."""
        self.client.login(email='dono@escola.pt', password='123')
        dados = {'texto': ''}
        
        self.client.post(self.adicionar_url, dados)
        
        # Só deve existir 1 comentário na BD (o que foi criado no setUp)
        self.assertEqual(Comment.objects.count(), 1)

    def test_apagar_comentario_pelo_dono(self):
        """Garante que o autor do comentário consegue apagá-lo."""
        self.client.login(email='dono@escola.pt', password='123')
        response = self.client.get(self.apagar_url)
        
        self.assertRedirects(response, self.detalhes_recurso_url)
        self.assertEqual(Comment.objects.count(), 0) # Apagou com sucesso

    def test_apagar_comentario_pelo_admin(self):
        """Garante que um utilizador staff consegue apagar o comentário de outra pessoa."""
        self.client.login(email='admin@escola.pt', password='123')
        response = self.client.get(self.apagar_url)
        
        self.assertRedirects(response, self.detalhes_recurso_url)
        self.assertEqual(Comment.objects.count(), 0) # Apagou com sucesso

    def test_apagar_comentario_bloqueado_para_intrusos(self):
        """Garante que um aluno normal não consegue apagar os comentários dos outros."""
        self.client.login(email='intruso@escola.pt', password='123')
        response = self.client.get(self.apagar_url)
        
        self.assertRedirects(response, self.detalhes_recurso_url)
        # O comentário TEM de continuar a existir na Base de Dados
        self.assertEqual(Comment.objects.count(), 1)