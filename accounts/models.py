import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import F
from django.utils import timezone

from .validators import validate_email_institucional


class UserManager(BaseUserManager):
    """Gestor de utilizadores personalizado que usa email em vez de username."""

    def create_user(self, email, nome, curso, ano_letivo, instituicao, password=None):
        """Cria e devolve um utilizador normal (aluno)."""
        if not email:
            raise ValueError("O utilizador deve ter um email institucional")

        email = self.normalize_email(email)
        user  = self.model(
            email=email,
            nome=nome,
            curso=curso,
            ano_letivo=ano_letivo,
            instituicao=instituicao,
            is_active=True,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        password=None,
        nome="Administrador",
        curso="Admin",
        ano_letivo="12",
        instituicao="Sistema",
    ):
        """Cria e devolve um superutilizador (admin) com permissões completas."""
        user = self.create_user(
            email=email,
            nome=nome,
            curso=curso,
            ano_letivo=ano_letivo,
            instituicao=instituicao,
            password=password,
        )
        user.is_staff     = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de utilizador personalizado para alunos e administradores.
    Autentica por email em vez de username.
    """

    ANOS_LETIVOS = [
        ("10", "10º Ano"),
        ("11", "11º Ano"),
        ("12", "12º Ano"),
    ]

    # Cursos do ensino secundário português (DL 55/2018 e portarias em vigor)
    CURSOS = [
        # ── Ciências e Tecnologias ────────────────────────────────────────
        ("CT",  "Ciências e Tecnologias"),
        ("CSE", "Ciências Socioeconómicas"),
        # ── Humanidades ───────────────────────────────────────────────────
        ("LH",  "Línguas e Humanidades"),
        ("AV",  "Artes Visuais"),
        # ── Cursos Profissionais (exemplos mais comuns) ───────────────────
        ("TGPSI",  "Técnico de Gestão e Programação de Sistemas Informáticos"),
        ("TPSI",   "Técnico de Programação Informática"),
        ("TGE",    "Técnico de Gestão"),
        ("TM",     "Técnico de Marketing"),
        ("TAD",    "Técnico de Auxiliar de Saúde"),
        ("TGRC",   "Técnico de Gestão e Recursos Humanos e Comunicação"),
        ("TAAM",   "Técnico de Apoio à Gestão Desportiva"),
        ("TCOM",   "Técnico de Comunicação / Marketing e Publicidade"),
        ("TIT",    "Técnico de Instalações Elétricas"),
        ("TRSI",   "Técnico de Redes e Sistemas Informáticos"),
        ("TCMA",   "Técnico de Construção Civil / Medições e Orçamentos"),
        ("TGA",    "Técnico de Restauração / Cozinha e Pastelaria"),
        ("TTUR",   "Técnico de Turismo"),
        ("TAGRO",  "Técnico de Agropecuária"),
        ("TDG",    "Técnico de Design Gráfico"),
        ("TMOD",   "Técnico de Multimédia"),
        ("TELE",   "Técnico de Eletrónica, Automação e Computadores"),
        ("TMEC",   "Técnico de Mecatrónica"),
        ("TAUT",   "Técnico de Manutenção Industrial / Eletromecânica"),
        ("OUTRO",  "Outro"),
    ]

    # Índice de labels para acesso rápido ao nome completo a partir do código
    CURSOS_DICT = dict(CURSOS)

    # Dados do perfil
    email       = models.EmailField(unique=True, verbose_name="Email institucional")
    nome        = models.CharField(max_length=150)
    curso       = models.CharField(max_length=10, choices=CURSOS)
    ano_letivo  = models.CharField(max_length=2, choices=ANOS_LETIVOS)
    instituicao = models.CharField(max_length=150)

    # Flags de controlo de acesso
    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    # Contadores de actividade (usados para calcular créditos de download)
    total_uploads        = models.PositiveIntegerField(default=0)
    total_downloads      = models.PositiveIntegerField(default=0)
    total_reports_falsos = models.PositiveIntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["nome", "curso", "ano_letivo", "instituicao"]

    class Meta:
        verbose_name        = "Utilizador"
        verbose_name_plural = "Utilizadores"

    def clean(self):
        """
        Valida o email institucional apenas para alunos.
        Staff e superutilizadores podem ter qualquer email.
        """
        super().clean()
        if not self.is_staff and not self.is_superuser:
            validate_email_institucional(self.email)

    def __str__(self):
        return self.email

    # ------------------------------------------------------------------ #
    #  REGRAS DE NEGÓCIO                                                   #
    # ------------------------------------------------------------------ #

    def pode_fazer_download(self):
        """
        Verifica se o utilizador tem créditos para fazer download.
        Regra: 1 download de bónus ao criar conta + 2 por cada upload feito.
        Staff e superutilizadores não têm limite.
        """
        if self.is_superuser or self.is_staff:
            return True

        limite = (self.total_uploads * 2) + 1
        return self.total_downloads < limite

    def apagar_conteudo(self):
        """
        Apaga todo o conteúdo do utilizador: recursos, comentários e favoritos.
        Chamado quando a conta é bloqueada automaticamente.

        Decrementa total_salvos nos recursos favoritados antes de apagar
        os favoritos, para manter os contadores correctos.
        """
        from apps.comments.models import Comment
        from apps.favorites.models import Favorite
        from apps.resources.models import Resource

        # Apaga comentários do utilizador
        Comment.objects.filter(usuario=self).delete()

        # Decrementa total_salvos antes de apagar favoritos em bulk
        favoritos = Favorite.objects.filter(usuario=self).select_related("recurso")
        for fav in favoritos:
            Resource.objects.filter(pk=fav.recurso_id, total_salvos__gt=0).update(
                total_salvos=F("total_salvos") - 1
            )
        favoritos.delete()

        # Apaga todos os recursos (cascade apaga comentários e favoritos associados)
        self.resources.all().delete()

    def bloquear_por_abuso(self):
        """
        Bloqueia a conta automaticamente por excesso de reports falsos
        e apaga todo o conteúdo imediatamente.
        Tem guarda para não executar se a conta já estiver bloqueada.
        """
        if not self.is_active:
            return  # já bloqueada, evita apagamento duplo
        self.apagar_conteudo()
        self.is_active = False
        self.save()


class EmailActivationToken(models.Model):
    """
    Token único enviado por email para activar a conta de um novo aluno.
    Válido por 24 horas após criação. Pode ser utilizado apenas uma vez.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activation_tokens",
        verbose_name="Utilizador",
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Token",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    utilizado = models.BooleanField(default=False, verbose_name="Utilizado")

    class Meta:
        verbose_name        = "Token de activação"
        verbose_name_plural = "Tokens de activação"

    def esta_expirado(self) -> bool:
        """Devolve True se o token tiver mais de 24 horas."""
        from datetime import timedelta
        return timezone.now() > self.criado_em + timedelta(hours=24)

    def __str__(self):
        return f"Token de {self.user.email}"
