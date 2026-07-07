from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'recurso', 'resumo_texto', 'criado_em', 'ativo')
    list_filter = ('ativo', 'criado_em')
    # CORRIGIDO: 'usuario__nome_completo' nao existe — o campo e 'nome'
    search_fields = ('texto', 'usuario__email', 'usuario__nome', 'recurso__nome')
    actions = ['ocultar_comentarios', 'tornar_visiveis']
    readonly_fields = ('criado_em',)

    def resumo_texto(self, obj):
        """Corta o texto se for muito grande para não estragar a tabela do admin."""
        return obj.texto[:50] + "..." if len(obj.texto) > 50 else obj.texto
    resumo_texto.short_description = "Comentário"

    def ocultar_comentarios(self, request, queryset):
        """Esconde os comentários selecionados do site."""
        queryset.update(ativo=False)
    ocultar_comentarios.short_description = "Ocultar comentários selecionados (Moderação)"

    def tornar_visiveis(self, request, queryset):
        """Mostra os comentários selecionados no site."""
        queryset.update(ativo=True)
    tornar_visiveis.short_description = "Tornar visível novamente"