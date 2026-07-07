from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tipo",
        "motivo_tipo",
        "denunciante",
        "recurso",
        "usuario_denunciado",
        "status",
        "data_criacao",
        "data_resolucao",
    )
    list_filter = ("status", "tipo", "motivo_tipo", "data_criacao")
    search_fields = (
        "denunciante__email",
        "denunciante__nome",
        "recurso__nome",
        "usuario_denunciado__email",
        "usuario_denunciado__nome",
        "motivo",
    )
    readonly_fields = ("data_criacao", "data_resolucao", "tipo", "denunciante",
                       "recurso", "usuario_denunciado", "motivo_tipo", "motivo", "status")
    ordering = ("-data_criacao",)
    list_per_page = 20

    fieldsets = (
        ("Denúncia", {
            "fields": ("tipo", "denunciante", "recurso", "usuario_denunciado", "motivo_tipo", "motivo")
        }),
        ("Estado", {
            "fields": ("status", "data_criacao", "data_resolucao")
        }),
    )

    def has_add_permission(self, request):
        """
        Reports são criados pelos alunos no site, não pelo admin manualmente.
        O admin só deve ver e resolver reports existentes via painel dedicado.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        O admin não deve alterar reports diretamente aqui — apenas via
        o painel de resolução de reports no site, que aplica toda a lógica
        de negócio (bloquear conta, apagar conteúdo, penalizar denunciante).
        Alterar o status diretamente pelo admin contornaria essa lógica.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Permite ao admin apagar reports se necessário (ex: reports spam).
        """
        return True