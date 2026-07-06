from django.conf import settings
from django.db import models

from apps.resources.models import Resource


class Comment(models.Model):
    """
    Comentário deixado por um aluno num recurso.
    Podem existir múltiplos comentários do mesmo aluno no mesmo recurso.
    O campo 'ativo' permite ao admin ocultar comentários inapropriados
    sem os apagar da base de dados.
    """

    # Autor do comentário
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comentarios",
        verbose_name="Autor",
    )

    # Recurso onde o comentário foi deixado
    recurso = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="comentarios",
        verbose_name="Recurso comentado",
    )

    texto = models.TextField(
        verbose_name="Comentário",
        help_text="Escreva a sua dúvida, agradecimento ou sugestão.",
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    # Campo de moderação — False oculta o comentário no site mas mantém-no na BD
    ativo = models.BooleanField(
        default=True,
        verbose_name="Visível no site?",
        help_text="Desmarque para ocultar este comentário sem o apagar.",
    )

    class Meta:
        verbose_name        = "Comentário"
        verbose_name_plural = "Comentários"
        ordering            = ["-criado_em"]  # mais recentes primeiro

    def __str__(self):
        return f"Comentário de {self.usuario} em {self.recurso}"
