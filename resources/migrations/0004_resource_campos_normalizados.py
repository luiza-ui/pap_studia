from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adiciona campos normalizados (sem acentos, minúsculas) ao model Resource.
    Estes campos são usados na pesquisa para que "matematica" encontre "Matemática".
    São preenchidos automaticamente pelo Resource.save().
    """

    dependencies = [
        ('resources', '0003_remove_resource_total_reports_falsos'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='nome_normalizado',
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name='resource',
            name='disciplina_normalizada',
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AddField(
            model_name='resource',
            name='professor_normalizado',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
