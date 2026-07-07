from django.contrib.auth import get_user_model

User = get_user_model()


def existe_email(email):
    """
    Retorna True se o email já estiver registado
    """
    return User.objects.filter(email=email).exists()


def bloquear_aluno_manual(user):
    """
    Bloqueia manualmente a conta de um aluno (ação do admin).
    APENAS bloqueia o acesso — o conteúdo permanece visível.
    O admin decide manualmente o que apagar.

    NOTA: Esta função é para bloqueio manual pelo admin.
    Para bloqueio automático por abuso (que apaga conteúdo),
    usa user.bloquear_por_abuso().
    """
    user.is_active = False
    user.save(update_fields=["is_active"])