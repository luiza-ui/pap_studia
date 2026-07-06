from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuração do utilizador no Django Admin.
    """

    ordering = ("email",)
    list_display = (
        "email",
        "nome",
        "curso",
        "ano_letivo",
        "instituicao",
        "is_active",
        "is_staff",
        "total_reports_falsos",
    )
    list_filter = ("is_active", "is_staff", "ano_letivo", "curso")
    search_fields = ("email", "nome", "curso", "instituicao")
    actions = ["bloquear_contas", "desbloquear_contas"]

    fieldsets = (
        ("Informações Pessoais", {
            "fields": (
                "email",
                "password",
                "nome",
                "curso",
                "ano_letivo",
                "instituicao",
            )
        }),
        ("Permissões", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Estatísticas", {
            "fields": (
                "total_uploads",
                "total_downloads",
                "total_reports_falsos",
            ),
            "description": "Estatísticas do utilizador (somente leitura)"
        }),
        ("Datas", {
            "fields": ("last_login", "date_joined"),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "nome",
                "curso",
                "ano_letivo",
                "instituicao",
                "password1",
                "password2",
                "is_staff",
                "is_superuser",
            ),
        }),
    )

    readonly_fields = (
        "date_joined",
        "last_login",
        "total_uploads",
        "total_downloads",
        "total_reports_falsos",
    )

    filter_horizontal = ("groups", "user_permissions")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return ()

    def has_delete_permission(self, request, obj=None):
        """Bloqueia a eliminação de superutilizadores pelo painel."""
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def bloquear_contas(self, request, queryset):
        """
        Bloqueia manualmente as contas selecionadas.
        APENAS bloqueia o acesso — o conteúdo permanece visível.
        O admin decide manualmente o que apagar.

        NOTA: Este é o bloqueio MANUAL (admin). Não apaga conteúdo.
        O bloqueio automático (por abuso/report) apaga tudo — esse é
        feito via user.bloquear_por_abuso() na lógica de reports.
        """
        superusers = queryset.filter(is_superuser=True)
        if superusers.exists():
            self.message_user(
                request,
                "Não é possível bloquear superutilizadores.",
                level=messages.ERROR
            )
            return

        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{count} conta(s) bloqueada(s). O conteúdo permanece visível.",
            level=messages.WARNING
        )
    bloquear_contas.short_description = "Bloquear contas selecionadas (mantém conteúdo)"

    def desbloquear_contas(self, request, queryset):
        """Desbloqueia as contas selecionadas."""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{count} conta(s) desbloqueada(s) com sucesso.",
            level=messages.SUCCESS
        )
    desbloquear_contas.short_description = "Desbloquear contas selecionadas"