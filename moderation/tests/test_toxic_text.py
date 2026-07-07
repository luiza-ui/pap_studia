from django.test import TestCase, override_settings

class ToxicTextStubTestes(TestCase):
    @override_settings(PERSPECTIVE_API_KEY='')
    def test_stub_devolve_true_sem_chave(self):
        from apps.moderation.services.toxic_text import verificar_texto_seguro
        self.assertTrue(verificar_texto_seguro('qualquer texto'))

    @override_settings(PERSPECTIVE_API_KEY='')
    def test_stub_com_string_vazia(self):
        from apps.moderation.services.toxic_text import verificar_texto_seguro
        self.assertTrue(verificar_texto_seguro(''))

    @override_settings(PERSPECTIVE_API_KEY='')
    def test_stub_nao_levanta_excepcao(self):
        from apps.moderation.services.toxic_text import verificar_texto_seguro
        try:
            resultado = verificar_texto_seguro('texto de teste')
            self.assertIsInstance(resultado, bool)
        except Exception as e:
            self.fail(f'Excepção: {e}')
