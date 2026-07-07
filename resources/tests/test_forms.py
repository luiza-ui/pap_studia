from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from apps.resources.forms import ResourceForm
from apps.resources.models import Resource

User = get_user_model()


class ResourceFormTests(TestCase):

    def setUp(self):
        self.dono = User.objects.create_user(
            email='dono.form@escola.pt', password='PasseForte9!Xy', nome='Dono',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.dados_base = {
            'nome': 'Apontamentos de Redes',
            'ano_letivo': '12',
            'disciplina': 'Redes de Computadores',
            'professor': 'Prof. Silva',
        }
        self.ficheiro_teste = SimpleUploadedFile(
            "teste.pdf", b"conteudo do ficheiro", content_type="application/pdf"
        )

    def test_form_valido_com_arquivo(self):
        form = ResourceForm(
            data=self.dados_base,
            files={'arquivo': self.ficheiro_teste}
        )
        self.assertTrue(form.is_valid())

    def test_erro_sem_ficheiro(self):
        """O formulário exige um ficheiro."""
        form = ResourceForm(data=self.dados_base)
        self.assertFalse(form.is_valid())
        self.assertIn('Tens de fornecer um Ficheiro.', form.non_field_errors())

    def test_arquivo_duplicado_nao_bloqueia_form(self):
        """
        Ficheiros duplicados (mesmo hash) já não são bloqueados ao nível do
        formulário: são aceites e passam pela verificação de plágio/moderação
        assíncrona feita na view após o guardar (ver apps.moderation).
        """
        Resource.objects.create(
            usuario=self.dono,
            nome='Original', curso='TGPSI', ano_letivo='12',
            disciplina='Redes', instituicao='Escola',
            hash_arquivo='hash-repetido',
        )
        form = ResourceForm(data=self.dados_base, files={'arquivo': self.ficheiro_teste})
        self.assertTrue(form.is_valid())

    def test_erro_ficheiro_demasiado_grande(self):
        ficheiro_grande = SimpleUploadedFile(
            "gigante.pdf", b"x", content_type="application/pdf"
        )
        ficheiro_grande.size = 51 * 1024 * 1024  # 51MB
        form = ResourceForm(data=self.dados_base, files={'arquivo': ficheiro_grande})
        self.assertFalse(form.is_valid())
        self.assertIn('arquivo', form.errors)
        self.assertIn('50 MB', form.errors['arquivo'][0])

    def test_ficheiro_dentro_do_limite_aceite(self):
        ficheiro_pequeno = SimpleUploadedFile(
            "pequeno.pdf", b"conteudo pequeno", content_type="application/pdf"
        )
        ficheiro_pequeno.size = 10 * 1024 * 1024  # 10MB
        form = ResourceForm(data=self.dados_base, files={'arquivo': ficheiro_pequeno})
        self.assertTrue(form.is_valid())
