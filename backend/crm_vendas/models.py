"""
Modelos do CRM Vendas - multi-tenant (LojaIsolationMixin).
Compatível com dashboard estilo Salesforce: Leads, Contas, Contatos,
Oportunidades, Pipeline, Atividades, Vendedores.
"""
from django.db import models
from django.conf import settings
from core.mixins import LojaIsolationMixin, LojaIsolationManager
from .managers import (
    ProdutoServicoManager,
    OportunidadeManager,
    PropostaManager,
    ContratoManager,
    LeadManager,
)
import logging

logger = logging.getLogger(__name__)


class Vendedor(LojaIsolationMixin, models.Model):
    """Vendedor da loja (equipe de vendas)."""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, default='Vendedor')
    comissao_padrao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Porcentagem de comissão padrão (ex: 5.00 para 5%)'
    )
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_vendedor'
        ordering = ['nome']
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        indexes = [
            models.Index(fields=['loja_id', 'is_active'], name='crm_vend_loja_active_idx'),
            models.Index(fields=['loja_id', 'email'], name='crm_vend_loja_email_idx'),
        ]

    def __str__(self):
        return self.nome


class Conta(LojaIsolationMixin, models.Model):
    """Conta (empresa)."""
    nome = models.CharField(max_length=255, help_text='Nome fantasia da empresa')
    razao_social = models.CharField(max_length=255, blank=True, help_text='Razão social da empresa')
    cnpj = models.CharField(max_length=18, blank=True, help_text='CNPJ da empresa (formato: 00.000.000/0000-00)')
    inscricao_estadual = models.CharField(max_length=20, blank=True, help_text='Inscrição estadual')
    vendedor = models.ForeignKey(
        'Vendedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas',
        help_text='Vendedor responsável pela conta (quando criado por vendedor)',
    )
    segmento = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)
    site = models.URLField(blank=True, null=True, help_text='Website da empresa')
    # Endereço completo
    cep = models.CharField(max_length=10, blank=True, help_text='CEP (formato: 00000-000)')
    logradouro = models.CharField(max_length=255, blank=True, help_text='Rua, avenida, etc.')
    numero = models.CharField(max_length=20, blank=True, help_text='Número do endereço')
    complemento = models.CharField(max_length=100, blank=True, help_text='Complemento (apto, sala, etc.)')
    bairro = models.CharField(max_length=100, blank=True, help_text='Bairro')
    cidade = models.CharField(max_length=100, blank=True, help_text='Cidade')
    uf = models.CharField(max_length=2, blank=True, help_text='Estado (UF)')
    # Campos antigos mantidos para compatibilidade
    endereco = models.CharField(max_length=255, blank=True, help_text='Endereço completo (campo legado)')
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_conta'
        ordering = ['nome']
        verbose_name = 'Conta'
        verbose_name_plural = 'Contas'
        indexes = [
            models.Index(fields=['loja_id', 'nome'], name='crm_conta_loja_nome_idx'),
            models.Index(fields=['loja_id', 'vendedor'], name='crm_conta_loja_vend_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_conta_loja_created_idx'),
        ]

    def __str__(self):
        return self.nome


class Lead(LojaIsolationMixin, models.Model):
    """Lead (potencial cliente)."""
    # Choices mantidas para referência, mas não mais usadas no campo
    # As origens são configuráveis via CRMConfig.origens_leads
    ORIGEM_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('site', 'Site'),
        ('indicacao', 'Indicação'),
        ('outro', 'Outro'),
    ]
    STATUS_CHOICES = [
        ('novo', 'Novo'),
        ('contato', 'Contato feito'),
        ('qualificado', 'Qualificado'),
        ('perdido', 'Perdido'),
    ]

    nome = models.CharField(max_length=200)
    empresa = models.CharField(max_length=200, blank=True)
    cpf_cnpj = models.CharField(max_length=18, blank=True, help_text='CPF ou CNPJ do lead')
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    origem = models.CharField(
        max_length=50,
        default='site',
        help_text='Origem do lead (valores configuráveis via CRMConfig)'
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='novo')
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conta = models.ForeignKey(
        Conta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
    )
    contato = models.ForeignKey(
        'Contato',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        help_text='Contato específico vinculado ao lead',
    )
    vendedor = models.ForeignKey(
        'Vendedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        help_text='Vendedor responsável pelo lead (quando criado por vendedor)',
    )
    observacoes = models.TextField(blank=True)
    # Endereço
    cep = models.CharField(max_length=10, blank=True)
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LeadManager()

    class Meta:
        db_table = 'crm_vendas_lead'
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='crm_lead_loja_status_idx'),
            models.Index(fields=['loja_id', 'origem'], name='crm_lead_loja_origem_idx'),
            models.Index(fields=['loja_id', 'vendedor'], name='crm_lead_loja_vend_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_lead_loja_created_idx'),
            models.Index(fields=['loja_id', 'conta'], name='crm_lead_loja_conta_idx'),
            models.Index(fields=['loja_id', 'contato'], name='crm_lead_loja_contato_idx'),
        ]

    def __str__(self):
        return f"{self.nome} ({self.empresa or '-'})"


