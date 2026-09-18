"""Models — procedimentos e protocolos."""

from django.db import models
from django.utils.text import slugify

from agenda_base.models import ServicoBase
from core.mixins import LojaIsolationManager, LojaIsolationMixin

# slug → nome (seed da loja)
CATEGORIAS_PROCEDIMENTO_PADRAO = [
    ("soroterapia", "Soroterapia"),
    ("estetica", "Estética (geral)"),
    ("facial", "Facial"),
    ("corporal", "Corporal"),
    ("capilar", "Capilar"),
    ("depilacao", "Depilação"),
    ("injetavel", "Injetável"),
    ("geral", "Geral"),
    ("outro", "Outro"),
]


class CategoriaProcedimento(LojaIsolationMixin, models.Model):
    """Categoria configurável de procedimentos da clínica."""

    nome = models.CharField(max_length=100, verbose_name="Nome")
    slug = models.SlugField(max_length=50, verbose_name="Slug")
    cor = models.CharField(max_length=7, default="#8B3D52", verbose_name="Cor")
    ordem = models.IntegerField(default=0, verbose_name="Ordem")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Categoria de procedimento"
        verbose_name_plural = "Categorias de procedimento"
        ordering = ["ordem", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "slug"],
                name="cb_proc_cat_loja_slug_uniq",
            ),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug and self.nome:
            self.slug = slugify(self.nome)[:50] or "categoria"
        super().save(*args, **kwargs)


class Procedure(ServicoBase):
    """Procedimentos/Serviços oferecidos (herda de ServicoBase)"""

    termo_consentimento = models.TextField(
        blank=True, default="", verbose_name="Termo de consentimento esclarecido",
        help_text="Use {paciente_nome}, {profissional_nome}, {clinica_nome}, {procedimentos}, {data}.",
    )
    termo_consentimento_ativo = models.BooleanField(
        default=False, verbose_name="Exigir termo de consentimento",
    )
    termo_template = models.ForeignKey(
        "TermoConsentimentoTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="procedimentos",
        verbose_name="Template de termo",
    )

    class Meta(ServicoBase.Meta):
        app_label = "clinica_beleza"
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["termo_template"],
                name="clin_cb_proc_termo_tpl_uniq",
            ),
        ]

    def __str__(self):
        return self.nome




class ProcedureProtocol(LojaIsolationMixin, models.Model):
    """Protocolos padronizados vinculados a procedimentos (Clínica da Beleza)."""

    nome = models.CharField(max_length=200, verbose_name="Nome do protocolo")
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name="protocolos",
        verbose_name="Procedimento",
    )
    descricao = models.TextField(blank=True, default="", verbose_name="Descrição")
    preparacao = models.TextField(blank=True, default="", verbose_name="Preparação")
    execucao = models.TextField(blank=True, default="", verbose_name="Execução")
    pos_procedimento = models.TextField(blank=True, default="", verbose_name="Pós-procedimento")
    tempo_estimado = models.PositiveIntegerField(default=30, verbose_name="Tempo estimado (min)")
    materiais_necessarios = models.TextField(blank=True, default="", verbose_name="Materiais necessários")
    contraindicacoes = models.TextField(blank=True, default="", verbose_name="Contraindicações")
    cuidados_especiais = models.TextField(blank=True, default="", verbose_name="Cuidados especiais")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_protocolos"
        ordering = ["procedure__nome", "nome"]
        verbose_name = "Protocolo de procedimento"
        verbose_name_plural = "Protocolos de procedimentos"

    def __str__(self):
        return f"{self.procedure.nome} — {self.nome}"


