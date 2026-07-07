"""
Management command para popular a BD com dados de demonstração completos
para a apresentação da PAP.

Cobre todos os cenários testáveis:
  - Superutilizador (admin)
  - Alunos de cursos e anos diferentes
  - Recursos de todos os tipos (PDF, DOCX, PPTX, IMG)
  - Comentários em recursos
  - Favoritos
  - Denúncias pendentes (recurso e utilizador), com todos os motivos
  - Um aluno bloqueado (is_active=False)
  - Um aluno sem créditos para descarregamento
  - Um aluno com denúncias falsas

Todas as contas de demonstração têm palavras-passe fortes e únicas
(ver CREDENCIAIS no final da execução do comando).

Uso:
    python manage.py popular_bd
"""

import hashlib
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

User = get_user_model()

# ---------------------------------------------------------------------- #
#  CREDENCIAIS DE DEMONSTRAÇÃO                                            #
#  Palavras-passe fortes e únicas por conta (maiúsculas, minúsculas,      #
#  números e símbolo), para usar na apresentação da PAP.                 #
# ---------------------------------------------------------------------- #
CREDENCIAIS = {
    "admin@escola.pt":        "Studia#Admin26!",
    "ana@escola.pt":          "AnaSilva!Tgpsi92",
    "joao@escola.pt":         "JoaoCosta#Ct71x",
    "maria@escola.pt":        "MariaFerreira$Lh03",
    "semcreditos@escola.pt":  "SemCreditos&Av17",
    "bloqueado@escola.pt":    "Bloqueado%Tge26z",
    "denunciante@escola.pt":  "Denuncia@Tpsi55q",
}


def pdf(nome, texto=""):
    """Ficheiro PDF mínimo com conteúdo único para evitar colisão de hash."""
    conteudo = f"%PDF-1.4 Studia — {nome} — {texto}".encode("utf-8")
    return ContentFile(conteudo, name=nome.replace(" ", "_")[:50] + ".pdf")

def docx(nome):
    conteudo = f"DOCX Studia — {nome}".encode("utf-8")
    return ContentFile(conteudo, name=nome.replace(" ", "_")[:50] + ".docx")

def pptx(nome):
    conteudo = f"PPTX Studia — {nome}".encode("utf-8")
    return ContentFile(conteudo, name=nome.replace(" ", "_")[:50] + ".pptx")

def img(nome):
    # PNG mínimo válido (1x1 px vermelho)
    conteudo = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
        b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        + nome.encode("utf-8")  # torna o hash único por recurso
    )
    return ContentFile(conteudo, name=nome.replace(" ", "_")[:50] + ".png")


def criar_recurso(usuario, nome, disciplina, ano, arquivo_fn, professor=""):
    from apps.resources.models import Resource
    r = Resource(
        usuario=usuario,
        nome=nome,
        curso=usuario.curso,
        ano_letivo=ano,
        disciplina=disciplina,
        instituicao=usuario.instituicao,
        professor=professor,
    )
    r.arquivo = arquivo_fn(nome)
    r._skip_full_clean = True
    r.save()
    return r


