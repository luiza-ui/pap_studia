from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from apps.resources.forms import ResourceForm


class ResourceFormTests(TestCase):

    def setUp(self):
        self.dados_base = {
            'nome': 'Apontamentos de Redes',
            'ano_letivo': '12',
            'disciplina': 'Redes de Computadores',
            'professor': 'Prof. Silva',
        }
        self.ficheiro_teste = SimpleUploadedFile(
            "teste.pdf", b"conteudo do ficheiro", content_type="application/pdf"
        )

    @patch('apps.resources.forms.verificar_arquivo_duplicado')
    def test_form_valido_com_arquivo(self, mock_verificar):
        mock_verificar.return_value = None
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

    @patch('apps.resources.forms.verificar_arquivo_duplicado')
    def test_erro_arquivo_duplicado(self, mock_verificar):
        mensagem_erro = "Já existe um recurso com este arquivo."
        mock_verificar.side_effect = Exception(mensagem_erro)
        form = ResourceForm(data=self.dados_base, files={'arquivo': self.ficheiro_teste})
        self.assertFalse(form.is_valid())
        self.assertIn('arquivo', form.errors)
        self.assertEqual(form.errors['arquivo'][0], mensagem_erro)

    def test_erro_ficheiro_demasiado_grande(self):
        ficheiro_grande = SimpleUploadedFile(
            "gigante.pdf", b"x", content_type="application/pdf"
        )
        ficheiro_grande.size = 51 * 1024 * 1024  # 51MB
        form = ResourceForm(data=self.dados_base, files={'arquivo': ficheiro_grande})
        self.assertFalse(form.is_valid())
        self.assertIn('arquivo', form.errors)
        self.assertIn('50 MB', form.errors['arquivo'][0])

    @patch('apps.resources.forms.verificar_arquivo_duplicado')
    def test_ficheiro_dentro_do_limite_aceite(self, mock_verificar):
        mock_verificar.return_value = None
        ficheiro_pequeno = SimpleUploadedFile(
            "pequeno.pdf", b"conteudo pequeno", content_type="application/pdf"
        )
        ficheiro_pequeno.size = 10 * 1024 * 1024  # 10MB
        form = ResourceForm(data=self.dados_base, files={'arquivo': ficheiro_pequeno})
        self.assertTrue(form.is_valid())
