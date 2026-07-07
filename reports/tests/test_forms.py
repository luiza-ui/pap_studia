from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.resources.models import Resource
from apps.reports.models import Report
from apps.reports.forms import ReportRecursoForm, ReportUsuarioForm

User = get_user_model()


class ReportRecursoFormTests(TestCase):

    def setUp(self):
        self.denunciante = User.objects.create_user(
            email='denunciante@escola.pt', password='123', nome='Denunciante',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.dono = User.objects.create_user(
            email='dono@escola.pt', password='123', nome='Dono',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.recurso = Resource.objects.create(
            usuario=self.dono, nome='Ficheiro Suspeito', curso='TGPSI',
            ano_letivo='12', disciplina='Redes', instituicao='Escola'
        )

    def test_form_valido(self):
        form = ReportRecursoForm(
            data={'motivo_tipo': 'improprio', 'motivo': 'Conteúdo impróprio'},
            usuario=self.denunciante,
            recurso=self.recurso
        )
        self.assertTrue(form.is_valid())

    def test_form_invalido_sem_motivo(self):
        """Quando o tipo é 'outro', os detalhes (motivo) passam a ser obrigatórios."""
        form = ReportRecursoForm(
            data={'motivo_tipo': 'outro', 'motivo': ''},
            usuario=self.denunciante,
            recurso=self.recurso
        )
        self.assertFalse(form.is_valid())
        self.assertIn('motivo', form.errors)

    def test_bloqueia_report_duplicado_independente_de_status(self):
        """
        Após já ter sido feito um report (qualquer status), não pode fazer outro.
        Corrigido: antes só bloqueava se o report anterior estava PENDENTE.
        """
        # Cria primeiro report já resolvido
        Report.objects.create(
            denunciante=self.denunciante, recurso=self.recurso,
            tipo='RECURSO', motivo='Primeira denúncia', status='RESOLVIDO'
        )
        form = ReportRecursoForm(
            data={'motivo': 'Segunda tentativa'},
            usuario=self.denunciante,
            recurso=self.recurso
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Já enviaste uma denúncia para este recurso.', form.non_field_errors())

    def test_bloqueia_reportar_proprio_recurso(self):
        form = ReportRecursoForm(
            data={'motivo': 'Auto-report'},
            usuario=self.dono,
            recurso=self.recurso
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Não podes reportar os teus próprios recursos.', form.non_field_errors())


class ReportUsuarioFormTests(TestCase):

    def setUp(self):
        self.denunciante = User.objects.create_user(
            email='denunciante@escola.pt', password='123', nome='Denunciante',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )
        self.denunciado = User.objects.create_user(
            email='denunciado@escola.pt', password='123', nome='Denunciado',
            curso='TGPSI', ano_letivo='12', instituicao='Escola'
        )

    def test_form_valido(self):
        form = ReportUsuarioForm(
            data={'motivo_tipo': 'ofensa', 'motivo': 'Comportamento inadequado'},
            usuario=self.denunciante,
            denunciado=self.denunciado
        )
        self.assertTrue(form.is_valid())

    def test_bloqueia_auto_report(self):
        form = ReportUsuarioForm(
            data={'motivo': 'Auto-report'},
            usuario=self.denunciante,
            denunciado=self.denunciante
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Não podes reportar a ti mesmo.', form.non_field_errors())

    def test_bloqueia_report_duplicado_independente_de_status(self):
        Report.objects.create(
            denunciante=self.denunciante, usuario_denunciado=self.denunciado,
            tipo='USUARIO', motivo='Primeira denúncia', status='REJEITADO'
        )
        form = ReportUsuarioForm(
            data={'motivo': 'Segunda tentativa'},
            usuario=self.denunciante,
            denunciado=self.denunciado
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Já enviaste uma denúncia sobre este utilizador.', form.non_field_errors())
