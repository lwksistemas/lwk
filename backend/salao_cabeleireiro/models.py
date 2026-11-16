"""Agenda do salão. Reusa os modelos abstratos da agenda e troca o vocabulário da clínica."""
from datetime import timedelta
from decimal import Decimal

from django.db import models

from core.mixins import LojaIsolationManager

from salao_cabeleireiro.models_fiscal import SalaoNFSeConfig, SalaoNfceConfig  # noqa: F401

from agenda_base.models import (
    BloqueioAgendaBase,
    ClienteBase,
    HorarioTrabalhoProfissionalBase,
    ProfissionalBase,
    ServicoBase,
)


PAINEIS = (
    ("operacao", "Operação do dia"),
    ("gestao", "Gestão do mês"),
    ("semana", "Agenda da semana"),
)

STATUS_AGENDAMENTO = (
    ("SCHEDULED", "Aguardando"),
    ("CONFIRMED", "Confirmado"),
    ("IN_PROGRESS", "Em atendimento"),
    ("COMPLETED", "Concluído"),
    ("CANCELLED", "Cancelado"),
    ("NO_SHOW", "Faltou"),
)

STATUS_OCUPA_HORARIO = ("SCHEDULED", "CONFIRMED", "IN_PROGRESS", "COMPLETED")

FORMAS_PAGAMENTO = (
    ("dinheiro", "Dinheiro"),
    ("pix", "Pix"),
    ("debito", "Débito"),
    ("credito", "Crédito"),
)


class SalaoConfig(models.Model):
    """Painel escolhido pelo administrador. Vale para a loja inteira."""

    loja_id = models.IntegerField(unique=True, db_index=True)
    painel = models.CharField(max_length=20, choices=PAINEIS, default="operacao")
    enviar_confirmacao = models.BooleanField(default=False)
    enviar_lembrete = models.BooleanField(default=False)
    lembrete_horas = models.PositiveSmallIntegerField(default=24)
    enviar_reagendamento = models.BooleanField(default=False)
    enviar_cancelamento = models.BooleanField(default=False)
    modelo = models.CharField(max_length=20, default="recepcionista")
    local_recebimento = models.CharField(max_length=20, default="caixa")
    objects = LojaIsolationManager()

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Configuração do salão"


class Cliente(ClienteBase):
    class Meta:
        verbose_name = "Cliente"
        ordering = ["nome"]


class Profissional(ProfissionalBase):
    comissao_tipo = models.CharField(max_length=12, default="percentual")
    comissao_fixa = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name = "Profissional"
        ordering = ["nome"]


class Servico(ServicoBase):
    class Meta:
        verbose_name = "Serviço"
        ordering = ["categoria", "nome"]


class ComissaoProcedimento(models.Model):
    """Comissão deste profissional neste serviço. Sem registro, vale a comissão padrão dele."""

    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name="comissoes")
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name="comissoes")
    tipo = models.CharField(max_length=12, default="percentual")
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name = "Comissão do procedimento"
        constraints = [
            models.UniqueConstraint(fields=["profissional", "servico"], name="salao_comissao_profissional_servico"),
        ]


class HorarioTrabalho(HorarioTrabalhoProfissionalBase):
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="horarios",
    )

    class Meta:
        verbose_name = "Horário de trabalho"
        ordering = ["dia_semana"]
        unique_together = [["profissional", "dia_semana"]]


class Bloqueio(BloqueioAgendaBase):
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="bloqueios",
    )

    class Meta:
        verbose_name = "Bloqueio"
        ordering = ["data_inicio"]


class Agendamento(models.Model):
    loja_id = models.IntegerField(db_index=True)
    inicio = models.DateTimeField(verbose_name="Início")
    duracao_minutos = models.PositiveIntegerField(verbose_name="Duração (min)")
    status = models.CharField(max_length=20, choices=STATUS_AGENDAMENTO, default="SCHEDULED")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="agendamentos")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="agendamentos")
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name="agendamentos")
    observacoes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = LojaIsolationManager()

    class Meta:
        verbose_name = "Agendamento"
        ordering = ["inicio"]
        indexes = [
            models.Index(fields=["loja_id", "inicio"]),
            models.Index(fields=["profissional", "inicio"]),
        ]

    @property
    def fim(self):
        return self.inicio + timedelta(minutes=int(self.duracao_minutos or 0))

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)