class Contato(LojaIsolationMixin, models.Model):
    """Contato (pessoa) vinculado a uma conta."""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    conta = models.ForeignKey(
        Conta,
        on_delete=models.CASCADE,
        related_name='contatos',
    )
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_contato'
        ordering = ['nome']
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        indexes = [
            models.Index(fields=['loja_id', 'conta'], name='crm_contato_loja_conta_idx'),
            models.Index(fields=['loja_id', 'email'], name='crm_contato_loja_email_idx'),
        ]

    def __str__(self):
        return self.nome


class Oportunidade(LojaIsolationMixin, models.Model):
    """Oportunidade (deal) no pipeline de vendas."""
    ETAPA_CHOICES = [
        ('prospecting', 'Prospecção'),
        ('qualification', 'Qualificação'),
        ('proposal', 'Proposta'),
        ('negotiation', 'Negociação'),
        ('closed_won', 'Fechado ganho'),
        ('closed_lost', 'Fechado perdido'),
    ]

    titulo = models.CharField(max_length=255)
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='oportunidades',
    )
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    etapa = models.CharField(max_length=50, choices=ETAPA_CHOICES, default='prospecting')
    vendedor = models.ForeignKey(
        Vendedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='oportunidades',
    )
    probabilidade = models.IntegerField(default=50)  # 0-100
    data_fechamento_prevista = models.DateField(null=True, blank=True)
    data_fechamento = models.DateField(null=True, blank=True)
    data_fechamento_ganho = models.DateField(null=True, blank=True, help_text='Data em que a oportunidade foi fechada como ganha')
    data_fechamento_perdido = models.DateField(null=True, blank=True, help_text='Data em que a oportunidade foi fechada como perdida')
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Valor da comissão para esta oportunidade')
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OportunidadeManager()

    class Meta:
        db_table = 'crm_vendas_oportunidade'
        ordering = ['-created_at']
        verbose_name = 'Oportunidade'
        verbose_name_plural = 'Oportunidades'
        indexes = [
            models.Index(fields=['loja_id', 'etapa'], name='crm_opor_loja_etapa_idx'),
            models.Index(fields=['loja_id', 'vendedor'], name='crm_opor_loja_vend_idx'),
            models.Index(fields=['loja_id', 'lead'], name='crm_opor_loja_lead_idx'),
            models.Index(fields=['loja_id', 'data_fechamento'], name='crm_opor_loja_dtfech_idx'),
            models.Index(fields=['loja_id', 'data_fechamento_ganho'], name='crm_opor_loja_dtfechganho_idx'),
            models.Index(fields=['loja_id', 'data_fechamento_perdido'], name='crm_opor_loja_dtfechperd_idx'),
            models.Index(fields=['loja_id', 'etapa', 'vendedor'], name='crm_opor_loja_etapa_vend_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_opor_loja_created_idx'),
        ]

    def __str__(self):
        return f"{self.titulo} - R$ {self.valor}"


