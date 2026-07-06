from django import forms
from django.core.exceptions import ValidationError

from .models import Report


class ReportRecursoForm(forms.ModelForm):
    """
    Formulário para denunciar um recurso.
    O utilizador escolhe o tipo de motivo (RadioSelect) e pode adicionar
    detalhes opcionais — obrigatório apenas quando o tipo é 'outro'.
    """

    class Meta:
        model  = Report
        fields = ["motivo_tipo", "motivo"]
        widgets = {
            "motivo_tipo": forms.RadioSelect(attrs={"class": "list-unstyled"}),
            "motivo": forms.Textarea(attrs={
                "class":       "form-control mt-2",
                "rows":        3,
                "placeholder": "Detalha o problema (opcional, obrigatório se escolheres 'Outro')...",
                "id":          "id_motivo",
            }),
        }
        labels = {
            "motivo_tipo": "Motivo da denúncia",
            "motivo":      "Detalhes adicionais",
        }

    def __init__(self, *args, **kwargs):
        # Parâmetros injectados pela view — não fazem parte do POST
        self.usuario = kwargs.pop("usuario", None)
        self.recurso = kwargs.pop("recurso", None)
        super().__init__(*args, **kwargs)
        # motivo (detalhes) não é obrigatório por defeito — validado no clean()
        self.fields["motivo"].required = False

    def _post_clean(self):
        """
        Evita que Report.clean() corra durante a validação do form.
        O form já valida tudo o que é necessário — correr o clean() do model
        neste momento causaria o erro 'deve ter recurso ou utilizador'
        porque o recurso ainda não foi atribuído à instância.
        """
        if self.instance:
            self.instance._skip_full_clean = True
        try:
            super()._post_clean()
        finally:
            if self.instance:
                self.instance._skip_full_clean = False

    def clean(self):
        """
        Regras de negócio:
        1. Se motivo_tipo='outro', o campo motivo (detalhes) é obrigatório.
        2. Não pode denunciar o próprio recurso.
        3. Não pode repetir uma denúncia sobre o mesmo recurso.
        """
        cleaned_data = super().clean()

        # Regra 1 — detalhes obrigatórios quando tipo é "outro"
        motivo_tipo = cleaned_data.get("motivo_tipo")
        motivo      = cleaned_data.get("motivo", "").strip()
        if motivo_tipo == "outro" and not motivo:
            self.add_error("motivo", "Por favor descreve o problema quando escolhes 'Outro'.")

        if self.usuario and self.recurso:
            # Regra 2 — dono não pode denunciar o próprio recurso
            if self.recurso.usuario == self.usuario:
                raise ValidationError("Não podes reportar os teus próprios recursos.")

            # Regra 3 — já existe uma denúncia deste aluno sobre este recurso
            if Report.objects.filter(
                denunciante=self.usuario,
                recurso=self.recurso,
                tipo="RECURSO",
            ).exists():
                raise ValidationError("Já enviaste uma denúncia para este recurso.")

        return cleaned_data


class ReportUsuarioForm(forms.ModelForm):
    """
    Formulário para denunciar um utilizador.
    O utilizador escolhe o tipo de motivo e pode adicionar detalhes opcionais.
    """

    class Meta:
        model  = Report
        fields = ["motivo_tipo", "motivo"]
        widgets = {
            "motivo_tipo": forms.RadioSelect(attrs={"class": "list-unstyled"}),
            "motivo": forms.Textarea(attrs={
                "class":       "form-control mt-2",
                "rows":        3,
                "placeholder": "Detalha o comportamento (opcional, obrigatório se escolheres 'Outro')...",
                "id":          "id_motivo",
            }),
        }
        labels = {
            "motivo_tipo": "Motivo da denúncia",
            "motivo":      "Detalhes adicionais",
        }

    def __init__(self, *args, **kwargs):
        # Parâmetros injectados pela view
        self.usuario   = kwargs.pop("usuario",   None)
        self.denunciado = kwargs.pop("denunciado", None)
        super().__init__(*args, **kwargs)
        self.fields["motivo"].required = False

    def _post_clean(self):
        """Evita que Report.clean() corra durante a validação do form (ver ReportRecursoForm)."""
        if self.instance:
            self.instance._skip_full_clean = True
        try:
            super()._post_clean()
        finally:
            if self.instance:
                self.instance._skip_full_clean = False

    def clean(self):
        """
        Regras de negócio:
        1. Se motivo_tipo='outro', o campo motivo (detalhes) é obrigatório.
        2. Não pode denunciar a si mesmo.
        3. Não pode repetir uma denúncia sobre o mesmo utilizador.
        """
        cleaned_data = super().clean()

        # Regra 1 — detalhes obrigatórios quando tipo é "outro"
        motivo_tipo = cleaned_data.get("motivo_tipo")
        motivo      = cleaned_data.get("motivo", "").strip()
        if motivo_tipo == "outro" and not motivo:
            self.add_error("motivo", "Por favor descreve o problema quando escolhes 'Outro'.")

        if self.usuario and self.denunciado:
            # Regra 2 — auto-denúncia bloqueada
            if self.usuario == self.denunciado:
                raise ValidationError("Não podes reportar a ti mesmo.")

            # Regra 3 — já existe uma denúncia deste aluno sobre este utilizador
            if Report.objects.filter(
                denunciante=self.usuario,
                usuario_denunciado=self.denunciado,
                tipo="USUARIO",
            ).exists():
                raise ValidationError("Já enviaste uma denúncia sobre este utilizador.")

        return cleaned_data
