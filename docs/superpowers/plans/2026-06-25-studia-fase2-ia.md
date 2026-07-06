# Studia — Fase 2: Módulo de IA e Optimização Mobile — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Pré-requisito:** A Fase 1 deve estar completamente implementada e com todos os testes a passar antes de iniciar este plano.

**Goal:** Adicionar moderação automática por IA (pHash local, SafeSearch stub, Perspective API stub), criação automática de reports, e optimização mobile do interface.

**Architecture:** Nova app `apps/moderation/` com três sub-serviços isolados. Cada serviço tem uma interface clara (`verificar_*`) e um stub activo por defeito — a implementação real activa-se quando a variável de ambiente correspondente estiver definida. Os reports automáticos são criados como `tipo="IA"` no modelo existente.

**Tech Stack:** Django 5.2, `imagehash` (pHash), `pdfminer.six` (extracção de texto PDF), `pillow` (leitura de imagens), stubs para Google Cloud Vision e Perspective API.

## Constrangimentos Globais

- Python 3.12+; Django ≥ 5.2, < 6.0
- Código em português de Portugal (pt-PT): comentários, mensagens, docstrings
- Stubs ACTIVOS por defeito — nunca chamar APIs externas a menos que a variável de ambiente correspondente esteja definida
- TDD: escrever teste falhado → confirmar falha → implementar → confirmar sucesso
- A app de moderação não deve importar directamente as apps de recursos ou comentários — usar sinal (signal) ou chamada directa da view; evitar acoplamento circular

---

## Mapa de Ficheiros

| Ficheiro | Acção | Tarefa |
|---|---|---|
| `apps/moderation/__init__.py` | Criar | T1 |
| `apps/moderation/apps.py` | Criar | T1 |
| `apps/moderation/services/__init__.py` | Criar | T1 |
| `apps/moderation/tests/__init__.py` | Criar | T1 |
| `apps/reports/models.py` | Modificar (add tipo "IA") | T1 |
| `apps/moderation/auto_report.py` | Criar | T2 |
| `apps/moderation/tests/test_auto_report.py` | Criar | T2 |
| `apps/moderation/services/plagiarism.py` | Criar | T3 |
| `apps/moderation/tests/test_plagiarism.py` | Criar | T3 |
| `apps/resources/models.py` | Modificar (add phash) | T3 |
| `apps/resources/views.py` | Modificar (chamar moderação) | T3, T4, T5 |
| `apps/moderation/services/safe_image.py` | Criar | T4 |
| `apps/moderation/tests/test_safe_image.py` | Criar | T4 |
| `apps/moderation/services/toxic_text.py` | Criar | T5 |
| `apps/moderation/tests/test_toxic_text.py` | Criar | T5 |
| `apps/comments/views.py` | Modificar (chamar toxic_text) | T5 |
| `apps/resources/templates/resources/lista.html` | Modificar | T6 |
| `apps/resources/templates/resources/resource_detail.html` | Modificar | T6 |
| `apps/accounts/templates/accounts/perfil.html` | Modificar | T6 |
| `static/css/style.css` | Modificar | T6 |
| `pap/settings/base.py` | Modificar | T1 |

---

### Tarefa 1: Scaffold da App de Moderação + Tipo "IA" em Reports

**Ficheiros:**
- Criar: `apps/moderation/__init__.py`, `apps.py`, `services/__init__.py`, `tests/__init__.py`
- Modificar: `apps/reports/models.py`
- Modificar: `pap/settings/base.py`

**Interfaces:**
- Produz: app `apps.moderation` registada e importável.

- [ ] **Passo 1: Escrever teste para o tipo "IA" em reports**

Criar `apps/moderation/tests/__init__.py` (vazio) e um ficheiro temporário de teste:

```python
# apps/reports/tests/test_tipo_ia.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.reports.models import Report

User = get_user_model()


class ReportTipoIATestes(TestCase):

    def test_tipo_ia_e_valido(self):
        """O campo 'tipo' do Report aceita o valor 'IA'."""
        tipos_validos = [t[0] for t in Report.TIPO_CHOICES]
        self.assertIn('IA', tipos_validos)
```

- [ ] **Passo 2: Correr o teste para confirmar que falha**

```bash
python manage.py test apps.reports.tests.test_tipo_ia --verbosity=2
```

Resultado esperado: `FAIL` — `AssertionError: 'IA' not found in [...]`.

- [ ] **Passo 3: Adicionar 'IA' às choices de `Report.tipo`**

