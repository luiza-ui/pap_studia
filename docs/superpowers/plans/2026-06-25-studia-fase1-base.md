# Studia — Fase 1: Base Sólida e Deployável — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir problemas visuais, remover código morto, implementar autocomplete por relevância, confirmação de email por token, configuração de produção para Railway e páginas de erro 404/500.

**Architecture:** Seis tarefas independentes sobre a mesma base Django 5.2. A Tarefa 4 (email) introduz um novo modelo `EmailActivationToken` e altera o fluxo de registo; as restantes são melhorias cirúrgicas. TDD em todas as tarefas que introduzem lógica Python — fixes de CSS/HTML verificam-se visualmente.

**Tech Stack:** Django 5.2, Bootstrap 5, SQLite (dev) / PostgreSQL (prod), Gmail SMTP, Railway, Gunicorn, WhiteNoise, python-decouple.

## Constrangimentos Globais

- Python 3.12+; Django ≥ 5.2, < 6.0
- Código em português de Portugal (pt-PT): comentários, mensagens de utilizador, docstrings
- Nomes de variáveis e funções em português (padrão existente no projecto)
- TDD: escrever teste falhado → confirmar falha → implementar → confirmar sucesso → commit
- Sem `pip install` manual — usar `dnf` ou verificar com o utilizador
- Nunca modificar `pap/settings.py` directamente — substituído na Tarefa 5

---

## Mapa de Ficheiros

| Ficheiro | Acção | Tarefa |
|---|---|---|
| `static/css/style.css` | Modificar | T1 |
| `apps/resources/templates/resources/resource_detail.html` | Modificar | T1 |
| `apps/accounts/templates/accounts/perfil.html` | Modificar | T1 |
| `apps/resources/templates/resources/lista.html` | Modificar | T1, T3 |
| `apps/core/management/` | Eliminar directório | T2 |
| `apps/resources/views.py` | Modificar | T3 |
| `apps/resources/urls.py` | Modificar | T3 |
| `apps/resources/tests/test_autocomplete.py` | Criar | T3 |
| `apps/accounts/models.py` | Modificar | T4 |
| `apps/accounts/forms.py` | Modificar | T4 |
| `apps/accounts/views.py` | Modificar | T4 |
| `apps/accounts/urls.py` | Modificar | T4 |
| `apps/accounts/templates/accounts/activacao_pendente.html` | Criar | T4 |
| `apps/accounts/templates/accounts/reenviar_activacao.html` | Criar | T4 |
| `apps/accounts/templates/accounts/email/activacao.html` | Criar | T4 |
| `apps/accounts/templates/accounts/email/activacao.txt` | Criar | T4 |
| `apps/accounts/management/commands/popular_bd.py` | Modificar | T4 |
| `apps/accounts/tests/test_email_activation.py` | Criar | T4 |
| `pap/settings.py` | Substituído por `pap/settings/` | T5 |
| `pap/settings/__init__.py` | Criar | T5 |
| `pap/settings/base.py` | Criar | T5 |
| `pap/settings/development.py` | Criar | T5 |
| `pap/settings/production.py` | Criar | T5 |
| `manage.py` | Modificar | T5 |
| `pap/wsgi.py` | Modificar | T5 |
| `pap/asgi.py` | Modificar | T5 |
| `requirements.txt` | Preencher | T5 |
| `Procfile` | Criar | T5 |
| `railway.toml` | Criar | T5 |
| `.env.example` | Criar | T5 |
| `templates/404.html` | Criar | T6 |
| `templates/500.html` | Criar | T6 |
| `pap/urls.py` | Modificar | T6 |

---

### Tarefa 1: Correcção de Problemas de Layout

**Ficheiros:**
- Modificar: `static/css/style.css`
- Modificar: `apps/resources/templates/resources/resource_detail.html`
- Modificar: `apps/accounts/templates/accounts/perfil.html`
- Modificar: `apps/resources/templates/resources/lista.html`

**Interfaces:** Sem interfaces Python — verificação visual no browser.

- [ ] **Passo 1: Corrigir `.st-stat-label` no CSS**

Em `static/css/style.css`, localizar e substituir o bloco `.st-stat-label` (linha ~387):

```css
/* ANTES */
.st-stat-label {
  font-size: .75rem;
  color: var(--st-text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: .05em;
}

/* DEPOIS */
.st-stat-label {
  font-size: .72rem;
  color: var(--st-text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .01em;
  overflow-wrap: break-word;
  word-break: break-word;
  line-height: 1.3;
}
```

- [ ] **Passo 2: Corrigir bloco de estatísticas em `resource_detail.html`**

Em `apps/resources/templates/resources/resource_detail.html`, localizar o `<div class="row g-2">` dentro do card "Estatísticas" (~linha 208) e substituir `col-4` por `col-12 col-sm-4` em todas as três colunas:

```html
<!-- ANTES -->
<div class="row g-2">
  <div class="col-4">
    <div class="st-stat">
      <div class="st-stat-value">{{ recurso.total_downloads }}</div>
      <div class="st-stat-label">Downloads</div>
    </div>
  </div>
  <div class="col-4">
    <div class="st-stat">
      <div class="st-stat-value">{{ recurso.total_salvos }}</div>
      <div class="st-stat-label">Guardados</div>
    </div>
  </div>
  <div class="col-4">
    <div class="st-stat">
      <div class="st-stat-value">{{ comentarios|length }}</div>
      <div class="st-stat-label">Comentários</div>
    </div>
  </div>
</div>

<!-- DEPOIS -->
<div class="row g-2">
  <div class="col-12 col-sm-4">
    <div class="st-stat">
      <div class="st-stat-value">{{ recurso.total_downloads }}</div>
      <div class="st-stat-label">Downloads</div>
    </div>
  </div>
  <div class="col-12 col-sm-4">
    <div class="st-stat">
      <div class="st-stat-value">{{ recurso.total_salvos }}</div>
      <div class="st-stat-label">Guardados</div>
    </div>
  </div>
  <div class="col-12 col-sm-4">
    <div class="st-stat">
      <div class="st-stat-value">{{ comentarios|length }}</div>
      <div class="st-stat-label">Comentários</div>
    </div>
  </div>
</div>
```

- [ ] **Passo 3: Corrigir layout de metadados no perfil**

Em `apps/accounts/templates/accounts/perfil.html`, localizar o bloco `<div class="mb-3" style="font-size:.875rem;">` com os campos Curso, Ano letivo e Instituição (~linha 33) e substituir:

```html
<!-- ANTES -->
<div class="mb-3" style="font-size:.875rem;">
  <div class="d-flex justify-content-between mb-1">
    <span class="text-muted">Curso</span>
    <span class="fw-semibold">{{ user.get_curso_display }}</span>
  </div>
  <div class="d-flex justify-content-between mb-1">
    <span class="text-muted">Ano letivo</span>
    <span class="fw-semibold">{{ user.ano_letivo }}º Ano</span>
  </div>
  <div class="d-flex justify-content-between">
    <span class="text-muted">Instituição</span>
    <span class="fw-semibold" style="text-align:right;max-width:160px;">{{ user.instituicao }}</span>
  </div>
</div>

<!-- DEPOIS -->
<div class="mb-3" style="font-size:.875rem;">
  <div class="d-flex align-items-start gap-2 mb-1">
    <span class="text-muted flex-shrink-0" style="min-width:80px;">Curso</span>
    <span class="fw-semibold text-end">{{ user.get_curso_display }}</span>
  </div>
  <div class="d-flex align-items-center gap-2 mb-1">
    <span class="text-muted flex-shrink-0" style="min-width:80px;">Ano letivo</span>
    <span class="fw-semibold ms-auto">{{ user.ano_letivo }}º Ano</span>
  </div>
  <div class="d-flex align-items-start gap-2">
    <span class="text-muted flex-shrink-0" style="min-width:80px;">Instituição</span>
    <span class="fw-semibold text-end">{{ user.instituicao }}</span>
  </div>
</div>
```

- [ ] **Passo 4: Truncar nome do curso nos cartões da lista de recursos**

Em `apps/resources/templates/resources/lista.html`, localizar a linha com `{{ r.get_curso_display }}` (~linha 164) e substituir:

```html
<!-- ANTES -->
<p class="text-muted mb-0" style="font-size:.8rem;">{{ r.get_curso_display }}</p>

<!-- DEPOIS -->
<p class="text-muted mb-0 text-truncate" style="font-size:.8rem;" title="{{ r.get_curso_display }}">{{ r.get_curso_display }}</p>
```

- [ ] **Passo 5: Verificar visualmente no browser**

Iniciar o servidor:
```bash
cd /home/livia/livia/pap_studia
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/` e verificar:
1. Perfil de utilizador → campos Curso e Instituição com texto longo ficam alinhados sem colapsar.
2. Detalhe de recurso → bloco de estatísticas: "Downloads", "Guardados", "Comentários" sem palavras partidas.
3. Lista de recursos → cartões com nome de curso longo truncado com `...` e tooltip completo em hover.

---

### Tarefa 2: Remoção de Código Morto

**Ficheiros:**
- Eliminar: `apps/core/management/` (directório completo)

**Interfaces:** Nenhuma.

- [ ] **Passo 1: Identificar o que existe no directório a eliminar**

```bash
find /home/livia/livia/pap_studia/apps/core/management -type f
```

Resultado esperado:
```
apps/core/management/__init__.py
apps/core/management/commands/__init__.py
apps/core/management/commands/popular_bd.py
```

O `apps/core/management/commands/popular_bd.py` é a seed antiga que usa `tipo_arquivo="LINK"` (tipo inexistente no modelo actual) e strings de curso em vez de códigos (ex: `"Ciências e Tecnologias"` em vez de `"CT"`). A seed actualizada está em `apps/accounts/management/commands/popular_bd.py`.

- [ ] **Passo 2: Eliminar o directório**

```bash
rm -rf /home/livia/livia/pap_studia/apps/core/management
```

- [ ] **Passo 3: Confirmar que o comando `popular_bd` da app accounts ainda funciona**

```bash
cd /home/livia/livia/pap_studia
python manage.py popular_bd
```

Resultado esperado: mensagem de sucesso com utilizadores e recursos criados.

- [ ] **Passo 4: Confirmar que os testes existentes passam**

```bash
python manage.py test apps.core apps.accounts --verbosity=2
```

Resultado esperado: todos os testes passam (PASS).

---

### Tarefa 3: Autocomplete de Pesquisa por Relevância

**Ficheiros:**
- Modificar: `apps/resources/views.py`
- Modificar: `apps/resources/urls.py`
- Modificar: `apps/resources/templates/resources/lista.html`
- Criar: `apps/resources/tests/test_autocomplete.py`

**Interfaces:**
- Produz: `GET /resources/autocomplete/?q=<termo>` → `{"sugestoes": ["Matemática A", ...]}`

- [ ] **Passo 1: Escrever os testes para o endpoint de autocomplete**

Criar `apps/resources/tests/test_autocomplete.py`:

```python
"""Testes para o endpoint de autocomplete de pesquisa por relevância."""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from apps.resources.models import Resource

User = get_user_model()


def criar_utilizador(email='teste@escola.pt', **kwargs):
    """Cria um utilizador de teste activo (bypass do email de confirmação)."""
    defaults = dict(
        nome='Teste', curso='CT', ano_letivo='12',
        instituicao='Escola Teste',
    )
    defaults.update(kwargs)
    user = User.objects.create_user(email=email, password='passe123', **defaults)
    # Garante conta activa independentemente do default de is_active
    User.objects.filter(pk=user.pk).update(is_active=True)
    user.refresh_from_db()
    return user


def criar_recurso(utilizador, disciplina, professor=''):
    """Cria um recurso mínimo de teste."""
    r = Resource(
        usuario=utilizador,
        nome=f'Recurso {disciplina}',
        curso=utilizador.curso,
        ano_letivo='12',
        disciplina=disciplina,
        instituicao=utilizador.instituicao,
        professor=professor,
    )
    r.arquivo = ContentFile(b'%PDF conteudo', name=f'{disciplina}.pdf')
    r._skip_full_clean = True
    r.save()
    return r


class AutocompleteViewTestes(TestCase):

    def setUp(self):
        self.utilizador = criar_utilizador()
        self.client.login(username='teste@escola.pt', password='passe123')
        self.url = reverse('resources:autocomplete')

    def test_resposta_json_com_query_curta_vazia(self):
        """Query com menos de 2 caracteres devolve lista vazia."""
        resposta = self.client.get(self.url, {'q': 'm'})
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.json()
        self.assertEqual(dados['sugestoes'], [])

    def test_resposta_json_sem_query(self):
        """Sem parâmetro q devolve lista vazia."""
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['sugestoes'], [])

    def test_disciplinas_ordenadas_por_frequencia(self):
        """Disciplina com mais recursos aparece primeiro."""
        criar_recurso(self.utilizador, 'Matemática A')
        criar_recurso(self.utilizador, 'Matemática A')
        criar_recurso(self.utilizador, 'Matemática B')

        resposta = self.client.get(self.url, {'q': 'mat'})
        dados = resposta.json()

        self.assertIn('Matemática A', dados['sugestoes'])
        self.assertIn('Matemática B', dados['sugestoes'])
        # Matemática A tem mais recursos → aparece primeiro
        indice_a = dados['sugestoes'].index('Matemática A')
        indice_b = dados['sugestoes'].index('Matemática B')
        self.assertLess(indice_a, indice_b)

    def test_pesquisa_insensivel_a_acentos(self):
        """'mat' encontra 'Matemática' (normalização de diacríticos)."""
        criar_recurso(self.utilizador, 'Matemática A')
        resposta = self.client.get(self.url, {'q': 'mat'})
        self.assertIn('Matemática A', resposta.json()['sugestoes'])

    def test_professores_incluidos_nas_sugestoes(self):
        """Professores também aparecem nas sugestões."""
        criar_recurso(self.utilizador, 'Física', professor='Prof. Silva')
        resposta = self.client.get(self.url, {'q': 'sil'})
        self.assertIn('Prof. Silva', resposta.json()['sugestoes'])

    def test_maximo_oito_sugestoes(self):
        """Nunca devolvem mais de 8 sugestões."""
        for i in range(15):
            criar_recurso(self.utilizador, f'Disciplina{i:02d}')
        resposta = self.client.get(self.url, {'q': 'disc'})
        self.assertLessEqual(len(resposta.json()['sugestoes']), 8)

    def test_requer_autenticacao(self):
        """Endpoint requer login."""
        self.client.logout()
        resposta = self.client.get(self.url, {'q': 'mat'})
        # Redireciona para login
        self.assertEqual(resposta.status_code, 302)
```