class Command(BaseCommand):
    help = "Popula a BD com dados de teste completos para todos os cenários."

    def handle(self, *args, **options):
        from apps.resources.models import Resource
        from apps.comments.models import Comment
        from apps.favorites.models import Favorite
        from apps.reports.models import Report

        self.stdout.write("A limpar dados existentes...")
        Report.objects.all().delete()
        Comment.objects.all().delete()
        Favorite.objects.all().delete()
        Resource.objects.all().delete()
        User.objects.all().delete()

        # ── UTILIZADORES ──────────────────────────────────────────────────

        self.stdout.write("A criar utilizadores...")

        admin = User.objects.create_superuser(
            email="admin@escola.pt",
            password=CREDENCIAIS["admin@escola.pt"],
            nome="Administrador",
            curso="TGPSI",
            ano_letivo="12",
            instituicao="AE Carlos Amarante — Braga",
        )

        # Aluno principal — tem uploads, downloads e comentários
        ana = User.objects.create_user(
            email="ana@escola.pt",
            password=CREDENCIAIS["ana@escola.pt"],
            nome="Ana Silva",
            curso="TGPSI",
            ano_letivo="12",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=ana.pk).update(is_active=True)
        ana.refresh_from_db()

        # Aluno de outro curso
        joao = User.objects.create_user(
            email="joao@escola.pt",
            password=CREDENCIAIS["joao@escola.pt"],
            nome="João Costa",
            curso="CT",
            ano_letivo="11",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=joao.pk).update(is_active=True)
        joao.refresh_from_db()

        # Aluno de outra escola
        maria = User.objects.create_user(
            email="maria@escola.pt",
            password=CREDENCIAIS["maria@escola.pt"],
            nome="Maria Ferreira",
            curso="LH",
            ano_letivo="10",
            instituicao="ES Dona Maria II — Braga",
        )
        User.objects.filter(pk=maria.pk).update(is_active=True)
        maria.refresh_from_db()

        # Aluno sem créditos (0 uploads, já fez 1 download = esgotou o bónus)
        sem_creditos = User.objects.create_user(
            email="semcreditos@escola.pt",
            password=CREDENCIAIS["semcreditos@escola.pt"],
            nome="Carlos Sem Créditos",
            curso="AV",
            ano_letivo="11",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=sem_creditos.pk).update(is_active=True, total_downloads=1)
        sem_creditos.refresh_from_db()

        # Aluno bloqueado (is_active=False) — não consegue fazer login
        bloqueado = User.objects.create_user(
            email="bloqueado@escola.pt",
            password=CREDENCIAIS["bloqueado@escola.pt"],
            nome="Pedro Bloqueado",
            curso="TGE",
            ano_letivo="12",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=bloqueado.pk).update(is_active=False)

        # Aluno com reports falsos (3 denúncias rejeitadas)
        denunciante = User.objects.create_user(
            email="denunciante@escola.pt",
            password=CREDENCIAIS["denunciante@escola.pt"],
            nome="Rita Denunciante",
            curso="TPSI",
            ano_letivo="12",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=denunciante.pk).update(is_active=True, total_reports_falsos=3)
        denunciante.refresh_from_db()

        # Mais dois alunos, só para dar mais volume à lista/estatísticas
        CREDENCIAIS["rui@escola.pt"] = "RuiAlmeida!Ct84m"
        rui = User.objects.create_user(
            email="rui@escola.pt",
            password=CREDENCIAIS["rui@escola.pt"],
            nome="Rui Almeida",
            curso="CT",
            ano_letivo="12",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=rui.pk).update(is_active=True)
        rui.refresh_from_db()

        CREDENCIAIS["sofia@escola.pt"] = "SofiaLopes#Tm47"
        sofia = User.objects.create_user(
            email="sofia@escola.pt",
            password=CREDENCIAIS["sofia@escola.pt"],
            nome="Sofia Lopes",
            curso="TM",
            ano_letivo="11",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=sofia.pk).update(is_active=True)
        sofia.refresh_from_db()

        # ── RECURSOS ──────────────────────────────────────────────────────

        self.stdout.write("A criar recursos...")

        r_pdf = criar_recurso(ana, "Resumos de Redes — Capítulo 3",
            "Redes de Computadores", "12", pdf, professor="Professora Helena")

        r_pdf2 = criar_recurso(ana, "Ficha de Matemática — Limites e Continuidade",
            "Matemática A", "12", pdf, professor="Prof. Rodrigues")

        r_docx = criar_recurso(joao, "Relatório de Física — Eletromagnetismo",
            "Física e Química A", "11", docx, professor="Dr. Mendes")

        r_pptx = criar_recurso(joao, "Apresentação de História — Século XX",
            "História A", "11", pptx)

        r_img = criar_recurso(maria, "Esquema de Inglês — Past Perfect",
            "Inglês", "10", img, professor="Professora Marta")

        r_para_reportar = criar_recurso(maria, "Recurso com Conteúdo Suspeito",
            "Português", "10", pdf)

        r_sem_downloads = criar_recurso(ana, "Recurso sem Descarregamentos",
            "Programação", "12", pdf, professor="Prof. Sousa")

        r_pdf3 = criar_recurso(rui, "Resumo de Física — Leis de Newton",
            "Física e Química A", "12", pdf, professor="Dr. Mendes")

        r_docx2 = criar_recurso(sofia, "Plano de Marketing — Estudo de Caso",
            "Marketing", "11", docx, professor="Professora Cátia")

        r_pptx2 = criar_recurso(rui, "Apresentação de Biologia — Genética",
            "Biologia e Geologia", "12", pptx, professor="Professor Lima")

        r_img2 = criar_recurso(sofia, "Esquema de Economia — Mercados",
            "Economia A", "11", img)

        r_pdf4 = criar_recurso(ana, "Ficha de Programação — Estruturas de Dados",
            "Programação", "12", pdf, professor="Professora Helena")

        # Simular descarregamentos em alguns recursos
        Resource.objects.filter(pk=r_pdf.pk).update(total_downloads=28)
        Resource.objects.filter(pk=r_pdf2.pk).update(total_downloads=15)
        Resource.objects.filter(pk=r_docx.pk).update(total_downloads=9)
        Resource.objects.filter(pk=r_img.pk).update(total_downloads=4)
        Resource.objects.filter(pk=r_pdf3.pk).update(total_downloads=11)
        Resource.objects.filter(pk=r_docx2.pk).update(total_downloads=6)
        Resource.objects.filter(pk=r_pptx2.pk).update(total_downloads=17)
        Resource.objects.filter(pk=r_img2.pk).update(total_downloads=2)
        Resource.objects.filter(pk=r_pdf4.pk).update(total_downloads=7)

        # ── COMENTÁRIOS ───────────────────────────────────────────────────

        self.stdout.write("A criar comentários...")

        Comment.objects.create(usuario=joao, recurso=r_pdf,
            texto="Muito bom! Ajudou-me muito na preparação para o teste.")
        Comment.objects.create(usuario=maria, recurso=r_pdf,
            texto="Os resumos do capítulo 3 estão excelentes, obrigada!")
        Comment.objects.create(usuario=joao, recurso=r_pdf2,
            texto="Tens mais fichas de Matemática? Precisava do capítulo de derivadas.")
        Comment.objects.create(usuario=ana, recurso=r_docx,
            texto="Bom relatório, mas faltam as referências bibliográficas.")
        Comment.objects.create(usuario=maria, recurso=r_pptx,
            texto="A apresentação está muito completa!")
        Comment.objects.create(usuario=sofia, recurso=r_pdf3,
            texto="Ajudou-me a rever a matéria antes do teste, obrigada!")
        Comment.objects.create(usuario=ana, recurso=r_pptx2,
            texto="Os esquemas de genética estão muito bem organizados.")
        Comment.objects.create(usuario=rui, recurso=r_docx2,
            texto="Excelente estudo de caso, deu para perceber tudo.")

        # ── FAVORITOS ─────────────────────────────────────────────────────

        self.stdout.write("A criar favoritos...")

        Favorite.objects.create(usuario=joao,   recurso=r_pdf)
        Favorite.objects.create(usuario=maria,  recurso=r_pdf)
        Favorite.objects.create(usuario=ana,    recurso=r_docx)
        Favorite.objects.create(usuario=joao,   recurso=r_img)
        Favorite.objects.create(usuario=maria,  recurso=r_pdf2)
        Favorite.objects.create(usuario=sofia,  recurso=r_pdf3)
        Favorite.objects.create(usuario=ana,    recurso=r_pptx2)
        Favorite.objects.create(usuario=rui,    recurso=r_docx2)

        # Atualizar total_salvos
        Resource.objects.filter(pk=r_pdf.pk).update(total_salvos=2)
        Resource.objects.filter(pk=r_docx.pk).update(total_salvos=1)
        Resource.objects.filter(pk=r_img.pk).update(total_salvos=1)
        Resource.objects.filter(pk=r_pdf2.pk).update(total_salvos=1)
        Resource.objects.filter(pk=r_pdf3.pk).update(total_salvos=1)
        Resource.objects.filter(pk=r_pptx2.pk).update(total_salvos=1)
        Resource.objects.filter(pk=r_docx2.pk).update(total_salvos=1)

        # ── REPORTS ───────────────────────────────────────────────────────

        self.stdout.write("A criar denúncias...")

        # Report de recurso — pendente (para testar a fila de moderação)
        Report.objects.create(
            denunciante=joao,
            recurso=r_para_reportar,
            tipo="RECURSO",
            motivo_tipo="plagio",
            motivo="Este recurso parece ser uma cópia de um trabalho publicado online.",
            status="PENDENTE",
        )

        # Report de recurso com motivo "outro" (tem detalhes)
        Report.objects.create(
            denunciante=maria,
            recurso=r_pdf2,
            tipo="RECURSO",
            motivo_tipo="outro",
            motivo="O conteúdo tem erros graves que podem induzir os alunos em erro.",
            status="PENDENTE",
        )

        # Report de utilizador — pendente
        Report.objects.create(
            denunciante=denunciante,
            usuario_denunciado=joao,
            tipo="USUARIO",
            motivo_tipo="ofensa",
            motivo="Comentário ofensivo noutro contexto.",
            status="PENDENTE",
        )

        # Report já aceite (histórico)
        Report.objects.create(
            denunciante=ana,
            recurso=r_sem_downloads,
            tipo="RECURSO",
            motivo_tipo="spam",
            status="ACEITE",
        )

        # Report rejeitado (denúncia falsa — penalizou o denunciante)
        Report.objects.create(
            denunciante=denunciante,
            recurso=r_pdf,
            tipo="RECURSO",
            motivo_tipo="improprio",
            status="REJEITADO",
        )

        # ── RESUMO ────────────────────────────────────────────────────────

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 64))
        self.stdout.write(self.style.SUCCESS("  BD de demonstração populada com sucesso!"))
        self.stdout.write(self.style.SUCCESS("=" * 64))
        self.stdout.write("")
        self.stdout.write("  CREDENCIAIS (palavras-passe fortes e únicas por conta):")
        self.stdout.write("  " + "-" * 60)
        descricoes = {
            "admin@escola.pt":       "Administrador (acesso ao /admin/ e denúncias)",
            "ana@escola.pt":        "TGPSI 12º — tem recursos, comentários e favoritos",
            "joao@escola.pt":       "CT 11º — tem comentários e favoritos",
            "maria@escola.pt":      "LH 10º — outra escola (ES Dona Maria II)",
            "semcreditos@escola.pt": "AV 11º — sem créditos para descarregamento",
            "bloqueado@escola.pt":  "TGE 12º — conta bloqueada (não consegue entrar)",
            "denunciante@escola.pt": "TPSI 12º — 3 denúncias falsas registadas",
            "rui@escola.pt":        "CT 12º — recursos extra para a demonstração",
            "sofia@escola.pt":      "TM 11º — recursos extra para a demonstração",
        }
        for email, password in CREDENCIAIS.items():
            self.stdout.write(f"  {email:<24} {password:<20} {descricoes.get(email, '')}")
        self.stdout.write("  " + "-" * 60)
        self.stdout.write("")
        self.stdout.write(f"  RECURSOS    : {Resource.objects.count()} (PDF, DOCX, PPTX, IMG)")
        self.stdout.write(f"  COMENTÁRIOS : {Comment.objects.count()}")
        self.stdout.write(f"  FAVORITOS   : {Favorite.objects.count()}")
        self.stdout.write(f"  DENÚNCIAS   : {Report.objects.count()} "
                          f"({Report.objects.filter(status='PENDENTE').count()} pendentes)")
        self.stdout.write("")
        self.stdout.write(f"  Admin Django: /admin/   ({'admin@escola.pt'} / {CREDENCIAIS['admin@escola.pt']})")
        self.stdout.write(self.style.SUCCESS("=" * 64))
