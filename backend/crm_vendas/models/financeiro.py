"""Financeiro CRM — receitas e despesas por vendedor."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class GrupoFinanceiroCRM(LojaIsolationMixin, models.Model):
    """Grupo/categoria para receitas ou despesas do vendedor."""

    TIPO_RECEITA = "receita"
    TIPO_DESPESA = "despesa"
    TIPO_CHOICES = (
        (TIPO_RECEITA, "Receita"),
        (TIPO_DESPESA, "Despesa"),
    )

    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "crm_vendas"
        db_table = "crm_financeiro_grupo"
        verbose_name = "Grupo financeiro CRM"
        verbose_name_plural = "Grupos financeiros CRM"
        ordering = ["tipo", "ordem", "nome"]
        indexes = [
            models.Index(fields=["loja_id", "tipo", "is_active"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.nome}"


class LancamentoFinanceiroCRM(LojaIsolationMixin, models.Model):
    """Lançamento de receita ou despesa vinculado a um vendedor."""

    TIPO_RECEITA = "receita"
    TIPO_DESPESA = "despesa"
    TIPO_CHOICES = (
        (TIPO_RECEITA, "Receita"),
        (TIPO_DESPESA, "Despesa"),
    )

    STATUS_PENDENTE = "pendente"
    STATUS_PAGO = "pago"
    STATUS_CANCELADO = "cancelado"
    STATUS_CHOICES = (
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_PAGO, "Pago"),
        (STATUS_CANCELADO, "Cancelado"),
    )

    ORIGEM_MANUAL = "manual"
    ORIGEM_COMISSAO = "comissao_venda"
    ORIGEM_RECORRENCIA = "recorrencia"
    ORIGEM_CHOICES = (
        (ORIGEM_MANUAL, "Manual"),
        (ORIGEM_COMISSAO, "Comissão de venda"),
        (ORIGEM_RECORRENCIA, "Recorrência automática"),
    )

    vendedor = models.ForeignKey(
        "crm_vendas.Vendedor",
        on_delete=models.CASCADE,
        related_name="lancamentos_financeiros",
        verbose_name="Vendedor",
    )
    grupo = models.ForeignKey(
        GrupoFinanceiroCRM,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos",
        verbose_name="Grupo",
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default=ORIGEM_MANUAL,
        verbose_name="Origem",
    )
    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor (R$)")
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        verbose_name="Status",
    )
    data_vencimento = models.DateField(verbose_name="Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data do pagamento")
    oportunidade = models.OneToOneField(
        "crm_vendas.Oportunidade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamento_comissao",
        verbose_name="Oportunidade (comissão)",
    )
    observacoes = models.TextField(blank=True, default="", verbose_name="Observações")
    recorrencia = models.ForeignKey(
        "crm_vendas.RecorrenciaFinanceiroCRM",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos_gerados",
        verbose_name="Recorrência",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "crm_vendas"
        db_table = "crm_financeiro_lancamento"
        verbose_name = "Lançamento financeiro CRM"
        verbose_name_plural = "Lançamentos financeiros CRM"
        ordering = ["-data_vencimento", "-created_at"]
        indexes = [
            models.Index(fields=["loja_id", "tipo", "status"]),
            models.Index(fields=["loja_id", "vendedor_id", "tipo"]),
            models.Index(fields=["loja_id", "data_vencimento"]),
            models.Index(fields=["loja_id", "data_pagamento"], name="crm_lanc_loja_dtpag_idx"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.descricao} — R$ {self.valor}"


class RecorrenciaFinanceiroCRM(LojaIsolationMixin, models.Model):
    """Modelo de despesa/receita recorrente — gera lançamentos automaticamente."""

    FREQ_MENSAL = "mensal"
    FREQ_TRIMESTRAL = "trimestral"
    FREQ_ANUAL = "anual"
    FREQ_CHOICES = (
        (FREQ_MENSAL, "Mensal"),
        (FREQ_TRIMESTRAL, "Trimestral"),
        (FREQ_ANUAL, "Anual"),
    )

    vendedor = models.ForeignKey(
        "crm_vendas.Vendedor",
        on_delete=models.CASCADE,
        related_name="recorrencias_financeiras",
        verbose_name="Vendedor",
    )
    grupo = models.ForeignKey(
        GrupoFinanceiroCRM,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorrencias",
        verbose_name="Grupo",
    )
    tipo = models.CharField(max_length=10, choices=GrupoFinanceiroCRM.TIPO_CHOICES, verbose_name="Tipo")
    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor (R$)")
    frequencia = models.CharField(
        max_length=12,
        choices=FREQ_CHOICES,
        default=FREQ_MENSAL,
        verbose_name="Frequência",
    )
    proximo_vencimento = models.DateField(verbose_name="Próximo vencimento")
    data_fim = models.DateField(null=True, blank=True, verbose_name="Encerrar em")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    observacoes = models.TextField(blank=True, default="", verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "crm_vendas"
        db_table = "crm_financeiro_recorrencia"
        verbose_name = "Recorrência financeira CRM"
        verbose_name_plural = "Recorrências financeiras CRM"
        ordering = ["tipo", "descricao"]
        indexes = [
            models.Index(fields=["loja_id", "is_active", "proximo_vencimento"]),
            models.Index(fields=["loja_id", "vendedor_id", "tipo"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} recorrente — {self.descricao}"