class Atividade(LojaIsolationMixin, models.Model):
    """Atividade (tarefa, ligação, reunião, email)."""
    TIPO_CHOICES = [
        ('call', 'Ligação'),
        ('meeting', 'Reunião'),
        ('email', 'Email'),
        ('task', 'Tarefa'),
    ]

    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='task')
    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='atividades',
        null=True,
        blank=True,
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='atividades',
        null=True,
        blank=True,
    )
    data = models.DateTimeField()
    duracao_minutos = models.PositiveIntegerField(
        default=60,
        help_text='Duração estimada da atividade em minutos'
    )
    concluido = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True, help_text='ID do evento no Google Calendar (sincronização)')
    criado_por_vendedor_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Vendedor que criou/importou esta atividade (órfã). Null = proprietário. Usado para filtrar calendário por vendedor.',
    )

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_atividade'
        ordering = ['data']
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
        indexes = [
            models.Index(fields=['loja_id', 'data'], name='crm_ativ_loja_data_idx'),
            models.Index(fields=['loja_id', 'concluido'], name='crm_ativ_loja_concl_idx'),
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_ativ_loja_opor_idx'),
            models.Index(fields=['loja_id', 'lead'], name='crm_ativ_loja_lead_idx'),
            models.Index(fields=['loja_id', 'data', 'concluido'], name='crm_ativ_loja_data_concl_idx'),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"


class CategoriaProdutoServico(LojaIsolationMixin, models.Model):
    """Categoria para organizar produtos e serviços em grupos."""
    nome = models.CharField(max_length=100, help_text='Nome da categoria (ex: Hardware, Software, Consultoria)')
    descricao = models.TextField(blank=True, help_text='Descrição da categoria')
    cor = models.CharField(max_length=7, default='#3B82F6', help_text='Cor para identificação visual (hex)')
    ordem = models.IntegerField(default=0, help_text='Ordem de exibição')
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_categoria_produto_servico'
        ordering = ['ordem', 'nome']
        verbose_name = 'Categoria de Produto/Serviço'
        verbose_name_plural = 'Categorias de Produtos/Serviços'
        indexes = [
            models.Index(fields=['loja_id', 'ativo'], name='crm_cat_ps_loja_ativo_idx'),
            models.Index(fields=['loja_id', 'ordem'], name='crm_cat_ps_loja_ordem_idx'),
        ]

    def __str__(self):
        return self.nome


class ProdutoServico(LojaIsolationMixin, models.Model):
    """Produto ou serviço cadastrado para uso em oportunidades e propostas."""
    TIPO_CHOICES = [
        ('produto', 'Produto'),
        ('servico', 'Serviço'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='produto')
    codigo = models.CharField(
        max_length=50, 
        blank=True,
        help_text='Código interno único (ex: PROD-001, SERV-CONS-01)'
    )
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(
        CategoriaProdutoServico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos_servicos',
        help_text='Categoria/Grupo do produto ou serviço'
    )
    preco = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProdutoServicoManager()

    class Meta:
        db_table = 'crm_vendas_produto_servico'
        ordering = ['categoria__ordem', 'categoria__nome', 'codigo', 'nome']
        verbose_name = 'Produto/Serviço'
        verbose_name_plural = 'Produtos e Serviços'
        indexes = [
            models.Index(fields=['loja_id', 'tipo'], name='crm_ps_loja_tipo_idx'),
            models.Index(fields=['loja_id', 'ativo'], name='crm_ps_loja_ativo_idx'),
            models.Index(fields=['loja_id', 'categoria'], name='crm_ps_loja_cat_idx'),
            models.Index(fields=['loja_id', 'codigo'], name='crm_ps_loja_codigo_idx'),
        ]
        # Garantir que o código seja único dentro da loja
        constraints = [
            models.UniqueConstraint(
                fields=['loja_id', 'codigo'],
                name='crm_ps_unique_codigo_loja',
                condition=models.Q(codigo__isnull=False) & ~models.Q(codigo='')
            )
        ]

    def __str__(self):
        if self.codigo:
            return f"[{self.codigo}] {self.nome}"
        return f"{self.get_tipo_display()}: {self.nome}"

    def save(self, *args, **kwargs):
        """Gera código automático se não fornecido usando o Manager."""
        if not self.codigo:
            self.codigo = self.__class__.objects.gerar_proximo_codigo(
                self.tipo,
                self.loja_id
            )
        super().save(*args, **kwargs)


class OportunidadeItem(LojaIsolationMixin, models.Model):
    """Item (produto/serviço) vinculado a uma oportunidade."""
    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='itens',
    )
    produto_servico = models.ForeignKey(
        ProdutoServico,
        on_delete=models.CASCADE,
        related_name='oportunidade_itens',
    )
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    observacao = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_oportunidade_item'
        ordering = ['id']
        verbose_name = 'Item da Oportunidade'
        verbose_name_plural = 'Itens da Oportunidade'
        indexes = [
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_oi_loja_opor_idx'),
        ]

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario


class Proposta(LojaIsolationMixin, models.Model):
    """Proposta comercial vinculada a uma oportunidade."""
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviada', 'Enviada'),
        ('aceita', 'Aceita'),
        ('rejeitada', 'Rejeitada'),
        ('cancelada', 'Cancelada'),
    ]
    
    STATUS_ASSINATURA_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('aguardando_cliente', 'Aguardando Cliente'),
        ('aguardando_vendedor', 'Aguardando Vendedor'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    DESCONTO_TIPO_CHOICES = [
        ('percentual', 'Percentual'),
        ('valor', 'Valor fixo'),
    ]

    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='propostas',
    )
    numero = models.CharField(max_length=50, blank=True, help_text='Número sequencial da proposta (ex: 001, 002, 003)')
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField(blank=True, help_text='Conteúdo da proposta em texto ou HTML')
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    desconto_tipo = models.CharField(
        max_length=15,
        choices=DESCONTO_TIPO_CHOICES,
        default='percentual',
        help_text='Tipo de desconto: percentual (%) ou valor fixo (R$)',
    )
    desconto_valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Valor do desconto (percentual ou fixo, conforme desconto_tipo)',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    data_envio = models.DateTimeField(null=True, blank=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    nome_vendedor_assinatura = models.CharField(max_length=255, blank=True, help_text='Nome do vendedor para assinatura no PDF')
    nome_cliente_assinatura = models.CharField(max_length=255, blank=True, help_text='Nome do cliente para assinatura no PDF')
    status_assinatura = models.CharField(
        max_length=20,
        choices=STATUS_ASSINATURA_CHOICES,
        default='rascunho',
        help_text='Status do processo de assinatura digital'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PropostaManager()

    class Meta:
        db_table = 'crm_vendas_proposta'
        ordering = ['-created_at']
        verbose_name = 'Proposta'
        verbose_name_plural = 'Propostas'
        indexes = [
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_prop_loja_opor_idx'),
            models.Index(fields=['loja_id', 'status'], name='crm_prop_loja_status_idx'),
        ]

    def __str__(self):
        return f"{self.numero or self.titulo} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Gera número sequencial automaticamente se não fornecido."""
        # Garantir que loja_id está definido (chamando save do mixin primeiro se necessário)
        if not self.loja_id:
            from tenants.middleware import get_current_loja_id
            current_loja_id = get_current_loja_id()
            if current_loja_id:
                self.loja_id = current_loja_id
        
        # Gerar número se não fornecido e loja_id está disponível
        if not self.numero and self.loja_id:
            # Buscar o último número da loja
            ultima_proposta = Proposta.objects.filter(
                loja_id=self.loja_id
            ).exclude(numero='').order_by('-id').first()
            
            if ultima_proposta and ultima_proposta.numero:
                try:
                    ultimo_num = int(ultima_proposta.numero)
                    proximo_num = ultimo_num + 1
                except (ValueError, TypeError):
                    proximo_num = 1
            else:
                proximo_num = 1
            
            self.numero = str(proximo_num).zfill(3)  # 001, 002, 003, etc.
        
        super().save(*args, **kwargs)

    @property
    def valor_com_desconto(self):
        """Calcula o valor final após aplicar o desconto."""
        from decimal import Decimal
        base = self.valor_total or Decimal('0')
        desconto = self.desconto_valor or Decimal('0')
        if desconto <= 0 or base <= 0:
            return base
        if self.desconto_tipo == 'percentual':
            return max(base - (base * desconto / Decimal('100')), Decimal('0'))
        return max(base - desconto, Decimal('0'))


class Contrato(LojaIsolationMixin, models.Model):
    """Contrato gerado a partir de oportunidade fechada como ganha."""
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviado', 'Enviado'),
        ('assinado', 'Assinado'),
        ('cancelado', 'Cancelado'),
    ]
    
    STATUS_ASSINATURA_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('aguardando_cliente', 'Aguardando Cliente'),
        ('aguardando_vendedor', 'Aguardando Vendedor'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    DESCONTO_TIPO_CHOICES = [
        ('percentual', 'Percentual'),
        ('valor', 'Valor fixo'),
    ]

    oportunidade = models.OneToOneField(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='contrato',
    )
    numero = models.CharField(max_length=50, blank=True)
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField(blank=True, help_text='Conteúdo do contrato')
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    desconto_tipo = models.CharField(
        max_length=15,
        choices=DESCONTO_TIPO_CHOICES,
        default='percentual',
        help_text='Tipo de desconto: percentual (%) ou valor fixo (R$)',
    )
    desconto_valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Valor do desconto (percentual ou fixo, conforme desconto_tipo)',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    data_envio = models.DateTimeField(null=True, blank=True)
    data_assinatura = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    nome_vendedor_assinatura = models.CharField(max_length=255, blank=True, help_text='Nome do vendedor para assinatura no PDF')
    nome_cliente_assinatura = models.CharField(max_length=255, blank=True, help_text='Nome do cliente para assinatura no PDF')
    status_assinatura = models.CharField(
        max_length=20,
        choices=STATUS_ASSINATURA_CHOICES,
        default='rascunho',
        help_text='Status do processo de assinatura digital'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ContratoManager()

    class Meta:
        db_table = 'crm_vendas_contrato'
        ordering = ['-created_at']
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        indexes = [
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_cont_loja_opor_idx'),
            models.Index(fields=['loja_id', 'status'], name='crm_cont_loja_status_idx'),
        ]

    def __str__(self):
        return f"{self.numero or self.titulo or 'Contrato'} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Gera número sequencial automaticamente se não fornecido."""
        # Garantir que loja_id está definido (chamando save do mixin primeiro se necessário)
        if not self.loja_id:
            from tenants.middleware import get_current_loja_id
            current_loja_id = get_current_loja_id()
            if current_loja_id:
                self.loja_id = current_loja_id
        
        # Gerar número se não fornecido e loja_id está disponível
        if not self.numero and self.loja_id:
            # Buscar o último número da loja
            ultimo_contrato = Contrato.objects.filter(
                loja_id=self.loja_id
            ).exclude(numero='').order_by('-id').first()
            
            if ultimo_contrato and ultimo_contrato.numero:
                try:
                    ultimo_num = int(ultimo_contrato.numero)
                    proximo_num = ultimo_num + 1
                except (ValueError, TypeError):
                    proximo_num = 1
            else:
                proximo_num = 1
            
            self.numero = str(proximo_num).zfill(3)  # 001, 002, 003, etc.
        
        super().save(*args, **kwargs)

    @property
    def valor_com_desconto(self):
        """Calcula o valor final após aplicar o desconto."""
        from decimal import Decimal
        base = self.valor_total or Decimal('0')
        desconto = self.desconto_valor or Decimal('0')
        if desconto <= 0 or base <= 0:
            return base
        if self.desconto_tipo == 'percentual':
            return max(base - (base * desconto / Decimal('100')), Decimal('0'))
        return max(base - desconto, Decimal('0'))


class PropostaTemplate(LojaIsolationMixin, models.Model):
    """Template de proposta para reutilização."""
    nome = models.CharField(max_length=255, help_text='Nome do template (ex: Proposta Padrão, Proposta Premium)')
    conteudo = models.TextField(help_text='Conteúdo do template em texto ou HTML')
    is_padrao = models.BooleanField(default=False, help_text='Template padrão usado ao criar novas propostas')
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_proposta_template'
        ordering = ['-is_padrao', 'nome']
        verbose_name = 'Template de Proposta'
        verbose_name_plural = 'Templates de Propostas'
        indexes = [
            models.Index(fields=['loja_id', 'ativo'], name='crm_pt_loja_ativo_idx'),
            models.Index(fields=['loja_id', 'is_padrao'], name='crm_pt_loja_padrao_idx'),
        ]

    def __str__(self):
        padrao = ' (PADRÃO)' if self.is_padrao else ''
        return f"{self.nome}{padrao}"

    def save(self, *args, **kwargs):
        """Se marcar como padrão, desmarcar outros templates da mesma loja."""
        if self.is_padrao:
            # Desmarcar outros templates como padrão
            PropostaTemplate.objects.filter(loja_id=self.loja_id, is_padrao=True).exclude(id=self.id).update(is_padrao=False)
        super().save(*args, **kwargs)


class ContratoTemplate(LojaIsolationMixin, models.Model):
    """Template de contrato para reutilização."""
    nome = models.CharField(max_length=255, help_text='Nome do template (ex: Contrato Padrão, Contrato Premium)')
    conteudo = models.TextField(help_text='Conteúdo do template em texto ou HTML')
    is_padrao = models.BooleanField(default=False, help_text='Template padrão usado ao criar novos contratos')
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_contrato_template'
        ordering = ['-is_padrao', 'nome']
        verbose_name = 'Template de Contrato'
        verbose_name_plural = 'Templates de Contratos'
        indexes = [
            models.Index(fields=['loja_id', 'ativo'], name='crm_ct_loja_ativo_idx'),
            models.Index(fields=['loja_id', 'is_padrao'], name='crm_ct_loja_padrao_idx'),
        ]

    def __str__(self):
        padrao = ' (PADRÃO)' if self.is_padrao else ''
        return f"{self.nome}{padrao}"

    def save(self, *args, **kwargs):
        """Se marcar como padrão, desmarcar outros templates da mesma loja."""
        if self.is_padrao:
            # Desmarcar outros templates como padrão
            ContratoTemplate.objects.filter(loja_id=self.loja_id, is_padrao=True).exclude(id=self.id).update(is_padrao=False)
        super().save(*args, **kwargs)


class AssinaturaDigital(LojaIsolationMixin, models.Model):
    """
    Registro de assinatura digital para Propostas e Contratos.
    Armazena dados de assinatura: IP, timestamp, token único.
    """
    TIPO_CHOICES = [
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
    ]
    
    # Relacionamento direto (proposta OU contrato)
    # Usar ForeignKey direto ao invés de GenericForeignKey para evitar problemas cross-database
    proposta = models.ForeignKey(
        'Proposta',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assinaturas',
        help_text='Proposta sendo assinada'
    )
    contrato = models.ForeignKey(
        'Contrato',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assinaturas',
        help_text='Contrato sendo assinado'
    )
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, help_text='Tipo de assinante')
    nome_assinante = models.CharField(max_length=200, help_text='Nome completo do assinante')
    email_assinante = models.EmailField(help_text='Email do assinante')
    
    # Dados de segurança da assinatura
    ip_address = models.GenericIPAddressField(help_text='Endereço IP do assinante')
    timestamp = models.DateTimeField(auto_now_add=True, help_text='Data/hora de criação do token')
    user_agent = models.TextField(blank=True, help_text='User agent do navegador')
    
    # Token único para esta assinatura
    token = models.CharField(max_length=255, unique=True, db_index=True, help_text='Token único de assinatura')
    token_expira_em = models.DateTimeField(help_text='Data/hora de expiração do token')
    
    # Status da assinatura
    assinado = models.BooleanField(default=False, help_text='Se o documento foi assinado')
    assinado_em = models.DateTimeField(null=True, blank=True, help_text='Data/hora da assinatura')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()
    
    class Meta:
        db_table = 'crm_vendas_assinatura_digital'
        ordering = ['-created_at']
        verbose_name = 'Assinatura Digital'
        verbose_name_plural = 'Assinaturas Digitais'
        indexes = [
            models.Index(fields=['loja_id', 'token'], name='crm_assin_loja_token_idx'),
            models.Index(fields=['loja_id', 'tipo', 'assinado'], name='crm_assin_loja_tipo_idx'),
            models.Index(fields=['proposta'], name='crm_assin_proposta_idx'),
            models.Index(fields=['contrato'], name='crm_assin_contrato_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(proposta__isnull=False, contrato__isnull=True) |
                    models.Q(proposta__isnull=True, contrato__isnull=False)
                ),
                name='crm_assin_proposta_ou_contrato'
            )
        ]
    
    def __str__(self):
        status = 'Assinado' if self.assinado else 'Pendente'
        return f"{self.get_tipo_display()} - {self.nome_assinante} ({status})"
    
    @property
    def documento(self):
        """Retorna o documento (proposta ou contrato) para compatibilidade."""
        return self.proposta or self.contrato
    
    def is_expirado(self):
        """Verifica se o token está expirado."""
        from django.utils import timezone
        return timezone.now() > self.token_expira_em


# Importar modelo de configuração
from .models_config import CRMConfig
