from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.forms import UserRegistrationForm, LoginForm, EditarPerfilForm

User = get_user_model()

class UserRegistrationFormTests(TestCase):
    """
    Testes para o formulário de Registo de Alunos.
    """

    def test_registo_valido(self):
        """O formulário deve ser válido com dados corretos."""
        form_data = {
            'nome': 'Novo Aluno',
            'curso': 'TGPSI',
            'ano_letivo': 10,
            'instituicao': 'Escola Secundária',
            'email': 'novo@escola.pt',
            'password1': 'PasseForte9!Xy',
            'password2': 'PasseForte9!Xy'  # Senhas iguais
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes(self):
        """O formulário deve dar erro se as senhas não coincidirem."""
        form_data = {
            'nome': 'Aluno Teste',
            'curso': 'TGPSI',
            'ano_letivo': 10,
            'instituicao': 'Escola X',
            'email': 'teste@escola.pt',
            'password1': 'PasseForte9!Xy',
            'password2': 'outraSenha'  # Senhas diferentes
        }
        form = UserRegistrationForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors) # O erro deve estar no campo da 2ª senha
        self.assertEqual(form.errors['password2'][0], "As senhas não coincidem.")

    def test_email_duplicado(self):
        """O formulário não pode aceitar um email que já existe."""
        # 1. Criar um utilizador primeiro
        User.objects.create_user(
            email='duplicado@escola.pt', 
            password='123', 
            nome='Original',
            curso='X', ano_letivo=10, instituicao='Y'
        )

        # 2. Tentar registar outro com o mesmo email
        form_data = {
            'nome': 'Impostor',
            'curso': 'TGPSI',
            'ano_letivo': 10,
            'instituicao': 'Escola X',
            'email': 'duplicado@escola.pt', # Email repetido
            'password1': 'PasseForte9!Xy',
            'password2': 'PasseForte9!Xy'
        }
        form = UserRegistrationForm(data=form_data)

        self.assertFalse(form.is_valid())
        # Verifica se o erro foi parar ao campo específico 'email'
        self.assertIn('email', form.errors) 
        # Verifica se a mensagem de erro é a correta
        self.assertEqual(form.errors['email'][0], "Este email já está registado.")
        # Nota: No teu form, tu lanças ValidationError no clean_email, então o erro deve estar em 'email'
        # Vamos verificar se está em 'email' ou '__all__' (ajustarei se falhar)
        
class LoginFormTests(TestCase):
    """
    Testes para o formulário de Login.
    """
    def setUp(self):
        self.email = 'login@teste.com'
        self.password = 'PasseForte9!Xy'
        self.user = User.objects.create_user(
            email=self.email, 
            password=self.password, 
            nome='User Login',
            curso='X', ano_letivo=10, instituicao='Y'
        )

    def test_login_form_valido(self):
        """Formulário aceita credenciais corretas."""
        form_data = {
            'email': self.email,
            'password': self.password
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Verifica se o user foi anexado ao cleaned_data (lógica do teu form)
        self.assertEqual(form.cleaned_data['user'], self.user)

    def test_login_senha_incorreta(self):
        """Formulário rejeita senha errada."""
        form_data = {
            'email': self.email,
            'password': 'errada'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        # O erro geralmente vem em __all__ (erros não associados a campo específico) 
        # ou associado a um campo se usares add_error.
        # No teu código usaste raise ValidationError("..."), o que vai para __all__
        self.assertIn('__all__', form.errors)
        
class EditarPerfilFormTests(TestCase):
    """
    Testes para o formulário de Edição de Perfil.
    """

    def setUp(self):
        # A view real sempre passa instance=request.user (com email já definido).
        # Um form sem instance tem um User em branco com email='', o que faz o
        # User.clean() (validação de domínio institucional) falhar sempre.
        self.user = User.objects.create_user(
            email='perfilform@escola.pt', password='PasseForte9!Xy', nome='Nome',
            curso='TGPSI', ano_letivo='11', instituicao='Escola Y'
        )

    def test_editar_perfil_valido_sem_senha(self):
        """O form deve ser válido se o aluno só mudar os dados e não a senha."""
        form_data = {
            'nome': 'Nome Atualizado',
            'curso': 'TGPSI',
            'ano_letivo': 11,
            'instituicao': 'Escola Nova'
        }
        form = EditarPerfilForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_editar_perfil_com_senha_valida(self):
        """O form deve ser válido se o aluno quiser mudar a senha e as duas baterem certo."""
        form_data = {
            'nome': 'Nome', 'curso': 'TGPSI', 'ano_letivo': 11, 'instituicao': 'Escola Y',
            'password1': 'novaSenha123',
            'password2': 'novaSenha123'
        }
        form = EditarPerfilForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_editar_perfil_senhas_diferentes(self):
        """O form deve dar erro se as novas senhas não coincidirem."""
        form_data = {
            'nome': 'Nome', 'curso': 'TGPSI', 'ano_letivo': 11, 'instituicao': 'Escola Y',
            'password1': 'novaSenha123',
            'password2': 'senhaDiferente'
        }
        form = EditarPerfilForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertEqual(form.errors['password2'][0], "As senhas não coincidem.")