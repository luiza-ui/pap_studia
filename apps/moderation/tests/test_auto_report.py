from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from apps.reports.models import Report
from apps.resources.models import Resource

User = get_user_model()

def _utilizador(email='mod@escola.pt'):
    u = User.objects.create_user(email=email, password='Teste1234!', nome='Mod', curso='CT', ano_letivo='12', instituicao='Escola Teste')
    User.objects.filter(pk=u.pk).update(is_active=True)
    u.refresh_from_db()
    return u

def _recurso(utilizador):
    r = Resource(usuario=utilizador, nome='Recurso IA Teste', curso=utilizador.curso, ano_letivo='12', disciplina='Teste', instituicao=utilizador.instituicao)
    r.arquivo = ContentFile(b'%PDF conteudo unico 1', name='teste.pdf')
    r._skip_full_clean = True
    r.save()
    return r

class CriarReportIATestes(TestCase):
    def setUp(self):
        self.utilizador = _utilizador()
        self.recurso = _recurso(self.utilizador)

    def test_cria_report_de_recurso_com_tipo_ia(self):
        from apps.moderation.auto_report import criar_report_ia
        report = criar_report_ia(recurso=self.recurso, motivo_tipo='plagio', motivo='Teste.')
        self.assertEqual(report.tipo, 'IA')
        self.assertEqual(report.status, 'PENDENTE')
        self.assertEqual(report.recurso, self.recurso)
        self.assertIsNone(report.denunciante)

    def test_cria_report_de_utilizador_com_tipo_ia(self):
        from apps.moderation.auto_report import criar_report_ia
        report = criar_report_ia(usuario=self.utilizador, motivo_tipo='improprio', motivo='Teste.')
        self.assertEqual(report.tipo, 'IA')
        self.assertEqual(report.usuario_denunciado, self.utilizador)

    def test_motivo_guardado_correctamente(self):
        from apps.moderation.auto_report import criar_report_ia
        motivo = 'Imagem imprópria.'
        report = criar_report_ia(recurso=self.recurso, motivo_tipo='improprio', motivo=motivo)
        self.assertEqual(report.motivo, motivo)
