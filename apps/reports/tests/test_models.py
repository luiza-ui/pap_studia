from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.reports.models import Report

User = get_user_model()


class ReportModelTests(TestCase):

    def setUp(self):
        self.denunciante = User.objects.create_user(
            email='denunciante@escola.pt', password='123', nome='Denunciante',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.infrator = User.objects.create_user(
            email='infrator@escola.pt', password='123', nome='Infrator',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.recurso = Resource.objects.create(
            usuario=self.infrator, nome='Ficheiro Suspeito', curso='TGPSI',
            ano_letivo='12', disciplina='Redes', instituicao='Escola'
        )
        self.report = Report.objects.create(
            denunciante=self.denunciante, recurso=self.recurso,
            tipo='RECURSO', motivo='Este ficheiro contém respostas de testes.'
        )

    def test_valores_padrao_do_report(self):
        self.assertEqual(self.report.status, 'PENDENTE')
        self.assertEqual(self.report.tipo, 'RECURSO')
        self.assertIsNotNone(self.report.data_criacao)
        self.assertIsNone(self.report.data_resolucao)

    def test_str_report(self):
        """__str__ segue o formato: Report #N (TIPO) — Status — alvo"""
        esperado = f"Report #{self.report.id} (RECURSO) — Pendente — {self.recurso}"
        self.assertEqual(str(self.report), esperado)

    def test_metodo_resolver_atualiza_status_e_data(self):
        self.report.resolver('RESOLVIDO')
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'RESOLVIDO')
        self.assertIsNotNone(self.report.data_resolucao)

    def test_ordenacao_reports_mais_recente_primeiro(self):
        report_novo = Report.objects.create(
            denunciante=self.denunciante, usuario_denunciado=self.infrator,
            tipo='USUARIO', motivo='Spam nos comentários.'
        )
        primeiro_report = Report.objects.first()
        self.assertEqual(primeiro_report, report_novo)
