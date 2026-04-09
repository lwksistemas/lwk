"""
Modelo de configuração do CRM Vendas.
Permite personalizar origens, etapas, colunas visíveis, etc.
"""
from django.db import models
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class CRMConfig(LojaIsolationMixin, models.Model):
    """
    Configurações personalizadas do CRM por loja.
    
    Permite ao admin personalizar:
    - Origens de leads
    - Etapas do pipeline
    - Colunas visíveis nas listagens
    - Módulos ativos/inativos
    """
    
    # Origens de leads personalizadas
    # Formato: [{"key": "instagram", "label": "Instagram", "ativo": true}, ...]
    origens_leads = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de origens personalizadas para leads'
    )
    
    # Etapas do pipeline personalizadas
    # Formato: [{"key": "prospecting", "label": "Prospecção", "ativo": true, "ordem": 1}, ...]
    etapas_pipeline = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de etapas personalizadas do pipeline'
    )
    
    # Colunas visíveis na listagem de leads
    # Formato: ["nome", "empresa", "telefone", "status", "origem"]
    colunas_leads = models.JSONField(
        default=list,
        blank=True,
        help_text='Colunas visíveis na listagem de leads'
    )
    
    # Módulos ativos
    # Formato: {"contas": true, "contatos": true, "pipeline": true}
    modulos_ativos = models.JSONField(
        default=dict,
        blank=True,
        help_text='Módulos ativos no CRM'
    )

    # Conteúdo padrão da proposta (Proposta PADRAO) - salvo para reutilizar em novas propostas
    proposta_conteudo_padrao = models.TextField(
        blank=True,
        default='',
        help_text='Conteúdo padrão da proposta comercial (reutilizado ao criar novas propostas)'
    )
    
    # ============================================================================
    # CONFIGURAÇÕES DE EMISSÃO DE NFS-e
    # ============================================================================
    
    PROVEDOR_NF_CHOICES = [
        ('asaas', 'Asaas (Intermediário - Padrão)'),
        ('issnet', 'ISSNet - Ribeirão Preto (Direto)'),
        ('nacional', 'API Nacional NFS-e (Direto)'),
        ('manual', 'Emissão Manual (Sem integração)'),
    ]
    
    provedor_nf = models.CharField(
        max_length=20,
        choices=PROVEDOR_NF_CHOICES,
        default='asaas',
        verbose_name='Provedor de Nota Fiscal',
        help_text='Sistema usado para emitir notas fiscais de serviço'
    )
    
    # Configurações ISSNet (Ribeirão Preto)
    issnet_usuario = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Usuário ISSNet',
        help_text='Usuário de acesso ao webservice ISSNet'
    )
    
    issnet_senha = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Senha ISSNet',
        help_text='Senha de acesso ao webservice ISSNet'
    )
    
    issnet_certificado = models.FileField(
        upload_to='certificados_nfse/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Certificado Digital A1',
        help_text='Arquivo .pfx do certificado digital A1 (e-CNPJ)'
    )
    
    issnet_senha_certificado = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Senha do Certificado',
        help_text='Senha do arquivo .pfx do certificado digital'
    )
    
    # Configurações gerais de NFS-e
    codigo_servico_municipal = models.CharField(
        max_length=10,
        default='1401',
        verbose_name='Código do Serviço Municipal',
        help_text='Código do serviço na lista de serviços do município (ex: 1401)'
    )
    
    descricao_servico_padrao = models.TextField(
        default='Desenvolvimento e licenciamento de software sob demanda',
        verbose_name='Descrição Padrão do Serviço',
        help_text='Descrição que aparecerá nas notas fiscais emitidas'
    )
    
    aliquota_iss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.00,
        verbose_name='Alíquota ISS (%)',
        help_text='Alíquota do ISS aplicada (geralmente 2% a 5%)'
    )
    
    emitir_nf_automaticamente = models.BooleanField(
        default=True,
        verbose_name='Emitir NF Automaticamente',
        help_text='Emitir nota fiscal automaticamente ao confirmar pagamento'
    )

    # Conta Asaas da própria loja (NFS-e para clientes — não confundir com cobrança LWK)
    asaas_api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='API Key Asaas (loja)',
        help_text='Chave de API v3 da conta Asaas da loja (Integrações). Necessária para emissão via Asaas por loja.',
    )
    asaas_sandbox = models.BooleanField(
        default=False,
        verbose_name='Asaas sandbox (homologação)',
        help_text='Se True, usa api sandbox.asaas.com (chave de testes).',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()
    
    class Meta:
        db_table = 'crm_vendas_config'
        verbose_name = 'Configuração CRM'
        verbose_name_plural = 'Configurações CRM'
        indexes = [
            models.Index(fields=['loja_id'], name='crm_config_loja_idx'),
        ]
    
    def __str__(self):
        return f'Config CRM - Loja {self.loja_id}'
    
    @classmethod
    def get_or_create_for_loja(cls, loja_id):
        """
        Retorna ou cria configuração para a loja com valores padrão.
        """
        config, created = cls.objects.get_or_create(
            loja_id=loja_id,
            defaults={
                'origens_leads': cls.get_default_origens(),
                'etapas_pipeline': cls.get_default_etapas(),
                'colunas_leads': cls.get_default_colunas_leads(),
                'modulos_ativos': cls.get_default_modulos(),
            }
        )
        return config
    
    @staticmethod
    def get_default_origens():
        """Origens padrão de leads."""
        return [
            {'key': 'whatsapp', 'label': 'WhatsApp', 'ativo': True},
            {'key': 'facebook', 'label': 'Facebook', 'ativo': True},
            {'key': 'instagram', 'label': 'Instagram', 'ativo': True},
            {'key': 'site', 'label': 'Site', 'ativo': True},
            {'key': 'indicacao', 'label': 'Indicação', 'ativo': True},
            {'key': 'outro', 'label': 'Outro', 'ativo': True},
        ]
    
    @staticmethod
    def get_default_etapas():
        """Etapas padrão do pipeline."""
        return [
            {'key': 'prospecting', 'label': 'Prospecção', 'ativo': True, 'ordem': 1},
            {'key': 'qualification', 'label': 'Qualificação', 'ativo': True, 'ordem': 2},
            {'key': 'proposal', 'label': 'Proposta', 'ativo': True, 'ordem': 3},
            {'key': 'negotiation', 'label': 'Negociação', 'ativo': True, 'ordem': 4},
            {'key': 'closed_won', 'label': 'Fechado (ganho)', 'ativo': True, 'ordem': 5},
            {'key': 'closed_lost', 'label': 'Fechado (perdido)', 'ativo': True, 'ordem': 6},
        ]
    
    @staticmethod
    def get_default_colunas_leads():
        """Colunas padrão visíveis na listagem de leads."""
        return ['nome', 'empresa', 'telefone', 'email', 'origem', 'status', 'valor_estimado']
    
    @staticmethod
    def get_default_modulos():
        """Módulos padrão ativos."""
        return {
            'leads': True,
            'contas': True,
            'contatos': True,
            'pipeline': True,
            'atividades': True,
        }
