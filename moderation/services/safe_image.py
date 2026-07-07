import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def verificar_imagem_segura(caminho_ficheiro):
    credenciais = getattr(settings, 'GOOGLE_CLOUD_CREDENTIALS', '')
    if not credenciais:
        logger.debug('SafeSearch: stub activo, assumindo seguro: %s', caminho_ficheiro)
        return True
    try:
        from google.cloud import vision
        import io
        cliente = vision.ImageAnnotatorClient()
        with io.open(caminho_ficheiro, 'rb') as f:
            conteudo = f.read()
        imagem = vision.Image(content=conteudo)
        resposta = cliente.safe_search_detection(image=imagem)
        anotacao = resposta.safe_search_annotation
        niveis = {vision.Likelihood.LIKELY, vision.Likelihood.VERY_LIKELY}
        if anotacao.adult in niveis or anotacao.violence in niveis or anotacao.racy in niveis:
            return False
        return True
    except ImportError:
        return True
    except Exception as e:
        logger.error('Erro SafeSearch: %s', e)
        return True
