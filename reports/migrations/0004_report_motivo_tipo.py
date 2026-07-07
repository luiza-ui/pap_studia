from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0003_alter_report_options_alter_report_status_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="motivo_tipo",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("plagio",    "Plágio / Cópia sem créditos"),
                    ("improprio", "Conteúdo impróprio"),
                    ("spam",      "Spam ou publicidade"),
                    ("falso",     "Informação falsa ou errada"),
                    ("ofensa",    "Linguagem ofensiva"),
                    ("outro",     "Outro"),
                ],
                default="outro",
                verbose_name="Tipo de motivo",
            ),
        ),
    ]
