"""Modelos Super Admin."""

from django.db import models
from django.utils.text import slugify


class TipoLoja(models.Model):
    """Tipos de app com dashboard específico (ex.: Clínica de Estética, Cabeleireiro)."""
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    # Código único imutável para uso em lógica sensível (backup, migrations, segurança).
    # Não usar slug para isso: codigo é estável e não deve ser alterado.
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        blank=True,
        help_text='Código único do tipo (ex: CLIEST, CABEL). Usado em backup e isolamento de dados.'
    )
    descricao = models.TextField(blank=True)
    
    # Configuração do Dashboard
    dashboard_template = models.CharField(max_length=50, default='default')
    cor_primaria = models.CharField(max_length=7, default='#10B981')  # Verde
    cor_secundaria = models.CharField(max_length=7, default='#059669')
    logo_padrao = models.URLField(blank=True)
    
    # Funcionalidades habilitadas por padrão
    tem_produtos = models.BooleanField(default=True)
    tem_servicos = models.BooleanField(default=False)
    tem_agendamento = models.BooleanField(default=False)
    tem_delivery = models.BooleanField(default=False)
    tem_estoque = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True, help_text='Se inativo, não aparece na lista pública de cadastro')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tipo de App'
        verbose_name_plural = 'Tipos de App'
        ordering = ['nome']
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['slug'], name='tipo_loja_slug_idx'),
            models.Index(fields=['dashboard_template'], name='tipo_loja_template_idx'),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        # Atribuir código único a partir do slug se estiver vazio (novos tipos de app)
        if not self.codigo and self.slug:
            slug_to_codigo = {
                'clinica-de-estetica': 'CLIBEL', 'clinica-da-beleza': 'CLIBEL',
                'clinica-beleza': 'CLIBEL',
                'crm-vendas': 'CRMVND', 'e-commerce': 'ECOMM', 'ecommerce': 'ECOMM',
                'restaurante': 'REST', 'servicos': 'SERV', 'cabeleireiro': 'CABEL',
                'clinica-estetica': 'CLIBEL',
                # Hotelaria
                'hotel': 'HOTEL', 'pousada': 'HOTEL', 'hotel-pousada': 'HOTEL', 'pousada-hotel': 'HOTEL',
            }
            self.codigo = slug_to_codigo.get((self.slug or '').strip(), '')
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nome


class PlanoAssinatura(models.Model):
    """Planos de assinatura para as lojas"""
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descricao = models.TextField()
    
    # Vinculação com tipos de app
    tipos_loja = models.ManyToManyField(TipoLoja, related_name='planos', blank=True,
                                       help_text='Tipos de app que podem usar este plano')
    
    # Preços
    preco_mensal = models.DecimalField(max_digits=10, decimal_places=2)
    preco_anual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Limites
    max_produtos = models.IntegerField(default=100)
    max_usuarios = models.IntegerField(default=5)
    max_pedidos_mes = models.IntegerField(default=1000)
    espaco_storage_gb = models.IntegerField(default=5)
    
    # Funcionalidades
    tem_relatorios_avancados = models.BooleanField(default=False)
    tem_api_acesso = models.BooleanField(default=False)
    tem_suporte_prioritario = models.BooleanField(default=False)
    tem_dominio_customizado = models.BooleanField(default=False)
    tem_whatsapp_integration = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0)  # Para ordenar na exibição
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Plano de Assinatura'
        verbose_name_plural = 'Planos de Assinatura'
        ordering = ['ordem', 'preco_mensal']
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['is_active', 'ordem'], name='plano_active_ordem_idx'),
            models.Index(fields=['slug'], name='plano_slug_idx'),
        ]
    
    def __str__(self):
        return f"{self.nome} - R$ {self.preco_mensal}/mês"


