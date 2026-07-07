from django.db import migrations, models

CURSOS = [
    ("CT",    "Ciências e Tecnologias"),
    ("CSE",   "Ciências Socioeconómicas"),
    ("LH",    "Línguas e Humanidades"),
    ("AV",    "Artes Visuais"),
    ("TGPSI", "Técnico de Gestão e Programação de Sistemas Informáticos"),
    ("TPSI",  "Técnico de Programação Informática"),
    ("TGE",   "Técnico de Gestão"),
    ("TM",    "Técnico de Marketing"),
    ("TAD",   "Técnico de Auxiliar de Saúde"),
    ("TGRC",  "Técnico de Gestão e Recursos Humanos e Comunicação"),
    ("TAAM",  "Técnico de Apoio à Gestão Desportiva"),
    ("TCOM",  "Técnico de Comunicação / Marketing e Publicidade"),
    ("TIT",   "Técnico de Instalações Elétricas"),
    ("TRSI",  "Técnico de Redes e Sistemas Informáticos"),
    ("TCMA",  "Técnico de Construção Civil / Medições e Orçamentos"),
    ("TGA",   "Técnico de Restauração / Cozinha e Pastelaria"),
    ("TTUR",  "Técnico de Turismo"),
    ("TAGRO", "Técnico de Agropecuária"),
    ("TDG",   "Técnico de Design Gráfico"),
    ("TMOD",  "Técnico de Multimédia"),
    ("TELE",  "Técnico de Eletrónica, Automação e Computadores"),
    ("TMEC",  "Técnico de Mecatrónica"),
    ("TAUT",  "Técnico de Manutenção Industrial / Eletromecânica"),
    ("OUTRO", "Outro"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_remove_email_validator"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="curso",
            field=models.CharField(max_length=10, choices=CURSOS),
        ),
    ]
