from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # Admin
    path("", views.lista_reports_view, name="lista"),
    path("<int:pk>/", views.detalhes_report_view, name="detalhes"),
    path("<int:report_id>/resolver/<str:acao>/", views.resolver_report_view, name="resolver"),

    # Alunos — reportar recurso
    path("recurso/<int:recurso_id>/", views.criar_report_recurso_view, name="criar_recurso"),

    # Alunos — reportar utilizador
    path("utilizador/<int:usuario_id>/", views.criar_report_usuario_view, name="criar_usuario"),
]