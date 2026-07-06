from django.urls import path
from . import views

app_name = "resources"

urlpatterns = [
    # Lista de recursos
    path("", views.lista_recursos_view, name="lista"),

    # Autocomplete de pesquisa (AJAX)
    path("autocomplete/", views.autocomplete_recursos_view, name="autocomplete"),

    # Detalhes de um recurso
    path("<int:pk>/", views.detalhes_recurso_view, name="detalhes"),

    # Upload de recurso
    path("upload/", views.upload_recurso_view, name="upload"),

    # Editar recurso
    path("<int:pk>/editar/", views.editar_recurso_view, name="editar"),

    # Apagar recurso
    path("<int:pk>/apagar/", views.apagar_recurso_view, name="apagar"),

    # Download de recurso
    path("<int:pk>/download/", views.download_recurso_view, name="download"),

]
