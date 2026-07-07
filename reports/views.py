from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.resources.models import Resource

from .forms import ReportRecursoForm, ReportUsuarioForm
from .models import Report

User = get_user_model()

# Número de reports falsos que desencadeia o bloqueio automático
LIMITE_REPORTS_FALSOS = 3


def eh_staff(user):
    """Predicado usado pelo @user_passes_test para restringir acesso a staff."""
    return user.is_staff


# ------------------------------------------------------------------ #
#  REPORTAR RECURSO                                                    #
# ------------------------------------------------------------------ #

@login_required
def criar_report_recurso_view(request, recurso_id):
    """
    Permite a um aluno denunciar um recurso de outro aluno.
    O dono do recurso não pode denunciar o seu próprio recurso.
    """
    recurso = get_object_or_404(Resource, pk=recurso_id)

    # Bloquear o dono de denunciar o próprio recurso
    if recurso.usuario == request.user:
        messages.error(request, "Não podes reportar os teus próprios recursos.")
        return redirect("resources:detalhes", pk=recurso_id)

    if request.method == "POST":
        form = ReportRecursoForm(request.POST, usuario=request.user, recurso=recurso)
        if form.is_valid():
            report             = form.save(commit=False)
            report.denunciante = request.user
            report.recurso     = recurso
            report.tipo        = "RECURSO"
            report.save()
            messages.success(request, "Denúncia enviada. Iremos analisar em breve.")
            return redirect("resources:detalhes", pk=recurso_id)
    else:
        form = ReportRecursoForm(usuario=request.user, recurso=recurso)

    return render(request, "reports/criar_recurso.html", {"form": form, "recurso": recurso})


# ------------------------------------------------------------------ #
#  REPORTAR UTILIZADOR                                                 #
# ------------------------------------------------------------------ #

@login_required
def criar_report_usuario_view(request, usuario_id):
    """
    Permite a um aluno denunciar outro utilizador.
    Não pode denunciar a si mesmo nem utilizadores já bloqueados.
    """
    denunciado = get_object_or_404(User, pk=usuario_id)

    # Bloquear auto-denúncia
    if denunciado == request.user:
        messages.error(request, "Não podes reportar a ti mesmo.")
        return redirect("resources:lista")

    # Não faz sentido denunciar uma conta já bloqueada
    if not denunciado.is_active:
        messages.info(request, "Este utilizador já está bloqueado.")
        return redirect("resources:lista")

    if request.method == "POST":
        form = ReportUsuarioForm(request.POST, usuario=request.user, denunciado=denunciado)
        if form.is_valid():
            report                    = form.save(commit=False)
            report.denunciante        = request.user
            report.usuario_denunciado = denunciado
            report.tipo               = "USUARIO"
            report.save()
            messages.success(request, "Denúncia enviada. Iremos analisar em breve.")
            return redirect("resources:lista")
    else:
        form = ReportUsuarioForm(usuario=request.user, denunciado=denunciado)

    return render(request, "reports/criar_usuario.html", {"form": form, "denunciado": denunciado})


# ------------------------------------------------------------------ #
#  LISTA DE REPORTS (ADMIN)                                            #
# ------------------------------------------------------------------ #

@login_required
@user_passes_test(eh_staff)
def lista_reports_view(request):
    """Lista de reports pendentes — apenas acessível a staff/admin."""
    reports = Report.objects.filter(status="PENDENTE").order_by("-data_criacao")
    return render(request, "reports/index.html", {"reports": reports})


# ------------------------------------------------------------------ #
#  DETALHES DE UM REPORT (ADMIN)                                       #
# ------------------------------------------------------------------ #

@login_required
@user_passes_test(eh_staff)
def detalhes_report_view(request, pk):
    """
    Vista de detalhe de um report — mantida para não quebrar URLs existentes,
    mas redireciona para a lista de reports (a informação relevante está lá).
    O botão "Ver" foi removido do template da lista.
    """
    return redirect("reports:lista")


# ------------------------------------------------------------------ #
#  RESOLVER UM REPORT (ADMIN)                                          #
# ------------------------------------------------------------------ #

@login_required
@user_passes_test(eh_staff)
@require_POST  # acções destrutivas só por POST — previne execução por link
def resolver_report_view(request, report_id, acao):
    """
    Resolve um report pendente.

    aceitar + RECURSO  — apaga o recurso, report fica Resolvido.
    aceitar + USUARIO  — bloqueia a conta e apaga todo o conteúdo, report fica Resolvido.
    rejeitar           — mantém tudo, penaliza o denunciante com +1 report falso;
                         bloqueia automaticamente ao atingir o limite.
    """
    if acao not in ("aceitar", "rejeitar"):
        raise Http404("Ação inválida.")

    report = get_object_or_404(Report, pk=report_id)

    if acao == "aceitar":
        _aceitar_report(request, report)
    else:
        _rejeitar_report(request, report)

    return redirect("reports:lista")


def _aceitar_report(request, report):
    """Lógica interna de aceitação de um report."""
    if report.tipo in ("RECURSO", "IA"):
        if report.recurso:
            report.recurso.delete()
            report.refresh_from_db()
        report.resolver("RESOLVIDO")
        messages.success(request, "Recurso apagado e denúncia fechada.")

    elif report.tipo == "USUARIO":
        denunciado = report.usuario_denunciado
        if denunciado:
            denunciado.bloquear_por_abuso()
            messages.success(
                request,
                f"Conta de {denunciado.email} bloqueada e todo o conteúdo apagado.",
            )
        report.resolver("RESOLVIDO")


def _rejeitar_report(request, report):
    """
    Lógica interna de rejeição de um report.
    Reports de IA não têm denunciante — reactivam o recurso suspenso.
    Reports humanos penalizam o denunciante com +1 report falso.
    """
    # Reports de IA: reactivar recurso, sem penalizar ninguém
    if report.tipo == "IA":
        if report.recurso:
            type(report.recurso).objects.filter(pk=report.recurso.pk).update(suspenso=False)
        report.resolver("REJEITADO")
        messages.info(request, "Denúncia de IA rejeitada. Recurso reactivado.")
        return

    report.resolver("REJEITADO")

    denunciante = report.denunciante
    if denunciante is None:
        messages.info(request, "Denúncia rejeitada.")
        return

    User.objects.filter(pk=denunciante.pk).update(
        total_reports_falsos=F("total_reports_falsos") + 1
    )
    denunciante.refresh_from_db(fields=["total_reports_falsos", "is_active"])

    if denunciante.total_reports_falsos >= LIMITE_REPORTS_FALSOS:
        denunciante.bloquear_por_abuso()
        messages.warning(
            request,
            f"A conta de {denunciante.email} foi bloqueada automaticamente "
            f"por excesso de denúncias falsas.",
        )
    else:
        restantes = LIMITE_REPORTS_FALSOS - denunciante.total_reports_falsos
        messages.info(
            request,
            f"Denúncia rejeitada. O utilizador {denunciante.email} tem "
            f"{denunciante.total_reports_falsos} denúncia(s) falsa(s) "
            f"({restantes} até ao bloqueio automático).",
        )