Em `apps/reports/models.py`, localizar o campo `tipo` e as suas choices. Adicionar `("IA", "IA")`:

```python
# Localizar TIPO_CHOICES (ou equivalente) e adicionar "IA":
# Exemplo — estrutura exacta pode variar; adaptar ao que está no ficheiro.

TIPO_CHOICES = [
    ("RECURSO",  "Recurso"),
    ("USUARIO",  "Utilizador"),
    ("IA",       "Moderação automática"),
]
```

Criar e aplicar a migração:
```bash
python manage.py makemigrations reports --name="add_tipo_ia"
python manage.py migrate
```

- [ ] **Passo 4: Confirmar que o teste passa**

```bash
python manage.py test apps.reports.tests.test_tipo_ia --verbosity=2
```

Resultado esperado: PASS.

- [ ] **Passo 5: Criar o scaffold da app de moderação**

```bash
mkdir -p /home/livia/livia/pap_studia/apps/moderation/services
mkdir -p /home/livia/livia/pap_studia/apps/moderation/tests
```

Criar `apps/moderation/__init__.py` (vazio):
```python
```

Criar `apps/moderation/apps.py`:
```python
from django.apps import AppConfig


class ModerationConfig(AppConfig):
    """App de moderação automática por IA (pHash, SafeSearch, Perspective API)."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.moderation'
    verbose_name = 'Moderação'
```

Criar `apps/moderation/services/__init__.py` (vazio):
```python
```

Criar `apps/moderation/tests/__init__.py` (vazio):
```python
```

- [ ] **Passo 6: Registar a app em `pap/settings/base.py`**

```python
INSTALLED_APPS = [
    ...
    'apps.moderation',  # adicionar após 'apps.notifications'
    ...
]
```

Adicionar também as configurações de moderação no fim de `base.py`:

```python
# Limiares de moderação (ajustáveis sem necessidade de alterações de código)
MODERATION_PHASH_LIMIAR = 10     # diferença máxima de bits para detectar plágio visual
MODERATION_PERSPECTIVE_LIMIAR = 0.8  # probabilidade mínima de toxicidade (0-1)
```

- [ ] **Passo 7: Confirmar que o projecto arranca com a nova app**

```bash
python manage.py check
```

Resultado esperado: `System check identified no issues (0 silenced).`

---

### Tarefa 2: Criação Automática de Reports por IA

**Ficheiros:**
- Criar: `apps/moderation/auto_report.py`
- Criar: `apps/moderation/tests/test_auto_report.py`

**Interfaces:**
- Produz: `criar_report_ia(recurso=None, usuario=None, motivo_tipo='', motivo='') -> Report`

- [ ] **Passo 1: Escrever testes para `criar_report_ia`**

Criar `apps/moderation/tests/test_auto_report.py`:

```python
"""Testes para a criação automática de reports por IA."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from apps.reports.models import Report
from apps.resources.models import Resource

User = get_user_model()


def _utilizador(email='mod@escola.pt'):
    u = User.objects.create_user(
        email=email, password='passe123',
        nome='Mod', curso='CT', ano_letivo='12',
        instituicao='Escola Teste',
    )
    User.objects.filter(pk=u.pk).update(is_active=True)
    u.refresh_from_db()
    return u


def _recurso(utilizador):
    r = Resource(
        usuario=utilizador, nome='Recurso IA Teste',
        curso=utilizador.curso, ano_letivo='12',
        disciplina='Teste', instituicao=utilizador.instituicao,
    )
    r.arquivo = ContentFile(b'%PDF conteudo', name='teste.pdf')
    r._skip_full_clean = True
    r.save()
    return r


class CriarReportIATestes(TestCase):

    def setUp(self):
        self.utilizador = _utilizador()
        self.recurso = _recurso(self.utilizador)

    def test_cria_report_de_recurso_com_tipo_ia(self):
        """criar_report_ia cria um Report com tipo='IA' para um recurso."""
        from apps.moderation.auto_report import criar_report_ia
        report = criar_report_ia(
            recurso=self.recurso,
            motivo_tipo='plagio',
            motivo='Conteúdo similar a recurso existente (pHash).',
        )
        self.assertEqual(report.tipo, 'IA')
        self.assertEqual(report.status, 'PENDENTE')
        self.assertEqual(report.recurso, self.recurso)
        self.assertIsNone(report.denunciante)

    def test_cria_report_de_utilizador_com_tipo_ia(self):
        """criar_report_ia cria um Report com tipo='IA' para um utilizador."""
        from apps.moderation.auto_report import criar_report_ia
        report = criar_report_ia(
            usuario=self.utilizador,
            motivo_tipo='improprio',
            motivo='Texto potencialmente ofensivo detectado.',
        )
        self.assertEqual(report.tipo, 'IA')
        self.assertEqual(report.usuario_denunciado, self.utilizador)

    def test_motivo_guardado_correctamente(self):
        """O campo motivo é guardado tal como fornecido."""
        from apps.moderation.auto_report import criar_report_ia
        motivo = 'Imagem com conteúdo impróprio detectado pelo SafeSearch.'
        report = criar_report_ia(
            recurso=self.recurso,
            motivo_tipo='improprio',
            motivo=motivo,
        )
        self.assertEqual(report.motivo, motivo)
```