- [ ] **Passo 2: Correr os testes para confirmar que falham**

```bash
cd /home/livia/livia/pap_studia
python manage.py test apps.resources.tests.test_autocomplete --verbosity=2
```

Resultado esperado: `ERROR` — `NoReverseMatch: 'resources:autocomplete'` porque o URL ainda não existe.

- [ ] **Passo 3: Adicionar a view de autocomplete em `apps/resources/views.py`**

Adicionar a função no fim de `apps/resources/views.py`, antes do último bloco de código:

```python
# ------------------------------------------------------------------ #
#  AUTOCOMPLETE DE PESQUISA                                           #
# ------------------------------------------------------------------ #

@login_required
def autocomplete_recursos_view(request):
    """
    Devolve sugestões de autocomplete para disciplinas e professores,
    ordenadas por frequência (maior número de recursos primeiro).
    Usado pelo campo de pesquisa da lista de recursos via AJAX.
    Aceita GET com parâmetro 'q' (mínimo 2 caracteres).
    Devolve JSON: {"sugestoes": ["Matemática A", "Prof. Silva", ...]}
    """
    from django.http import JsonResponse
    from django.db.models import Count

    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"sugestoes": []})

    q_norm = normalizar_query_pesquisa(q)

    disciplinas = list(
        Resource.objects
        .filter(disciplina_normalizada__icontains=q_norm)
        .values("disciplina")
        .annotate(n=Count("id"))
        .order_by("-n")
        .values_list("disciplina", flat=True)[:5]
    )

    professores = list(
        Resource.objects
        .filter(professor_normalizado__icontains=q_norm)
        .exclude(professor="")
        .values("professor")
        .annotate(n=Count("id"))
        .order_by("-n")
        .values_list("professor", flat=True)[:3]
    )

    sugestoes = (disciplinas + professores)[:8]
    return JsonResponse({"sugestoes": sugestoes})
```

- [ ] **Passo 4: Registar o URL em `apps/resources/urls.py`**

```python
# ANTES (fim do ficheiro)
urlpatterns = [
    path("", views.lista_recursos_view, name="lista"),
    path("<int:pk>/", views.detalhes_recurso_view, name="detalhes"),
    path("upload/", views.upload_recurso_view, name="upload"),
    path("<int:pk>/editar/", views.editar_recurso_view, name="editar"),
    path("<int:pk>/apagar/", views.apagar_recurso_view, name="apagar"),
    path("<int:pk>/download/", views.download_recurso_view, name="download"),
]

# DEPOIS — adicionar o caminho de autocomplete antes do final
urlpatterns = [
    path("", views.lista_recursos_view, name="lista"),
    path("autocomplete/", views.autocomplete_recursos_view, name="autocomplete"),
    path("<int:pk>/", views.detalhes_recurso_view, name="detalhes"),
    path("upload/", views.upload_recurso_view, name="upload"),
    path("<int:pk>/editar/", views.editar_recurso_view, name="editar"),
    path("<int:pk>/apagar/", views.apagar_recurso_view, name="apagar"),
    path("<int:pk>/download/", views.download_recurso_view, name="download"),
]
```

- [ ] **Passo 5: Correr os testes para confirmar que passam**

```bash
python manage.py test apps.resources.tests.test_autocomplete --verbosity=2
```

Resultado esperado: todos os testes PASS.

- [ ] **Passo 6: Substituir o datalist estático por dropdown AJAX em `lista.html`**

Em `apps/resources/templates/resources/lista.html`, localizar o `<datalist>` e o `{% block extra_scripts %}` e substituir o bloco completo de autocomplete:

Substituir o campo de pesquisa (na secção de filtros, ~linha 22-29):

```html
<!-- ANTES -->
<input type="search" name="q" id="campo-pesquisa"
       value="{{ filtros.q }}"
       class="form-control"
       placeholder="Ex: Matemática, Funções, Prof. Silva…"
       autocomplete="off">
<datalist id="sugestoes-pesquisa"></datalist>

<!-- DEPOIS -->
<div class="position-relative">
  <input type="search" name="q" id="campo-pesquisa"
         value="{{ filtros.q }}"
         class="form-control"
         placeholder="Ex: Matemática, Funções, Prof. Silva…"
         autocomplete="off"
         aria-autocomplete="list"
         aria-controls="dropdown-autocomplete">
  <ul id="dropdown-autocomplete"
      class="list-group position-absolute w-100 shadow-sm"
      style="z-index:1050;display:none;top:100%;left:0;max-height:260px;overflow-y:auto;border-radius:8px;border:1px solid var(--st-border);">
  </ul>
</div>
```

Substituir o bloco `{% block extra_scripts %}` completo:

```html
{% block extra_scripts %}
<script>
(function () {
  'use strict';

  const input    = document.getElementById('campo-pesquisa');
  const dropdown = document.getElementById('dropdown-autocomplete');
  const URL_BASE = '{% url "resources:autocomplete" %}';

  if (!input || !dropdown) return;

  let temporizador = null;

  function normalizar(str) {
    return str.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function fecharDropdown() {
    dropdown.style.display = 'none';
    dropdown.innerHTML = '';
  }

  function abrirDropdown(sugestoes) {
    dropdown.innerHTML = '';
    if (!sugestoes.length) { fecharDropdown(); return; }

    const query = input.value.trim().toLowerCase();
    sugestoes.forEach(function (s) {
      const li = document.createElement('li');
      li.className = 'list-group-item list-group-item-action py-2';
      li.style.cursor = 'pointer';
      li.style.fontSize = '.875rem';

      // Realçar a parte que corresponde à pesquisa
      const sNorm = normalizar(s);
      const qNorm = normalizar(query);
      const idx   = sNorm.indexOf(qNorm);
      if (idx >= 0) {
        li.innerHTML =
          s.slice(0, idx) +
          '<strong>' + s.slice(idx, idx + query.length) + '</strong>' +
          s.slice(idx + query.length);
      } else {
        li.textContent = s;
      }

      li.addEventListener('mousedown', function (e) {
        e.preventDefault();  // evita que o blur feche o dropdown antes do click
        input.value = s;
        fecharDropdown();
        // Submete o formulário automaticamente ao seleccionar
        input.closest('form').submit();
      });
      dropdown.appendChild(li);
    });
    dropdown.style.display = 'block';
  }

  input.addEventListener('input', function () {
    clearTimeout(temporizador);
    const q = input.value.trim();
    if (q.length < 2) { fecharDropdown(); return; }

    temporizador = setTimeout(function () {
      fetch(URL_BASE + '?q=' + encodeURIComponent(q), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
        .then(function (r) { return r.json(); })
        .then(function (dados) { abrirDropdown(dados.sugestoes || []); })
        .catch(function () { fecharDropdown(); });
    }, 200);  // debounce de 200ms
  });

  input.addEventListener('blur', function () {
    // Pequeno delay para deixar o mousedown do item disparar primeiro
    setTimeout(fecharDropdown, 150);
  });

  // Fechar ao clicar fora
  document.addEventListener('click', function (e) {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      fecharDropdown();
    }
  });
})();
</script>
{% endblock %}
```

- [ ] **Passo 7: Verificar autocomplete no browser**

Abrir `http://127.0.0.1:8000/resources/`, escrever "mat" no campo de pesquisa e confirmar que o dropdown aparece com sugestões de disciplinas/professores contendo "mat", ordenadas por frequência.

---

### Tarefa 4: Confirmação de Email por Token

**Ficheiros:**
- Modificar: `apps/accounts/models.py`
- Modificar: `apps/accounts/forms.py`
- Modificar: `apps/accounts/views.py`
- Modificar: `apps/accounts/urls.py`
- Criar: `apps/accounts/templates/accounts/activacao_pendente.html`
- Criar: `apps/accounts/templates/accounts/reenviar_activacao.html`
- Criar: `apps/accounts/templates/accounts/email/activacao.html`
- Criar: `apps/accounts/templates/accounts/email/activacao.txt`
- Modificar: `apps/accounts/management/commands/popular_bd.py`
- Criar: `apps/accounts/tests/test_email_activation.py`

**Interfaces:**
- Produz: `GET /accounts/activar/<uuid>/` → activa conta
- Produz: `GET /accounts/reenviar-activacao/` → formulário de reenvio
- Produz: `POST /accounts/reenviar-activacao/` → reenvia email

- [ ] **Passo 1: Escrever os testes para activação de email**

Criar `apps/accounts/tests/test_email_activation.py`:

```python
"""Testes para o fluxo de confirmação de email por token."""

import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


def _criar_user_inactivo(email='novo@escola.pt'):
    """Cria utilizador inactivo directamente (sem passar pelo formulário)."""
    user = User.objects.create_user(
        email=email, password='passe123',
        nome='Novo', curso='CT', ano_letivo='12',
        instituicao='Escola Teste',
    )
    User.objects.filter(pk=user.pk).update(is_active=False)
    user.refresh_from_db()
    return user


class EmailActivationTokenModelTestes(TestCase):

    def test_token_criado_com_uuid_unico(self):
        """Cada token tem um UUID diferente."""
        from apps.accounts.models import EmailActivationToken
        user = _criar_user_inactivo()
        t1 = EmailActivationToken.objects.create(user=user)
        t2 = EmailActivationToken.objects.create(user=user)
        self.assertNotEqual(t1.token, t2.token)

    def test_token_nao_expirado_dentro_de_24h(self):
        """Token criado agora não está expirado."""
        from apps.accounts.models import EmailActivationToken
        user = _criar_user_inactivo()
        token = EmailActivationToken.objects.create(user=user)
        self.assertFalse(token.esta_expirado())

    def test_token_expirado_apos_24h(self):
        """Token com criado_em há mais de 24h está expirado."""
        from apps.accounts.models import EmailActivationToken
        user = _criar_user_inactivo()
        token = EmailActivationToken.objects.create(user=user)
        EmailActivationToken.objects.filter(pk=token.pk).update(
            criado_em=timezone.now() - timedelta(hours=25)
        )
        token.refresh_from_db()
        self.assertTrue(token.esta_expirado())


class ActivarContaViewTestes(TestCase):

    def _criar_token(self, email='activar@escola.pt'):
        from apps.accounts.models import EmailActivationToken
        user = _criar_user_inactivo(email)
        token = EmailActivationToken.objects.create(user=user)
        return user, token

    def test_activacao_com_token_valido(self):
        """Token válido activa a conta e marca o token como utilizado."""
        from apps.accounts.models import EmailActivationToken
        user, token = self._criar_token()

        url = reverse('accounts:activar_conta', kwargs={'token': str(token.token)})
        resposta = self.client.get(url)

        user.refresh_from_db()
        token.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(token.utilizado)
        self.assertRedirects(resposta, reverse('accounts:login'))

    def test_activacao_com_token_invalido(self):
        """UUID inválido redireciona para login com mensagem de erro."""
        url = reverse('accounts:activar_conta', kwargs={'token': str(uuid.uuid4())})
        resposta = self.client.get(url)
        self.assertRedirects(resposta, reverse('accounts:login'))

    def test_activacao_com_token_ja_utilizado(self):
        """Token já utilizado não reactiva conta (não causa erro)."""
        from apps.accounts.models import EmailActivationToken
        user, token = self._criar_token()
        token.utilizado = True
        token.save()

        url = reverse('accounts:activar_conta', kwargs={'token': str(token.token)})
        self.client.get(url)  # não deve levantar excepção

    def test_activacao_com_token_expirado(self):
        """Token expirado não activa a conta."""
        from apps.accounts.models import EmailActivationToken
        user, token = self._criar_token()
        EmailActivationToken.objects.filter(pk=token.pk).update(
            criado_em=timezone.now() - timedelta(hours=25)
        )

        url = reverse('accounts:activar_conta', kwargs={'token': str(token.token)})
        self.client.get(url)

        user.refresh_from_db()
        self.assertFalse(user.is_active)


class RegistoComEmailTestes(TestCase):

    def test_registo_cria_conta_inactiva(self):
        """Após registo, conta fica inactiva até confirmar email."""
        dados = {
            'nome': 'Ana Teste',
            'curso': 'CT',
            'ano_letivo': '12',
            'instituicao': 'Escola Teste',
            'email': 'ana@escola.pt',
            'password1': 'SenhaSegura123!',
            'password2': 'SenhaSegura123!',
        }
        self.client.post(reverse('accounts:registo'), dados)
        user = User.objects.get(email='ana@escola.pt')
        self.assertFalse(user.is_active)

    def test_registo_envia_email_de_activacao(self):
        """Após registo, é enviado um email de activação."""
        dados = {
            'nome': 'Ana Teste',
            'curso': 'CT',
            'ano_letivo': '12',
            'instituicao': 'Escola Teste',
            'email': 'ana@escola.pt',
            'password1': 'SenhaSegura123!',
            'password2': 'SenhaSegura123!',
        }
        self.client.post(reverse('accounts:registo'), dados)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('ana@escola.pt', mail.outbox[0].to)

    def test_login_com_conta_inactiva_mostra_mensagem(self):
        """Tentativa de login com conta não confirmada mostra mensagem útil."""
        _criar_user_inactivo('bloqueado@escola.pt')
        dados = {'email': 'bloqueado@escola.pt', 'password': 'passe123'}
        resposta = self.client.post(reverse('accounts:login'), dados)
        self.assertContains(resposta, 'activ', status_code=200)
```

