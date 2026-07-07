from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.http import require_POST

from .forms import EditarPerfilForm, LoginForm, UserRegistrationForm
from .validators import DOMINIO_PARA_INSTITUICAO

User = get_user_model()


# ------------------------------------------------------------------ #
#  FUNÇÃO AUXILIAR DE ACTIVAÇÃO                                        #
# ------------------------------------------------------------------ #

def _enviar_email_activacao(user, request):
    """
    Cria um novo token de activação e envia o email de confirmação ao utilizador.
    Chamada após o registo e no reenvio de activação.

    Devolve o URL de activação: em produção o email chega directo à caixa de
    correio e o link é clicável, mas em desenvolvimento os emails são apenas
    impressos no terminal (EMAIL_BACKEND=console) em formato "quoted-printable",
    que quebra URLs longos a meio com um "=" de continuação de linha. Copiar
    manualmente esse texto do terminal produz um link cortado e inválido — por
    isso devolvemos o URL para a view poder mostrá-lo directamente na página
    quando DEBUG está activo, sem depender de copiar/colar do terminal.
    """
    from .models import EmailActivationToken
    # Invalidar tokens anteriores não utilizados
    EmailActivationToken.objects.filter(user=user, utilizado=False).update(utilizado=True)
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
    return url_activacao


# ------------------------------------------------------------------ #
#  REGISTO                                                             #
# ------------------------------------------------------------------ #

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
            except IntegrityError:
                form.add_error("email", "Este email já está registado.")
                messages.error(request, "Corrije os erros abaixo.")
            else:
                try:
                    url_activacao = _enviar_email_activacao(user, request)
                    messages.success(
                        request,
                        format_html(
                            "Conta criada! Enviámos um email para "
                            "<strong>{}</strong> com o link de activação.",
                            user.email,
                        ),
                    )
                    if True:
                        messages.info(
                            request,
                            format_html(
                                "Modo de desenvolvimento: o email é apenas impresso no "
                                "terminal e copiar o link de lá pode cortá-lo a meio. "
                                "Usa este link directo para testar: "
                                '<a href="{}">{}</a>',
                                url_activacao, url_activacao,
                            ),
                        )
                except Exception:
                    messages.warning(
                        request,
                        "Conta criada, mas não foi possível enviar o email de activação. "
                        "Usa o botão de reenvio na página seguinte.",
                    )
                return redirect("accounts:activacao_pendente")
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = UserRegistrationForm()

    import json
    return render(request, "accounts/registo.html", {
        "form": form,
        "dominio_instituicao_json": json.dumps(DOMINIO_PARA_INSTITUICAO, ensure_ascii=False),
    })


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
        except User.DoesNotExist:
            messages.info(
                request,
                "Se este email pertencer a uma conta inactiva, "
                "receberás um novo link em breve.",
            )
        else:
            try:
                url_activacao = _enviar_email_activacao(user, request)
                messages.success(
                    request,
                    format_html(
                        "Novo email de activação enviado para <strong>{}</strong>.",
                        email,
                    ),
                )
                if True:
                    messages.info(
                        request,
                        format_html(
                            "Modo de desenvolvimento: usa este link directo para testar "
                            "(evita o corte do link ao copiar do terminal): "
                            '<a href="{}">{}</a>',
                            url_activacao, url_activacao,
                        ),
                    )
            except Exception:
                messages.error(
                    request,
                    "Não foi possível enviar o email de activação. "
                    "Tenta novamente mais tarde.",
                )
            return redirect("accounts:activacao_pendente")

    return render(request, "accounts/reenviar_activacao.html")


# ------------------------------------------------------------------ #
#  LOGIN                                                               #
# ------------------------------------------------------------------ #

_MAX_TENTATIVAS = 5
_BLOQUEIO_SEGUNDOS = 3600  # 1 hora


def login_view(request):
    """
    Login por email institucional e senha.
    Redireciona utilizadores já autenticados para a lista de recursos.
    Após 5 tentativas falhadas para o mesmo email, bloqueia 1 hora.
    """
    if request.user.is_authenticated:
        return redirect("resources:lista")

    if request.method == "POST":
        email_raw    = request.POST.get("email",    "").lower().strip()
        password_raw = request.POST.get("password", "").strip()

        from django.core.cache import cache
        cache_key  = f"login_attempts_{email_raw}"
        tentativas = cache.get(cache_key, 0)

        # Bloqueado? Nem deixar tentar
        if email_raw and tentativas >= _MAX_TENTATIVAS:
            messages.error(
                request,
                "Conta temporariamente bloqueada por excesso de tentativas. "
                "Tenta novamente daqui a 1 hora.",
            )
            return render(request, "accounts/login.html", {"form": LoginForm()})

        form = LoginForm(request.POST)
        if form.is_valid():
            cache.delete(cache_key)
            user = form.cleaned_data["user"]
            login(request, user)
            messages.success(request, "Login efetuado com sucesso!")
            return redirect("resources:lista")
        else:
            # Só contar como tentativa de força bruta quando email E senha foram preenchidos
            # (evita contar submissões de formulário vazio ou com campos em falta)
            if email_raw and password_raw:
                nova_contagem = tentativas + 1
                cache.set(cache_key, nova_contagem, _BLOQUEIO_SEGUNDOS)
                restantes = _MAX_TENTATIVAS - nova_contagem
                if restantes <= 0:
                    messages.error(
                        request,
                        "Conta temporariamente bloqueada por excesso de tentativas. "
                        "Tenta novamente daqui a 1 hora.",
                    )
                elif restantes <= 3:
                    messages.warning(
                        request,
                        f"Atenção: {restantes} tentativa(s) restante(s) antes do bloqueio temporário.",
                    )
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


