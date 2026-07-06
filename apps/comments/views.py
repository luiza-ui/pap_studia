from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.resources.models import Resource

from .forms import CommentForm
from .models import Comment


@login_required
@require_POST
def adicionar_comentario(request, resource_id):
    """
    Adiciona um comentário a um recurso.
    Apenas aceita POST — o @require_POST bloqueia pedidos GET.
    Qualquer aluno autenticado pode comentar qualquer recurso.
    """
    recurso = get_object_or_404(Resource, pk=resource_id)
    form    = CommentForm(request.POST)

    if form.is_valid():
        comentario         = form.save(commit=False)
        comentario.usuario = request.user
        comentario.recurso = recurso
        try:
            from apps.moderation.services.toxic_text import verificar_texto_seguro
            texto_verificar = request.POST.get('texto', '').strip()
            if not verificar_texto_seguro(texto_verificar):
                messages.error(request, 'O teu comentário contém linguagem que não é permitida. Por favor revê o texto.')
                return redirect('resources:detalhes', pk=resource_id)
        except Exception as _e:
            import logging as _log
            _log.getLogger(__name__).error('Erro Perspective: %s', _e)
        comentario.save()
        messages.success(request, "Comentário adicionado com sucesso!")
    else:
        messages.error(request, "Erro ao adicionar comentário. Verifica o texto.")

    return redirect("resources:detalhes", pk=resource_id)


@login_required
def apagar_comentario(request, comment_id):
    """
    Apaga um comentário.
    Apenas o autor do comentário ou staff pode apagar.
    """
    comentario  = get_object_or_404(Comment, pk=comment_id)
    resource_id = comentario.recurso.id

    if request.user == comentario.usuario or request.user.is_staff:
        comentario.delete()
        messages.success(request, "Comentário removido.")
    else:
        messages.error(request, "Não tens permissão para apagar este comentário.")

    return redirect("resources:detalhes", pk=resource_id)
