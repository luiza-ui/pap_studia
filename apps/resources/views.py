import os

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import smart_str

from apps.comments.forms import CommentForm
from apps.favorites.services import is_favorito
from apps.reports.models import Report

from .forms import ResourceForm
from .models import Resource, normalizar_texto, normalizar_query_pesquisa

User = get_user_model()
from .services import incrementar_download, pode_usuario_fazer_download


# ------------------------------------------------------------------ #
#  LISTA DE RECURSOS                                                   #
# ------------------------------------------------------------------ #

@login_required
def lista_recursos_view(request):
    """
    Lista todos os recursos disponíveis com filtros e ordenação.
    Filtros disponíveis: curso, disciplina, ano letivo, tipo de ficheiro, pesquisa livre.
    Ordenações: mais recentes, mais descarregados, mais guardados.
    """
    recursos = Resource.objects.filter(suspenso=False)

    # Leitura dos parâmetros de filtro do URL
    curso        = request.GET.get("curso",        "").strip()
    instituicao  = request.GET.get("instituicao",  "").strip()
    ano_letivo   = request.GET.get("ano_letivo",   "").strip()
    tipo_arquivo = request.GET.get("tipo_arquivo", "").strip()
    pesquisa     = request.GET.get("q",            "").strip()

    # Aplicação dos filtros estruturados (exactos)
    if curso:
        recursos = recursos.filter(curso__iexact=curso)
    if instituicao:
        recursos = recursos.filter(instituicao__iexact=instituicao)
    if ano_letivo:
        recursos = recursos.filter(ano_letivo=ano_letivo)
    if tipo_arquivo:
        recursos = recursos.filter(tipo_arquivo=tipo_arquivo)

    if pesquisa:
        pesquisa_norm = normalizar_query_pesquisa(pesquisa)
        # Encontrar códigos de cursos cujo label contenha o termo de pesquisa
        codigos_curso = [
            codigo for codigo, label in User.CURSOS
            if pesquisa.lower() in label.lower() or pesquisa.lower() in codigo.lower()
        ]
        curso_q = Q(curso__in=codigos_curso) if codigos_curso else Q()
        recursos = recursos.filter(
            Q(nome_normalizado__icontains=pesquisa_norm)
            | Q(disciplina_normalizada__icontains=pesquisa_norm)
            | Q(professor_normalizado__icontains=pesquisa_norm)
            | curso_q
        )

    # Ordenação com whitelist para segurança
    ordem = request.GET.get("ordem", "-data_upload")
    ordens_validas = {
        "-data_upload":      "-data_upload",
        "data_upload":       "data_upload",
        "-total_downloads":  "-total_downloads",
        "-total_salvos":     "-total_salvos",
    }
    recursos = recursos.order_by(ordens_validas.get(ordem, "-data_upload"))

    # Sugestões para datalist (autocomplete nativo HTML5 — sem dependências JS)
    # Combinamos disciplinas e professores numa lista única de sugestões para
    # o campo de pesquisa, ordenada e sem duplicados.
    sugestoes_pesquisa = sorted(set(
        list(Resource.objects.exclude(disciplina="")
             .values_list("disciplina", flat=True).distinct())
        + [p for p in Resource.objects.exclude(professor="")
              .values_list("professor", flat=True).distinct() if p]
    ))

    return render(request, "resources/lista.html", {
        "recursos": recursos,
        "filtros": {
            "curso": curso, "instituicao": instituicao,
            "ano_letivo": ano_letivo, "tipo_arquivo": tipo_arquivo,
            "q": pesquisa, "ordem": ordem,
        },
        "tipo_arquivo_choices": Resource.TIPO_ARQUIVO_CHOICES,
        "anos_letivos": [("10", "10º Ano"), ("11", "11º Ano"), ("12", "12º Ano")],
        # Lista fixa de cursos (choices do modelo User)
        "cursos_disponiveis": User.CURSOS,
        # Para o select de Instituição: lista de instituições existentes na BD
        "instituicoes_disponiveis": (
            Resource.objects
            .exclude(instituicao="")
            .values_list("instituicao", flat=True)
            .distinct()
            .order_by("instituicao")
        ),
        # Para o datalist da pesquisa livre
        "sugestoes_pesquisa": sugestoes_pesquisa,
    })


# ------------------------------------------------------------------ #
#  DETALHES DO RECURSO                                                 #
# ------------------------------------------------------------------ #

