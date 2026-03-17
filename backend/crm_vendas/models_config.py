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
