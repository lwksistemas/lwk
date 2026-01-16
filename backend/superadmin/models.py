"""
Modelos para o Super Admin gerenciar o sistema
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class TipoLoja(models.Model):
    """Tipos de loja com dashboard específico"""
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tipo de Loja'
        verbose_name_plural = 'Tipos de Loja'
        ordering = ['nome']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nome


class PlanoAssinatura(models.Model):
    """Planos de assinatura para as lojas"""
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descricao = models.TextField()
    
    # Vinculação com tipos de loja
    tipos_loja = models.ManyToManyField(TipoLoja, related_name='planos', blank=True, 
                                       help_text='Tipos de loja que podem usar este plano')
    
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
    
    def __str__(self):
        return f"{self.nome} - R$ {self.preco_mensal}/mês"


class Loja(models.Model):
    """Loja gerenciada pelo Super Admin"""
    # Informações básicas
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(blank=True)
    
    # Documentos
    cpf_cnpj = models.CharField(max_length=18, blank=True, help_text='CPF ou CNPJ da loja')
    
    # Tipo e Plano
    tipo_loja = models.ForeignKey(TipoLoja, on_delete=models.PROTECT, related_name='lojas')
    plano = models.ForeignKey(PlanoAssinatura, on_delete=models.PROTECT, related_name='lojas')
    
    # Tipo de assinatura
    TIPO_ASSINATURA_CHOICES = [
        ('mensal', 'Mensal'),
        ('anual', 'Anual'),
    ]
    tipo_assinatura = models.CharField(max_length=10, choices=TIPO_ASSINATURA_CHOICES, default='mensal')
    
    # Proprietário
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lojas_owned')
    
    # Senha provisória (para mostrar ao super admin)
    senha_provisoria = models.CharField(max_length=50, blank=True, help_text='Senha provisória gerada automaticamente')
    senha_foi_alterada = models.BooleanField(default=False, help_text='Indica se o proprietário já alterou a senha provisória')
    
    # Banco de dados isolado
    database_name = models.CharField(max_length=100, unique=True)  # ex: loja_tech_store
    database_created = models.BooleanField(default=False)
    
    # Personalização
    logo = models.URLField(blank=True)
    cor_primaria = models.CharField(max_length=7, blank=True)
    cor_secundaria = models.CharField(max_length=7, blank=True)
    dominio_customizado = models.CharField(max_length=255, blank=True, unique=True, null=True)
    
    # Página de login personalizada
    login_page_url = models.CharField(max_length=255, blank=True)  # ex: /loja/tech-store/login
    login_background = models.URLField(blank=True)
    login_logo = models.URLField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Datas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        if not self.database_name:
            self.database_name = f'loja_{self.slug.replace("-", "_")}'
        if not self.login_page_url:
            self.login_page_url = f'/loja/{self.slug}/login'
        # Herdar cores do tipo de loja se não definidas
        if not self.cor_primaria and self.tipo_loja:
            self.cor_primaria = self.tipo_loja.cor_primaria
        if not self.cor_secundaria and self.tipo_loja:
            self.cor_secundaria = self.tipo_loja.cor_secundaria
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} ({self.plano.nome})"


class FinanceiroLoja(models.Model):
    """Controle financeiro de cada loja"""
    loja = models.OneToOneField(Loja, on_delete=models.CASCADE, related_name='financeiro')
    
    # Assinatura
    data_proxima_cobranca = models.DateField()
    valor_mensalidade = models.DecimalField(max_digits=10, decimal_places=2)
    dia_vencimento = models.IntegerField(default=10)  # Dia do mês
    
    # Status de pagamento
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('pendente', 'Pagamento Pendente'),
        ('atrasado', 'Atrasado'),
        ('suspenso', 'Suspenso'),
        ('cancelado', 'Cancelado'),
    ]
    status_pagamento = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    
    # Totalizadores
    total_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pendente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Dados de pagamento
    forma_pagamento = models.CharField(max_length=50, blank=True)  # cartao, boleto, pix
    ultimo_pagamento = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Financeiro da Loja'
        verbose_name_plural = 'Financeiros das Lojas'
    
    def __str__(self):
        return f"Financeiro - {self.loja.nome}"


class PagamentoLoja(models.Model):
    """Histórico de pagamentos de cada loja"""
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='pagamentos')
    financeiro = models.ForeignKey(FinanceiroLoja, on_delete=models.CASCADE, related_name='pagamentos')
    
    # Dados do pagamento
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    referencia_mes = models.DateField()  # Mês de referência
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    # Detalhes
    forma_pagamento = models.CharField(max_length=50)
    comprovante = models.URLField(blank=True)
    observacoes = models.TextField(blank=True)
    
    # Datas
    data_vencimento = models.DateField()
    data_pagamento = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-data_vencimento']
    
    def __str__(self):
        return f"{self.loja.nome} - {self.referencia_mes.strftime('%m/%Y')} - R$ {self.valor}"


class UsuarioSistema(models.Model):
    """Usuários do sistema (Super Admin e Suporte)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_sistema')
    
    TIPO_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('suporte', 'Suporte'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # Informações adicionais
    telefone = models.CharField(max_length=20, blank=True)
    foto = models.URLField(blank=True)
    
    # Permissões específicas
    pode_criar_lojas = models.BooleanField(default=False)
    pode_gerenciar_financeiro = models.BooleanField(default=False)
    pode_acessar_todas_lojas = models.BooleanField(default=False)
    
    # Lojas que pode acessar (para suporte)
    lojas_acesso = models.ManyToManyField(Loja, blank=True, related_name='usuarios_suporte')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usuário do Sistema'
        verbose_name_plural = 'Usuários do Sistema'
    
    def __str__(self):
        return f"{self.user.username} ({self.get_tipo_display()})"
