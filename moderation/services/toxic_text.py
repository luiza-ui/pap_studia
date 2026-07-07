import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Lista de termos proibidos em português (PT-PT e PT-BR).
# Normalizada sem acentos — a comparação também normaliza o input.
_TERMOS_PROIBIDOS = {
    # Palavrões
    "porra", "caralho", "merda", "foda", "foder", "fodasse", "fodase",
    "puta", "putaria", "putinha", "prostituta",
    "cona", "cu", "cuzao", "cuzão",
    "cacete", "pica", "piça",
    "buceta", "bunda",
    "viado", "bicha", "traveco",
    "corno", "cornudo",
    "arrombado", "arrombada",
    "fdp", "vsf", "tnc", "pqp",
    # Insultos
    "idiota", "imbecil", "retardado", "retardada", "mongol",
    "burro", "burra", "estupido", "estupida",
    "escoria",
    "macaco", "macaca",
    "nazi", "fascista",
    "vagabundo", "vagabunda",
    "safado", "safada",
    "desgraçado", "desgraçada",
    # Ameaças
    "suicidio",
}


def _normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas."""
    sem_acentos = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sem_acentos if unicodedata.category(c) != "Mn")


def verificar_texto_seguro(texto: str) -> bool:
    """
    Retorna True se o texto for seguro, False se contiver linguagem proibida.
    Filtro local — não requer nenhuma API externa.
    """
    if not texto or not texto.strip():
        return True

    texto_norm = _normalizar(texto)
    palavras = set(re.findall(r"[a-z]+", texto_norm))

    for termo in _TERMOS_PROIBIDOS:
        termo_norm = _normalizar(termo)
        if " " in termo_norm:
            if termo_norm in texto_norm:
                logger.debug("Texto bloqueado: expressão '%s' encontrada.", termo)
                return False
        else:
            if termo_norm in palavras:
                logger.debug("Texto bloqueado: palavra '%s' encontrada.", termo)
                return False

    return True
