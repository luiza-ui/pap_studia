from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.resources.models import Resource

from .models import Favorite


@login_required
@require_POST
def toggle_favorito_view(request, recurso_id):
    """
    Adiciona ou remove um recurso dos favoritos (botão na página de detalhes).
    - Se não estava nos favoritos: adiciona e incrementa total_salvos.
    - Se já estava: remove e decrementa total_salvos.
    Redireciona sempre de volta para a página de detalhes do recurso.
    """
    recurso = get_object_or_404(Resource, pk=recurso_id)

    # Bloquear o dono de favoritar o próprio recurso
    if recurso.usuario == request.user:
        messages.error(request, "Não podes adicionar os teus próprios recursos aos favoritos.")
        return redirect("resources:detalhes", pk=recurso.pk)

    favorito_existente = Favorite.objects.filter(usuario=request.user, recurso=recurso).first()

    if not favorito_existente:
        # Adicionar aos favoritos (o save() do Favorite incrementa total_salvos)
        Favorite.objects.create(usuario=request.user, recurso=recurso)
        messages.success(request, "Recurso adicionado aos favoritos.")
    else:
        # Remover dos favoritos e decrementar total_salvos
        favorito_existente.delete()
        Resource.objects.filter(pk=recurso.pk, total_salvos__gt=0).update(
            total_salvos=F("total_salvos") - 1
        )
        messages.info(request, "Recurso removido dos favoritos.")

    return redirect("resources:detalhes", pk=recurso.pk)


@login_required
@require_POST
def remover_favorito_view(request, recurso_id):
    """
    Remove explicitamente um favorito (botão na página de perfil).
    Redireciona para o perfil após remover.
    """
    recurso  = get_object_or_404(Resource, pk=recurso_id)
    favorito = Favorite.objects.filter(usuario=request.user, recurso=recurso).first()

    if favorito:
        favorito.delete()
        Resource.objects.filter(pk=recurso.pk, total_salvos__gt=0).update(
            total_salvos=F("total_salvos") - 1
        )
        messages.info(request, "Favorito removido.")

    return redirect("accounts:perfil")
