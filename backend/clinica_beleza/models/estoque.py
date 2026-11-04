"""Models — estoque."""
from django.db import models
from django.utils.text import slugify

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .appointments import Appointment
from .procedures import Procedure
from .professionals import Professional

# Categorias padrão (seed) — slug → nome
CATEGORIAS_ESTOQUE_PADRAO = [
    ("injetavel", "Injetável"),
    ("soroterapia", "Soroterapia"),
    ("cosmético", "Cosmético"),
    ("medicamentos", "Medicamentos"),
    ("descartavel", "Descartável"),
    ("equipamento", "Equipamento"),
    ("outro", "Outro"),
]


class CategoriaEstoque(LojaIsolationMixin, models.Model):
    """Categoria configurável do estoque da clínica."""

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
        verbose_name = "Categoria de estoque"
        verbose_name_plural = "Categorias de estoque"
        ordering = ["ordem", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "slug"],
                name="cb_estoque_cat_loja_slug_uniq",
            ),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug and self.nome:
            self.slug = slugify(self.nome, allow_unicode=True)[:50] or "categoria"
        super().save(*args, **kwargs)


class ProdutoEstoque(LojaIsolationMixin, models.Model):
    """Produto do estoque da clínica (botox, ácido hialurônico, soro, etc.)"""

    # Compat / seed; preferir FK categoria.
    CATEGORIA_CHOICES = list(CATEGORIAS_ESTOQUE_PADRAO)

    nome = models.CharField(max_length=200, verbose_name="Nome do produto")
    categoria = models.ForeignKey(
        CategoriaEstoque,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="produtos",
        verbose_name="Categoria",
    )
    marca = models.CharField(max_length=100, blank=True, default="", verbose_name="Marca/Fabricante")
    unidade_medida = models.CharField(
        max_length=30,
        default="unidade",
        verbose_name="Unidade de medida",
        help_text="Ex: unidade, ml, mg, ampola, frasco",
    )
    quantidade_atual = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Quantidade atual",
    )
    quantidade_minima = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Estoque mínimo",
        help_text="Alerta quando atingir este valor",
    )
    preco_custo = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Preço de custo (R$)",
    )
    preco_venda = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Preço de venda (R$)",
    )
    vende_ao_cliente = models.BooleanField(
        default=False,
        verbose_name="Pode vender ao cliente",
        help_text="Insumo de procedimento continua só baixando o estoque. Só o marcado aqui entra no recibo.",
    )
    validade = models.DateField(null=True, blank=True, verbose_name="Data de validade")
    lote = models.CharField(max_length=50, blank=True, default="", verbose_name="Lote")
    numero_nota = models.CharField(
        max_length=50, blank=True, default="", verbose_name="Número da nota fiscal",
    )
    observacoes = models.TextField(blank=True, default="", verbose_name="Observações")
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="produtos_estoque",
        verbose_name="Procedimento vinculado",
        help_text="Vincula o produto ao procedimento (ex.: termo de consentimento).",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    dias_alerta_validade = models.PositiveIntegerField(
        default=90,
        verbose_name="Dias para alerta de validade",
        help_text="Quantidade de dias antes do vencimento para emitir alerta (ex: 90).",
    )
    exige_lote = models.BooleanField(
        default=False,
        verbose_name="Exigir lote e validade na entrada",
        help_text="A NF-e só entra se o item tiver lote e validade. O saldo já lançado não muda.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Produto do estoque"
        verbose_name_plural = "Produtos do estoque"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["validade"], name="cb_estoque_validade_idx"),
        ]

    def __str__(self):
        return f"{self.nome} ({self.quantidade_atual} {self.unidade_medida})"

    @property
    def categoria_slug(self):
        return self.categoria.slug if self.categoria_id else "outro"

    @property
    def categoria_display(self):
        return self.categoria.nome if self.categoria_id else "Outro"

    @property
    def estoque_baixo(self):
        return self.quantidade_atual <= self.quantidade_minima

    @property
    def validade_proxima(self):
        if not self.validade:
            return False
        from datetime import date, timedelta
        limite = date.today() + timedelta(days=self.dias_alerta_validade)
        return self.validade <= limite


class MovimentacaoEstoque(LojaIsolationMixin, models.Model):
    """Registro de entrada/saída de produtos do estoque."""

    TIPO_CHOICES = [
        ("entrada", "Entrada"),
        ("saida", "Saída"),
        ("ajuste", "Ajuste de inventário"),
    ]

    produto = models.ForeignKey(ProdutoEstoque, on_delete=models.CASCADE, related_name="movimentacoes")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade")
    motivo = models.CharField(max_length=200, blank=True, default="", verbose_name="Motivo/Observação")
    profissional = models.ForeignKey(
        Professional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Profissional responsável",
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Agendamento vinculado",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data da movimentação")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["produto", "-created_at"], name="cb_movest_produto_idx"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})"


