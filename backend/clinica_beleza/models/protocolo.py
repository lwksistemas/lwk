"""Contrato comercial do protocolo e produtos por sessão."""

from decimal import Decimal

from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .convenios import LocalAtendimento
from .estoque import ProdutoEstoque
from .patients import Patient
from .procedures import ProcedureProtocol
from .professionals import Professional


class ProtocoloProduto(LojaIsolationMixin, models.Model):
    """Quantidade de um produto do estoque consumida em cada sessão."""

    protocol = models.ForeignKey(
        ProcedureProtocol,
        on_delete=models.CASCADE,
        related_name="produtos",
        verbose_name="Protocolo",
    )
    produto = models.ForeignKey(
        ProdutoEstoque,
        on_delete=models.PROTECT,
        related_name="protocolos",
        verbose_name="Produto",
    )
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade por sessão")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_protocolo_produto"
        verbose_name = "Produto do protocolo"
        verbose_name_plural = "Produtos do protocolo"
        constraints = [
            models.UniqueConstraint(
                fields=["protocol", "produto"],
                name="cb_protocolo_produto_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.produto_id} x{self.quantidade}"


class ProtocoloContrato(LojaIsolationMixin, models.Model):
    """Plano vendido a um paciente: sessões na agenda e forma de cobrança."""

    FORMA_CHOICES = (
        ("", "A definir"),
        ("POR_CONSULTA", "Por consulta"),
        ("TOTAL", "Valor total"),
    )

    protocol = models.ForeignKey(
        ProcedureProtocol,
        on_delete=models.PROTECT,
        related_name="contratos",
        verbose_name="Protocolo",
        null=True,
        blank=True,
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="protocolos_contratados",
        verbose_name="Paciente",
    )
    professional = models.ForeignKey(
        Professional,
        on_delete=models.PROTECT,
        related_name="protocolos_contratados",
        verbose_name="Profissional",
        null=True,
        blank=True,
    )
    local_atendimento = models.ForeignKey(
        LocalAtendimento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="protocolos_contratados",
        verbose_name="Local de atendimento",
    )
    DESCONTO_FIXO = "fixo"
    DESCONTO_PERCENTUAL = "percentual"
    DESCONTO_CHOICES = (
        ("", "—"),
        (DESCONTO_FIXO, "Valor fixo"),
        (DESCONTO_PERCENTUAL, "Porcentagem"),
    )

    forma_cobranca = models.CharField(
        max_length=20, choices=FORMA_CHOICES, blank=True, default="", verbose_name="Forma de cobrança",
    )
    nome = models.CharField(max_length=200, blank=True, default="", verbose_name="Nome do tratamento")
    valor_bruto = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Soma dos procedimentos (R$)",
    )
    desconto_tipo = models.CharField(
        max_length=20, choices=DESCONTO_CHOICES, blank=True, default="", verbose_name="Tipo de desconto",
    )
    desconto_valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Desconto informado",
    )
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor do protocolo (R$)")
    tempo_minutos = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Duração de cada atendimento (min)",
    )
    intervalo_quantidade = models.PositiveIntegerField(null=True, blank=True, verbose_name="Intervalo")
    intervalo_unidade = models.CharField(max_length=10, blank=True, default="", verbose_name="Unidade do intervalo")
    data_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Primeira sessão")
    sessoes = models.PositiveIntegerField(verbose_name="Sessões")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_protocolo_contrato"
        verbose_name = "Contrato de protocolo"
        verbose_name_plural = "Contratos de protocolo"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nome or self.protocol_id} · paciente {self.patient_id}"


class ProtocoloContratoProcedimento(LojaIsolationMixin, models.Model):
    """Procedimento que compõe o protocolo personalizado da cliente."""

    contrato = models.ForeignKey(
        ProtocoloContrato,
        on_delete=models.CASCADE,
        related_name="procedimentos",
        verbose_name="Contrato",
    )
    procedure = models.ForeignKey(
        "Procedure",
        on_delete=models.PROTECT,
        related_name="protocolos_personalizados",
        verbose_name="Procedimento",
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor no pacote (R$)")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_protocolo_contrato_procedimento"
        verbose_name = "Procedimento do protocolo personalizado"
        verbose_name_plural = "Procedimentos do protocolo personalizado"
        constraints = [
            models.UniqueConstraint(
                fields=["contrato", "procedure"],
                name="cb_protocolo_contrato_proc_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.procedure_id} · {self.valor}"


class ProtocoloContratoProduto(LojaIsolationMixin, models.Model):
    """Quantidade de produto consumida em cada sessão do protocolo personalizado."""

    contrato = models.ForeignKey(
        ProtocoloContrato,
        on_delete=models.CASCADE,
        related_name="produtos_sessao",
        verbose_name="Contrato",
    )
    produto = models.ForeignKey(
        ProdutoEstoque,
        on_delete=models.PROTECT,
        related_name="protocolos_personalizados",
        verbose_name="Produto",
    )
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade por sessão")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_protocolo_contrato_produto"
        verbose_name = "Produto do protocolo personalizado"
        verbose_name_plural = "Produtos do protocolo personalizado"
        constraints = [
            models.UniqueConstraint(
                fields=["contrato", "produto"],
                name="cb_protocolo_contrato_produto_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.produto_id} x{self.quantidade}"
