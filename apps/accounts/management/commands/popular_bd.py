"""
Management command para popular a BD com dados de teste completos e ricos.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def pdf(nome, texto=""):
    conteudo = f"%PDF-1.4 Studia — {nome} — {texto}".encode("utf-8")
    return ContentFile(conteudo, name=nome.replace(" ", "_")[:50] + ".pdf")

def docx(nome):
    conteudo = f"DOCX Studia — {nome}".encode("utf-8")
    return ContentFile(conteudo, name=nome.replace(" ", "_")[:50] + ".docx")

def pptx(nome):
    conteudo = f"PPTX Studia — {nome}".encode("utf-8")
    return ContentFile(conteudo, name=nome.replace(" ", "_")[:50] + ".pptx")

def img(nome):
    conteudo = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
        b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        + nome.encode("utf-8")
    )
    return ContentFile(conteudo, name=nome.replace(" ", "_")[:50] + ".png")


def criar_recurso(usuario, nome, disciplina, ano, arquivo_fn, professor="", dias_atras=0):
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
    if dias_atras:
        Resource.objects.filter(pk=r.pk).update(
            data_upload=timezone.now() - timedelta(days=dias_atras)
        )
    return r


class Command(BaseCommand):
    help = "Popula a BD com um conjunto rico de dados de teste para apresentação."

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

        self.stdout.write("A criar utilizadores...")

        admin = User.objects.create_superuser(
            email="admin@escola.pt",
            password="admin123",
            nome="Administrador",
            curso="TGPSI",
            ano_letivo="12",
            instituicao="AE Carlos Amarante — Braga",
        )

        alunos_info = [
            ("ana@escola.pt",        "Ana Silva",           "TGPSI", "12", "AE Carlos Amarante — Braga"),
            ("joao@escola.pt",       "João Costa",          "CT",    "11", "AE Carlos Amarante — Braga"),
            ("maria@escola.pt",      "Maria Ferreira",      "LH",    "10", "ES Dona Maria II — Braga"),
            ("rui@escola.pt",        "Rui Pereira",         "TPSI",  "12", "AE Carlos Amarante — Braga"),
            ("beatriz@escola.pt",    "Beatriz Gonçalves",   "AV",    "11", "ES Sá de Miranda — Braga"),
            ("tiago@escola.pt",      "Tiago Ribeiro",       "TRSI",  "12", "AE Carlos Amarante — Braga"),
            ("sofia@escola.pt",      "Sofia Martins",       "CSE",   "10", "ES Dona Maria II — Braga"),
            ("diogo@escola.pt",      "Diogo Almeida",       "TM",    "11", "ES Alberto Sampaio — Braga"),
            ("carolina@escola.pt",   "Carolina Fernandes",  "TDG",   "12", "AE Carlos Amarante — Braga"),
            ("miguel@escola.pt",     "Miguel Sousa",        "TELE",  "11", "ES Sá de Miranda — Braga"),
            ("ines@escola.pt",       "Inês Rodrigues",      "CT",    "12", "ES Alberto Sampaio — Braga"),
            ("gustavo@escola.pt",    "Gustavo Lima",        "TMOD",  "10", "AE Carlos Amarante — Braga"),
        ]

        alunos = {}
        for email, nome, curso, ano, instituicao in alunos_info:
            u = User.objects.create_user(
                email=email, password="teste123", nome=nome,
                curso=curso, ano_letivo=ano, instituicao=instituicao,
            )
            User.objects.filter(pk=u.pk).update(is_active=True)
            u.refresh_from_db()
            alunos[email.split("@")[0]] = u

        ana, joao, maria, rui, beatriz, tiago, sofia, diogo, carolina, miguel, ines, gustavo = (
            alunos["ana"], alunos["joao"], alunos["maria"], alunos["rui"],
            alunos["beatriz"], alunos["tiago"], alunos["sofia"], alunos["diogo"],
            alunos["carolina"], alunos["miguel"], alunos["ines"], alunos["gustavo"],
        )

        sem_creditos = User.objects.create_user(
            email="semcreditos@escola.pt", password="teste123",
            nome="Carlos Sem Créditos", curso="AV", ano_letivo="11",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=sem_creditos.pk).update(is_active=True, total_downloads=1)

        User.objects.create_user(
            email="bloqueado@escola.pt", password="teste123",
            nome="Pedro Bloqueado", curso="TGE", ano_letivo="12",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(email="bloqueado@escola.pt").update(is_active=False)

        denunciante = User.objects.create_user(
            email="denunciante@escola.pt", password="teste123",
            nome="Rita Denunciante", curso="TPSI", ano_letivo="12",
            instituicao="AE Carlos Amarante — Braga",
        )
        User.objects.filter(pk=denunciante.pk).update(is_active=True, total_reports_falsos=3)
        denunciante.refresh_from_db()

        self.stdout.write("A criar recursos...")

        recursos_def = [
            (ana,      "Resumos de Redes — Capítulo 3",                  "Redes de Computadores",      "12", pdf,  "Professora Helena", 2),
            (ana,      "Ficha de Matemática — Limites e Continuidade",   "Matemática A",               "12", pdf,  "Prof. Rodrigues",   5),
            (ana,      "Recurso sem Downloads",                          "Programação",                "12", pdf,  "Prof. Sousa",       1),
            (joao,     "Relatório de Física — Eletromagnetismo",         "Física e Química A",         "11", docx, "Dr. Mendes",        3),
            (joao,     "Apresentação de História — Século XX",           "História A",                 "11", pptx, "",                   7),
            (joao,     "Exercícios de Inglês — Reported Speech",         "Inglês",                     "11", pdf,  "Professora Marta",   10),
            (maria,    "Esquema de Inglês — Past Perfect",                "Inglês",                     "10", img,  "Professora Marta",   4),
            (maria,    "Recurso com Conteúdo Suspeito",                  "Português",                  "10", pdf,  "",                   1),
            (maria,    "Resumo de Filosofia — Ética Kantiana",           "Filosofia",                  "10", pdf,  "Dr. Almeida",        6),
            (rui,      "Projeto Final — Sistema de Gestão Escolar",      "Programação",                "12", pptx, "Prof. Costa",        2),
            (rui,      "Apontamentos de Bases de Dados — Normalização",  "Bases de Dados",             "12", pdf,  "Prof. Costa",        8),
            (beatriz,  "Portfólio de Desenho — Estudos de Luz e Sombra", "Desenho A",                  "11", img,  "Professora Sara",    5),
            (beatriz,  "Trabalho de Geometria Descritiva",               "Geometria Descritiva A",     "11", pdf,  "Professor Nuno",     12),
            (tiago,    "Configuração de Redes — Laboratório VLAN",       "Redes e Sistemas",           "12", docx, "Prof. Oliveira",     3),
            (tiago,    "Ficha de Segurança Informática",                 "Segurança Informática",      "12", pdf,  "Prof. Oliveira",     9),
            (sofia,    "Resumo de Economia — Mercados e Preços",         "Economia A",                 "10", pdf,  "Professora Beatriz", 6),
            (diogo,    "Plano de Marketing Digital — Estudo de Caso",    "Marketing",                  "11", pptx, "Prof. Teixeira",     4),
            (carolina, "Cartaz Publicitário — Campanha Sustentável",     "Design Gráfico",              "12", img,  "Professora Marta",   2),
            (carolina, "Manual de Identidade Visual — Projeto Final",    "Design Gráfico",              "12", pdf,  "Professora Marta",   14),
            (miguel,   "Relatório de Eletrónica — Circuitos Digitais",   "Eletrónica",                 "11", docx, "Prof. Silva",        7),
            (ines,     "Resumo de Biologia — Genética Mendeliana",       "Biologia e Geologia",        "12", pdf,  "Professora Cátia",   3),
            (ines,     "Ficha de Química — Equilíbrio Químico",         "Física e Química A",         "12", pdf,  "Dr. Mendes",        11),
            (gustavo,  "Storyboard — Curta-metragem Animada",           "Multimédia",                 "10", pptx, "Prof. Ferreira",     5),
        ]

        recursos = {}
        for usuario, nome, disciplina, ano, fn, prof, dias in recursos_def:
            r = criar_recurso(usuario, nome, disciplina, ano, fn, professor=prof, dias_atras=dias)
            recursos[nome] = r

        downloads_simulados = {
            "Resumos de Redes — Capítulo 3": 24,
            "Ficha de Matemática — Limites e Continuidade": 17,
            "Relatório de Física — Eletromagnetismo": 9,
            "Apresentação de História — Século XX": 31,
            "Esquema de Inglês — Past Perfect": 5,
            "Exercícios de Inglês — Reported Speech": 14,
            "Projeto Final — Sistema de Gestão Escolar": 22,
            "Apontamentos de Bases de Dados — Normalização": 8,
            "Portfólio de Desenho — Estudos de Luz e Sombra": 6,
            "Configuração de Redes — Laboratório VLAN": 13,
            "Manual de Identidade Visual — Projeto Final": 19,
            "Resumo de Biologia — Genética Mendeliana": 27,
            "Ficha de Química — Equilíbrio Químico": 10,
        }
        for nome, total in downloads_simulados.items():
            Resource.objects.filter(pk=recursos[nome].pk).update(total_downloads=total)

        self.stdout.write("A criar comentários...")

        comentarios_def = [
            (joao,     "Resumos de Redes — Capítulo 3",              "Muito bom! Ajudou-me muito na preparação para o teste."),
            (maria,    "Resumos de Redes — Capítulo 3",              "Os resumos do capítulo 3 estão excelentes, obrigada!"),
            (rui,      "Resumos de Redes — Capítulo 3",              "Tens também o capítulo 4? Preciso para a próxima ficha."),
            (joao,     "Ficha de Matemática — Limites e Continuidade","Tens mais fichas de Matemática? Precisava do capítulo de derivadas."),
            (ana,      "Relatório de Física — Eletromagnetismo",     "Bom relatório, mas faltam as referências bibliográficas."),
            (maria,    "Apresentação de História — Século XX",       "A apresentação está muito completa!"),
            (beatriz,  "Apresentação de História — Século XX",       "Ajudou-me imenso a rever a matéria antes do teste, obrigada!"),
            (sofia,    "Exercícios de Inglês — Reported Speech",     "Excelente explicação dos exemplos, ficou tudo mais claro."),
            (tiago,    "Projeto Final — Sistema de Gestão Escolar",  "Código muito bem organizado, serviu-me de inspiração para o meu projeto."),
            (ines,     "Apontamentos de Bases de Dados — Normalização", "Finalmente percebi a diferença entre 2FN e 3FN, obrigada!"),
            (carolina, "Portfólio de Desenho — Estudos de Luz e Sombra", "Trabalho lindíssimo, dá para ver a evolução técnica."),
            (diogo,    "Cartaz Publicitário — Campanha Sustentável", "Adorei o conceito da campanha, muito criativo."),
            (miguel,   "Ficha de Química — Equilíbrio Químico",     "Os exercícios resolvidos ajudaram-me a perceber o deslocamento do equilíbrio."),
            (gustavo,  "Resumo de Biologia — Genética Mendeliana",  "Explicação muito clara dos cruzamentos, obrigado pela partilha!"),
        ]

        for usuario, nome_recurso, texto in comentarios_def:
            Comment.objects.create(usuario=usuario, recurso=recursos[nome_recurso], texto=texto)

        self.stdout.write("A criar favoritos...")

        favoritos_def = [
            (joao,     "Resumos de Redes — Capítulo 3"),
            (maria,    "Resumos de Redes — Capítulo 3"),
            (rui,      "Resumos de Redes — Capítulo 3"),
            (ana,      "Relatório de Física — Eletromagnetismo"),
            (joao,     "Esquema de Inglês — Past Perfect"),
            (maria,    "Ficha de Matemática — Limites e Continuidade"),
            (beatriz,  "Apresentação de História — Século XX"),
            (sofia,    "Exercícios de Inglês — Reported Speech"),
            (tiago,    "Apontamentos de Bases de Dados — Normalização"),
            (ines,     "Projeto Final — Sistema de Gestão Escolar"),
            (carolina, "Portfólio de Desenho — Estudos de Luz e Sombra"),
            (diogo,    "Manual de Identidade Visual — Projeto Final"),
            (miguel,   "Ficha de Química — Equilíbrio Químico"),
            (gustavo,  "Resumo de Biologia — Genética Mendeliana"),
            (rui,      "Configuração de Redes — Laboratório VLAN"),
        ]

        contagem_salvos = {}
        for usuario, nome_recurso in favoritos_def:
            Favorite.objects.create(usuario=usuario, recurso=recursos[nome_recurso])
            contagem_salvos[nome_recurso] = contagem_salvos.get(nome_recurso, 0) + 1

        for nome_recurso, total in contagem_salvos.items():
            Resource.objects.filter(pk=recursos[nome_recurso].pk).update(total_salvos=total)

        self.stdout.write("A criar denúncias...")

        Report.objects.create(
            denunciante=joao, recurso=recursos["Recurso com Conteúdo Suspeito"],
            tipo="RECURSO", motivo_tipo="plagio",
            motivo="Este recurso parece ser uma cópia de um trabalho publicado online.",
            status="PENDENTE",
        )
        Report.objects.create(
            denunciante=maria, recurso=recursos["Ficha de Matemática — Limites e Continuidade"],
            tipo="RECURSO", motivo_tipo="outro",
            motivo="O conteúdo tem erros graves que podem induzir os alunos em erro.",
            status="PENDENTE",
        )
        Report.objects.create(
            denunciante=sofia, recurso=recursos["Cartaz Publicitário — Campanha Sustentável"],
            tipo="RECURSO", motivo_tipo="outro",
            motivo="Parece usar imagens protegidas por direitos de autor sem crédito.",
            status="PENDENTE",
        )
        Report.objects.create(
            denunciante=denunciante, usuario_denunciado=joao,
            tipo="USUARIO", motivo_tipo="ofensa",
            motivo="Comentário ofensivo noutro contexto.",
            status="PENDENTE",
        )
        Report.objects.create(
            denunciante=ana, recurso=recursos["Recurso sem Downloads"],
            tipo="RECURSO", motivo_tipo="spam", status="ACEITE",
        )
        Report.objects.create(
            denunciante=miguel, usuario_denunciado=gustavo,
            tipo="USUARIO", motivo_tipo="spam",
            motivo="Publicou o mesmo recurso várias vezes em disciplinas diferentes.",
            status="ACEITE",
        )
        Report.objects.create(
            denunciante=denunciante, recurso=recursos["Resumos de Redes — Capítulo 3"],
            tipo="RECURSO", motivo_tipo="improprio", status="REJEITADO",
        )
        Report.objects.create(
            denunciante=denunciante, recurso=recursos["Apresentação de História — Século XX"],
            tipo="RECURSO", motivo_tipo="plagio", status="REJEITADO",
        )
        Report.objects.create(
            denunciante=denunciante, usuario_denunciado=ines,
            tipo="USUARIO", motivo_tipo="ofensa", status="REJEITADO",
        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 56))
        self.stdout.write(self.style.SUCCESS("  BD de teste populada com sucesso!"))
        self.stdout.write(self.style.SUCCESS("=" * 56))
        self.stdout.write("")
        self.stdout.write("  UTILIZADORES (alunos com password 'teste123'):")
        self.stdout.write("  admin@escola.pt       → Administrador  (admin123)")
        self.stdout.write("  ana@escola.pt         → TGPSI 12º — tem uploads e favoritos")
        self.stdout.write("  joao@escola.pt        → CT 11º — tem comentários e favoritos")
        self.stdout.write("  maria@escola.pt       → LH 10º — outra escola")
        self.stdout.write("  rui@escola.pt         → TPSI 12º — projeto final")
        self.stdout.write("  beatriz@escola.pt     → AV 11º — outra escola")
        self.stdout.write("  tiago@escola.pt       → TRSI 12º — redes e segurança")
        self.stdout.write("  sofia@escola.pt       → CSE 10º — outra escola")
        self.stdout.write("  diogo@escola.pt       → TM 11º — outra escola")
        self.stdout.write("  carolina@escola.pt    → TDG 12º — design gráfico")
        self.stdout.write("  miguel@escola.pt      → TELE 11º — outra escola")
        self.stdout.write("  ines@escola.pt        → CT 12º — outra escola")
        self.stdout.write("  gustavo@escola.pt     → TMOD 10º — multimédia")
        self.stdout.write("  semcreditos@escola.pt → sem créditos para download")
        self.stdout.write("  bloqueado@escola.pt   → conta bloqueada (is_active=False)")
        self.stdout.write("  denunciante@escola.pt → 3 reports falsos")
        self.stdout.write("")
        self.stdout.write(f"  RECURSOS    : {Resource.objects.count()} (PDF, DOCX, PPTX, IMG, várias disciplinas)")
        self.stdout.write(f"  COMENTÁRIOS : {Comment.objects.count()}")
        self.stdout.write(f"  FAVORITOS   : {Favorite.objects.count()}")
        self.stdout.write(f"  REPORTS     : {Report.objects.count()} "
                          f"({Report.objects.filter(status='PENDENTE').count()} pendentes)")
        self.stdout.write("")
        self.stdout.write("  Admin Django: /admin/   password: admin123")
        self.stdout.write(self.style.SUCCESS("=" * 56))