class ConsultaProdutoUtilizado(LojaIsolationMixin, models.Model):
    """Produto do estoque utilizado em uma consulta (baixa ao finalizar)."""

    consulta = models.ForeignKey(
        "Consulta",
        on_delete=models.CASCADE,
        related_name="produtos_estoque",
        verbose_name="Consulta",
    )
    produto = models.ForeignKey(
        ProdutoEstoque,
        on_delete=models.PROTECT,
        related_name="uso_em_consultas",
        verbose_name="Produto",
    )
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade utilizada")
    finalidade = models.CharField(
        max_length=10,
        choices=[("uso", "Utilizado no procedimento"), ("venda", "Vendido ao cliente")],
        default="uso",
        verbose_name="Finalidade",
    )
    preco_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Preço unitário de venda",
    )
    desconto = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Desconto da linha (R$)",
    )
    estornado = models.BooleanField(default=False, verbose_name="Venda estornada")
    lote = models.CharField(max_length=50, blank=True, default="", verbose_name="Lote utilizado")
    validade = models.DateField(null=True, blank=True, verbose_name="Validade do lote")
    estoque_baixado = models.BooleanField(default=False, verbose_name="Estoque já baixado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Registrado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Produto utilizado na consulta"
        verbose_name_plural = "Produtos utilizados na consulta"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.produto.nome} x{self.quantidade} (consulta {self.consulta_id})"


class NotaEntradaNfe(LojaIsolationMixin, models.Model):
    """NF-e de fornecedor aguardando confirmação para entrar no estoque."""

    STATUS_RESUMO = "resumo"
    STATUS_PENDENTE = "pendente"
    STATUS_IMPORTADA = "importada"
    STATUS_IGNORADA = "ignorada"
    STATUS_CHOICES = [
        (STATUS_RESUMO, "Aguardando XML"),
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_IMPORTADA, "Importada"),
        (STATUS_IGNORADA, "Ignorada"),
    ]
    ORIGEM_SEFAZ = "sefaz"
    ORIGEM_ARQUIVO = "arquivo"

    chave = models.CharField(max_length=44, verbose_name="Chave da NF-e")
    numero = models.CharField(max_length=20, blank=True, default="")
    fornecedor_nome = models.CharField(max_length=200, blank=True, default="")
    fornecedor_documento = models.CharField(max_length=20, blank=True, default="")
    destinatario_documento = models.CharField(max_length=20, blank=True, default="")
    data_emissao = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    xml = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    origem = models.CharField(max_length=20, default=ORIGEM_ARQUIVO)
    nsu = models.CharField(max_length=20, blank=True, default="")
    ultimo_erro = models.TextField(blank=True, default="")
    importada_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_notaentradanfe"
        verbose_name = "NF-e de entrada"
        ordering = ["-data_emissao", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["loja_id", "chave"], name="cb_nfe_entrada_loja_chave"),
        ]

    def __str__(self):
        return f"NF {self.numero or self.chave[-8:]}"


class VinculoProdutoFornecedor(LojaIsolationMixin, models.Model):
    """Código e preço de um fornecedor para um produto já existente no estoque."""

    produto = models.ForeignKey(
        ProdutoEstoque,
        on_delete=models.CASCADE,
        related_name="vinculos_fornecedor",
    )
    documento = models.CharField(max_length=20, verbose_name="CPF/CNPJ do fornecedor")
    codigo = models.CharField(max_length=60, verbose_name="Código na NF do fornecedor")
    gtin = models.CharField(max_length=14, blank=True, default="", verbose_name="GTIN/EAN")
    fator = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1,
        verbose_name="Unidades de estoque por unidade da nota",
    )
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Último custo unitário")
    nome_no_fornecedor = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_vinculo_produto_fornecedor"
        verbose_name = "Vínculo produto-fornecedor"
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "documento", "codigo"],
                name="cb_vinc_forn_codigo_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["loja_id", "gtin"], name="cb_vinc_forn_gtin_idx"),
        ]

    def __str__(self):
        return f"{self.documento} {self.codigo}"