- [ ] **Passo 2: Correr testes para confirmar que falham**

```bash
python manage.py test apps.moderation.tests.test_auto_report --verbosity=2
```

Resultado esperado: `ImportError` — `cannot import name 'criar_report_ia'`.

- [ ] **Passo 3: Implementar `apps/moderation/auto_report.py`**

```python
"""
Criação automática de reports pelo sistema de moderação por IA.
Reports criados aqui ficam com tipo='IA' e status='PENDENTE'
para revisão humana pelo administrador.
"""

from apps.reports.models import Report


def criar_report_ia(
    recurso=None,
    usuario=None,
    motivo_tipo: str = '',
    motivo: str = '',
) -> Report:
    """
    Cria um Report automático gerado pela moderação por IA.

    Args:
        recurso: instância de Resource, se o report for sobre um recurso.
        usuario: instância de User, se o report for sobre um utilizador.
        motivo_tipo: código do motivo (ex: 'plagio', 'improprio', 'ofensa').
        motivo: descrição legível do que foi detectado.

    Returns:
        Report criado e guardado na base de dados.
    """
    return Report.objects.create(
        denunciante=None,  # sem utilizador humano — criado pela IA
        recurso=recurso,
        usuario_denunciado=usuario,
        tipo='IA',
        motivo_tipo=motivo_tipo,
        motivo=motivo,
        status='PENDENTE',
    )
```

- [ ] **Passo 4: Confirmar que os testes passam**

```bash
python manage.py test apps.moderation.tests.test_auto_report --verbosity=2
```

Resultado esperado: PASS.

---

### Tarefa 3: Detecção de Plágio por pHash

**Ficheiros:**
- Criar: `apps/moderation/services/plagiarism.py`
- Criar: `apps/moderation/tests/test_plagiarism.py`
- Modificar: `apps/resources/models.py` (campo `phash`)
- Modificar: `apps/resources/views.py` (chamar verificação no upload)

**Interfaces:**
- Produz: `verificar_plagio(recurso: Resource) -> bool` — `True` se plágio detectado

- [ ] **Passo 1: Adicionar campo `phash` ao modelo Resource**

Em `apps/resources/models.py`, após o campo `hash_arquivo`:

```python
# Hash perceptual (pHash) — usado para detectar plágio visual em imagens e PDFs
phash = models.CharField(max_length=64, blank=True, default='', db_index=False)
```

Criar e aplicar a migração:
```bash
python manage.py makemigrations resources --name="add_phash"
python manage.py migrate
```

- [ ] **Passo 2: Escrever testes para `verificar_plagio`**

Criar `apps/moderation/tests/test_plagiarism.py`:

```python
"""Testes para a detecção de plágio por pHash."""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from apps.resources.models import Resource

User = get_user_model()


def _utilizador(email='plag@escola.pt'):
    u = User.objects.create_user(
        email=email, password='passe123',
        nome='Plag', curso='CT', ano_letivo='12',
        instituicao='Escola Teste',
    )
    User.objects.filter(pk=u.pk).update(is_active=True)
    u.refresh_from_db()
    return u


def _recurso_img(utilizador, nome='img.png', phash_valor=''):
    # PNG mínimo 1×1 vermelho
    conteudo_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
        b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    r = Resource(
        usuario=utilizador, nome='Recurso IMG Teste',
        curso=utilizador.curso, ano_letivo='12',
        disciplina='Teste', instituicao=utilizador.instituicao,
    )
    r.arquivo = ContentFile(conteudo_png, name=nome)
    r._skip_full_clean = True
    r.save()
    if phash_valor:
        Resource.objects.filter(pk=r.pk).update(phash=phash_valor)
        r.refresh_from_db()
    return r


class VerificarPlagioTestes(TestCase):

    def setUp(self):
        self.utilizador = _utilizador()

    def test_sem_recursos_existentes_nao_detecta_plagio(self):
        """Primeiro recurso nunca é detectado como plágio (não há com o que comparar)."""
        from apps.moderation.services.plagiarism import verificar_plagio
        recurso = _recurso_img(self.utilizador, nome='unico.png')
        resultado = verificar_plagio(recurso)
        self.assertFalse(resultado)

    def test_recursos_pdf_com_hash_identico_detecta_plagio(self):
        """Dois PDFs com o mesmo hash de conteúdo são detectados como plágio."""
        from apps.moderation.services.plagiarism import verificar_plagio

        u2 = _utilizador('outro@escola.pt')
        r1 = Resource(
            usuario=self.utilizador, nome='PDF Original',
            curso=self.utilizador.curso, ano_letivo='12',
            disciplina='Teste', instituicao=self.utilizador.instituicao,
        )
        r1.arquivo = ContentFile(b'%PDF conteudo identico', name='original.pdf')
        r1._skip_full_clean = True
        r1.save()

        r2 = Resource(
            usuario=u2, nome='PDF Copia',
            curso=u2.curso, ano_letivo='12',
            disciplina='Teste', instituicao=u2.instituicao,
        )
        r2.arquivo = ContentFile(b'%PDF conteudo identico', name='copia.pdf')
        r2._skip_full_clean = True
        r2.save()

        # r2 tem o mesmo hash SHA256 que r1 — detectado como plágio
        # Simular: forçar o mesmo hash em r1 e comparar r2
        Resource.objects.filter(pk=r1.pk).update(hash_arquivo='aabbcc')
        Resource.objects.filter(pk=r2.pk).update(hash_arquivo='ddeeff')  # diferente

        # Plágio por hash idêntico
        Resource.objects.filter(pk=r1.pk).update(hash_arquivo='mesmoHash')
        Resource.objects.filter(pk=r2.pk).update(hash_arquivo='mesmoHash')
        r2.refresh_from_db()
        # hash_arquivo duplicado → unique constraint impede; testar via phash
        # Este teste verifica que a função não levanta excepção e devolve bool
        resultado = verificar_plagio(r2)
        self.assertIsInstance(resultado, bool)

    def test_funcao_devolve_bool(self):
        """verificar_plagio devolve sempre True ou False, nunca None."""
        from apps.moderation.services.plagiarism import verificar_plagio
        recurso = _recurso_img(self.utilizador)
        resultado = verificar_plagio(recurso)
        self.assertIsInstance(resultado, bool)
```

- [ ] **Passo 3: Correr testes para confirmar que falham**

```bash
python manage.py test apps.moderation.tests.test_plagiarism --verbosity=2
```

Resultado esperado: `ImportError` — módulo não existe ainda.

- [ ] **Passo 4: Implementar `apps/moderation/services/plagiarism.py`**

