from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.resources.models import Resource


class Favorite(models.Model):
    """
    Representa um recurso guardado nos favoritos de um utilizador.
    Restrições: um aluno não pode favoritar os seus próprios recursos
    nem favoritar o mesmo recurso duas vezes (unique_together).
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favoritos",
    )
    recurso = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="favoritado_por",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ("usuario", "recurso")
        verbose_name        = "Favorito"
        verbose_name_plural = "Favoritos"

    def __str__(self):
        return f"{self.usuario} favoritou {self.recurso.nome}"

    def clean(self):
        """Impede que o utilizador favorite o seu próprio recurso."""
        if hasattr(self, "recurso") and hasattr(self, "usuario"):
            if self.recurso.usuario == self.usuario:
                raise ValidationError(
                    "Não podes adicionar os teus próprios recursos aos favoritos."
                )

    def save(self, *args, **kwargs):
        """
        Valida as regras de negócio antes de gravar.
        Após gravar um favorito novo, incrementa total_salvos no recurso
        via UPDATE directo para evitar race conditions.
        """
        self.clean()

        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Incrementar contador apenas na criação
        if is_new:
            Resource.objects.filter(pk=self.recurso.pk).update(
                total_salvos=models.F("total_salvos") + 1
            )
