# Design: Melhorias Completas do Studia
**Data:** 2026-06-25  
**Projecto:** pap_studia  
**Abordagem:** Fase 1 (base sólida) + Fase 2 (IA com stubs)

---

## Contexto

O Studia é uma plataforma Django 5.2 de partilha de recursos escolares entre alunos do ensino secundário português. O projecto serve como PAP (Prova de Aptidão Profissional) do curso TGPSI. A base de código já tem: autenticação por email, upload de ficheiros, favoritos, comentários, sistema de reports e um seed de dados.

---

## Fase 1 — Base Sólida e Deployável

### 1. Correcção de Espaçamentos

**Problema 1 — Stats block (`resource_detail.html`):**  
O bloco de estatísticas usa `col-4` fixo com labels em `text-transform: uppercase` e `letter-spacing: .05em`. Com esse espaçamento, palavras como "COMENTÁRIOS" quebram a meio ("COMENT/ÁRIOS") em ecrãs médios.  
**Solução:** Mudar `.st-stat-label` para remover `letter-spacing` e adicionar `overflow-wrap: break-word`. Nas colunas do bloco de stats, usar `col-12 col-sm-4` para dispositivos móveis.

**Problema 2 — Perfil (`perfil.html`):**  
O layout `d-flex justify-content-between` com o valor do campo "Curso" (ex: "Técnico de Gestão e Programação de Sistemas Informáticos") colapsa porque o valor longo não tem restrição de largura. Aparece sem espaço entre label e valor.  
**Solução:** Substituir o `d-flex justify-content-between` por uma grelha Bootstrap de 2 colunas (`col-5` label + `col-7` valor com `text-end` e `word-break: break-word`).

**Problema 3 — Cartão de recurso (`lista.html`):**  
O nome do curso sem truncagem faz o cartão crescer verticalmente de forma inconsistente.  
**Solução:** Adicionar `text-truncate` à linha do curso no cartão, com `title` para mostrar o nome completo em hover.

### 2. Remoção de Código Morto

- **Eliminar `apps/core/management/commands/popular_bd.py`:** seed antiga e incompatível com o modelo actual (usa `tipo_arquivo="LINK"` inexistente e strings de curso em vez de códigos como `"CT"`). O comando `popular_bd` activo e correcto está em `apps/accounts/management/commands/popular_bd.py`.
- **Manter `apps/notifications/`:** a app está incompleta mas pode ser expandida no futuro.
- **Eliminar código morto em `apps/core/`:** o `management/` inteiro fica vazio após remover o popular_bd antigo; apagar a pasta.

### 3. Autocomplete de Pesquisa por Relevância

**Estado actual:** datalist HTML5 com sugestões estáticas ordenadas alfabeticamente.

**Nova arquitectura:**
- Novo endpoint: `GET /resources/autocomplete/?q=<termo>` — view `autocomplete_recursos_view`.
- Pesquisa normalizada (sem acentos) nos campos `disciplina` e `professor` dos recursos.
- Ordenação por contagem decrescente (disciplinas/professores com mais recursos aparecem primeiro).
- Devolve JSON: `{"sugestoes": ["Matemática A", "Física e Química A", ...]}` com máximo 8 entradas.
- Frontend: substituir o `<datalist>` por um dropdown custom inline (CSS puro + JS minimal sem dependências), activado com ≥ 2 caracteres.
- O formulário continua a funcionar normalmente sem JS (degradação graciosa).

### 4. Confirmação de Email por Token

**Modelo novo:** `EmailActivationToken` em `apps/accounts/models.py`:
```
EmailActivationToken:
  user       → ForeignKey(User, on_delete=CASCADE)
  token      → UUIDField(default=uuid4, unique=True)
  criado_em  → DateTimeField(auto_now_add=True)
  utilizado  → BooleanField(default=False)
```

**Fluxo de registo:**
1. `create_user` cria conta com `is_active=False`.
2. Cria `EmailActivationToken` e envia email com link de activação.
3. Utilizador clica em `GET /accounts/activar/<uuid>/` → conta activada, token marcado como utilizado.
4. Tokens expiram ao fim de 24 horas (verificado na view de activação).
5. Vista `GET /accounts/reenviar-activacao/` permite pedir novo token.