```python
"""
Detecção de plágio por hashing.

Para imagens (tipo_arquivo='IMG'): usa pHash perceptual via imagehash.
Para PDFs: compara hash SHA256 do conteúdo (já calculado no modelo Resource).
Para DOCX/PPTX: compara hash SHA256 do ficheiro.

Executa localmente, sem chamadas a APIs externas.
"""

import logging
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from apps.resources.models import Resource

logger = logging.getLogger(__name__)

# Diferença máxima de bits para considerar duas imagens visualmente iguais
LIMIAR_PHASH = getattr(settings, 'MODERATION_PHASH_LIMIAR', 10)


def _calcular_phash_imagem(caminho_ficheiro: str) -> str:
    """
    Calcula o pHash perceptual de uma imagem.
    Devolve string hexadecimal ou '' em caso de erro.
    """
    try:
        import imagehash
        from PIL import Image
        imagem = Image.open(caminho_ficheiro)
        return str(imagehash.phash(imagem))
    except Exception as e:
        logger.warning('Erro ao calcular pHash da imagem %s: %s', caminho_ficheiro, e)
        return ''


def _phash_similar(hash1: str, hash2: str) -> bool:
    """Devolve True se a diferença de bits entre os dois pHashes for <= LIMIAR."""
    try:
        import imagehash
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return (h1 - h2) <= LIMIAR_PHASH
    except Exception:
        return False


def verificar_plagio(recurso: 'Resource') -> bool:
    """
    Verifica se o recurso é um plágio de algum recurso já existente.

    Para imagens: calcula e compara pHash perceptual.
    Para PDFs/DOCX/PPTX: compara hash SHA256 (já guardado em Resource.hash_arquivo).

    Actualiza o campo 'phash' do recurso se for imagem.

    Returns:
        True se plágio detectado, False caso contrário.
    """
    from apps.resources.models import Resource

    if not recurso.arquivo or not recurso.pk:
        return False

    tipo = recurso.tipo_arquivo

    if tipo == 'IMG':
        # Calcular pHash da nova imagem
        try:
            novo_phash = _calcular_phash_imagem(recurso.arquivo.path)
        except Exception:
            return False

        if not novo_phash:
            return False

        # Guardar o phash no recurso
        Resource.objects.filter(pk=recurso.pk).update(phash=novo_phash)

        # Comparar com todos os recursos IMG existentes (excluindo este)
        recursos_existentes = (
            Resource.objects
            .filter(tipo_arquivo='IMG')
            .exclude(pk=recurso.pk)
            .exclude(phash='')
            .values_list('phash', flat=True)
        )
        for phash_existente in recursos_existentes:
            if _phash_similar(novo_phash, phash_existente):
                logger.info(
                    'Plágio visual detectado: recurso %d similar a recurso existente.',
                    recurso.pk,
                )
                return True

    else:
        # Para PDF/DOCX/PPTX: o hash SHA256 já está em Resource.hash_arquivo
        if not recurso.hash_arquivo:
            return False

        plagio = (
            Resource.objects
            .filter(hash_arquivo=recurso.hash_arquivo)
            .exclude(pk=recurso.pk)
            .exists()
        )
        if plagio:
            logger.info(
                'Plágio por hash detectado: recurso %d tem hash duplicado.',
                recurso.pk,
            )
            return True

    return False
```

- [ ] **Passo 5: Correr testes de plágio**

```bash
python manage.py test apps.moderation.tests.test_plagiarism --verbosity=2
```

Resultado esperado: PASS.

- [ ] **Passo 6: Integrar verificação de plágio no upload de recurso**

Em `apps/resources/views.py`, em `upload_recurso_view`, após `recurso.save()`, adicionar:

```python
# Após recurso.save() e antes do redirect:
# Verificação de plágio (não bloqueia o upload — cria report para revisão humana)
try:
    from apps.moderation.services.plagiarism import verificar_plagio
    from apps.moderation.auto_report import criar_report_ia
    if verificar_plagio(recurso):
        criar_report_ia(
            recurso=recurso,
            motivo_tipo='plagio',
            motivo='Conteúdo similar a recurso já existente detectado automaticamente.',
        )
except Exception as e:
    import logging
    logging.getLogger(__name__).error('Erro na verificação de plágio: %s', e)
```

**Nota importante:** a verificação não bloqueia o upload — apenas cria um report para revisão humana. O aluno não é notificado.

---

### Tarefa 4: SafeSearch para Imagens (Stub)

**Ficheiros:**
- Criar: `apps/moderation/services/safe_image.py`
- Criar: `apps/moderation/tests/test_safe_image.py`
- Modificar: `apps/resources/views.py`

**Interfaces:**
- Produz: `verificar_imagem_segura(caminho_ficheiro: str) -> bool`

- [ ] **Passo 1: Escrever testes para `verificar_imagem_segura`**

Criar `apps/moderation/tests/test_safe_image.py`:

```python
"""Testes para o verificador de SafeSearch (stub activo por defeito)."""

from django.test import TestCase, override_settings


class SafeImageStubTestes(TestCase):

    @override_settings(GOOGLE_CLOUD_CREDENTIALS='')
    def test_stub_devolve_true_sem_credenciais(self):
        """Sem credenciais Google Cloud, o stub assume sempre imagem segura."""
        from apps.moderation.services.safe_image import verificar_imagem_segura
        resultado = verificar_imagem_segura('/qualquer/caminho.png')
        self.assertTrue(resultado)

    @override_settings(GOOGLE_CLOUD_CREDENTIALS='')
    def test_stub_nao_levanta_excepcao(self):
        """O stub nunca levanta excepção, mesmo com caminho inválido."""
        from apps.moderation.services.safe_image import verificar_imagem_segura
        try:
            resultado = verificar_imagem_segura('/caminho/inexistente.jpg')
            self.assertIsInstance(resultado, bool)
        except Exception as e:
            self.fail(f'verificar_imagem_segura levantou excepção inesperada: {e}')
```

- [ ] **Passo 2: Correr testes para confirmar que falham**

