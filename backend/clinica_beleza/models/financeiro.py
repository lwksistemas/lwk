"""Models — pagamentos e campanhas."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .appointments import Appointment


class Payment(LojaIsolationMixin, models.Model):
    """Pagamentos"""

    PAYMENT_METHOD_CHOICES = (
        ("CASH", "Dinheiro"),
        ("CREDIT_CARD", "Cartão de Crédito"),
        ("DEBIT_CARD", "Cartão de Débito"),
        ("PIX", "PIX"),
        ("TRANSFER", "Transferência"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pendente"),
        ("DRAFT", "Rascunho (consulta)"),
        ("PAID", "Pago"),
        ("PARTIAL", "Parcialmente pago"),
        ("CANCELLED", "Cancelado"),
    )

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, verbose_name="Agendamento")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor cobrado")
    valor_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Valor total original",
        help_text="Valor total do atendimento. Quando há parcelas, amount pode diferir.",
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Método de Pagamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", verbose_name="Status")
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name="Data do Pagamento")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    desconto = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Desconto (R$)",
        help_text="Valor de desconto concedido no atendimento.",
    )
    comissao_percentual = models.PositiveSmallIntegerField(default=0, verbose_name="Comissão %")
    comissao_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Comissão R$")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "payment_date"]),
            models.Index(fields=["appointment", "status"]),
            models.Index(fields=["loja_id", "payment_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["appointment"],
                name="uniq_payment_per_appointment",
            ),
        ]

    def __str__(self):
        return f"Pagamento {self.id} - R$ {self.amount}"

    @property
    def valor_total_efetivo(self):
        """Valor total do atendimento (usa valor_total se definido, senão amount)."""
        return self.valor_total if self.valor_total is not None else self.amount

    @property
    def valor_pago_parcelas(self):
        """Soma das parcelas PAID; se não houver parcelas, usa amount (legado/quitado à vista)."""
        from decimal import Decimal
        try:
            total = self.parcelas.filter(status="PAID").aggregate(
                total=models.Sum("valor"),
            )["total"]
            if total is not None:
                return total
        except Exception:
            pass
        # Sem parcelas: amount representa o já pago quando PARTIAL/PAID/DRAFT
        if self.status in ("PAID", "PARTIAL", "DRAFT"):
            return Decimal(str(self.amount or 0))
        return Decimal(0)

    @property
    def saldo_devedor(self):
        """Valor ainda em aberto = total - valor pago (parcelas ou amount)."""
        from decimal import Decimal
        try:
            saldo = self.valor_total_efetivo - self.valor_pago_parcelas
            return saldo if saldo > 0 else Decimal(0)
        except Exception:
            return self.valor_total_efetivo


class PaymentParcela(LojaIsolationMixin, models.Model):
    """Registro de cada entrada de pagamento parcial de um Payment."""

    PAYMENT_METHOD_CHOICES = Payment.PAYMENT_METHOD_CHOICES
    STATUS_CHOICES = (
        ("PAID", "Pago"),
        ("CANCELLED", "Cancelado"),
    )

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="parcelas",
        verbose_name="Pagamento",
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor recebido")
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Forma de pagamento",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PAID", verbose_name="Status")
    payment_date = models.DateField(verbose_name="Data do pagamento")
    observacoes = models.TextField(blank=True, default="", verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Parcela de pagamento"
        verbose_name_plural = "Parcelas de pagamento"
        ordering = ["payment_date", "created_at"]
        indexes = [
            models.Index(fields=["payment", "status"], name="cb_parcela_payment_status_idx"),
        ]

    def __str__(self):
        return f"Parcela {self.id} — R$ {self.valor} em {self.payment_date}"




class CampanhaPromocao(LojaIsolationMixin, models.Model):
    """Campanha de promoção: mensagem enviada em massa aos pacientes via WhatsApp.
    Tabela isolada por loja: cada loja tem sua própria tabela no schema (loja_*).
    Router: clinica_beleza está em loja_apps; migrate_all_lojas aplica em cada schema.
    """

    titulo = models.CharField(max_length=200, verbose_name="Título da campanha")
    mensagem = models.TextField(verbose_name="Mensagem (enviada por WhatsApp)")
    data_inicio = models.DateField(blank=True, null=True, verbose_name="Vigência início")
    data_fim = models.DateField(blank=True, null=True, verbose_name="Vigência fim")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    enviada_em = models.DateTimeField(blank=True, null=True, verbose_name="Enviada em")
    total_enviados = models.PositiveIntegerField(default=0, verbose_name="Total de mensagens enviadas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Campanha de promoção"
        verbose_name_plural = "Campanhas de promoções"
        ordering = ["-created_at"]

    def __str__(self):
        return self.titulo


CATEGORIAS_DESPESA_PADRAO = (
    "Aluguel",
    "Salários",
    "Fornecedores",
    "Impostos",
    "Marketing",
    "Equipamentos",
    "Outros",
)


class CategoriaDespesa(LojaIsolationMixin, models.Model):
    """Categoria para organizar despesas da clínica."""

    nome = models.CharField(max_length=100, verbose_name="Nome")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Categoria de despesa"
        verbose_name_plural = "Categorias de despesa"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Despesa(LojaIsolationMixin, models.Model):
    """Despesa operacional da clínica (aluguel, fornecedores, etc.)."""

    STATUS_CHOICES = Payment.STATUS_CHOICES
    PAYMENT_METHOD_CHOICES = Payment.PAYMENT_METHOD_CHOICES

    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    categoria = models.ForeignKey(
        CategoriaDespesa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="despesas",
        verbose_name="Categoria",
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING", verbose_name="Status",
    )
    data_vencimento = models.DateField(verbose_name="Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data do pagamento")
    forma_pagamento = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, default="", verbose_name="Forma de pagamento",
    )
    observacoes = models.TextField(blank=True, default="", verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ["-data_vencimento", "-created_at"]
        indexes = [
            models.Index(fields=["loja_id", "status"]),
            models.Index(fields=["loja_id", "data_vencimento"]),
            models.Index(fields=["loja_id", "data_pagamento"]),
        ]

    def __str__(self):
        return f"{self.descricao} — R$ {self.valor}"


# ═══════════════════════════════════════════════════════════════════════════════
# ESTOQUE — Controle de produtos (botox, ácido hialurônico, soros, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