class Recebimento(models.Model):
    """Dinheiro que entrou no caixa. O preço do serviço, sozinho, não é receita."""

    loja_id = models.IntegerField(db_index=True)
    agendamento = models.ForeignKey(Agendamento, on_delete=models.PROTECT, related_name="recebimentos")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="recebimentos")
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    forma = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO)
    partes = models.JSONField(default=list, blank=True)
    comissao_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    comissao_valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    observacao = models.CharField(max_length=200, blank=True, default="")
    venda = models.ForeignKey(
        "Venda",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="recebimentos_da_venda",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = LojaIsolationManager()

    class Meta:
        verbose_name = "Recebimento"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["agendamento"],
                condition=models.Q(is_active=True),
                name="salao_um_recebimento_ativo",
            ),
        ]

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)


class Produto(models.Model):
    """Produto vendido no caixa. O saldo só muda depois que a venda é confirmada."""

    loja_id = models.IntegerField(db_index=True)
    nome = models.CharField(max_length=200, verbose_name="Nome comercial")
    fornecedor = models.CharField(max_length=100, blank=True, default="", verbose_name="Nome do fornecedor")
    codigo_barras = models.CharField(max_length=40, blank=True, default="")
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    saldo = models.PositiveIntegerField(default=0)
    comissao_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = LojaIsolationManager()

    class Meta:
        verbose_name = "Produto"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "codigo_barras"],
                condition=~models.Q(codigo_barras="") & models.Q(is_active=True),
                name="salao_produto_codigo_ativo",
            ),
        ]

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)


class Venda(models.Model):
    """Um recebimento do caixa. Serviço e produto ficam separados por dentro."""

    loja_id = models.IntegerField(db_index=True)
    numero = models.PositiveIntegerField()
    agendamento = models.ForeignKey(Agendamento, null=True, blank=True, on_delete=models.PROTECT, related_name="vendas")
    recebimento = models.ForeignKey(Recebimento, null=True, blank=True, on_delete=models.PROTECT, related_name="vendas")
    cliente_nome = models.CharField(max_length=160, blank=True, default="")
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    valor_produtos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    forma = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO, default="dinheiro")
    partes = models.JSONField(default=list, blank=True)
    partes_produtos = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = LojaIsolationManager()

    class Meta:
        verbose_name = "Venda do caixa"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)


class VendaItem(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="itens")
    nome = models.CharField(max_length=200)
    quantidade = models.PositiveIntegerField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    comissao_valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    estoque_baixado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Item da venda"


class MovimentoEstoque(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="movimentos")
    venda = models.ForeignKey(Venda, null=True, blank=True, on_delete=models.SET_NULL, related_name="movimentos")
    tipo = models.CharField(max_length=20)
    quantidade = models.IntegerField()
    saldo_depois = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimento de estoque"
        ordering = ["-created_at"]


class NotaEntradaSalao(models.Model):
    """NF-e de fornecedor. O saldo só muda quando o caixa confirma a importação."""

    STATUS_RESUMO = "resumo"
    STATUS_PENDENTE = "pendente"
    STATUS_IMPORTADA = "importada"
    STATUS_IGNORADA = "ignorada"

    loja_id = models.IntegerField(db_index=True)
    chave = models.CharField(max_length=44)
    numero = models.CharField(max_length=20, blank=True, default="")
    fornecedor_nome = models.CharField(max_length=200, blank=True, default="")
    fornecedor_documento = models.CharField(max_length=20, blank=True, default="")
    destinatario_documento = models.CharField(max_length=20, blank=True, default="")
    data_emissao = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    xml = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, default=STATUS_PENDENTE)
    origem = models.CharField(max_length=20, default="arquivo")
    nsu = models.CharField(max_length=20, blank=True, default="")
    ultimo_erro = models.TextField(blank=True, default="")
    importada_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = LojaIsolationManager()

    class Meta:
        verbose_name = "NF-e de entrada"
        ordering = ["-data_emissao", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["loja_id", "chave"], name="salao_nfe_entrada_loja_chave"),
        ]

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)


class NfeDistribuicaoSalao(models.Model):
    """Último ponto da consulta de NF-e na SEFAZ deste salão."""

    loja_id = models.IntegerField(db_index=True)
    ult_nsu = models.CharField(max_length=15, default="000000000000000")
    max_nsu = models.CharField(max_length=15, default="000000000000000")
    consultado_em = models.DateTimeField(null=True, blank=True)
    ultimo_erro = models.TextField(blank=True, default="")
    objects = LojaIsolationManager()

    class Meta:
        verbose_name = "Consulta de NF-e"
        constraints = [
            models.UniqueConstraint(fields=["loja_id"], name="salao_nfe_dist_loja"),
        ]

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)
