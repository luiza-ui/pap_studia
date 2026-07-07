"""
Validadores de email institucional para o Studia.

Lista de domínios de escolas portuguesas com ensino secundário.
Foco na zona de Braga e agrupamentos com secundária incluída.

Para adicionar um novo domínio, basta acrescentar ao dicionário
DOMINIO_PARA_INSTITUICAO — não é necessário alterar mais nenhum ficheiro.
"""

from django.core.exceptions import ValidationError

# ---------------------------------------------------------------------------
# Mapeamento domínio → nome da instituição (fonte única de verdade)
# Usado para pré-preencher automaticamente o campo "instituicao" no registo.
# ---------------------------------------------------------------------------
DOMINIO_PARA_INSTITUICAO = {
    # --- Domínio genérico para testes e desenvolvimento ---
    "escola.pt": "Escola de Testes",

    # ── Braga (cidade e concelho) ──────────────────────────────────────────
    "alunos.esdm.pt":             "ES Dona Maria II — Braga",
    "alunos.aebragaocidente.pt":  "AE Braga Ocidente",
    "alunos.aebragaoriente.pt":   "AE Braga Oriente",
    "alunos.aesaovitor.pt":       "AE São Vítor — Braga",
    "alunos.aemaximos.pt":        "AE Maximinos — Braga",
    "alunos.aecabreiros.pt":      "AE Cabreiros e Passos — Braga",
    "alunos.esandrade.pt":        "ES André de Gouveia — Braga",
    "aebraga.pt":                 "AE Braga",

    # ── Guimarães ──────────────────────────────────────────────────────────
    "alunos.aeguimaraes.pt":      "AE Francisco de Holanda — Guimarães",
    "alunos.aemartinsarpas.pt":   "AE Martins Sarmento — Guimarães",
    "alunos.aecaldas.pt":         "AE Caldas de Vizela",
    "alunos.aefafe.pt":           "AE Fafe",
    "alunos.aeguimaraessul.pt":   "AE Guimarães Sul",

    # ── Barcelos / Esposende ───────────────────────────────────────────────
    "alunos.aebarcelosnorte.pt":  "AE Barcelos Norte — ES Gil Vicente",
    "alunos.aebarcelossul.pt":    "AE Barcelos Sul",
    "alunos.aesaopaio.pt":        "AE São Paio — Barcelos",
    "alunos.aeesposende.pt":      "AE Esposende",

    # ── Braga — concelhos limítrofes ───────────────────────────────────────
    "alunos.aevizela.pt":         "AE Vale de Vizela",
    "alunos.aecarlosamarante.pt": "AE Carlos Amarante — Braga",
    "alunos.aeverde.pt":          "AE Verde — Braga",
    "alunos.aepovoadevarzim.pt":  "AE Póvoa de Varzim",
    "alunos.aevilanova.pt":       "AE Vila Nova de Famalicão",
    "alunos.aecabeceiras.pt":     "AE Cabeceiras de Basto",
    "alunos.aeamares.pt":         "AE Amares",
    "alunos.aeterras.pt":         "AE Terras de Bouro",
    "alunos.aeponte.pt":          "AE Ponte",
    "alunos.aeviana.pt":          "AE Viana do Castelo",
    "alunos.aebragabacelos.pt":   "AE Bacelos — Braga",

    # ── Porto e Norte (complemento) ───────────────────────────────────────
    "alunos.esaq.pt":             "ES Aurélia de Sousa — Porto",
    "alunos.aemaia.pt":           "AE Maia",
    "alunos.aematosinhos.pt":     "AE Matosinhos",
    "alunos.aechaves.pt":         "AE Chaves",
    "alunos.aevmcorreia.pt":      "AE Vergílio Ferreira — Vila do Conde",

    # ── Lisboa e Sul ──────────────────────────────────────────────────────
    "edu.cm-lisboa.pt":           "Escola Municipal de Lisboa",
    "alunos.esmaior.pt":          "ES Rainha D. Leonor — Lisboa",
    "alunos.esccb.pt":            "ES Camilo Castelo Branco",

    # ── Plataformas nacionais de email escolar ─────────────────────────────
    "edu.azores.gov.pt":          "Escola — Açores",
    "edu.madeira.gov.pt":         "Escola — Madeira",
}

# Lista derivada do dicionário — fonte única de verdade
DOMINIOS_INSTITUCIONAIS = list(DOMINIO_PARA_INSTITUICAO.keys())

_DOMINIOS_SET = set(DOMINIOS_INSTITUCIONAIS)


def instituicao_para_dominio(email: str) -> str:
    """
    Dado um email institucional, devolve o nome da instituição correspondente.
    Devolve string vazia se o domínio não estiver mapeado.
    Usado no formulário de registo para pré-preencher o campo 'instituicao'.
    """
    if not email or "@" not in email:
        return ""
    dominio = email.lower().strip().split("@", 1)[1]
    return DOMINIO_PARA_INSTITUICAO.get(dominio, "")


def validate_email_institucional(email: str) -> None:
    """
    Valida se o email pertence a um domínio escolar reconhecido.
    Lança ValidationError se o domínio não estiver na lista.
    """
    if not email:
        raise ValidationError("O email é obrigatório.")

    email = email.lower().strip()

    if "@" not in email:
        raise ValidationError("Introduz um endereço de email válido.")

    dominio = email.split("@", 1)[1]

    if dominio not in _DOMINIOS_SET:
        raise ValidationError(
            f"O domínio '@{dominio}' não é reconhecido como institucional. "
            "Utiliza o email fornecido pela tua escola."
        )
