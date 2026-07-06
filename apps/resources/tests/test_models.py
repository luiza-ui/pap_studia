from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.resources.models import Resource

User = get_user_model()


def ficheiro_pdf(nome="apontamentos.pdf"):
    return SimpleUploadedFile(nome, b"Conteudo falso do ficheiro de teste", content_type="application/pdf")


class ResourceModelTests(TestCase):
    """Testes para o modelo Resource (sem links)."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='aluno1@escola.pt',
            password='123',
            nome='Aluno Um',
            curso='TGPSI',
            ano_letivo='12',
            instituicao='Escola'
        )

    def test_criar_recurso_com_ficheiro_sucesso(self):
        """Testa se o recurso gera o Hash e deteta o tipo ao enviar ficheiro."""
        recurso = Resource(
            usuario=self.user1,
            nome='Ficha de Matemática',
            curso='TGPSI',
            ano_letivo='12',
            disciplina='Matemática',
            instituicao='Escola',
            arquivo=ficheiro_pdf(),
        )
        recurso.clean()
        recurso.save()

        self.assertEqual(recurso.tipo_arquivo, 'PDF')
        self.assertIsNotNone(recurso.hash_arquivo)

        # Verifica se total_uploads do utilizador subiu
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.total_uploads, 1)

    def test_erro_sem_ficheiro(self):
        """Ficheiro é obrigatório."""
        recurso = Resource(
            usuario=self.user1,
            nome='Erro',
            curso='TGPSI',
            ano_letivo='12',
            disciplina='Matemática',
            instituicao='Escola',
        )
        with self.assertRaisesMessage(ValidationError, "Tens de fornecer um Ficheiro."):
            recurso.clean()

    def test_erro_ficheiro_duplicado(self):
        """Ficheiros duplicados (mesmo hash SHA256) devem ser bloqueados."""
        conteudo = b"conteudo identico para hash duplicado"
        Resource.objects.create(
            usuario=self.user1, nome='Original', curso='TGPSI', ano_letivo='12',
            disciplina='Redes', instituicao='Escola',
            arquivo=SimpleUploadedFile("orig.pdf", conteudo, content_type="application/pdf"),
        )

        recurso2 = Resource(
            usuario=self.user1, nome='Cópia', curso='TGPSI', ano_letivo='12',
            disciplina='Redes', instituicao='Escola',
            arquivo=SimpleUploadedFile("copia.pdf", conteudo, content_type="application/pdf"),
        )
        with self.assertRaisesMessage(ValidationError, "Este ficheiro já foi enviado anteriormente."):
            recurso2.clean()

    def test_incrementar_contadores(self):
        """Testa se os métodos de incrementar downloads e salvos funcionam."""
        recurso = Resource.objects.create(
            usuario=self.user1, nome='Teste', curso='TGPSI', ano_letivo='12',
            disciplina='Redes', instituicao='Escola',
            arquivo=ficheiro_pdf(),
        )
        recurso.incrementar_download()
        recurso.incrementar_salvo()
        recurso.incrementar_salvo()

        recurso.refresh_from_db()
        self.assertEqual(recurso.total_downloads, 1)
        self.assertEqual(recurso.total_salvos, 2)
