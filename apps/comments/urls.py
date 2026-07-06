from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    # Exemplo de uso: /comments/adicionar/5/ (onde 5 é o ID do recurso)
    path('adicionar/<int:resource_id>/', views.adicionar_comentario, name='adicionar_comentario'),
    
    # Exemplo de uso: /comments/apagar/10/ (onde 10 é o ID do comentário)
    path('apagar/<int:comment_id>/', views.apagar_comentario, name='apagar_comentario'),
]