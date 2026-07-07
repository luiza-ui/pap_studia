"""
Adiciona 'choices' ao campo Resource.curso.

Sem 'choices' o Django nunca gera o método get_curso_display() no modelo
Resource, pelo que {{ recurso.get_curso_display }} nos templates resolvia
sempre para uma string vazia (Curso aparecia em branco nos cartões e na
página de detalhes), mesmo quando o valor de 'curso' estava guardado
corretamente na base de dados.

Esta migração só altera metadados do campo (choices), não o tipo de coluna
nem os dados existentes — não é necessária qualquer transformação de dados.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0006_remove_resource_link"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resource",
            name="curso",
            field=models.CharField(
                max_length=10,
                choices=[
                    ("CT", "Ciências e Tecnologias"),
                    ("CSE", "Ciências Socioeconómicas"),
                    ("LH", "Línguas e Humanidades"),
                    ("AV", "Artes Visuais"),
                    ("TGPSI", "Técnico de Gestão e Programação de Sistemas Informáticos"),
                    ("TPSI", "Técnico de Programação Informática"),
                    ("TGE", "Técnico de Gestão"),
                    ("TM", "Técnico de Marketing"),
                    ("TAD", "Técnico de Auxiliar de Saúde"),
                    ("TGRC", "Técnico de Gestão e Recursos Humanos e Comunicação"),
                    ("TAAM", "Técnico de Apoio à Gestão Desportiva"),
                    ("TCOM", "Técnico de Comunicação / Marketing e Publicidade"),
                    ("TIT", "Técnico de Instalações Elétricas"),
                    ("TRSI", "Técnico de Redes e Sistemas Informáticos"),
                    ("TCMA", "Técnico de Construção Civil / Medições e Orçamentos"),
                    ("TGA", "Técnico de Restauração / Cozinha e Pastelaria"),
                    ("TTUR", "Técnico de Turismo"),
                    ("TAGRO", "Técnico de Agropecuária"),
                    ("TDG", "Técnico de Design Gráfico"),
                    ("TMOD", "Técnico de Multimédia"),
                    ("TELE", "Técnico de Eletrónica, Automação e Computadores"),
                    ("TMEC", "Técnico de Mecatrónica"),
                    ("TAUT", "Técnico de Manutenção Industrial / Eletromecânica"),
                    ("OUTRO", "Outro"),
                ],
            ),
        ),
    ]