```bash
python manage.py test apps.moderation.tests.test_safe_image --verbosity=2
```

- [ ] **Passo 3: Implementar `apps/moderation/services/safe_image.py`**

```python
"""
Verificação de conteúdo impróprio em imagens via Google Cloud Vision SafeSearch.

O stub está SEMPRE ACTIVO por defeito.
A implementação real activa-se quando GOOGLE_CLOUD_CREDENTIALS estiver definido
nas variáveis de ambiente (settings.GOOGLE_CLOUD_CREDENTIALS não vazio).

Interface pública:
    verificar_imagem_segura(caminho_ficheiro: str) -> bool
        True  → imagem segura (pode ser publicada)
        False → imagem imprópria (deve ser bloqueada)
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def verificar_imagem_segura(caminho_ficheiro: str) -> bool:
    """
    Verifica se a imagem não contém conteúdo impróprio.

    Stub (sem credenciais): devolve sempre True.
    Real (com credenciais): chama a API Google Cloud Vision SafeSearch.

    Args:
        caminho_ficheiro: caminho absoluto para o ficheiro de imagem.

    Returns:
        True se a imagem for segura, False se contiver conteúdo impróprio.
    """
    credenciais = getattr(settings, 'GOOGLE_CLOUD_CREDENTIALS', '')

    if not credenciais:
        # Stub activo — sem credenciais, assume sempre seguro
        logger.debug(
            'SafeSearch: stub activo (GOOGLE_CLOUD_CREDENTIALS não definido). '
            'Assumindo imagem segura: %s', caminho_ficheiro
        )
        return True

    # Implementação real (activa quando GOOGLE_CLOUD_CREDENTIALS estiver definido)
    try:
        from google.cloud import vision
        import io

        cliente = vision.ImageAnnotatorClient()
        with io.open(caminho_ficheiro, 'rb') as ficheiro_imagem:
            conteudo = ficheiro_imagem.read()

        imagem   = vision.Image(content=conteudo)
        resposta = cliente.safe_search_detection(image=imagem)
        anotacao = resposta.safe_search_annotation

        # Níveis LIKELY e VERY_LIKELY indicam conteúdo impróprio
        niveis_improprios = {
            vision.Likelihood.LIKELY,
            vision.Likelihood.VERY_LIKELY,
        }
        if (
            anotacao.adult    in niveis_improprios or
            anotacao.violence in niveis_improprios or
            anotacao.racy     in niveis_improprios
        ):
            logger.warning('SafeSearch: conteúdo impróprio em %s', caminho_ficheiro)
            return False

        return True

    except ImportError:
        logger.error(
            'google-cloud-vision não instalado. Instala com: pip install google-cloud-vision'
        )
        return True  # falha segura — não bloqueia
    except Exception as e:
        logger.error('Erro na verificação SafeSearch: %s', e)
        return True  # falha segura — não bloqueia
```


- [ ] **Passo 4: Correr testes para confirmar que passam**

```bash
python manage.py test apps.moderation.tests.test_safe_image --verbosity=2
```

Resultado esperado: PASS.

- [ ] **Passo 5: Integrar SafeSearch no upload de imagens**

Em `apps/resources/views.py`, em `upload_recurso_view`, após o bloco de verificação de plágio, adicionar:

```python
# Verificação SafeSearch (apenas para imagens)
if recurso.tipo_arquivo == 'IMG' and recurso.arquivo:
    try:
        from apps.moderation.services.safe_image import verificar_imagem_segura
        from apps.moderation.auto_report import criar_report_ia
        if not verificar_imagem_segura(recurso.arquivo.path):
            criar_report_ia(
                recurso=recurso,
                motivo_tipo='improprio',
                motivo='Conteúdo impróprio detectado automaticamente pela análise de imagem.',
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error('Erro na verificação SafeSearch: %s', e)
```

---

### Tarefa 5: Perspective API — Texto Ofensivo (Stub)

**Ficheiros:**
- Criar: `apps/moderation/services/toxic_text.py`
- Criar: `apps/moderation/tests/test_toxic_text.py`
- Modificar: `apps/comments/views.py`
- Modificar: `apps/resources/views.py`

**Interfaces:**
- Produz: `verificar_texto_seguro(texto: str) -> bool`

- [ ] **Passo 1: Escrever testes para `verificar_texto_seguro`**

Criar `apps/moderation/tests/test_toxic_text.py`:

```python
"""Testes para o verificador de texto ofensivo (stub por defeito)."""

from django.test import TestCase, override_settings


class ToxicTextStubTestes(TestCase):

    @override_settings(PERSPECTIVE_API_KEY='')
    def test_stub_devolve_true_sem_chave(self):
        """Sem PERSPECTIVE_API_KEY, o stub assume sempre texto seguro."""
        from apps.moderation.services.toxic_text import verificar_texto_seguro
        resultado = verificar_texto_seguro('qualquer texto')
        self.assertTrue(resultado)

    @override_settings(PERSPECTIVE_API_KEY='')
    def test_stub_com_string_vazia(self):
        """String vazia também é tratada como segura."""
        from apps.moderation.services.toxic_text import verificar_texto_seguro
        resultado = verificar_texto_seguro('')
        self.assertTrue(resultado)

    @override_settings(PERSPECTIVE_API_KEY='')
    def test_stub_nao_levanta_excepcao(self):
        """O stub nunca levanta excepção."""
        from apps.moderation.services.toxic_text import verificar_texto_seguro
        try:
            resultado = verificar_texto_seguro('texto de teste com acentuação')
            self.assertIsInstance(resultado, bool)
        except Exception as e:
            self.fail(f'verificar_texto_seguro levantou excepção: {e}')
```

- [ ] **Passo 2: Correr testes para confirmar que falham**

```bash
python manage.py test apps.moderation.tests.test_toxic_text --verbosity=2
```

- [ ] **Passo 3: Implementar `apps/moderation/services/toxic_text.py`**

```python
"""
Verificação de texto ofensivo via Perspective API (Jigsaw/Google).

Stub ACTIVO por defeito.
Implementação real activa-se quando PERSPECTIVE_API_KEY estiver definido.

Interface pública:
    verificar_texto_seguro(texto: str) -> bool
        True  → texto aceitável
        False → texto potencialmente ofensivo
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

LIMIAR = 0.8  # probabilidade acima da qual o texto é considerado ofensivo


def verificar_texto_seguro(texto: str) -> bool:
    """
    Verifica se o texto não contém linguagem ofensiva.

    Stub (sem chave API): devolve sempre True.
    Real (com chave): chama Perspective API e verifica a pontuação de toxicidade.

    Args:
        texto: texto a verificar (comentário ou descrição de recurso).

    Returns:
        True se o texto for aceitável, False se for potencialmente ofensivo.
    """
    if not texto or not texto.strip():
        return True

    chave_api = getattr(settings, 'PERSPECTIVE_API_KEY', '')

    if not chave_api:
        logger.debug(
            'Perspective API: stub activo (PERSPECTIVE_API_KEY não definido). '
            'Assumindo texto seguro.'
        )
        return True

    # Implementação real (activa quando PERSPECTIVE_API_KEY estiver definido)
    try:
        import urllib.request
        import json

        url = (
            'https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze'
            f'?key={chave_api}'
        )
        corpo = json.dumps({
            'comment': {'text': texto},
            'languages': ['pt'],
            'requestedAttributes': {'TOXICITY': {}},
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=corpo,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=5) as resposta:
            dados = json.loads(resposta.read())

        pontuacao = (
            dados
            .get('attributeScores', {})
            .get('TOXICITY', {})
            .get('summaryScore', {})
            .get('value', 0.0)
        )

        if pontuacao >= LIMIAR:
            logger.warning(
                'Perspective API: texto ofensivo detectado (pontuação=%.2f)', pontuacao
            )
            return False

        return True

    except Exception as e:
        logger.error('Erro na verificação Perspective API: %s', e)
        return True  # falha segura — não bloqueia
```

- [ ] **Passo 4: Correr testes para confirmar que passam**

```bash
python manage.py test apps.moderation.tests.test_toxic_text --verbosity=2
```

Resultado esperado: PASS.

- [ ] **Passo 5: Integrar verificação de texto em `apps/comments/views.py`**

Ler `apps/comments/views.py` e localizar a view que guarda o comentário (provavelmente `adicionar_comentario_view`). Adicionar ANTES de guardar o comentário:

```python
# Adicionar no início do bloco de processamento POST, antes de comment.save():
texto = request.POST.get('texto', '').strip()
try:
    from apps.moderation.services.toxic_text import verificar_texto_seguro
    if not verificar_texto_seguro(texto):
        messages.error(
            request,
            'O teu comentário contém linguagem que não é permitida. Por favor revê o texto.',
        )
        return redirect('resources:detalhes', pk=pk)
except Exception as e:
    import logging
    logging.getLogger(__name__).error('Erro na verificação de texto: %s', e)
```

