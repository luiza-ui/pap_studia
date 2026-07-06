from django.test import TestCase, override_settings

class SafeImageStubTestes(TestCase):
    @override_settings(GOOGLE_CLOUD_CREDENTIALS='')
    def test_stub_devolve_true_sem_credenciais(self):
        from apps.moderation.services.safe_image import verificar_imagem_segura
        self.assertTrue(verificar_imagem_segura('/qualquer/caminho.png'))

    @override_settings(GOOGLE_CLOUD_CREDENTIALS='')
    def test_stub_nao_levanta_excepcao(self):
        from apps.moderation.services.safe_image import verificar_imagem_segura
        try:
            resultado = verificar_imagem_segura('/inexistente.jpg')
            self.assertIsInstance(resultado, bool)
        except Exception as e:
            self.fail(f'Excepção inesperada: {e}')
