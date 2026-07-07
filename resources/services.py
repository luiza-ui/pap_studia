import hashlib

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import F

from .models import Resource


def calcular_hash_arquivo(arquivo):
    """
    Calcula o hash SHA256 de um ficheiro para detetar duplicados.
    Repõe o cursor antes e depois de ler para não deixar o stream consumido.
    """
    sha = hashlib.sha256()
    arquivo.seek(0)
    for chunk in arquivo.chunks():
        sha.update(chunk)
    arquivo.seek(0)
    return sha.hexdigest()


def verificar_arquivo_duplicado(arquivo, exclude_pk=None):
    """
    Verifica se já existe um recurso com o mesmo hash SHA256.
    Lança ValidationError se encontrar duplicado.

    Parâmetros:
      arquivo    — ficheiro em memória (InMemoryUploadedFile ou similar)
      exclude_pk — pk a ignorar na pesquisa (usado ao editar o próprio recurso)
    """
    hash_atual = calcular_hash_arquivo(arquivo)

    qs = Resource.objects.filter(hash_arquivo=hash_atual)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    if qs.exists():
        raise ValidationError("Já existe um recurso com este arquivo.")


def pode_usuario_fazer_download(user):
    """
    Verifica se o utilizador tem créditos suficientes para fazer download.
    Delega para o método do modelo User.
    """
    return user.pode_fazer_download()


def incrementar_download(resource, user):
    """
    Incrementa o total de downloads do recurso E do utilizador.
    Usa UPDATE directo com F() para evitar race conditions e não
    disparar o save() completo do Resource.
    """
    Resource.objects.filter(pk=resource.pk).update(
        total_downloads=F("total_downloads") + 1
    )
    UserModel = get_user_model()
    UserModel.objects.filter(pk=user.pk).update(
        total_downloads=F("total_downloads") + 1
    )


def incrementar_salvo(resource):
    """Incrementa o contador de vezes que o recurso foi guardado nos favoritos."""
    Resource.objects.filter(pk=resource.pk).update(
        total_salvos=F("total_salvos") + 1
    )


def decrementar_salvo(resource):
    """
    Decrementa o contador de vezes que o recurso foi guardado.
    Garante que o valor nunca fica abaixo de zero.
    """
    Resource.objects.filter(pk=resource.pk, total_salvos__gt=0).update(
        total_salvos=F("total_salvos") - 1
    )
