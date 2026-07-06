from apps.reports.models import Report


def criar_report_ia(recurso=None, usuario=None, motivo_tipo='', motivo=''):
    """Cria um report automático de IA e suspende o recurso imediatamente."""
    report = Report.objects.create(
        denunciante=None,
        recurso=recurso,
        usuario_denunciado=usuario,
        tipo='IA',
        motivo_tipo=motivo_tipo,
        motivo=motivo,
        status='PENDENTE',
    )
    # Suspender o recurso imediatamente — fica invisível até revisão humana
    if recurso is not None:
        type(recurso).objects.filter(pk=recurso.pk).update(suspenso=True)
    return report
