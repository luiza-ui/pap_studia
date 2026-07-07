from django.shortcuts import render

from apps.resources.models import Resource


def home_view(request):
    """
    Página inicial pública — acessível sem login.
    Mostra os recursos mais recentes e os mais descarregados.
    A secção "Mais Descarregados" só aparece se existirem recursos com downloads.
    """
    recursos_recentes  = Resource.objects.filter(suspenso=False).order_by("-data_upload")[:6]
    recursos_populares = (
        Resource.objects
        .filter(suspenso=False, total_downloads__gt=0)
        .order_by("-total_downloads")[:6]
    )

    return render(request, "core/index.html", {
        "recursos_recentes":  recursos_recentes,
        "recursos_populares": recursos_populares,
    })
