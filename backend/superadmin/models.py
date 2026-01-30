"""
Modelos para o Super Admin gerenciar o sistema
"""
import re
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone


class UserSession(models.Model):
    """
    Modelo para armazenar sessões únicas de usuários no banco de dados
    Garante que cada usuário tenha apenas uma sessão ativa
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='active_session', unique=True)
    session_id = models.CharField(max_length=64, unique=True, db_index=True)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)  # Hash do JWT token
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'Sessão de Usuário'
        verbose_name_plural = 'Sessões de Usuários'
        indexes = [
            models.Index(fields=['user', 'token_hash']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"Sessão de {self.user.username} - {self.session_id[:8]}..."
    
    def is_expired(self, timeout_minutes=30):
        """Verifica se a sessão expirou por inatividade"""
        from datetime import timedelta
        now = timezone.now()
        return (now - self.last_activity) > timedelta(minutes=timeout_minutes)
    
    def update_activity(self):
        """Atualiza o timestamp da última atividade"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


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
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['slug'], name='tipo_loja_slug_idx'),
            models.Index(fields=['dashboard_template'], name='tipo_loja_template_idx'),
        ]
    
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
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['is_active', 'ordem'], name='plano_active_ordem_idx'),
            models.Index(fields=['slug'], name='plano_slug_idx'),
        ]
    
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
    
    # Controle de bloqueio por inadimplência
    is_blocked = models.BooleanField(default=False, help_text='Loja bloqueada por inadimplência')
    blocked_at = models.DateTimeField(null=True, blank=True, help_text='Data do bloqueio')
    blocked_reason = models.CharField(max_length=255, blank=True, help_text='Motivo do bloqueio')
    days_overdue = models.IntegerField(default=0, help_text='Dias em atraso')
    
    # Datas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'
        ordering = ['-created_at']
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['is_active', '-created_at'], name='loja_active_created_idx'),
            models.Index(fields=['tipo_loja', 'is_active'], name='loja_tipo_active_idx'),
            models.Index(fields=['plano', 'is_active'], name='loja_plano_active_idx'),
            models.Index(fields=['owner', 'is_active'], name='loja_owner_active_idx'),
            models.Index(fields=['database_name'], name='loja_db_name_idx'),
            models.Index(fields=['is_trial', 'trial_ends_at'], name='loja_trial_idx'),
        ]
    
    def _get_slug_suffix_from_cpf_cnpj(self):
        """Extrai sufixo numérico do CPF/CNPJ para garantir slug único (ex: últimos 6 dígitos do CNPJ)."""
        if not self.cpf_cnpj:
            return None
        digits = re.sub(r'\D', '', self.cpf_cnpj)
        if not digits:
            return None
        # CNPJ: usar últimos 6 dígitos; CPF: usar últimos 4 para URL curta
        if len(digits) >= 12:  # CNPJ
            return digits[-6:]
        if len(digits) >= 4:
            return digits[-4:]
        return digits

    def _generate_unique_slug(self):
        """Gera slug único a partir do nome e, se houver, sufixo do CPF/CNPJ."""
        base = slugify(self.nome) or 'loja'
        suffix = self._get_slug_suffix_from_cpf_cnpj()
        candidate = f"{base}-{suffix}" if suffix else base
        # Garantir unicidade: se já existir, acrescentar -2, -3, ...
        orig = candidate
        n = 2
        while Loja.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f"{orig}-{n}"
            n += 1
        return candidate

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
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
    
    # Integração Asaas
    asaas_customer_id = models.CharField(max_length=100, blank=True, help_text='ID do cliente no Asaas')
    asaas_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento atual no Asaas')
    boleto_url = models.URLField(blank=True, help_text='URL do boleto no Asaas')
    boleto_pdf_url = models.URLField(blank=True, help_text='URL do PDF do boleto')
    pix_qr_code = models.TextField(blank=True, help_text='QR Code PIX')
    pix_copy_paste = models.TextField(blank=True, help_text='PIX Copia e Cola')
    
    # Totalizadores
    total_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pendente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Controle de sincronização
    last_sync_at = models.DateTimeField(null=True, blank=True, help_text='Última sincronização com Asaas')
    sync_error = models.TextField(blank=True, help_text='Último erro de sincronização')
    
    # Dados de pagamento
    forma_pagamento = models.CharField(max_length=50, blank=True)  # cartao, boleto, pix
    ultimo_pagamento = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Financeiro da Loja'
        verbose_name_plural = 'Financeiros das Lojas'
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['status_pagamento', 'data_proxima_cobranca'], name='fin_status_data_idx'),
            models.Index(fields=['loja', 'status_pagamento'], name='fin_loja_status_idx'),
            models.Index(fields=['asaas_customer_id'], name='fin_asaas_customer_idx'),
            models.Index(fields=['asaas_payment_id'], name='fin_asaas_payment_idx'),
        ]
    
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
    
    # Integração Asaas
    asaas_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento no Asaas')
    boleto_url = models.URLField(blank=True, help_text='URL do boleto')
    boleto_pdf_url = models.URLField(blank=True, help_text='URL do PDF do boleto')
    pix_qr_code = models.TextField(blank=True, help_text='QR Code PIX')
    pix_copy_paste = models.TextField(blank=True, help_text='PIX Copia e Cola')
    
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
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['loja', 'status', '-data_vencimento'], name='pag_loja_status_idx'),
            models.Index(fields=['status', 'data_vencimento'], name='pag_status_venc_idx'),
            models.Index(fields=['financeiro', '-data_vencimento'], name='pag_fin_venc_idx'),
            models.Index(fields=['asaas_payment_id'], name='pag_asaas_payment_idx'),
        ]
    
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
    
    # Senha provisória (para recuperação de senha)
    senha_provisoria = models.CharField(max_length=50, blank=True, help_text='Senha provisória gerada automaticamente')
    senha_foi_alterada = models.BooleanField(default=False, help_text='Indica se o usuário já alterou a senha provisória')
    
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
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['tipo', 'is_active'], name='usuario_tipo_active_idx'),
            models.Index(fields=['user', 'tipo'], name='usuario_user_tipo_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username} ({self.get_tipo_display()})"
