from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.reports.models import Report

User = get_user_model()


class ReportViewsTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.aluno = User.objects.create_user(
            email='aluno@escola.pt', password='123', nome='Aluno Teste',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.admin = User.objects.create_user(
            email='admin@escola.pt', password='123', nome='Admin Teste',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.admin.is_staff = True
        self.admin.save()

        self.dono_recurso = User.objects.create_user(
            email='dono@escola.pt', password='123', nome='Dono',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.recurso = Resource.objects.create(
            usuario=self.dono_recurso, nome='Recurso Teste', curso='TGPSI',
            ano_letivo='12', disciplina='Programação', instituicao='Escola'
        )
        self.report = Report.objects.create(
            denunciante=self.aluno, recurso=self.recurso,
            tipo='RECURSO', motivo='Conteúdo impróprio'
        )

        self.lista_url = reverse('reports:lista')
        self.aceitar_url = reverse('reports:resolver', args=[self.report.pk, 'aceitar'])
        self.rejeitar_url = reverse('reports:resolver', args=[self.report.pk, 'rejeitar'])

    def test_lista_reports_bloqueia_alunos(self):
        self.client.login(email='aluno@escola.pt', password='123')
        response = self.client.get(self.lista_url)
        self.assertEqual(response.status_code, 302)

    def test_lista_reports_permite_admin(self):
        self.client.login(email='admin@escola.pt', password='123')
        response = self.client.get(self.lista_url)
        self.assertEqual(response.status_code, 200)

    def test_resolver_report_rejeita_get(self):
        """Resolver um report por GET deve ser rejeitado (405)."""
        self.client.login(email='admin@escola.pt', password='123')
        response = self.client.get(self.aceitar_url)
        self.assertEqual(response.status_code, 405)

    def test_aceitar_report_apaga_recurso(self):
        """Aceitar um report por POST deve apagar o recurso."""
        self.client.login(email='admin@escola.pt', password='123')
        self.client.post(self.aceitar_url)
        self.assertFalse(Resource.objects.filter(pk=self.recurso.pk).exists())

    def test_aceitar_report_marca_resolvido(self):
        self.client.login(email='admin@escola.pt', password='123')
        self.client.post(self.aceitar_url)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'RESOLVIDO')

    def test_rejeitar_report_mantém_recurso(self):
        self.client.login(email='admin@escola.pt', password='123')
        self.client.post(self.rejeitar_url)
        self.assertTrue(Resource.objects.filter(pk=self.recurso.pk).exists())

    def test_rejeitar_report_incrementa_falsos_no_denunciante(self):
        self.client.login(email='admin@escola.pt', password='123')
        self.client.post(self.rejeitar_url)
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.total_reports_falsos, 1)

    def test_bloquear_conta_apos_3_reports_falsos(self):
        """Após 3 reports falsos, a conta do denunciante é bloqueada automaticamente."""
        self.client.login(email='admin@escola.pt', password='123')
        for i in range(3):
            recurso_extra = Resource.objects.create(
                usuario=self.admin, nome=f'Recurso Extra {i}', curso='TGPSI',
                ano_letivo='12', disciplina='Redes', instituicao='Escola'
            )
            report_extra = Report.objects.create(
                denunciante=self.aluno, recurso=recurso_extra,
                tipo='RECURSO', motivo='Denúncia falsa'
            )
            url = reverse('reports:resolver', args=[report_extra.pk, 'rejeitar'])
            self.client.post(url)
        self.aluno.refresh_from_db()
        self.assertFalse(self.aluno.is_active)

    def test_acao_invalida_retorna_404(self):
        self.client.login(email='admin@escola.pt', password='123')
        url_invalida = reverse('reports:resolver', args=[self.report.pk, 'inventada'])
        response = self.client.post(url_invalida)
        self.assertEqual(response.status_code, 404)

    def test_criar_report_recurso_sucesso(self):
        outro_aluno = User.objects.create_user(
            email='outro@escola.pt', password='123', nome='Outro',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.client.login(email='outro@escola.pt', password='123')
        url = reverse('reports:criar_recurso', args=[self.recurso.pk])
        response = self.client.post(url, {'motivo_tipo': 'spam', 'motivo': 'Nova denúncia'})
        self.assertEqual(Report.objects.count(), 2)
        self.assertRedirects(response, reverse('resources:detalhes', args=[self.recurso.pk]))
