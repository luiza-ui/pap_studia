"""
Migração de dados: preenche os campos _normalizado em todos os recursos
existentes que foram criados antes da migração 0004.

Sem esta migração, recursos antigos têm nome_normalizado="", pelo que a
pesquisa por autocomplete não encontra nada (compara texto com string vazia).
"""

from django.db import migrations


def preencher_normalizados(apps, schema_editor):
    import unicodedata

    def normalizar(texto):
        if not texto:
            return ""
        sem_acentos = unicodedata.normalize("NFD", texto.lower())
        return "".join(c for c in sem_acentos if unicodedata.category(c) != "Mn")

    Resource = apps.get_model("resources", "Resource")

    resources_para_atualizar = []
    for r in Resource.objects.all():
        r.nome_normalizado       = normalizar(r.nome or "")
        r.disciplina_normalizada = normalizar(r.disciplina or "")
        r.professor_normalizado  = normalizar(r.professor or "")
        resources_para_atualizar.append(r)

    if resources_para_atualizar:
        Resource.objects.bulk_update(
            resources_para_atualizar,
            ["nome_normalizado", "disciplina_normalizada", "professor_normalizado"],
            batch_size=500,
        )


def desfazer(apps, schema_editor):
    # Limpar os campos normalizados (reversível mas desnecessário em prática)
    Resource = apps.get_model("resources", "Resource")
    Resource.objects.all().update(
        nome_normalizado="",
        disciplina_normalizada="",
        professor_normalizado="",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0004_resource_campos_normalizados"),
    ]

    operations = [
        migrations.RunPython(preencher_normalizados, reverse_code=desfazer),
    ]