**Alterações ao `UserManager.create_user`:** `is_active=False` por defeito.  
**`create_superuser`:** mantém `is_active=True` explicitamente.  
**Seed `popular_bd`:** `create_user` passa a aceitar `is_active=True` como parâmetro opcional. A seed chama `User.objects.create_user(..., is_active=True)` para todos os utilizadores de teste, saltando o fluxo de email.

**Configuração SMTP (Gmail):**
```
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')  # App Password do Gmail
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@studia.pt')
```
Em desenvolvimento: `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`.

**Template do email:** HTML responsivo com design Studia (azul + branco), com versão texto simples como fallback.

### 5. Configuração de Produção (Railway)

**Estrutura de settings dividida:**
```
pap/settings/
  __init__.py
  base.py         ← configurações comuns a todos os ambientes
  development.py  ← DEBUG=True, SQLite, console email
  production.py   ← DEBUG=False, PostgreSQL, Gmail SMTP, WhiteNoise
```
`manage.py` usa `pap.settings.development` por defeito.  
Railway define a variável `DJANGO_SETTINGS_MODULE=pap.settings.production`.

**Ficheiros novos para Railway:**
- `requirements.txt` — preenchido com todas as dependências.
- `Procfile` — `web: gunicorn pap.wsgi --log-file -`.
- `railway.toml` — build e start command.
- `.env.example` — template de todas as variáveis de ambiente.

**Variáveis de ambiente de produção:**
```
SECRET_KEY=<chave gerada>
DATABASE_URL=<postgresql://...>
ALLOWED_HOSTS=<dominio.com>
EMAIL_HOST_USER=<conta@gmail.com>
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=noreply@studia.pt
GOOGLE_CLOUD_CREDENTIALS=  # vazio até activar SafeSearch
PERSPECTIVE_API_KEY=       # vazio até activar Perspective
```

### 6. Páginas de Erro Personalizadas

- `templates/404.html` — "Página não encontrada" com design Studia, link para a lista de recursos.
- `templates/500.html` — "Erro interno" com design Studia, link para a lista.
- `pap/urls.py` — `handler404` e `handler500` registados.
- Activas automaticamente quando `DEBUG=False`.

---

## Fase 2 — Módulo de IA

### 7. Arquitectura do Módulo de Moderação

Nova app `apps/moderation/`:
```
apps/moderation/
  __init__.py
  apps.py
  auto_report.py      ← cria Reports automáticos
  services/
    __init__.py
    plagiarism.py     ← pHash local (sem API externa)
    safe_image.py     ← Google Cloud Vision SafeSearch (stub por defeito)
    toxic_text.py     ← Perspective API (stub por defeito)
```

Registada em `INSTALLED_APPS` como `'apps.moderation'`.

### 7.1 pHash — Detecção de Plágio

**Biblioteca:** `imagehash` (local, sem API).

**Para imagens (tipo_arquivo="IMG"):**
- Calcula `imagehash.phash(Image.open(caminho))` no momento do upload.
- Compara com os hashes de todos os recursos do tipo IMG existentes.
- Se `diferença_hash < LIMIAR_PLAGIO` (configurável, default 10), chama `criar_report_ia`.

**Para PDFs:**
- Extrai texto com `pdfminer.six`.
- Calcula SHA-256 do texto normalizado (sem espaços/pontuação).
- Compara hash exacto com recursos PDF existentes.
- Se hash igual, chama `criar_report_ia`.

**Para DOCX/PPTX:** hash simples do conteúdo binário do ficheiro.

**Novo campo no modelo `Resource`:**
```python
phash = models.CharField(max_length=64, blank=True, default='')
```

### 7.2 Google Cloud Vision SafeSearch (stub)

```python
# apps/moderation/services/safe_image.py

def verificar_imagem_segura(caminho_ficheiro: str) -> bool:
    """Devolve True se a imagem for segura. False se conteúdo impróprio."""
    if not settings.GOOGLE_CLOUD_CREDENTIALS:
        return True  # stub: assume sempre seguro
    # ... implementação real com google-cloud-vision ...
```

