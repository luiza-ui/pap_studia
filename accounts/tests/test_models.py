from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

User = get_user_model()

class UserModelTests(TestCase):
    """
    Testes focados na estrutura de dados do Utilizador (Model).
    """

    def test_criar_user_normal_sucesso(self):
        """Testa a criação de um utilizador padrão com TODOS os dados obrigatórios."""
        email = 'aluno@escola.pt'
        password = 'senha_segura_123'
        nome = 'João Aluno'
        
        # AGORA COM OS CAMPOS QUE FALTAVAM:
        user = User.objects.create_user(
            email=email, 
            password=password, 
            nome=nome,
            curso='TGPSI',           # Campo obrigatório 1
            ano_letivo=12,           # Campo obrigatório 2
            instituicao='Escola X'   # Campo obrigatório 3
        )

        self.assertEqual(user.email, email)
        self.assertEqual(user.curso, 'TGPSI') # Verifica se gravou o curso
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)

    def test_criar_superuser_sucesso(self):
        """
        Testa se o superuser é criado corretamente.
        Geralmente superusers não precisam de curso/ano, mas depende do teu Manager.
        Se falhar, adicionamos curso/ano aqui também.
        """
        email = 'admin@escola.pt'
        password = 'admin_password'
        
        admin_user = User.objects.create_superuser(
            email=email, 
            password=password, 
            nome='Admin'
        )

        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_erro_criar_user_sem_email(self):
        """O sistema deve impedir criar utilizador sem email."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None, 
                password='123', 
                nome='Sem Email',
                curso='TGPSI', ano_letivo=10, instituicao='X'
            )
        
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='', 
                password='123', 
                nome='Email Vazio',
                curso='TGPSI', ano_letivo=10, instituicao='X'
            )

    def test_erro_criar_email_duplicado(self):
        """A base de dados deve impedir dois utilizadores com o mesmo email."""
        email = 'unico@escola.pt'
        
        # Cria o primeiro
        User.objects.create_user(
            email=email, password='123', nome='User 1',
            curso='TGPSI', ano_letivo=10, instituicao='X'
        )

        # Tenta criar o segundo igual
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email=email, password='456', nome='User 2',
                curso='TGPSI', ano_letivo=10, instituicao='X'
            )

    def test_validacao_formato_email(self):
        """
        Testa se o modelo rejeita emails inválidos.
        """
        user = User(
            email='email_sem_arroba', 
            password='123', 
            nome='Teste',
            curso='TGPSI', ano_letivo=10, instituicao='X'
        )
        
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_metodo_str(self):
        """O método __str__ deve retornar o email do utilizador."""
        email = 'teste@str.com'
        user = User.objects.create_user(
            email=email, password='123', nome='Teste Str',
            curso='TGPSI', ano_letivo=10, instituicao='X'
        )
        
        self.assertEqual(str(user), email)

    def test_nome_opcional_ou_obrigatorio(self):
        """Verifica se o nome foi gravado corretamente."""
        user = User.objects.create_user(
            email='nome@teste.com', password='123', nome='Carlos',
            curso='TGPSI', ano_letivo=10, instituicao='X'
        )
        self.assertEqual(user.nome, 'Carlos')