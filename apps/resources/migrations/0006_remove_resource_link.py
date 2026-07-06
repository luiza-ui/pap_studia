"""
Remove o campo 'link' do modelo Resource.

Antes de aplicar esta migração em produção, convém verificar se existem
recursos com tipo_arquivo='LINK' e decidir o que fazer com eles.
Script de diagnóstico:
    python manage.py shell -c "
    from apps.resources.models import Resource
    qs = Resource.objects.filter(tipo_arquivo='LINK')
    print(f'{qs.count()} recursos do tipo LINK encontrados')
    for r in qs: print(f'  #{r.pk} — {r.nome} — {r.link}')
    "
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0005_preencher_campos_normalizados"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="resource",
            name="link",
        ),
    ]
