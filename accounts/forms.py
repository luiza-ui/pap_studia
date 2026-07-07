from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import User
from .validators import validate_email_institucional


class UserRegistrationForm(forms.ModelForm):
    """
    Formulário de registo para novos alunos.
    Valida o domínio institucional do email e a confirmação de senha.
    """

    password1 = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="Mínimo de 8 caracteres. Evita senhas óbvias ou só com números.",
    )
    password2 = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model  = User
        fields = ["nome", "curso", "ano_letivo", "instituicao", "email"]
        widgets = {
            "nome":        forms.TextInput(attrs={"class": "form-control"}),
            "curso":       forms.Select(attrs={"class": "form-control"}),
            "ano_letivo":  forms.Select(attrs={"class": "form-control"}),
            "instituicao": forms.TextInput(attrs={"class": "form-control"}),
            "email":       forms.EmailInput(attrs={"class": "form-control"}),
        }
        labels = {
            "instituicao": "Escola / Instituição",
        }

    def clean_nome(self):
        """Verifica se o nome contém linguagem inapropriada."""
        nome = self.cleaned_data.get("nome", "")
        if nome:
            try:
                from apps.moderation.services.toxic_text import verificar_texto_seguro
                if not verificar_texto_seguro(nome):
                    raise forms.ValidationError("O nome contém linguagem que não é permitida.")
            except forms.ValidationError:
                raise
            except Exception:
                pass
        return nome

    def clean_email(self):
        """
        Normaliza o email, valida o domínio institucional e verifica duplicados.

        Uma conta que ainda está pendente de activação (is_active=False) não
        bloqueia um novo registo — nesse caso o utilizador é avisado para usar
        o reenvio do email de activação em vez de ficar preso sem poder
        entrar nem voltar a registar-se.
        """
        email = self.cleaned_data.get("email", "").lower().strip()
        if email:
            validate_email_institucional(email)
            existente = User.objects.filter(email=email).first()
            if existente:
                if existente.is_active:
                    raise forms.ValidationError("Este email já está registado.")
                raise forms.ValidationError(
                    "Já existe um registo pendente para este email. Verifica a tua "
                    "caixa de correio ou pede um novo email de activação na página de login."
                )
        return email

    def clean_password1(self):
        """Aplica a política de senha (obrigatória, mas moderada) definida em settings."""
        password1 = self.cleaned_data.get("password1")
        if password1:
            try:
                validate_password(password1)
            except DjangoValidationError as e:
                raise forms.ValidationError(e.messages)
        return password1

    def clean(self):
        """Verifica se as duas senhas coincidem."""
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "As senhas não coincidem.")
        return cleaned_data

    def save(self, commit=True):
        """Cria o utilizador com a senha encriptada. Conta inactiva até confirmação de email."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False  # activada após confirmação de email
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Formulário de login por email institucional e senha."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        """
        Normaliza o email, autentica e verifica se a conta está activa.
        Guarda o objecto user em cleaned_data para a view usar directamente.
        """
        cleaned_data = super().clean()
        email    = cleaned_data.get("email", "").lower().strip()
        password = cleaned_data.get("password")

        cleaned_data["email"] = email

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                # Verificar primeiro se sequer existe uma conta com este email
                try:
                    utilizador = User.objects.get(email=email)
                except User.DoesNotExist:
                    raise forms.ValidationError(
                        "Não existe nenhuma conta registada com este email. "
                        "Verifica se o escreveste correctamente ou regista-te."
                    )
                # Conta existe: distinguir conta inactiva de senha errada
                if not utilizador.is_active:
                    raise forms.ValidationError(
                        "Esta conta ainda não está activa. "
                        "Verifica o teu email e clica no link de activação. "
                        "Se não recebeste o email, podes pedir um novo na página de login."
                    )
                raise forms.ValidationError("Email ou senha incorretos.")
            cleaned_data["user"] = user

        return cleaned_data


class EditarPerfilForm(forms.ModelForm):
    """
    Formulário de edição de perfil.

    Permite alterar email (com validação de domínio institucional).
    Os campos de senha são opcionais: em branco = senha inalterada.
    """

    # Campo de email opcional na edição
    email_novo = forms.EmailField(
        label="Novo email institucional",
        widget=forms.EmailInput(attrs={
            "class":       "form-control",
            "placeholder": "Deixa em branco para manter o email actual",
        }),
        required=False,
        help_text="Preenche apenas se mudares de escola. Tem de ser um email institucional válido.",
    )

    password1 = forms.CharField(
        label="Nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        help_text="Deixa em branco para manter a senha actual. Se preencheres: mínimo 8 caracteres, nada de senhas óbvias.",
    )
    password2 = forms.CharField(
        label="Confirmar nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
    )

    class Meta:
        model  = User
        fields = ["nome", "curso", "ano_letivo", "instituicao"]
        widgets = {
            "nome":        forms.TextInput(attrs={"class": "form-control"}),
            "curso":       forms.Select(attrs={"class": "form-control"}),
            "ano_letivo":  forms.Select(attrs={"class": "form-control"}),
            "instituicao": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "instituicao": "Escola / Instituição",
        }

    def clean_nome(self):
        """Verifica se o nome contém linguagem inapropriada."""
        nome = self.cleaned_data.get("nome", "")
        if nome:
            try:
                from apps.moderation.services.toxic_text import verificar_texto_seguro
                if not verificar_texto_seguro(nome):
                    raise forms.ValidationError("O nome contém linguagem que não é permitida.")
            except forms.ValidationError:
                raise
            except Exception:
                pass
        return nome

    def clean_email_novo(self):
        """
        Valida o novo email (se fornecido):
        - Deve pertencer a um domínio institucional reconhecido.
        - Não pode já estar em uso por outro utilizador.
        """
        email = self.cleaned_data.get("email_novo", "").lower().strip()
        if not email:
            return email  # sem alteração

        validate_email_institucional(email)

        # Verifica duplicados (excluindo o próprio utilizador)
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este email já está registado por outro utilizador.")

        return email

    def clean_password1(self):
        """Se uma nova senha for indicada, aplica a política de senha (obrigatória, mas moderada)."""
        password1 = self.cleaned_data.get("password1")
        if password1:
            try:
                validate_password(password1)
            except DjangoValidationError as e:
                raise forms.ValidationError(e.messages)
        return password1

    def clean(self):
        """Verifica se as duas novas senhas coincidem (se preenchidas)."""
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if (p1 or p2) and p1 != p2:
            self.add_error("password2", "As senhas não coincidem.")
        return cleaned_data
