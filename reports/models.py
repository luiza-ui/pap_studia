from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Report(models.Model):
    """
    Modelo de denúncia sobre um recurso ou um utilizador.
    Cada report é de um tipo exclusivo: RECURSO ou USUARIO.
    """

    TIPO_CHOICES = [
        ("RECURSO",  "Recurso"),
        ("USUARIO",  "Utilizador"),
        ("IA",       "Moderação automática"),
    ]

    STATUS_CHOICES = [
        ("PENDENTE",   "Pendente"),
        ("RESOLVIDO",  "Resolvido"),
        ("REJEITADO",  "Rejeitado (Falso Alerta)"),
    ]

    # Quem fez a denúncia (null para reports automáticos por IA)
    denunciante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports_feitos",
        blank=True,
        null=True,
    )

    MOTIVO_CHOICES = [
        ("plagio",    "Plágio / Cópia sem créditos"),
        ("improprio", "Conteúdo impróprio"),
        ("spam",      "Spam ou publicidade"),
        ("falso",     "Informação falsa ou errada"),
        ("ofensa",    "Linguagem ofensiva"),
        ("outro",     "Outro"),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default="RECURSO")
    motivo_tipo = models.CharField(
        max_length=20,
        choices=MOTIVO_CHOICES,
        default="outro",
        verbose_name="Tipo de motivo",
    )

    # Alvo da denúncia — apenas um dos dois pode estar preenchido
    recurso = models.ForeignKey(
        "resources.Resource",
        on_delete=models.SET_NULL,
        related_name="reports",
        blank=True, null=True,
    )
    usuario_denunciado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="reports_recebidos",
        blank=True, null=True,
    )

    motivo       = models.TextField()
    status       = models.CharField(max_length=15, choices=STATUS_CHOICES, default="PENDENTE")
    data_criacao = models.DateTimeField(default=timezone.now)
    data_resolucao = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name        = "Report"
        verbose_name_plural = "Reports"
        ordering            = ["-data_criacao"]

    def __str__(self):
        if self.tipo == "RECURSO":
            alvo = str(self.recurso) if self.recurso else "(recurso apagado)"
        else:
            alvo = str(self.usuario_denunciado) if self.usuario_denunciado else "(utilizador apagado)"
        return f"Report #{self.id} ({self.tipo}) — {self.get_status_display()} — {alvo}"

    def clean(self):
        """
        Validações de integridade do Report ao nível do modelo.
        Usadas pelos testes de model e por full_clean() quando chamado directamente.

        Em contexto web, a view atribui recurso/usuario_denunciado ANTES de
        chamar save(), portanto os campos já estão preenchidos quando o
        Django 5.2 chama full_clean() automaticamente. O clean() funciona
        correctamente nesse cenário.
        """
        tem_recurso  = bool(self.recurso_id  or getattr(self, "recurso",  None))
        tem_usuario  = bool(self.usuario_denunciado_id or getattr(self, "usuario_denunciado", None))

        # Se nenhum dos dois está preenchido ainda (save intermédio), não validar
        if not tem_recurso and not tem_usuario:
            # Só lança erro se o tipo já estiver definido (indica que o save é intencional)
            if self.tipo:
                raise ValidationError(
                    "Um report deve ter um recurso ou um utilizador denunciado."
                )
            return

        # Não pode ter os dois ao mesmo tempo
        if tem_recurso and tem_usuario:
            raise ValidationError(
                "Um report deve ser sobre um recurso OU sobre um utilizador, nunca os dois."
            )

        # Não pode reportar a si mesmo
        if tem_usuario and self.usuario_denunciado == self.denunciante:
            raise ValidationError("Não podes reportar a ti mesmo.")

        # Não pode reportar o seu próprio recurso
        if tem_recurso and self.recurso and self.recurso.usuario == self.denunciante:
            raise ValidationError("Não podes reportar os teus próprios recursos.")

    def full_clean(self, exclude=None, validate_unique=True, validate_constraints=True):
        """
        Sobrescreve full_clean() para evitar duplicação de validação.
        Quando chamado automaticamente pelo Django 5.2 durante o save(),
        a flag _skip_full_clean está activa e o método retorna imediatamente.
        Quando chamado directamente (ex: testes), corre normalmente.
        """
        if getattr(self, "_skip_full_clean", False):
            return
        super().full_clean(
            exclude=exclude,
            validate_unique=validate_unique,
            validate_constraints=validate_constraints,
        )

    def save(self, *args, **kwargs):
        """
        Sobrescreve save() para activar a flag _skip_full_clean antes de gravar,
        evitando que full_clean() corra duas vezes (o formulário já validou).
        """
        self._skip_full_clean = True
        try:
            super().save(*args, **kwargs)
        finally:
            self._skip_full_clean = False

    def resolver(self, novo_status):
        """Marca o report como resolvido ou rejeitado e regista a data de resolução."""
        self.status          = novo_status
        self.data_resolucao  = timezone.now()
        self.save()