@login_required
def detalhes_recurso_view(request, pk):
    """
    Mostra os detalhes de um recurso, comentários e acções disponíveis.
    Calcula os créditos de download restantes para mostrar na barra lateral.
    """
    recurso    = get_object_or_404(Resource, pk=pk)

    # Recurso suspenso — apenas o dono e staff podem ver os detalhes
    if recurso.suspenso and recurso.usuario != request.user and not request.user.is_staff:
        messages.warning(request, "Este recurso não está disponível.")
        return redirect("resources:lista")

    comentarios = recurso.comentarios.filter(ativo=True)
    ja_favoritado      = is_favorito(request.user, recurso)
    tem_report_pendente = recurso.reports.filter(status="PENDENTE").exists()

    # Créditos calculados em Python para precisão
    user              = request.user
    limite_downloads  = (user.total_uploads * 2) + 1
    creditos_restantes = max(0, limite_downloads - user.total_downloads)

    return render(request, "resources/resource_detail.html", {
        "recurso":             recurso,
        "comentarios":         comentarios,
        "form_comentario":     CommentForm(),
        "ja_favoritado":       ja_favoritado,
        "tem_report_pendente": tem_report_pendente,
        "creditos_restantes":  creditos_restantes,
        "limite_downloads":    limite_downloads,
    })


# ------------------------------------------------------------------ #
#  UPLOAD DE RECURSO                                                   #
# ------------------------------------------------------------------ #

@login_required
def upload_recurso_view(request):
    """
    Permite ao aluno fazer upload de um recurso (ficheiro).
    curso e instituicao são preenchidos automaticamente do perfil.
    """
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            # Verificar toxicidade nos campos de texto antes de guardar
            try:
                from apps.moderation.services.toxic_text import verificar_texto_seguro
                campos_texto = {
                    "nome":       form.cleaned_data.get("nome", ""),
                    "disciplina": form.cleaned_data.get("disciplina", ""),
                    "professor":  form.cleaned_data.get("professor", ""),
                }
                for campo, valor in campos_texto.items():
                    if valor and not verificar_texto_seguro(valor):
                        form.add_error(campo, "Este campo contém linguagem que não é permitida.")
            except Exception:
                pass
            if form.errors:
                messages.error(request, "Corrija os erros do formulário.")
                return render(request, "resources/upload.html", {"form": form})

            recurso             = form.save(commit=False)
            recurso.usuario     = request.user
            recurso.curso       = request.user.curso
            recurso.instituicao = request.user.instituicao
            recurso.save()
            # Moderação após guardar — pode suspender o recurso
            suspenso_por_moderacao = False
            try:
                from apps.moderation.services.plagiarism import verificar_plagio
                from apps.moderation.auto_report import criar_report_ia
                if verificar_plagio(recurso):
                    criar_report_ia(recurso=recurso, motivo_tipo='plagio', motivo='Conteúdo similar a recurso existente detectado automaticamente.')
                    suspenso_por_moderacao = True
            except Exception as _e:
                import logging as _log
                _log.getLogger(__name__).error('Erro na verificação de plágio: %s', _e)
            if recurso.tipo_arquivo == 'IMG' and recurso.arquivo and not suspenso_por_moderacao:
                try:
                    from apps.moderation.services.safe_image import verificar_imagem_segura
                    from apps.moderation.auto_report import criar_report_ia as _criar
                    if not verificar_imagem_segura(recurso.arquivo.path):
                        _criar(recurso=recurso, motivo_tipo='improprio', motivo='Conteúdo impróprio detectado automaticamente.')
                        suspenso_por_moderacao = True
                except Exception as _e:
                    import logging as _log
                    _log.getLogger(__name__).error('Erro SafeSearch: %s', _e)
            if suspenso_por_moderacao:
                messages.warning(request, "O teu recurso foi enviado mas está em revisão por conteúdo duplicado ou impróprio. Ficará invisível até à decisão de um moderador.")
            else:
                messages.success(request, "Recurso enviado com sucesso!")
            return redirect("resources:lista")
        else:
            messages.error(request, "Corrija os erros do formulário.")
    else:
        # Pré-preenche o ano letivo com o do perfil do utilizador
        form = ResourceForm(initial={"ano_letivo": request.user.ano_letivo})

    return render(request, "resources/upload.html", {"form": form})


# ------------------------------------------------------------------ #
#  EDITAR RECURSO                                                      #
# ------------------------------------------------------------------ #

