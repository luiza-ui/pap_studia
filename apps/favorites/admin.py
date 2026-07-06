from django.contrib import admin
from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Configuração do Favorite no Django Admin
    """

    # ----------------------
    # Listagem
    # ----------------------
    list_display = (
        "usuario",
        "recurso",
        "criado_em",
    )

    list_filter = (
        "criado_em",
    )

    search_fields = (
        "usuario__nome",
        "usuario__email",
        "recurso__nome",
    )

    ordering = ("-criado_em",)

    # ----------------------
    # Campos somente leitura
    # ----------------------
    readonly_fields = ("criado_em",)

    # ----------------------
    # Proteções
    # ----------------------
    def has_change_permission(self, request, obj=None):
        """
        Evita edição manual de favoritos (só criar/apagar)
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Apenas staff pode remover favoritos
        """
        return request.user.is_staff