- [ ] **Passo 2: Correr os testes para confirmar que falham**

```bash
python manage.py test apps.accounts.tests.test_email_activation --verbosity=2
```

Resultado esperado: `ImportError` ou `AttributeError` — `EmailActivationToken` não existe ainda.

- [ ] **Passo 3: Adicionar `EmailActivationToken` ao modelo em `apps/accounts/models.py`**

Adicionar no fim de `apps/accounts/models.py`, após a classe `User`:

```python
import uuid as _uuid

from django.conf import settings as _settings
from django.utils import timezone as _timezone
from datetime import timedelta as _timedelta


class EmailActivationToken(models.Model):
    """
    Token único enviado por email para activar a conta de um novo aluno.
    Válido por 24 horas após criação. Pode ser utilizado apenas uma vez.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activation_tokens",
        verbose_name="Utilizador",
    )
    token = models.UUIDField(
        default=_uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Token",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    utilizado = models.BooleanField(default=False, verbose_name="Utilizado")

    class Meta:
        verbose_name        = "Token de activação"
        verbose_name_plural = "Tokens de activação"

    def esta_expirado(self) -> bool:
        """Devolve True se o token tiver mais de 24 horas."""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.criado_em + timedelta(hours=24)

    def __str__(self):
        return f"Token de {self.user.email}"
```

Nota: o `import uuid` e `from django.conf import settings` já devem estar presentes no topo do ficheiro; se não estiverem, adicionar:
```python
import uuid as _uuid
```

- [ ] **Passo 4: Criar e aplicar a migração**

```bash
python manage.py makemigrations accounts --name="add_emailactivationtoken"
python manage.py migrate
```

Resultado esperado: nova migração em `apps/accounts/migrations/` e `OK` no migrate.

- [ ] **Passo 5: Alterar `UserRegistrationForm.save()` para criar conta inactiva**

Em `apps/accounts/forms.py`, localizar o método `save()` da classe `UserRegistrationForm` (~linha 55) e alterar:

```python
# ANTES
def save(self, commit=True):
    """Cria o utilizador com a senha encriptada."""
    user = super().save(commit=False)
    user.set_password(self.cleaned_data["password1"])
    user.is_active = True
    if commit:
        user.save()
    return user

# DEPOIS
def save(self, commit=True):
    """Cria o utilizador com a senha encriptada. Conta inactiva até confirmação de email."""
    user = super().save(commit=False)
    user.set_password(self.cleaned_data["password1"])
    user.is_active = False  # activada após confirmação de email
    if commit:
        user.save()
    return user
```

- [ ] **Passo 6: Atualizar `LoginForm` para mensagem mais útil quando conta inactiva**

Em `apps/accounts/forms.py`, dentro de `LoginForm.clean()`, localizar:
```python
if not user.is_active:
    raise forms.ValidationError("Esta conta está desativada.")
```
E substituir por:
```python
if not user.is_active:
    raise forms.ValidationError(
        "Esta conta ainda não está activa. "
        "Verifica o teu email e clica no link de activação. "
        "Se não recebeste o email, podes pedir um novo na página de login."
    )
```

- [ ] **Passo 7: Adicionar função auxiliar de envio de email de activação em `apps/accounts/views.py`**

Adicionar no início de `views.py`, após os imports existentes:

```python
# adicionar aos imports do topo
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
```

Adicionar a função auxiliar antes das views:

```python
def _enviar_email_activacao(user, request):
    """
    Cria um novo token de activação e envia o email de confirmação ao utilizador.
    Chamada após o registo e no reenvio de activação.
    """
    from .models import EmailActivationToken
    token = EmailActivationToken.objects.create(user=user)
    url_activacao = request.build_absolute_uri(
        reverse("accounts:activar_conta", kwargs={"token": str(token.token)})
    )
    contexto = {"nome": user.nome, "url_activacao": url_activacao}

    corpo_html  = render_to_string("accounts/email/activacao.html", contexto)
    corpo_texto = render_to_string("accounts/email/activacao.txt", contexto)

    send_mail(
        subject="Studia — Activa a tua conta",
        message=corpo_texto,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@studia.pt"),
        recipient_list=[user.email],
        html_message=corpo_html,
        fail_silently=False,
    )
```

Adicionar também o import `reverse`:
```python
from django.urls import reverse
```

- [ ] **Passo 8: Actualizar `registro_view` para enviar email após registo**

Em `apps/accounts/views.py`, substituir `registro_view`:

```python
def registro_view(request):
    """
    Registo de novos alunos.
    Após registo bem-sucedido, cria token de activação e envia email de confirmação.
    A conta fica inactiva até o aluno clicar no link do email.
    """
    if request.user.is_authenticated:
        return redirect("resources:lista")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                _enviar_email_activacao(user, request)
                messages.success(
                    request,
                    "Conta criada! Enviámos um email para "
                    f"<strong>{user.email}</strong> com o link de activação.",
                )
                return redirect("accounts:activacao_pendente")
            except IntegrityError:
                form.add_error("email", "Este email já está registado.")
                messages.error(request, "Corrija os erros abaixo.")
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = UserRegistrationForm()

    import json
    return render(request, "accounts/registo.html", {
        "form": form,
        "dominio_instituicao_json": json.dumps(DOMINIO_PARA_INSTITUICAO, ensure_ascii=False),
    })
```