# ------------------------------------------------------------------ #
#  LOGOUT                                                              #
# ------------------------------------------------------------------ #

@require_POST
def logout_view(request):
    """
    Termina a sessão do utilizador.
    Apenas aceita POST para prevenir logout acidental por link (protecção CSRF).
    """
    logout(request)
    messages.success(request, "Logout efetuado com sucesso!")
    return redirect("accounts:login")


# ------------------------------------------------------------------ #
#  PERFIL                                                              #
# ------------------------------------------------------------------ #

@login_required
def perfil_view(request):
    """
    Mostra o perfil do aluno com os recursos enviados e favoritos.
    Calcula os créditos de download disponíveis em Python para precisão.
    """
    user             = request.user
    recursos_enviados = user.resources.all().order_by("-data_upload")
    favoritos         = user.favoritos.select_related("recurso").order_by("-criado_em")

    # Cálculo de créditos: 1 bónus inicial + (uploads × 2) - downloads já feitos
    limite_downloads  = (user.total_uploads * 2) + 1
    creditos_restantes = max(0, limite_downloads - user.total_downloads)

    return render(request, "accounts/perfil.html", {
        "user":               user,
        "recursos_enviados":  recursos_enviados,
        "favoritos":          favoritos,
        "limite_downloads":   limite_downloads,
        "creditos_restantes": creditos_restantes,
    })


# ------------------------------------------------------------------ #
#  EDITAR PERFIL                                                       #
# ------------------------------------------------------------------ #

@login_required
def editar_perfil_view(request):
    """
    Permite ao aluno actualizar os seus dados de perfil.
    - Email: pode ser alterado para outro email institucional (ex: mudança de escola).
    - Senha: se os campos forem deixados em branco, a senha não é alterada.
    """
    user = request.user

    if request.method == "POST":
        form = EditarPerfilForm(request.POST, instance=user)
        if form.is_valid():
            user_editado = form.save(commit=False)

            # Actualizar email se foi fornecido um novo
            email_novo = form.cleaned_data.get("email_novo")
            if email_novo:
                user_editado.email = email_novo

            # Actualizar senha se foi fornecida
            password = form.cleaned_data.get("password1")
            if password:
                user_editado.set_password(password)

            user_editado.save()
            update_session_auth_hash(request, user_editado)  # mantém sessão após mudança de senha
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("accounts:perfil")
    else:
        form = EditarPerfilForm(instance=user)

    return render(request, "accounts/editar_perfil.html", {"form": form, "email_atual": user.email})


# ------------------------------------------------------------------ #
#  APAGAR CONTA                                                        #
# ------------------------------------------------------------------ #

@login_required
def apagar_conta_view(request):
    """
    Apaga a conta do aluno e todo o seu conteúdo após confirmação de senha.

    Ordem correcta: apagar_conteudo() → logout() → delete()
    O logout() deve ser chamado ANTES do delete() para invalidar a sessão
    enquanto o objecto utilizador ainda existe na base de dados.
    """
    user = request.user

    if request.method == "POST":
        senha = request.POST.get("senha", "")

        # Verifica a senha antes de prosseguir
        if not user.check_password(senha):
            messages.error(request, "Senha incorreta. A conta não foi apagada.")
            return render(request, "accounts/apagar_conta.html")

        # Apaga conteúdo, invalida sessão e remove o utilizador
        user.apagar_conteudo()
        logout(request)
        user.delete()
        messages.success(request, "Conta apagada com sucesso!")
        return redirect("accounts:login")

    return render(request, "accounts/apagar_conta.html")


# ------------------------------------------------------------------ #
#  PERFIL PÚBLICO DE OUTRO UTILIZADOR                                  #
# ------------------------------------------------------------------ #

@login_required
def perfil_publico_view(request, pk):
    """
    Mostra o perfil público de outro utilizador.
    Exibe nome, curso, instituição e recursos públicos.
    Permite reportar o utilizador a partir daqui.
    """
    from django.contrib.auth import get_user_model
    from django.shortcuts import get_object_or_404
    User = get_user_model()

    aluno = get_object_or_404(User, pk=pk, is_active=True)

    # Não mostrar o perfil do próprio utilizador aqui — usa o perfil normal
    if aluno == request.user:
        return redirect("accounts:perfil")

    recursos_publicos = aluno.resources.all().order_by("-data_upload")
    total_downloads_publicos = sum(r.total_downloads for r in recursos_publicos)

    return render(request, "accounts/perfil_publico.html", {
        "aluno":                    aluno,
        "recursos_publicos":        recursos_publicos,
        "total_downloads_publicos": total_downloads_publicos,
    })
