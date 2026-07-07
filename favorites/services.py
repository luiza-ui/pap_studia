from django.core.exceptions import ValidationError
from django.db.models import F

from apps.accounts.models import User
from apps.resources.models import Resource

from .models import Favorite


def adicionar_favorito(usuario: User, recurso: Resource) -> Favorite:
    """
    Adiciona um recurso aos favoritos do utilizador.
    Lança ValidationError se o recurso já estiver nos favoritos.
    """
    if Favorite.objects.filter(usuario=usuario, recurso=recurso).exists():
        raise ValidationError("Este recurso já está nos favoritos.")

    return Favorite.objects.create(usuario=usuario, recurso=recurso)


def remover_favorito(usuario: User, recurso: Resource) -> bool:
    """
    Remove um recurso dos favoritos do utilizador.
    Decrementa total_salvos no recurso.
    Lança ValidationError se o favorito não existir.
    """
    favorito = Favorite.objects.filter(usuario=usuario, recurso=recurso).first()

    if not favorito:
        raise ValidationError("Este recurso não está nos favoritos.")

    favorito.delete()
    # Garantir que total_salvos nunca fica abaixo de zero
    Resource.objects.filter(pk=recurso.pk, total_salvos__gt=0).update(
        total_salvos=F("total_salvos") - 1
    )
    return True


def is_favorito(usuario: User, recurso: Resource) -> bool:
    """Verifica se um recurso está guardado nos favoritos do utilizador."""
    return Favorite.objects.filter(usuario=usuario, recurso=recurso).exists()