- [ ] **Passo 9: Adicionar as novas views de activação em `apps/accounts/views.py`**

Adicionar após `registro_view`:

```python
# ------------------------------------------------------------------ #
#  ACTIVAÇÃO DE CONTA POR EMAIL                                        #
# ------------------------------------------------------------------ #

def activacao_pendente_view(request):
    """Página informativa após registo — pede ao aluno para verificar o email."""
    return render(request, "accounts/activacao_pendente.html")


def activar_conta_view(request, token):
    """
    Activa a conta do aluno quando este clica no link do email.
    Verifica se o token é válido (existe, não foi utilizado, não expirou).
    """
    from .models import EmailActivationToken

    try:
        token_obj = EmailActivationToken.objects.select_related("user").get(
            token=token, utilizado=False
        )
    except EmailActivationToken.DoesNotExist:
        messages.error(request, "Link de activação inválido ou já utilizado.")
        return redirect("accounts:login")

    if token_obj.esta_expirado():
        messages.warning(
            request,
            "O link de activação expirou (válido 24h). "
            "Pede um novo abaixo.",
        )
        return redirect("accounts:reenviar_activacao")

    user = token_obj.user
    user.is_active = True
    user.save(update_fields=["is_active"])
    token_obj.utilizado = True
    token_obj.save(update_fields=["utilizado"])

    messages.success(request, "Conta activada com sucesso! Podes iniciar sessão.")
    return redirect("accounts:login")


def reenviar_activacao_view(request):
    """
    Permite ao aluno pedir um novo email de activação (se o anterior expirou).
    """
    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()
        try:
            user = User.objects.get(email=email, is_active=False)
            _enviar_email_activacao(user, request)
            messages.success(
                request,
                f"Novo email de activação enviado para <strong>{email}</strong>.",
            )
            return redirect("accounts:activacao_pendente")
        except User.DoesNotExist:
            # Mensagem genérica para não revelar se o email existe
            messages.info(
                request,
                "Se este email pertencer a uma conta inactiva, "
                "receberás um novo link em breve.",
            )

    return render(request, "accounts/reenviar_activacao.html")
```

- [ ] **Passo 10: Registar os novos URLs em `apps/accounts/urls.py`**

```python
# DEPOIS — ficheiro completo
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Registo de novos alunos
    path("registo/", views.registro_view, name="registo"),

    # Activação de conta por email
    path("activar/<uuid:token>/", views.activar_conta_view, name="activar_conta"),
    path("activacao-pendente/", views.activacao_pendente_view, name="activacao_pendente"),
    path("reenviar-activacao/", views.reenviar_activacao_view, name="reenviar_activacao"),

    # Login / Logout
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Perfil do aluno (próprio)
    path("perfil/", views.perfil_view, name="perfil"),
    path("perfil/editar/", views.editar_perfil_view, name="editar_perfil"),
    path("perfil/apagar/", views.apagar_conta_view, name="apagar_conta"),

    # Perfil público de outro utilizador
    path("utilizador/<int:pk>/", views.perfil_publico_view, name="perfil_publico"),
]
```

- [ ] **Passo 11: Criar o template de activação pendente**

Criar `apps/accounts/templates/accounts/activacao_pendente.html`:

