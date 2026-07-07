from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.resources.services import (
    calcular_hash_arquivo,
    verificar_arquivo_duplicado,
    pode_usuario_fazer_download,
    incrementar_download,
    incrementar_salvo
)
import hashlib
from unittest.mock import patch

User = get_user_model()


def recurso_simples(user, nome="Recurso", arquivo=None):
    """Cria um recurso de teste com ficheiro obrigatório."""
    if arquivo is None:
        arquivo = SimpleUploadedFile(f"{nome}.pdf", b"conteudo", content_type="application/pdf")
    return Resource.objects.create(
        usuario=user, nome=nome, curso='TGPSI',
        ano_letivo='12', disciplina='Redes', instituicao='Escola',
        arquivo=arquivo,
    )


class ServicesTests(TestCase):
    """Testes para a lógica de negócio isolada no services.py."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='services@escola.pt', password='123', nome='Testador',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )

        self.conteudo_ficheiro = b"Ficheiro super secreto para testar o hash"
        self.ficheiro = SimpleUploadedFile(
            "secreto.pdf",
            self.conteudo_ficheiro,
            content_type="application/pdf"
        )
        self.hash_esperado = hashlib.sha256(self.conteudo_ficheiro).hexdigest()

        # Recurso base para testes de download/salvo (usa ficheiro próprio)
        self.recurso = recurso_simples(self.user, nome='Recurso de Serviços')

    def test_calcular_hash_arquivo_sucesso(self):
        """Testa se a função de cálculo de Hash devolve a string SHA256 correta."""
        self.ficheiro.seek(0)
        resultado = calcular_hash_arquivo(self.ficheiro)
        self.assertEqual(resultado, self.hash_esperado)

    def test_verificar_arquivo_duplicado_passa(self):
        """Testa o caso em que o ficheiro é novo (não existe duplicado na BD)."""
        self.ficheiro.seek(0)
        verificar_arquivo_duplicado(self.ficheiro)  # não deve levantar erro

    def test_verificar_arquivo_duplicado_falha(self):
        """Testa se a função levanta ValidationError quando encontra o mesmo Hash na BD."""
        # Gravar um recurso com o hash do nosso ficheiro
        Resource.objects.create(
            usuario=self.user, nome='Cópia Antiga', curso='TGPSI',
            ano_letivo='12', disciplina='Redes', instituicao='Escola',
            hash_arquivo=self.hash_esperado
        )

        self.ficheiro.seek(0)
        with self.assertRaisesMessage(ValidationError, "Já existe um recurso com este arquivo."):
            verificar_arquivo_duplicado(self.ficheiro)

    def test_verificar_arquivo_duplicado_ignora_proprio_recurso(self):
        """Ao editar um recurso sem mudar o ficheiro não deve dar erro de duplicado."""
        recurso_existente = Resource.objects.create(
            usuario=self.user, nome='Recurso Existente', curso='TGPSI',
            ano_letivo='12', disciplina='Redes', instituicao='Escola',
            hash_arquivo=self.hash_esperado
        )

        self.ficheiro.seek(0)
        verificar_arquivo_duplicado(self.ficheiro, exclude_pk=recurso_existente.pk)

    @patch.object(User, 'pode_fazer_download')
    def test_pode_usuario_fazer_download(self, mock_metodo_user):
        """Testa se o serviço lê corretamente a permissão do Utilizador."""
        mock_metodo_user.return_value = True
        self.assertTrue(pode_usuario_fazer_download(self.user))

        mock_metodo_user.return_value = False
        self.assertFalse(pode_usuario_fazer_download(self.user))

    def test_incrementar_download(self):
        """Verifica se soma +1 download tanto no Recurso como no Utilizador."""
        incrementar_download(self.recurso, self.user)

        self.recurso.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(self.recurso.total_downloads, 1)
        self.assertEqual(self.user.total_downloads, 1)

    def test_incrementar_salvo(self):
        """Verifica se soma +1 no número de vezes que o Recurso foi salvo."""
        incrementar_salvo(self.recurso)

        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.total_salvos, 1)