Activada automaticamente quando `GOOGLE_CLOUD_CREDENTIALS` estiver definido.  
Se devolver `False`, chama `criar_report_ia` com `motivo_tipo="improprio"`.

### 7.3 Perspective API — Texto Ofensivo (stub)

```python
# apps/moderation/services/toxic_text.py

def verificar_texto_seguro(texto: str) -> bool:
    """Devolve True se o texto for aceitável. False se ofensivo."""
    if not settings.PERSPECTIVE_API_KEY:
        return True  # stub: assume sempre seguro
    # ... chamada à Perspective API ...
```

Aplicado a:
- Comentários ao serem submetidos (`comments/views.py`).
- Nomes e descrições de recursos no upload.

### 7.4 Reports Automáticos

```python
# apps/moderation/auto_report.py

def criar_report_ia(recurso=None, usuario=None, motivo_tipo: str = "", motivo: str = ""):
    """Cria um Report automático com origem na IA."""
    from apps.reports.models import Report
    Report.objects.create(
        recurso=recurso,
        usuario_denunciado=usuario,
        tipo="IA",
        motivo_tipo=motivo_tipo,
        motivo=motivo,
        status="PENDENTE",
    )
```

**Alteração ao modelo `Report`:** adicionar `"IA"` às escolhas de `tipo`.  
**Painel admin:** filtro por `tipo="IA"` para distinguir reports humanos de automáticos.

### 8. Optimização Mobile Bootstrap

- **Stats block:** `col-12 col-sm-4` em vez de `col-4`.
- **Perfil sidebar:** em mobile (`<md`), a sidebar de perfil aparece primeiro, em coluna única.
- **Cartões da lista:** já usam `row-cols-1 row-cols-md-2 row-cols-lg-3` — correcto.
- **Navbar:** verificar que o toggler e o dropdown funcionam em mobile (já usa Bootstrap 5 — deverá estar OK).
- **Detalhes do recurso:** a coluna lateral passa para baixo em mobile (`col-lg-4` já garante isso).
- **Formulário de filtros:** em mobile, cada filtro ocupa coluna completa (`col-12`) em vez de `col-md-2`.

---

## Fluxo de Dados

```
Upload de recurso
  → validação do formulário
  → save() do Resource
  → [FASE 2] plagiarism.verificar(recurso) → se plágio → criar_report_ia()
  → [FASE 2] safe_image.verificar(recurso) → se impróprio → criar_report_ia()
  → redirect para lista

Submissão de comentário
  → validação do formulário
  → [FASE 2] toxic_text.verificar(texto) → se ofensivo → bloquear + mensagem de erro
  → save() do Comment

Registo de utilizador
  → create_user(is_active=False)
  → criar EmailActivationToken
  → enviar email com link
  → redirect para página "confirma o teu email"

Activação de conta
  → verificar token (existe, não expirado, não usado)
  → is_active=True
  → token.utilizado=True
  → redirect para login com mensagem de sucesso
```

---

## Dependências

**requirements.txt completo (Fase 1 + Fase 2):**
```
django>=5.2,<6.0
crispy-forms
crispy-bootstrap5
gunicorn
whitenoise
psycopg2-binary
dj-database-url
pillow
imagehash
pdfminer.six
python-decouple
```

**Opcionais (activados com variáveis de ambiente, Fase 2):**
```
google-cloud-vision    # SafeSearch
```

---

## Testes

- Testes existentes: mantidos e corrigidos se afectados pelas alterações.
- Novos testes (Fase 1): `test_email_activation.py` em `apps/accounts/tests/`.
- Novos testes (Fase 1): `test_autocomplete.py` em `apps/resources/tests/`.
- Novos testes (Fase 2): `test_moderation.py` em `apps/moderation/tests/`.

---

## Migrações necessárias

1. `accounts/migrations/000X_add_emailactivationtoken.py` — novo modelo.
2. `resources/migrations/000X_add_phash.py` — novo campo `phash`.
3. `reports/migrations/000X_add_tipo_ia.py` — novo valor `"IA"` nas choices.
