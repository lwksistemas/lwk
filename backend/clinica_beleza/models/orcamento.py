"""Models — Orçamento de procedimentos para pacientes."""
from decimal import Decimal

from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class OrcamentoConsulta(LojaIsolationMixin, models.Model):
    """Orçamento vinculado a uma consulta — lista procedimentos com valores para o paciente."""

    STATUS_CHOICES = (
        ("RASCUNHO", "Rascunho"),
        ("ENVIADO", "Enviado"),
        ("ACEITO", "Aceito"),
        ("RECUSADO", "Recusado"),
    )

    consulta = models.ForeignKey(
        "clinica_beleza.Consulta",
        on_delete=models.CASCADE,
        related_name="orcamentos",
        verbose_name="Consulta",
    )
    patient = models.ForeignKey(
        "clinica_beleza.Patient",
        on_delete=models.CASCADE,
        related_name="orcamentos",
        verbose_name="Paciente",
    )
    professional = models.ForeignKey(
        "clinica_beleza.Professional",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orcamentos",
        verbose_name="Profissional",
    )
    observacoes = models.TextField(blank=True, default="", verbose_name="Observações")
    valor_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Valor Total",
    )
    validade_dias = models.PositiveIntegerField(default=30, verbose_name="Validade (dias)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RASCUNHO")
    enviado_email = models.BooleanField(default=False)
    enviado_whatsapp = models.BooleanField(default=False)
    data_envio = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_orcamento_consulta"
        ordering = ["-created_at"]
        verbose_name = "Orçamento"
        verbose_name_plural = "Orçamentos"

    def __str__(self):
        return f"Orçamento #{self.id} — {self.patient.nome if self.patient else '?'} (R$ {self.valor_total})"


class OrcamentoItem(models.Model):
    """Item do orçamento — procedimento com valor customizado."""

    orcamento = models.ForeignKey(
        OrcamentoConsulta, on_delete=models.CASCADE, related_name="itens",
    )
    procedure = models.ForeignKey(
        "clinica_beleza.Procedure", on_delete=models.SET_NULL, null=True, blank=True,
    )
    nome_procedimento = models.CharField(max_length=200, verbose_name="Procedimento")
    descricao_procedimento = models.TextField(blank=True, default="")
    valor_original = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Original")
    valor_customizado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Orçado")
    quantidade = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    observacao_item = models.TextField(blank=True, default="", verbose_name="Observação")

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_orcamento_item"
        ordering = ["id"]

    def __str__(self):
        return f"{self.nome_procedimento} x{self.quantidade} = R$ {self.valor_customizado * self.quantidade}"

    @property
    def subtotal(self):
        return self.valor_customizado * self.quantidade
