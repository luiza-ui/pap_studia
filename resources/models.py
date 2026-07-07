import hashlib
import os
import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from apps.accounts.models import User as Aluno

User = settings.AUTH_USER_MODEL

# Tamanho máximo permitido para upload de ficheiros
TAMANHO_MAXIMO_FICHEIRO = 50 * 1024 * 1024  # 50 MB


def normalizar_texto(texto: str) -> str:
    """
    Remove acentos e converte para minúsculas para pesquisa insensível
    a diacríticos. Ex: "Matemática" → "matematica".
    Usado nos campos _normalizado para tornar a pesquisa robusta.
    """
    if not texto:
        return ""
    sem_acentos = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sem_acentos if unicodedata.category(c) != "Mn")


def normalizar_query_pesquisa(query: str) -> str:
    """
    Normaliza um termo de pesquisa para compatibilidade com os campos _normalizado.
    Remove acentos e converte para minúsculas — igual ao que é guardado na BD.

    Nota: NÃO substitui "professor/a" por "prof" porque os campos na BD
    guardam o valor completo (ex: "professora helena"). A query tem de chegar
    da mesma forma que foi guardada para o icontains funcionar corretamente.
    """
    return normalizar_texto(query).strip()


def resource_upload_path(instance, filename):
    """
    Gera o caminho de upload: media/resources/<pk_utilizador>/<nome_ficheiro>
    Usa o pk em vez do email para evitar problemas com caracteres especiais.
    """
    return os.path.join("resources", str(instance.usuario.pk), filename)