```html
{% extends 'base.html' %}
{% block title %}Verifica o teu email — Studia{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card text-center">
      <div class="card-body p-5">
        <div class="mb-4">
          <i class="bi bi-envelope-check" style="font-size:3.5rem;color:var(--st-blue);"></i>
        </div>
        <h4 class="fw-bold mb-3">Verifica o teu email</h4>
        <p class="text-muted mb-4">
          Enviámos um link de activação para o teu email institucional.<br>
          Clica no link para activar a tua conta no Studia.
        </p>
        <p class="text-muted mb-4" style="font-size:.875rem;">
          O link é válido durante <strong>24 horas</strong>.<br>
          Não encontras o email? Verifica a pasta de spam.
        </p>
        <hr>
        <p class="mb-3" style="font-size:.875rem;">
          O link expirou ou não chegou?
        </p>
        <a href="{% url 'accounts:reenviar_activacao' %}" class="btn btn-outline-primary">
          <i class="bi bi-arrow-repeat me-1"></i>Pedir novo link
        </a>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Passo 12: Criar o template de reenvio de activação**

Criar `apps/accounts/templates/accounts/reenviar_activacao.html`:

```html
{% extends 'base.html' %}
{% block title %}Reenviar activação — Studia{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-5">
    <div class="card st-auth-card">
      <div class="card-body">
        <h5 class="fw-bold mb-1">Pedir novo link de activação</h5>
        <p class="text-muted mb-4" style="font-size:.875rem;">
          Introduz o teu email institucional e enviaremos um novo link.
        </p>

        {% if messages %}
        {% for msg in messages %}
        <div class="alert alert-{{ msg.tags }} mb-3">{{ msg|safe }}</div>
        {% endfor %}
        {% endif %}

        <form method="post">
          {% csrf_token %}
          <div class="mb-3">
            <label class="form-label">Email institucional</label>
            <input type="email" name="email" class="form-control"
                   placeholder="tu@escola.pt" required>
          </div>
          <button type="submit" class="btn btn-primary w-100">
            <i class="bi bi-send me-1"></i>Enviar novo link
          </button>
        </form>
        <div class="text-center mt-3">
          <a href="{% url 'accounts:login' %}" class="text-muted" style="font-size:.875rem;">
            Voltar ao login
          </a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Passo 13: Criar o template HTML do email**

Criar directório `apps/accounts/templates/accounts/email/` e o ficheiro `activacao.html`:

```html
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Activa a tua conta no Studia</title>
</head>
<body style="margin:0;padding:0;background:#f5f7fa;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fa;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.07);">
          <!-- Cabeçalho -->
          <tr>
            <td style="background:#0056d2;padding:28px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:800;letter-spacing:-.04em;">
                Studia<span style="color:#4285f4;">.</span>
              </h1>
            </td>
          </tr>
          <!-- Corpo -->
          <tr>
            <td style="padding:40px;">
              <h2 style="margin:0 0 16px;color:#1a1a2e;font-size:20px;font-weight:700;">
                Activa a tua conta
              </h2>
              <p style="margin:0 0 24px;color:#5f6880;font-size:15px;line-height:1.6;">
                Olá <strong>{{ nome }}</strong>,<br><br>
                Obrigado por te registares no Studia! Para activares a tua conta
                e começares a partilhar recursos, clica no botão abaixo.
              </p>
              <!-- Botão de activação -->
              <table cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <a href="{{ url_activacao }}"
                       style="display:inline-block;background:#0056d2;color:#ffffff;
                              text-decoration:none;padding:14px 36px;
                              border-radius:8px;font-size:15px;font-weight:700;">
                      Activar conta
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:28px 0 0;color:#8d95a8;font-size:13px;line-height:1.6;">
                Este link é válido durante <strong>24 horas</strong>.<br>
                Se não criaste esta conta no Studia, podes ignorar este email em segurança.
              </p>
              <p style="margin:12px 0 0;color:#8d95a8;font-size:12px;word-break:break-all;">
                Se o botão não funcionar, copia este endereço para o teu browser:<br>
                <a href="{{ url_activacao }}" style="color:#0056d2;">{{ url_activacao }}</a>
              </p>
            </td>
          </tr>
          <!-- Rodapé -->
          <tr>
            <td style="background:#f5f7fa;padding:16px 40px;text-align:center;
                       border-top:1px solid #dde3ee;">
              <p style="margin:0;color:#8d95a8;font-size:12px;">
                © 2026 Studia · Plataforma de recursos escolares para o ensino secundário português
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

- [ ] **Passo 14: Criar a versão texto simples do email**

Criar `apps/accounts/templates/accounts/email/activacao.txt`:

```
Studia — Activa a tua conta
============================

Olá {{ nome }},

Obrigado por te registares no Studia!

Para activares a tua conta, acede ao seguinte endereço:

{{ url_activacao }}

Este link é válido durante 24 horas.

Se não criaste esta conta, podes ignorar este email.

---
Studia · Plataforma de recursos escolares
```

- [ ] **Passo 15: Actualizar o seed para criar utilizadores activos**

Em `apps/accounts/management/commands/popular_bd.py`, nos blocos de criação de utilizadores, adicionar `is_active=True` a cada `create_user` (ou usar `update` logo após a criação). Os utilizadores do seed devem estar activos imediatamente, sem passar pelo fluxo de email.

Localizar e actualizar a criação do utilizador `ana` (e todos os outros alunos) com a mesma abordagem:

O `UserManager.create_user` actual não aceita `is_active` como parâmetro — usar `update()` logo após cada `create_user`:

```python
# Padrão a aplicar a TODOS os create_user no seed:
ana = User.objects.create_user(
    email="ana@escola.pt",
    password="passe123",
    nome="Ana Silva",
    curso="TGPSI",
    ano_letivo="12",
    instituicao="AE Carlos Amarante — Braga",
)
User.objects.filter(pk=ana.pk).update(is_active=True)
ana.refresh_from_db()
```

Aplicar a mesma linha `User.objects.filter(pk=...).update(is_active=True)` a todos os alunos criados com `create_user` no seed.

**Nota:** os utilizadores criados com `create_superuser` já têm `is_active=True` definido internamente — não precisam desta linha adicional.

- [ ] **Passo 16: Correr todos os testes de activação**

```bash
python manage.py test apps.accounts.tests.test_email_activation --verbosity=2
```

Resultado esperado: todos os testes PASS.

- [ ] **Passo 17: Correr todos os testes da app accounts para detectar regressões**

```bash
python manage.py test apps.accounts --verbosity=2
```

Se algum teste falhar porque `user.is_active` é agora `False` por defeito:
- Procurar utilizações de `create_user` nos testes: `grep -r "create_user" apps/accounts/tests/`
- Adicionar `User.objects.filter(pk=user.pk).update(is_active=True)` após cada criação nos testes afectados.

- [ ] **Passo 18: Adicionar configuração de email de desenvolvimento no settings (temporário)**

Confirmar que `pap/settings.py` tem (ou adicionar antes da Tarefa 5):

```python
# Email — apenas em desenvolvimento (imprime no terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

- [ ] **Passo 19: Testar o fluxo completo no browser**

```bash
python manage.py runserver
```

1. Abrir `http://127.0.0.1:8000/accounts/registo/` e registar uma conta nova.
2. Verificar que redireccionou para a página "Verifica o teu email".
3. Verificar no terminal do servidor o email impresso (com o link de activação).
4. Copiar o link e abrir no browser.
5. Confirmar mensagem "Conta activada com sucesso!".
6. Fazer login com as credenciais.

---

### Tarefa 5: Configuração de Produção para Railway

**Ficheiros:**
- Substituir: `pap/settings.py` → `pap/settings/` (directório)
- Criar: `pap/settings/__init__.py`, `base.py`, `development.py`, `production.py`
- Modificar: `manage.py`, `pap/wsgi.py`, `pap/asgi.py`
- Criar: `requirements.txt`, `Procfile`, `railway.toml`, `.env.example`

**Interfaces:** Sem interfaces Python — configuração de infra-estrutura.

- [ ] **Passo 1: Criar o directório de settings**

```bash
mkdir -p /home/livia/livia/pap_studia/pap/settings
```

- [ ] **Passo 2: Criar `pap/settings/base.py`**

Conteúdo: extraído de `pap/settings.py` actual, removendo tudo o que é ambiente-específico.

```python
"""
Configurações base do Studia — comuns a todos os ambientes.
Não usar directamente; usar development.py ou production.py.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = None  # obrigatoriamente definido em development.py e production.py

DEBUG = False  # desactivado por defeito; development.py sobrepõe para True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.resources',
    'apps.favorites',
    'apps.comments',
    'apps.reports',
    'apps.notifications',
    'apps.core',
    'crispy_forms',
    'crispy_bootstrap5',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # servir estáticos em produção
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pap.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pap.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Europe/Lisbon'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL          = 'accounts:login'
LOGIN_REDIRECT_URL = 'resources:lista'
LOGOUT_REDIRECT_URL = 'accounts:login'

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG:   'secondary',
    message_constants.INFO:    'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR:   'danger',
}

DEFAULT_FROM_EMAIL = 'noreply@studia.pt'
```

- [ ] **Passo 3: Criar `pap/settings/development.py`**

```python
"""
Configurações de desenvolvimento local.
Usa SQLite, imprime emails no terminal, DEBUG activo.
"""

from .base import *

DEBUG = True

SECRET_KEY = 'django-insecure-n4rnloeo7mc4moy^x9mwyj__5n$b@mn-2)y-xi8o@#qqoz3c4g'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Emails impressos no terminal — sem envio real
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

- [ ] **Passo 4: Criar `pap/settings/production.py`**

```python
"""
Configurações de produção (Railway).
Todas as variáveis sensíveis vêm de variáveis de ambiente.
"""

import os
import dj_database_url
from .base import *

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Base de dados PostgreSQL via DATABASE_URL (Railway injeta automaticamente)
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Email via Gmail SMTP
EMAIL_BACKEND    = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST       = 'smtp.gmail.com'
EMAIL_PORT       = 587
EMAIL_USE_TLS    = True
EMAIL_HOST_USER  = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@studia.pt')

# Moderação por IA (stubs activos enquanto variáveis não estiverem definidas)
GOOGLE_CLOUD_CREDENTIALS = os.environ.get('GOOGLE_CLOUD_CREDENTIALS', '')
PERSPECTIVE_API_KEY      = os.environ.get('PERSPECTIVE_API_KEY', '')

# Segurança HTTPS
SECURE_SSL_REDIRECT         = True
SESSION_COOKIE_SECURE       = True
CSRF_COOKIE_SECURE          = True
SECURE_HSTS_SECONDS         = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

- [ ] **Passo 5: Criar `pap/settings/__init__.py` vazio**

```python
# Este ficheiro existe para que pap/settings/ seja reconhecido como package Python.
```

- [ ] **Passo 6: Actualizar `manage.py`**

Substituir a linha `os.environ.setdefault(...)`:

```python
# ANTES
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pap.settings')

# DEPOIS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pap.settings.development')
```

- [ ] **Passo 7: Actualizar `pap/wsgi.py`**

```python
# ANTES
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pap.settings')

# DEPOIS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pap.settings.production')
```

- [ ] **Passo 8: Actualizar `pap/asgi.py`**

```python
# ANTES
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pap.settings')

# DEPOIS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pap.settings.production')
```

- [ ] **Passo 9: Eliminar o `pap/settings.py` original**

```bash
rm /home/livia/livia/pap_studia/pap/settings.py
```

- [ ] **Passo 10: Confirmar que o servidor inicia correctamente**

```bash
cd /home/livia/livia/pap_studia
python manage.py check
python manage.py runserver
```

Resultado esperado: `System check identified no issues (0 silenced).`

- [ ] **Passo 11: Preencher `requirements.txt`**

```
django>=5.2,<6.0
django-crispy-forms
crispy-bootstrap5
gunicorn
whitenoise
psycopg2-binary
dj-database-url
pillow
imagehash
pdfminer.six
```

- [ ] **Passo 12: Criar `Procfile`**

```
web: gunicorn pap.wsgi --log-file -
```

- [ ] **Passo 13: Criar `railway.toml`**

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn pap.wsgi --log-file -"
healthcheckPath = "/"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

- [ ] **Passo 14: Criar `.env.example`**

```
# Copiar para .env (nunca commitar .env)

# Segurança
SECRET_KEY=substitui-por-uma-chave-segura-gerada-com-django-get-random-secret-key

# Servidor
ALLOWED_HOSTS=studia.pt,www.studia.pt
DEBUG=False

# Base de dados (Railway injeta DATABASE_URL automaticamente)
DATABASE_URL=postgresql://usuario:senha@host:5432/studia

# Email Gmail (usar App Password — não a senha da conta)
EMAIL_HOST_USER=tua-conta@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx
DEFAULT_FROM_EMAIL=noreply@studia.pt

# IA — deixar em branco para usar stubs (sem chamadas a APIs externas)
GOOGLE_CLOUD_CREDENTIALS=
PERSPECTIVE_API_KEY=
```

- [ ] **Passo 15: Correr todos os testes do projecto**

```bash
python manage.py test --verbosity=2
```

Resultado esperado: todos os testes PASS com o novo módulo de settings.

---

### Tarefa 6: Páginas de Erro Personalizadas (404 e 500)

**Ficheiros:**
- Criar: `templates/404.html`
- Criar: `templates/500.html`
- Modificar: `pap/urls.py`

**Interfaces:** Sem interfaces Python — activas automaticamente com `DEBUG=False`.

- [ ] **Passo 1: Criar `templates/404.html`**

```html
{% extends 'base.html' %}
{% block title %}Página não encontrada — Studia{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6 text-center">
    <div class="py-5">
      <div style="font-size:6rem;font-weight:800;color:var(--st-blue);letter-spacing:-.04em;line-height:1;">
        404
      </div>
      <h2 class="fw-bold mt-3 mb-2">Página não encontrada</h2>
      <p class="text-muted mb-4">
        A página que procuras não existe ou foi movida.<br>
        Verifica o endereço ou volta à lista de recursos.
      </p>
      <a href="{% url 'resources:lista' %}" class="btn btn-primary">
        <i class="bi bi-arrow-left me-1"></i>Ver recursos
      </a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Passo 2: Criar `templates/500.html`**

```html
{% extends 'base.html' %}
{% block title %}Erro interno — Studia{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6 text-center">
    <div class="py-5">
      <div style="font-size:6rem;font-weight:800;color:var(--st-danger);letter-spacing:-.04em;line-height:1;">
        500
      </div>
      <h2 class="fw-bold mt-3 mb-2">Algo correu mal</h2>
      <p class="text-muted mb-4">
        Ocorreu um erro interno no servidor. Já fomos notificados.<br>
        Tenta novamente em alguns minutos.
      </p>
      <a href="{% url 'resources:lista' %}" class="btn btn-primary">
        <i class="bi bi-arrow-left me-1"></i>Voltar ao início
      </a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Passo 3: Registar os handlers em `pap/urls.py`**

Adicionar ao fim de `pap/urls.py`:

```python
# Handlers de erro para produção (DEBUG=False)
# Django usa estes handlers automaticamente — não precisam de estar em urlpatterns
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
```

Na prática o Django já usa estes por defeito, mas registá-los aqui clarifica a intenção. Para usar os templates personalizados, o Django procura `404.html` e `500.html` nos `TEMPLATES['DIRS']` quando `DEBUG=False` — o directório `templates/` já está configurado como `DIRS` nas settings.

- [ ] **Passo 4: Verificar as páginas de erro localmente**

Como `DEBUG=True` em desenvolvimento não mostra as páginas personalizadas, testar forçando um 404:

```python
# Criar vista temporária em pap/urls.py para testar (apagar depois):
from django.views.defaults import page_not_found
urlpatterns += [
    path('test-404/', lambda r: page_not_found(r, None), name='test_404'),
]
```

Abrir `http://127.0.0.1:8000/test-404/` e confirmar que mostra a página personalizada.
Apagar a vista temporária após verificação.

- [ ] **Passo 5: Correr todos os testes do projecto**

```bash
python manage.py test --verbosity=2
```

Resultado esperado: todos os testes PASS.

---

## Verificação Final

- [ ] Correr `python manage.py check --deploy` (com `DJANGO_SETTINGS_MODULE=pap.settings.production` e as variáveis de ambiente de exemplo definidas) — sem erros críticos.
- [ ] Correr todos os testes: `python manage.py test --verbosity=2` — todos PASS.
- [ ] Verificar visualmente no browser: layout, autocomplete, registo + activação por email, páginas de erro.
