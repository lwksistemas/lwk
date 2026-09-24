"""Contrato comercial do protocolo e produtos por sessão."""

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
        ("POR_CONSULTA", "Por consulta"),
        ("TOTAL", "Valor total"),
    )

    protocol = models.ForeignKey(
        ProcedureProtocol,
        on_delete=models.PROTECT,
        related_name="contratos",
        verbose_name="Protocolo",
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
    )
    local_atendimento = models.ForeignKey(
        LocalAtendimento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="protocolos_contratados",
        verbose_name="Local de atendimento",
    )
    forma_cobranca = models.CharField(max_length=20, choices=FORMA_CHOICES, verbose_name="Forma de cobrança")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor do protocolo (R$)")
    data_inicio = models.DateTimeField(verbose_name="Primeira sessão")
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
        return f"{self.protocol_id} · paciente {self.patient_id}"