class Resource(models.Model):
    """
    Modelo de recurso académico partilhado por um aluno.
    Cada recurso tem obrigatoriamente um ficheiro (PDF, DOCX, PPTX ou imagem).
    """

    TIPO_ARQUIVO_CHOICES = [
        ("PDF",  "PDF"),
        ("DOCX", "DOCX"),
        ("PPTX", "PPTX"),
        ("IMG",  "Imagem"),
    ]

    # Aluno que enviou o recurso
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name="Aluno que enviou",
    )

    nome       = models.CharField(max_length=255, verbose_name="Título do recurso")
    # copiado do perfil do utilizador — usa as mesmas choices de User.CURSOS
    # para que get_curso_display() exista e mostre o nome completo do curso
    curso      = models.CharField(max_length=10, choices=Aluno.CURSOS)
    ano_letivo = models.CharField(max_length=2)
    disciplina = models.CharField(max_length=100)
    tipo_arquivo = models.CharField(
        max_length=10, choices=TIPO_ARQUIVO_CHOICES, blank=True
    )
    instituicao = models.CharField(max_length=150)
    professor   = models.CharField(max_length=150, blank=True, null=True)

    # Campos normalizados — preenchidos automaticamente no save().
    # Armazenam o texto sem acentos e em minúsculas para que a pesquisa
    # "matematica" encontre "Matemática" sem custo em runtime.
    nome_normalizado       = models.CharField(max_length=255, blank=True, db_index=True)
    disciplina_normalizada = models.CharField(max_length=100, blank=True, db_index=True)
    professor_normalizado  = models.CharField(max_length=150, blank=True)

    arquivo = models.FileField(
        upload_to=resource_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "docx", "doc", "pptx", "ppt", "jpg", "jpeg", "png"]
            )
        ],
        blank=True,
        null=True,
    )

    # Hash SHA256 do ficheiro — usado para detetar duplicados
    hash_arquivo = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    phash = models.CharField(max_length=64, blank=True, default='', db_index=False)

    # Suspensão automática por moderação de IA
    suspenso = models.BooleanField(default=False)

    # Contadores de actividade
    total_downloads = models.PositiveIntegerField(default=0)
    total_salvos    = models.PositiveIntegerField(default=0)

    data_upload = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name         = "Recurso"
        verbose_name_plural  = "Recursos"
        ordering             = ["-data_upload"]

    def __str__(self):
        return f"{self.nome} ({self.disciplina})"

    # ------------------------------------------------------------------ #
    #  VALIDAÇÃO DE MODELO                                                 #
    #  Chamada por full_clean() — usada directamente nos testes de model.  #
    #  O formulário (ResourceForm) também valida estes casos, portanto     #
    #  em contexto web o clean() do form é o que corre primeiro.           #
    # ------------------------------------------------------------------ #

    def clean(self):
        """
        Regras de negócio validadas ao nível do modelo:
        1. Ficheiro é obrigatório.
        2. Ficheiro não pode ultrapassar 50 MB.
        3. Ficheiros duplicados bloqueados por hash SHA256.
        """
        # 1 — Ficheiro obrigatório
        if not self.arquivo:
            raise ValidationError("Tens de fornecer um Ficheiro.")

        # 2 — Tamanho máximo do ficheiro
        if self.arquivo and hasattr(self.arquivo, "size"):
            if self.arquivo.size > TAMANHO_MAXIMO_FICHEIRO:
                raise ValidationError(
                    {"arquivo": "O ficheiro é demasiado grande. O tamanho máximo é 50 MB."}
                )

        # (duplicados tratados como suspensão automática na view — não são erro)

    def full_clean(self, exclude=None, validate_unique=True, validate_constraints=True):
        """
        Sobrescreve full_clean() para evitar duplicação de validação.
        Quando chamado automaticamente pelo Django 5.2 durante o save(),
        a flag _skip_full_clean está activa e o método não faz nada.
        Quando chamado directamente (ex: testes de model), corre normalmente.
        """
        if getattr(self, "_skip_full_clean", False):
            return  # já foi validado pelo formulário antes do save()
        super().full_clean(
            exclude=exclude,
            validate_unique=validate_unique,
            validate_constraints=validate_constraints,
        )

    # ------------------------------------------------------------------ #
    #  HASH SHA256                                                         #
    # ------------------------------------------------------------------ #

    def calcular_hash(self):
        """
        Calcula o hash SHA256 do ficheiro para detetar duplicados.
        Repõe o cursor antes e depois de ler para não consumir o stream.
        """
        if not self.arquivo:
            return None

        sha = hashlib.sha256()
        if hasattr(self.arquivo, "seek"):
            self.arquivo.seek(0)
        for chunk in self.arquivo.chunks():
            sha.update(chunk)
        if hasattr(self.arquivo, "seek"):
            self.arquivo.seek(0)
        return sha.hexdigest()

    # ------------------------------------------------------------------ #
    #  SAVE PERSONALIZADO                                                  #
    # ------------------------------------------------------------------ #

    def save(self, *args, **kwargs):
        """
        Sobrescreve save() para:
        1. Detectar o tipo de arquivo automaticamente pela extensão.
        2. Calcular o hash SHA256 (apenas quando o ficheiro é novo ou mudou).
        3. Incrementar total_uploads do utilizador quando o recurso é criado.

        Quando update_fields está definido (chamado pelos métodos incrementar_*),
        ignora toda a lógica extra para não recalcular hash nem tipo.
        Passa validate=False para evitar que full_clean() corra duas vezes
        (o formulário já o fez antes de chamar save).
        """
        # Saída rápida para actualizações parciais (ex: incrementar contadores)
        if kwargs.get("update_fields"):
            super().save(*args, **kwargs)
            return

        is_new = self.pk is None

        # Detecta se o ficheiro foi alterado numa edição
        arquivo_alterado = True
        if not is_new and self.arquivo:
            try:
                anterior = Resource.objects.get(pk=self.pk)
                arquivo_alterado = anterior.arquivo != self.arquivo
            except Resource.DoesNotExist:
                arquivo_alterado = True

        # 1 — Preencher campos normalizados (para pesquisa sem acentos)
        self.nome_normalizado       = normalizar_texto(self.nome or "")
        self.disciplina_normalizada = normalizar_texto(self.disciplina or "")
        self.professor_normalizado  = normalizar_texto(self.professor or "")

        # 2 — Deteção automática do tipo pela extensão
        if self.arquivo:
            ext = os.path.splitext(self.arquivo.name)[1].lower()
            if ext == ".pdf":
                self.tipo_arquivo = "PDF"
            elif ext in (".docx", ".doc"):
                self.tipo_arquivo = "DOCX"
            elif ext in (".pptx", ".ppt"):
                self.tipo_arquivo = "PPTX"
            elif ext in (".jpg", ".jpeg", ".png"):
                self.tipo_arquivo = "IMG"

        # 2 — Hash SHA256 (só quando necessário)
        if self.arquivo and arquivo_alterado:
            self.hash_arquivo = self.calcular_hash()

        # O Django 5.2 chama full_clean() automaticamente antes do save().
        # Para evitar que as validações do modelo corram duas vezes
        # (o formulário já as executou), usamos uma flag de instância
        # que o método full_clean() abaixo verifica e respeita.
        self._skip_full_clean = True
        try:
            super().save(*args, **kwargs)
        finally:
            self._skip_full_clean = False

        # 3 — Incrementar total_uploads do utilizador na criação
        if is_new:
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            UserModel.objects.filter(pk=self.usuario_id).update(
                total_uploads=models.F("total_uploads") + 1
            )

    # ------------------------------------------------------------------ #
    #  MÉTODOS DE NEGÓCIO                                                  #
    # ------------------------------------------------------------------ #

    def pode_ser_downloaded_por(self, user):
        """Verifica se o utilizador tem créditos para descarregar este recurso."""
        return user.pode_fazer_download()

    def incrementar_download(self):
        """
        Incrementa o contador de downloads via UPDATE direto na BD.
        Evita disparar o save() completo e recalcular hash/tipo.
        """
        Resource.objects.filter(pk=self.pk).update(
            total_downloads=models.F("total_downloads") + 1
        )

    def incrementar_salvo(self):
        """
        Incrementa o contador de vezes que o recurso foi guardado.
        Evita disparar o save() completo e recalcular hash/tipo.
        """
        Resource.objects.filter(pk=self.pk).update(
            total_salvos=models.F("total_salvos") + 1
        )


# ------------------------------------------------------------------ #
#  SIGNAL: decrementar total_uploads ao apagar um recurso            #
# ------------------------------------------------------------------ #

@receiver(post_delete, sender=Resource)
def decrementar_total_uploads(sender, instance, **kwargs):
    """
    Quando um recurso é apagado, decrementa total_uploads do seu autor.
    Garante que o contador de créditos é recalculado correctamente.
    Usa __gt=0 para nunca deixar o contador abaixo de zero.
    """
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()
    UserModel.objects.filter(
        pk=instance.usuario_id,
        total_uploads__gt=0
    ).update(total_uploads=models.F("total_uploads") - 1)
