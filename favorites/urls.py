from django.urls import path
from . import views

app_name = "favorites"

urlpatterns = [
    path("toggle/<int:recurso_id>/", views.toggle_favorito_view, name="toggle"),
    path("remover/<int:recurso_id>/", views.remover_favorito_view, name="remover"),
]
