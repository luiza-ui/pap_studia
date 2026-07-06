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