class CompraFornecedorEstoque(LojaIsolationMixin, models.Model):
    """Cada entrada de NF-e de um fornecedor para o mesmo produto interno."""

    produto = models.ForeignKey(
        ProdutoEstoque,
        on_delete=models.CASCADE,
        related_name="compras_fornecedor",
    )
    documento = models.CharField(max_length=20, blank=True, default="")
    fornecedor_nome = models.CharField(max_length=200, blank=True, default="")
    codigo = models.CharField(max_length=60, blank=True, default="")
    chave = models.CharField(max_length=44, blank=True, default="")
    numero_nota = models.CharField(max_length=20, blank=True, default="")
    data_compra = models.DateField(null=True, blank=True)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidade = models.CharField(max_length=30, blank=True, default="")
    quantidade_estoque = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidade_estoque = models.CharField(max_length=30, blank=True, default="")
    fator = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lote = models.CharField(max_length=50, blank=True, default="")
    validade = models.DateField(null=True, blank=True)
    usuario = models.CharField(max_length=80, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_compra_fornecedor_estoque"
        verbose_name = "Compra de fornecedor"
        ordering = ["-data_compra", "-id"]
        indexes = [
            models.Index(fields=["loja_id", "produto", "-created_at"], name="cb_compra_forn_prod_idx"),
        ]

    def __str__(self):
        return f"NF {self.numero_nota} · {self.produto_id}"


class LoteProdutoEstoque(LojaIsolationMixin, models.Model):
    """Saldo de um lote. O saldo do produto continua em quantidade_atual."""

    produto = models.ForeignKey(
        ProdutoEstoque,
        on_delete=models.CASCADE,
        related_name="lotes_estoque",
    )
    codigo = models.CharField(max_length=50, blank=True, default="", verbose_name="Lote")
    validade = models.DateField(null=True, blank=True)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    documento = models.CharField(max_length=20, blank=True, default="")
    fornecedor_nome = models.CharField(max_length=200, blank=True, default="")
    numero_nota = models.CharField(max_length=20, blank=True, default="")
    chave = models.CharField(max_length=44, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_lote_produto_estoque"
        verbose_name = "Lote do produto"
        ordering = ["validade", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "produto", "codigo", "validade"],
                name="cb_lote_prod_uniq",
                nulls_distinct=False,
            ),
        ]

    def __str__(self):
        return f"{self.codigo or 'sem lote'} ({self.quantidade})"


class NfeDistribuicaoEstado(LojaIsolationMixin, models.Model):
    """Ponto da consulta de NF-e na SEFAZ, uma linha por loja."""

    ult_nsu = models.CharField(max_length=15, default="000000000000000")
    max_nsu = models.CharField(max_length=15, default="000000000000000")
    consultado_em = models.DateTimeField(null=True, blank=True)
    ultimo_erro = models.TextField(blank=True, default="")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_nfedistribuicaoestado"
        constraints = [
            models.UniqueConstraint(fields=["loja_id"], name="cb_nfe_dist_loja"),
        ]


class SessaoCaixa(LojaIsolationMixin, models.Model):
    """Gaveta aberta pela secretária. O recebimento da profissional não entra aqui."""

    STATUS_ABERTA = "aberta"
    STATUS_FECHADA = "fechada"
    operador_id = models.IntegerField(null=True, blank=True)
    operador_nome = models.CharField(max_length=150, blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=[(STATUS_ABERTA, "Aberta"), (STATUS_FECHADA, "Fechada")],
        default=STATUS_ABERTA,
    )
    aberta_em = models.DateTimeField(auto_now_add=True)
    fechada_em = models.DateTimeField(null=True, blank=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        ordering = ["-aberta_em"]


class VendaBalcao(LojaIsolationMixin, models.Model):
    """Venda de produto sem atendimento. O recibo sai pelo pagamento ligado."""

    STATUS_CONCLUIDA = "concluida"
    STATUS_CANCELADA = "cancelada"
    paciente = models.ForeignKey(
        "Patient", null=True, blank=True, on_delete=models.PROTECT, related_name="vendas_balcao", verbose_name="Cliente",
    )
    nome_cliente = models.CharField(max_length=200, blank=True, default="")
    telefone_cliente = models.CharField(max_length=30, blank=True, default="")
    email_cliente = models.CharField(max_length=200, blank=True, default="")
    operador_id = models.IntegerField(null=True, blank=True)
    operador_nome = models.CharField(max_length=150, blank=True, default="")
    chave = models.CharField(max_length=64, blank=True, default="")
    sessao = models.ForeignKey(
        SessaoCaixa, null=True, blank=True, on_delete=models.SET_NULL, related_name="vendas",
    )
    payment = models.OneToOneField(
        "Payment", null=True, blank=True, on_delete=models.SET_NULL, related_name="venda_balcao",
    )
    status = models.CharField(
        max_length=12,
        choices=[(STATUS_CONCLUIDA, "Concluída"), (STATUS_CANCELADA, "Cancelada")],
        default=STATUS_CONCLUIDA,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "chave"],
                condition=~models.Q(chave=""),
                name="cb_venda_balcao_chave",
            ),
        ]


class VendaBalcaoItem(LojaIsolationMixin, models.Model):
    venda = models.ForeignKey(VendaBalcao, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(ProdutoEstoque, on_delete=models.PROTECT, related_name="vendas_balcao")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estoque_baixado = models.BooleanField(default=False)
    estornado = models.BooleanField(default=False)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
