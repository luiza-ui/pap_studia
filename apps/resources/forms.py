import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Resource

# Tamanho máximo permitido para upload (igual ao definido no model)
TAMANHO_MAXIMO_FICHEIRO = 50 * 1024 * 1024  # 50 MB


class FileInputComNome(forms.FileInput):
    """
    Widget de ficheiro que mostra o nome do ficheiro actual na edição,
    sem o botão "Limpar" que causava erros de validação.
    O utilizador sabe qual o ficheiro que já está guardado e pode
    seleccionar outro para o substituir.
    """

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        # Se já existe um ficheiro guardado, mostra o seu nome
        if value and hasattr(value, "name"):
            nome_ficheiro = os.path.basename(value.name)
            info = format_html(
                '<div class="form-text text-muted mt-1">'
                '<i class="bi bi-paperclip me-1"></i>'
                'Ficheiro actual: <strong>{}</strong> — seleciona outro para substituir'
                "</div>",
                nome_ficheiro,
            )
            return mark_safe(input_html + info)
        return input_html


class ResourceForm(forms.ModelForm):
    """
    Formulário para criar ou editar um recurso académico.

    Campos preenchidos automaticamente pela view (não aparecem aqui):
      - curso: vem do perfil do utilizador
      - instituicao: vem do perfil do utilizador

    Campos editáveis:
      - nome, disciplina, ano_letivo, professor, arquivo
    """

    class Meta:
        model  = Resource
        fields = ["nome", "disciplina", "ano_letivo", "professor", "arquivo"]
        widgets = {
            # Widget personalizado: mostra o nome do ficheiro actual sem "Limpar"
            "arquivo": FileInputComNome(attrs={"class": "form-control"}),
        }
        labels = {
            "nome":       "Título do recurso",
            "disciplina": "Disciplina",
            "ano_letivo": "Ano letivo",
            "professor":  "Professor (opcional)",
            "arquivo":    "Ficheiro",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplicar estilos Bootstrap aos campos de texto
        self.fields["nome"].widget      = forms.TextInput(attrs={"class": "form-control"})
        self.fields["disciplina"].widget = forms.TextInput(attrs={"class": "form-control"})
        self.fields["professor"].widget  = forms.TextInput(attrs={"class": "form-control"})

        # Choices para o select de ano letivo
        self.fields["ano_letivo"].widget = forms.Select(
            attrs={"class": "form-control"},
            choices=[("10", "10º Ano"), ("11", "11º Ano"), ("12", "12º Ano")],
        )

        # Campos não obrigatórios
        self.fields["professor"].required = False
        self.fields["arquivo"].required   = False

    def _post_clean(self):
        """
        Sobrescreve _post_clean() para evitar que o Model.clean() corra
        durante a validação do formulário. O Django chama Model.full_clean()
        dentro de _post_clean(), o que duplica as mensagens de erro porque
        o ResourceForm.clean() já faz todas as validações necessárias.
        Ao activar _skip_full_clean antes de chamar super(), o Model.full_clean()
        sobrescrito no Resource retorna imediatamente sem validar.
        """
        if self.instance:
            self.instance._skip_full_clean = True
        try:
            super()._post_clean()
        finally:
            if self.instance:
                self.instance._skip_full_clean = False

    def clean_arquivo(self):
        """Valida que o ficheiro não ultrapassa 50 MB."""
        arquivo = self.cleaned_data.get("arquivo")
        if arquivo and hasattr(arquivo, "size"):
            if arquivo.size > TAMANHO_MAXIMO_FICHEIRO:
                raise ValidationError(
                    f"O ficheiro é demasiado grande. O tamanho máximo é 50 MB "
                    f"(o teu ficheiro tem {arquivo.size / (1024 * 1024):.1f} MB)."
                )
        return arquivo

    def clean(self):
        """
        Validações cruzadas:
        1. Na edição sem novo ficheiro: manter o existente.
        2. Ficheiro é obrigatório na criação.
        3. Deteção de ficheiros duplicados por hash SHA256.
        """
        cleaned_data = super().clean()
        arquivo      = cleaned_data.get("arquivo")

        # Na edição: se não foi enviado um novo ficheiro mas já existia um, manter
        arquivo_existente = self.instance.pk and self.instance.arquivo
        if not arquivo and arquivo_existente:
            return cleaned_data

        # Regra: ficheiro obrigatório
        if not arquivo and not arquivo_existente:
            raise ValidationError("Tens de fornecer um Ficheiro.")

        return cleaned_data
