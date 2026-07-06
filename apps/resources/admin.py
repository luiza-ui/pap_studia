from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Resource


@admin.action(description="Levantar suspensão dos recursos selecionados")
def levantar_suspensao(modeladmin, request, queryset):
    queryset.update(suspenso=False)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "usuario",
        "disciplina",
        "curso",
        "ano_letivo",
        "tipo_arquivo",
        "instituicao",
        "suspenso",
        "total_downloads",
        "total_salvos",
        "data_upload",
    )

    list_filter = ("suspenso", "curso", "ano_letivo", "tipo_arquivo", "disciplina")
    search_fields = ("nome", "disciplina", "usuario__nome", "usuario__email")
    list_per_page = 20
    actions = [levantar_suspensao]

    readonly_fields = (
        "suspenso",
        "curso",
        "instituicao",
        "tipo_arquivo",
        "hash_arquivo",
        "total_downloads",
        "total_salvos",
        "data_upload",
    )

    fieldsets = (
        ("Informações do Recurso", {
            "fields": (
                "nome",
                "usuario",
                "curso",
                "ano_letivo",
                "disciplina",
                "tipo_arquivo",
                "instituicao",
                "professor",
                "arquivo",
            )
        }),
        ("Moderação", {
            "fields": ("suspenso",),
            "description": "Suspensão automática por moderação de IA (somente leitura — use a ação 'Levantar suspensão')"
        }),
        ("Estatísticas", {
            "fields": (
                "total_downloads",
                "total_salvos",
                "hash_arquivo",
            ),
            "description": "Contadores e hash do recurso (somente leitura)"
        }),
        ("Datas", {
            "fields": ("data_upload",),
        }),
    )