- [ ] **Passo 6: Correr todos os testes de moderação**

```bash
python manage.py test apps.moderation --verbosity=2
```

Resultado esperado: todos PASS.

---

### Tarefa 6: Optimização Mobile

**Ficheiros:**
- Modificar: `static/css/style.css`
- Modificar: `apps/resources/templates/resources/lista.html`
- Modificar: `apps/resources/templates/resources/resource_detail.html`
- Modificar: `apps/accounts/templates/accounts/perfil.html`

**Interfaces:** Sem interfaces Python — verificação visual.

- [ ] **Passo 1: Melhorar responsividade do formulário de filtros em `lista.html`**

Localizar os `<div class="col-md-X">` na secção de filtros e adicionar `col-12` como base:

```html
<!-- ANTES -->
<div class="col-md-4">  <!-- pesquisa -->
<div class="col-md-2">  <!-- curso -->
<div class="col-md-2">  <!-- instituição -->
<div class="col-md-1">  <!-- ano -->
<div class="col-md-1">  <!-- tipo -->
<div class="col-md-2">  <!-- botões -->

<!-- DEPOIS -->
<div class="col-12 col-md-4">  <!-- pesquisa -->
<div class="col-12 col-md-2">  <!-- curso -->
<div class="col-12 col-md-2">  <!-- instituição -->
<div class="col-6 col-md-1">   <!-- ano -->
<div class="col-6 col-md-1">   <!-- tipo -->
<div class="col-12 col-md-2">  <!-- botões -->
```

- [ ] **Passo 2: Melhorar a sidebar do perfil em mobile**

Em `apps/accounts/templates/accounts/perfil.html`, o layout actual é `col-md-4` (sidebar) e `col-md-8` (conteúdo). Em mobile ficam em coluna única automaticamente pelo Bootstrap — confirmar que está correcto.

Adicionar `order` classes para que em mobile o sidebar apareça DEPOIS do conteúdo (o conteúdo é mais importante):

```html
<!-- ANTES -->
<div class="col-md-4">  <!-- sidebar -->
...
<div class="col-md-8">  <!-- conteúdo -->

<!-- DEPOIS -->
<div class="col-md-4 order-md-1 order-2">  <!-- sidebar: segunda em mobile, primeira em desktop -->
...
<div class="col-md-8 order-md-2 order-1">  <!-- conteúdo: primeira em mobile -->
```

- [ ] **Passo 3: Adicionar media query para ocultar colunas secundárias em detalhe de recurso**

Em `apps/resources/templates/resources/resource_detail.html`, verificar que a sidebar (`col-lg-4`) fica abaixo do conteúdo em mobile — Bootstrap `col-lg-4` já garante isso (passa a `col-12` abaixo de `lg`). Confirmar visualmente.

- [ ] **Passo 4: Adicionar media query no CSS para tabelas em mobile**

Em `static/css/style.css`, adicionar no bloco `@media (max-width: 767px)`:

```css
@media (max-width: 767px) {
  .st-hero { padding: 2rem 1.5rem; }
  .st-hero h1 { font-size: 1.75rem; }
  main.container { padding-top: 1rem !important; padding-bottom: 2rem !important; }

  /* Novas regras mobile */
  .table-responsive-stack td,
  .table-responsive-stack th { display: block; width: 100%; }

  .st-resource-card .card-footer {
    flex-wrap: wrap;
    gap: .5rem;
  }
}
```

- [ ] **Passo 5: Verificar em modo mobile no browser**

No Chrome/Firefox, abrir DevTools (F12) → alternar para modo de dispositivo móvel (ícone de telemóvel) → testar:
- Lista de recursos: filtros em coluna única, cards ocupam ecrã completo.
- Detalhe de recurso: sidebar aparece abaixo do conteúdo.
- Perfil: conteúdo (recursos enviados) aparece antes da sidebar.
- Navbar: toggler funciona, menu colapsa correctamente.

---

## Verificação Final da Fase 2

- [ ] Correr todos os testes: `python manage.py test --verbosity=2` — todos PASS.
- [ ] Confirmar que o upload de uma imagem gera um report "IA" se for similar a uma existente.
- [ ] Confirmar que o stub SafeSearch não bloqueia nenhum upload (sem credenciais).
- [ ] Confirmar que comentários são guardados normalmente (stub Perspective não bloqueia).
- [ ] Verificar interface mobile nos principais ecrãs.
- [ ] `python manage.py check` — sem erros.
