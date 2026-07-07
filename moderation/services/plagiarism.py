import logging
from django.conf import settings

logger = logging.getLogger(__name__)
LIMIAR_PHASH = getattr(settings, 'MODERATION_PHASH_LIMIAR', 10)

def _calcular_phash_imagem(caminho_ficheiro):
    try:
        import imagehash
        from PIL import Image
        return str(imagehash.phash(Image.open(caminho_ficheiro)))
    except Exception as e:
        logger.warning('Erro ao calcular pHash: %s', e)
        return ''

def _phash_similar(hash1, hash2):
    try:
        import imagehash
        return (imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)) <= LIMIAR_PHASH
    except Exception:
        return False

def verificar_plagio(recurso):
    from apps.resources.models import Resource
    if not recurso.arquivo or not recurso.pk:
        return False
    if recurso.tipo_arquivo == 'IMG':
        try:
            novo_phash = _calcular_phash_imagem(recurso.arquivo.path)
        except Exception:
            return False
        if not novo_phash:
            return False
        Resource.objects.filter(pk=recurso.pk).update(phash=novo_phash)
        for h in Resource.objects.filter(tipo_arquivo='IMG').exclude(pk=recurso.pk).exclude(phash='').values_list('phash', flat=True):
            if _phash_similar(novo_phash, h):
                return True
    else:
        if not recurso.hash_arquivo:
            return False
        if Resource.objects.filter(hash_arquivo=recurso.hash_arquivo).exclude(pk=recurso.pk).exists():
            return True
    return False