@login_required
def editar_recurso_view(request, pk):
    """
    Permite ao dono editar o seu recurso.
    Bloqueado se o recurso tiver denúncias pendentes.
    curso e instituicao são sempre mantidos do perfil — não são editáveis.
    """
    recurso = get_object_or_404(Resource, pk=pk, usuario=request.user)

    # Bloqueia edição se houver denúncias pendentes
    if recurso.reports.filter(status="PENDENTE").exists():
        messages.error(request, "Não podes editar este recurso enquanto tiver denúncias pendentes.")
        return redirect("resources:detalhes", pk=recurso.pk)

    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES, instance=recurso)
        if form.is_valid():
            # Verificar toxicidade nos campos de texto
            try:
                from apps.moderation.services.toxic_text import verificar_texto_seguro
                campos_texto = {
                    "nome":       form.cleaned_data.get("nome", ""),
                    "disciplina": form.cleaned_data.get("disciplina", ""),
                    "professor":  form.cleaned_data.get("professor", ""),
                }
                for campo, valor in campos_texto.items():
                    if valor and not verificar_texto_seguro(valor):
                        form.add_error(campo, "Este campo contém linguagem que não é permitida.")
            except Exception:
                pass
            if form.errors:
                messages.error(request, "Corrija os erros do formulário.")
                return render(request, "resources/editar.html", {"form": form, "recurso": recurso})

            ficheiro_novo = bool(request.FILES.get("arquivo"))
            recurso_editado             = form.save(commit=False)
            recurso_editado.curso       = recurso.curso
            recurso_editado.instituicao = recurso.instituicao
            recurso_editado.save()

            # Re-moderar se o ficheiro foi substituído
            if ficheiro_novo:
                try:
                    from apps.moderation.services.plagiarism import verificar_plagio
                    from apps.moderation.auto_report import criar_report_ia
                    if verificar_plagio(recurso_editado):
                        criar_report_ia(recurso=recurso_editado, motivo_tipo='plagio', motivo='Conteúdo similar detectado na edição.')
                except Exception as _e:
                    import logging as _log
                    _log.getLogger(__name__).error('Erro plágio (edição): %s', _e)
                if recurso_editado.tipo_arquivo == 'IMG' and recurso_editado.arquivo:
                    try:
                        from apps.moderation.services.safe_image import verificar_imagem_segura
                        from apps.moderation.auto_report import criar_report_ia as _criar
                        if not verificar_imagem_segura(recurso_editado.arquivo.path):
                            _criar(recurso=recurso_editado, motivo_tipo='improprio', motivo='Conteúdo impróprio detectado na edição.')
                    except Exception as _e:
                        import logging as _log
                        _log.getLogger(__name__).error('Erro SafeSearch (edição): %s', _e)

            messages.success(request, "Recurso atualizado com sucesso!")
            return redirect("resources:detalhes", pk=recurso.pk)
        else:
            messages.error(request, "Corrija os erros do formulário.")
    else:
        form = ResourceForm(instance=recurso)

    return render(request, "resources/editar.html", {"form": form, "recurso": recurso})


# ------------------------------------------------------------------ #
#  APAGAR RECURSO                                                      #
# ------------------------------------------------------------------ #

@login_required
def apagar_recurso_view(request, pk):
    """
    Apaga um recurso.
    - O dono pode apagar o seu próprio recurso.
    - Staff/admin pode apagar qualquer recurso.
    """
    if request.user.is_staff:
        recurso = get_object_or_404(Resource, pk=pk)
    else:
        recurso = get_object_or_404(Resource, pk=pk, usuario=request.user)

    if request.method == "POST":
        recurso.delete()
        messages.success(request, "Recurso apagado com sucesso!")
        return redirect("resources:lista")

    return render(request, "resources/apagar.html", {"recurso": recurso})


# ------------------------------------------------------------------ #
#  DOWNLOAD DE RECURSO                                                 #
# ------------------------------------------------------------------ #

@login_required
def download_recurso_view(request, pk):
    """
    Serve o ficheiro para download.
    - Download do próprio recurso: sem consumir créditos nem incrementar contadores.
    - Download de recursos de outros: requer créditos e incrementa contadores.
    """
    recurso          = get_object_or_404(Resource, pk=pk)
    proprio_recurso  = (recurso.usuario == request.user)

    # Bloquear download de recursos suspensos (excepto pelo dono e staff)
    if recurso.suspenso and not proprio_recurso and not request.user.is_staff:
        messages.error(request, "Este recurso não está disponível para download.")
        return redirect("resources:lista")

    # Verificar créditos (só para recursos de outros alunos)
    if not proprio_recurso and not pode_usuario_fazer_download(request.user):
        messages.error(
            request,
            "Não tens créditos suficientes. Faz upload de um recurso para ganhar mais downloads.",
        )
        return redirect("resources:detalhes", pk=pk)

    # Verificar se o recurso tem ficheiro
    if not recurso.arquivo:
        messages.error(request, "Este recurso não possui ficheiro para download.")
        return redirect("resources:detalhes", pk=pk)

    # Incrementar contadores (apenas para recursos de outros alunos)
    if not proprio_recurso:
        incrementar_download(recurso, request.user)

    # Servir o ficheiro
    file_path = recurso.arquivo.path
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            nome_ficheiro = os.path.basename(recurso.arquivo.name)
            response["Content-Disposition"] = f'attachment; filename="{smart_str(nome_ficheiro)}"'
            return response
    else:
        messages.error(request, "Ficheiro não encontrado no servidor.")
        raise Http404("Ficheiro não encontrado")


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
