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
    
    # Endereço
    cep = models.CharField(max_length=9, blank=True)
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    
    # Tipo e Plano
    tipo_loja = models.ForeignKey(TipoLoja, on_delete=models.PROTECT, related_name='lojas')
    plano = models.ForeignKey(PlanoAssinatura, on_delete=models.PROTECT, related_name='lojas')
    
    # Tipo de assinatura
    TIPO_ASSINATURA_CHOICES = [
        ('mensal', 'Mensal'),
        ('anual', 'Anual'),
    ]
    tipo_assinatura = models.CharField(max_length=10, choices=TIPO_ASSINATURA_CHOICES, default='mensal')
    
    # Provedor de boleto preferido para esta loja (Asaas ou Mercado Pago)
    PROVEDOR_BOLETO_CHOICES = [
        ('asaas', 'Asaas'),
        ('mercadopago', 'Mercado Pago'),
    ]
    provedor_boleto_preferido = models.CharField(
        max_length=20,
        choices=PROVEDOR_BOLETO_CHOICES,
        default='asaas',
        help_text='Provedor de boleto a usar nas cobranças desta loja'
    )
    
    # Proprietário (administrador da loja — não editável nem excluível após criação)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lojas_owned')
    owner_telefone = models.CharField(max_length=20, blank=True, help_text='Telefone do administrador da loja')
    
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
    
    # Controle de bloqueio por inadimplência
    is_blocked = models.BooleanField(default=False, help_text='Loja bloqueada por inadimplência')
    blocked_at = models.DateTimeField(null=True, blank=True, help_text='Data do bloqueio')
    blocked_reason = models.CharField(max_length=255, blank=True, help_text='Motivo do bloqueio')
    days_overdue = models.IntegerField(default=0, help_text='Dias em atraso')
    
    # ✅ NOVO v738: Monitoramento de Storage
    storage_usado_mb = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Espaço em disco usado pela loja (em MB)'
    )
    storage_limite_mb = models.IntegerField(
        default=500,
        help_text='Limite de storage da loja (em MB) - baseado no plano'
    )
    storage_alerta_enviado = models.BooleanField(
        default=False,
        help_text='Indica se alerta de 80% já foi enviado'
    )
    storage_ultima_verificacao = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Data da última verificação de storage'
    )
    
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
            models.Index(fields=['storage_ultima_verificacao'], name='loja_storage_check_idx'),
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
    
    def clean(self):
        """
        Validações customizadas antes de salvar
        
        SEGURANÇA: Garante que database_name é único e válido
        """
        from django.core.exceptions import ValidationError
        import re
        
        # Validar database_name único
        if self.database_name:
            # Validar formato (apenas letras, números e underscore)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.database_name):
                raise ValidationError({
                    'database_name': 'Database name deve conter apenas letras, números e underscore, e começar com letra ou underscore'
                })
            
            # Validar unicidade
            existing = Loja.objects.filter(database_name=self.database_name).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({
                    'database_name': f'Já existe uma loja com database_name "{self.database_name}". Cada loja deve ter um database_name único.'
                })
        
        # Validar que database_name não muda após criação (prevenir acidentes)
        if self.pk:  # Se já existe (update)
            try:
                old = Loja.objects.get(pk=self.pk)
                if old.database_name != self.database_name:
                    raise ValidationError({
                        'database_name': 'Não é permitido alterar database_name de uma loja existente. Isso pode causar perda de dados.'
                    })
            except Loja.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        if not self.database_name:
            self.database_name = f'loja_{self.slug.replace("-", "_")}'
        if not self.login_page_url:
            self.login_page_url = f'/loja/{self.slug}/login'
        # Herdar cores do tipo de app se não definidas
        if not self.cor_primaria and self.tipo_loja:
            self.cor_primaria = self.tipo_loja.cor_primaria
        if not self.cor_secundaria and self.tipo_loja:
            self.cor_secundaria = self.tipo_loja.cor_secundaria
        
        # ✅ NOVO v738: Definir limite de storage baseado no plano
        if self.plano and self.storage_limite_mb == 500:  # Valor padrão
            self.storage_limite_mb = self.plano.espaco_storage_gb * 1024
        
        # Executar validações antes de salvar
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    def get_storage_percentual(self):
        """
        Retorna o percentual de uso de storage.
        
        Returns:
            float: Percentual de uso (0-100)
        """
        if self.storage_limite_mb == 0:
            return 0
        return (float(self.storage_usado_mb) / self.storage_limite_mb) * 100
    
    def is_storage_critical(self):
        """
        Verifica se o storage está em nível crítico (>= 80%).
        
        Returns:
            bool: True se >= 80%, False caso contrário
        """
        return self.get_storage_percentual() >= 80
    
    def is_storage_full(self):
        """
        Verifica se o storage está cheio (>= 100%).
        
        Returns:
            bool: True se >= 100%, False caso contrário
        """
        return self.get_storage_percentual() >= 100
    
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
    
    # Provedor de boleto: asaas ou mercadopago
    PROVEDOR_BOLETO_CHOICES = [
        ('asaas', 'Asaas'),
        ('mercadopago', 'Mercado Pago'),
    ]
    provedor_boleto = models.CharField(
        max_length=20, choices=PROVEDOR_BOLETO_CHOICES, default='asaas',
        help_text='Provedor usado para gerar boleto desta cobrança'
    )
    mercadopago_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento boleto no Mercado Pago')
    mercadopago_pix_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento PIX no Mercado Pago')
    
    # Integração Asaas
    asaas_customer_id = models.CharField(max_length=100, blank=True, help_text='ID do cliente no Asaas')
    asaas_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento atual no Asaas')
    boleto_url = models.URLField(blank=True, help_text='URL do boleto (Asaas ou Mercado Pago)')
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
    
    # Controle de envio de senha provisória
    senha_enviada = models.BooleanField(default=False, help_text='Indica se a senha provisória já foi enviada')
    data_envio_senha = models.DateTimeField(null=True, blank=True, help_text='Data e hora do envio da senha provisória')
    
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
            models.Index(fields=['mercadopago_payment_id'], name='fin_mp_payment_idx'),
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
    
    # Provedor do boleto
    provedor_boleto = models.CharField(
        max_length=20,
        choices=FinanceiroLoja.PROVEDOR_BOLETO_CHOICES,
        default='asaas',
        help_text='Provedor do boleto (Asaas ou Mercado Pago)'
    )
    mercadopago_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento boleto no Mercado Pago')
    mercadopago_pix_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento PIX no Mercado Pago')
    
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
            models.Index(fields=['mercadopago_payment_id'], name='pag_mp_payment_idx'),
        ]
    
    def __str__(self):
        return f"{self.loja.nome} - {self.referencia_mes.strftime('%m/%Y')} - R$ {self.valor}"


class MercadoPagoConfig(models.Model):
    """Configuração da integração Mercado Pago para boletos das lojas"""
    singleton_key = models.CharField(max_length=10, default='config', unique=True)
    access_token = models.TextField(blank=True, verbose_name='Access Token (Produção ou Teste)')
    public_key = models.CharField(
        max_length=80, blank=True,
        verbose_name='Public Key (para SDK no frontend)',
        help_text='Chave pública para inicializar MercadoPago.js no frontend'
    )
    enabled = models.BooleanField(default=False, verbose_name='Integração habilitada')
    use_for_boletos = models.BooleanField(
        default=False,
        verbose_name='Usar Mercado Pago para novos boletos',
        help_text='Se ativo, novas cobranças de lojas usarão boleto via Mercado Pago em vez do Asaas'
    )
    chave_pix_estatica = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Chave PIX estática (fallback)',
        help_text='Chave PIX (copia e cola) exibida na página do boleto quando não houver PIX dinâmico do Mercado Pago. Ex.: chave aleatória para pagamento manual.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'superadmin_mercadopago_config'
        verbose_name = 'Configuração Mercado Pago'
        verbose_name_plural = 'Configurações Mercado Pago'

    def __str__(self):
        status = 'Habilitado' if self.enabled else 'Desabilitado'
        return f"Mercado Pago - {status}"

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(
            singleton_key='config',
            defaults={'enabled': False, 'use_for_boletos': False}
        )
        return obj


class UsuarioSistema(models.Model):
    """Usuários do sistema (Super Admin e Suporte)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_sistema')
    
    TIPO_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('suporte', 'Suporte'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # Informações adicionais
    cpf = models.CharField(max_length=14, blank=True, help_text='CPF do usuário (apenas números ou formatado)')
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


class ProfissionalUsuario(models.Model):
    """
    Vínculo User (Django auth, schema public) <-> Professional (clinica_beleza, schema tenant).
    Permite que o profissional faça login em /loja/{slug}/login com o mesmo fluxo da loja.
    perfil define o tipo de acesso: administrador, profissional, recepcionista, caixa, limpeza, estoque.
    """
    PERFIL_ADMINISTRADOR = 'administrador'
    PERFIL_PROFISSIONAL = 'profissional'
    PERFIL_RECEPCAO = 'recepcao'  # legado; equivalente a recepcionista
    PERFIL_RECEPCIONISTA = 'recepcionista'
    PERFIL_CAIXA = 'caixa'
    PERFIL_LIMPEZA = 'limpeza'
    PERFIL_ESTOQUE = 'estoque'
    PERFIL_CHOICES = [
        (PERFIL_ADMINISTRADOR, 'Administrador'),
        (PERFIL_PROFISSIONAL, 'Profissional (só agenda e bloqueios próprios)'),
        (PERFIL_RECEPCAO, 'Recepção (acesso completo)'),  # legado
        (PERFIL_RECEPCIONISTA, 'Recepcionista'),
        (PERFIL_CAIXA, 'Caixa'),
        (PERFIL_LIMPEZA, 'Limpeza'),
        (PERFIL_ESTOQUE, 'Estoque'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profissional_lojas')
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='profissionais_usuarios')
    professional_id = models.PositiveIntegerField(help_text='ID do Professional no schema da loja')
    perfil = models.CharField(
        max_length=20,
        choices=PERFIL_CHOICES,
        default=PERFIL_PROFISSIONAL,
        help_text='Tipo de acesso: administrador, profissional, recepcionista, caixa, limpeza, estoque.',
    )
    precisa_trocar_senha = models.BooleanField(default=True, help_text='Obrigar troca de senha no primeiro acesso')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Profissional (acesso)'
        verbose_name_plural = 'Profissionais (acesso)'
        unique_together = [['user', 'loja']]
        indexes = [
            models.Index(fields=['user', 'loja'], name='prof_usuario_loja_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} -> loja {self.loja.slug} (prof_id={self.professional_id})"


class HistoricoAcessoGlobal(models.Model):
    """
    Histórico global de acessos e ações de TODOS os usuários do sistema
    
    Usado pelo SuperAdmin para monitorar atividades em todas as lojas.
    Não usa LojaIsolationMixin pois precisa ser acessível globalmente.
    
    Boas práticas aplicadas:
    - Single Responsibility: Apenas registra ações
    - DRY: Reutiliza choices e estrutura
    - Clean Code: Nomes descritivos e documentação clara
    - Performance: Índices otimizados para queries comuns
    """
    
    ACAO_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('criar', 'Criar'),
        ('editar', 'Editar'),
        ('excluir', 'Excluir'),
        ('visualizar', 'Visualizar'),
        ('exportar', 'Exportar'),
        ('importar', 'Importar'),
        ('aprovar', 'Aprovar'),
        ('rejeitar', 'Rejeitar'),
    ]
    
    # Informações do usuário
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='historico_acoes',
        help_text='Usuário que realizou a ação'
    )
    usuario_email = models.EmailField(help_text='Email do usuário (backup se user for deletado)')
    usuario_nome = models.CharField(max_length=200, help_text='Nome completo do usuário')
    
    # Informações da loja
    loja = models.ForeignKey(
        Loja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_acoes',
        help_text='Loja onde a ação foi realizada (null para ações do SuperAdmin)'
    )
    loja_nome = models.CharField(max_length=200, blank=True, help_text='Nome da loja (backup)')
    loja_slug = models.CharField(max_length=100, blank=True, help_text='Slug da loja')
    
    # Informações da ação
    acao = models.CharField(
        max_length=20, 
        choices=ACAO_CHOICES,
        db_index=True,
        help_text='Tipo de ação realizada'
    )
    recurso = models.CharField(
        max_length=100,
        blank=True,
        help_text='Recurso afetado (ex: Cliente, Produto, Agendamento)'
    )
    recurso_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID do recurso afetado'
    )
    detalhes = models.TextField(
        blank=True,
        help_text='Detalhes adicionais da ação (JSON ou texto)'
    )
    
    # Informações técnicas
    ip_address = models.GenericIPAddressField(help_text='Endereço IP do usuário')
    user_agent = models.TextField(blank=True, help_text='User Agent do navegador')
    metodo_http = models.CharField(
        max_length=10,
        blank=True,
        help_text='Método HTTP (GET, POST, PUT, DELETE)'
    )
    url = models.CharField(
        max_length=500,
        blank=True,
        help_text='URL da requisição'
    )
    
    # Resultado da ação
    sucesso = models.BooleanField(
        default=True,
        help_text='Indica se a ação foi bem-sucedida'
    )
    erro = models.TextField(
        blank=True,
        help_text='Mensagem de erro (se houver)'
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'superadmin_historico_acesso_global'
        verbose_name = 'Histórico de Acesso Global'
        verbose_name_plural = 'Histórico de Acessos Global'
        ordering = ['-created_at']
        
        # ✅ OTIMIZAÇÃO: Índices compostos para queries comuns do SuperAdmin
        indexes = [
            # Busca por usuário + data
            models.Index(fields=['user', '-created_at'], name='hist_user_date_idx'),
            # Busca por loja + data
            models.Index(fields=['loja', '-created_at'], name='hist_loja_date_idx'),
            # Busca por ação + data
            models.Index(fields=['acao', '-created_at'], name='hist_acao_date_idx'),
            # Busca por email (para usuários deletados)
            models.Index(fields=['usuario_email', '-created_at'], name='hist_email_date_idx'),
            # Busca por IP (segurança)
            models.Index(fields=['ip_address', '-created_at'], name='hist_ip_date_idx'),
            # Busca por sucesso (erros)
            models.Index(fields=['sucesso', '-created_at'], name='hist_sucesso_date_idx'),
        ]
    
    def __str__(self):
        loja_info = f" - {self.loja_nome}" if self.loja_nome else " - SuperAdmin"
        return f"{self.usuario_nome} - {self.get_acao_display()}{loja_info} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def navegador(self):
        """Extrai nome do navegador do user agent"""
        if not self.user_agent:
            return 'Desconhecido'
        
        ua = self.user_agent.lower()
        if 'chrome' in ua and 'edg' not in ua:
            return 'Chrome'
        elif 'firefox' in ua:
            return 'Firefox'
        elif 'safari' in ua and 'chrome' not in ua:
            return 'Safari'
        elif 'edg' in ua:
            return 'Edge'
        elif 'opera' in ua or 'opr' in ua:
            return 'Opera'
        else:
            return 'Outro'
    
    @property
    def sistema_operacional(self):
        """Extrai sistema operacional do user agent"""
        if not self.user_agent:
            return 'Desconhecido'
        
        ua = self.user_agent.lower()
        if 'windows' in ua:
            return 'Windows'
        elif 'mac' in ua:
            return 'macOS'
        elif 'linux' in ua:
            return 'Linux'
        elif 'android' in ua:
            return 'Android'
        elif 'iphone' in ua or 'ipad' in ua:
            return 'iOS'
        else:
            return 'Outro'


class ViolacaoSeguranca(models.Model):
    """
    Registra violações de segurança detectadas automaticamente

    Tipos de violações:
    - acesso_cross_tenant: Tentativa de acessar recursos de outra loja
    - brute_force: Múltiplas tentativas de login falhadas
    - rate_limit_exceeded: Excesso de requisições em curto período
    - privilege_escalation: Tentativa de acessar recursos sem permissão
    - mass_deletion: Exclusão em massa de registros
    - ip_change: Mudança suspeita de IP
    - suspicious_pattern: Outros padrões suspeitos

    Boas práticas aplicadas:
    - Single Responsibility: Apenas registra violações
    - Clean Code: Nomes descritivos e documentação clara
    - Performance: Índices otimizados para queries comuns
    - Auditoria: Rastreamento completo de investigação e resolução
    """

    TIPO_CHOICES = [
        ('acesso_cross_tenant', 'Acesso Cross-Tenant'),
        ('brute_force', 'Tentativa de Brute Force'),
        ('rate_limit_exceeded', 'Rate Limit Excedido'),
        ('privilege_escalation', 'Escalação de Privilégios'),
        ('mass_deletion', 'Exclusão em Massa'),
        ('ip_change', 'Mudança de IP'),
        ('suspicious_pattern', 'Padrão Suspeito'),
    ]

    CRITICIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    STATUS_CHOICES = [
        ('nova', 'Nova'),
        ('investigando', 'Investigando'),
        ('resolvida', 'Resolvida'),
        ('falso_positivo', 'Falso Positivo'),
    ]

    # Identificação
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        db_index=True,
        help_text='Tipo de violação detectada'
    )
    criticidade = models.CharField(
        max_length=20,
        choices=CRITICIDADE_CHOICES,
        db_index=True,
        help_text='Nível de criticidade da violação'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='nova',
        db_index=True,
        help_text='Status da investigação'
    )

    # Contexto do usuário
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='violacoes_seguranca',
        help_text='Usuário que cometeu a violação'
    )
    usuario_email = models.EmailField(help_text='Email do usuário (backup)')
    usuario_nome = models.CharField(max_length=200, help_text='Nome do usuário')

    # Contexto da loja
    loja = models.ForeignKey(
        Loja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='violacoes_seguranca',
        help_text='Loja onde ocorreu a violação'
    )
    loja_nome = models.CharField(max_length=200, blank=True, help_text='Nome da loja (backup)')

    # Detalhes da violação
    descricao = models.TextField(help_text='Descrição da violação detectada')
    detalhes_tecnicos = models.JSONField(
        default=dict,
        help_text='Detalhes técnicos adicionais (JSON)'
    )
    ip_address = models.GenericIPAddressField(help_text='IP de origem da violação')

    # Logs relacionados
    logs_relacionados = models.ManyToManyField(
        HistoricoAcessoGlobal,
        related_name='violacoes',
        blank=True,
        help_text='Logs que evidenciam a violação'
    )

    # Gestão da violação
    resolvido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='violacoes_resolvidas',
        help_text='SuperAdmin que resolveu a violação'
    )
    resolvido_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data/hora da resolução'
    )
    notas = models.TextField(
        blank=True,
        help_text='Notas sobre investigação e resolução'
    )

    # Notificação
    notificado = models.BooleanField(
        default=False,
        help_text='Indica se SuperAdmin foi notificado'
    )
    notificado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data/hora da notificação'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'superadmin_violacoes_seguranca'
        verbose_name = 'Violação de Segurança'
        verbose_name_plural = 'Violações de Segurança'
        ordering = ['-created_at']

        # ✅ OTIMIZAÇÃO: Índices compostos para queries comuns
        indexes = [
            # Dashboard de alertas: violações não resolvidas por criticidade
            models.Index(
                fields=['status', 'criticidade', '-created_at'],
                name='viol_status_crit_idx'
            ),
            # Busca por tipo + data
            models.Index(
                fields=['tipo', '-created_at'],
                name='viol_tipo_date_idx'
            ),
            # Busca por usuário + data
            models.Index(
                fields=['user', '-created_at'],
                name='viol_user_date_idx'
            ),
            # Busca por loja + data
            models.Index(
                fields=['loja', '-created_at'],
                name='viol_loja_date_idx'
            ),
            # Busca por IP (segurança)
            models.Index(
                fields=['ip_address', '-created_at'],
                name='viol_ip_date_idx'
            ),
            # Violações não notificadas
            models.Index(
                fields=['notificado', 'criticidade'],
                name='viol_notif_crit_idx'
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.usuario_nome} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    def get_criticidade_color(self):
        """Retorna cor para exibição baseada na criticidade"""
        colors = {
            'baixa': '#10B981',    # Verde
            'media': '#F59E0B',    # Amarelo
            'alta': '#EF4444',     # Vermelho
            'critica': '#DC2626',  # Vermelho escuro
        }
        return colors.get(self.criticidade, '#6B7280')  # Cinza padrão

    def get_tipo_display_friendly(self):
        """Retorna descrição amigável do tipo de violação"""
        descriptions = {
            'acesso_cross_tenant': 'Tentativa de acessar dados de outra loja',
            'brute_force': 'Múltiplas tentativas de login falhadas',
            'rate_limit_exceeded': 'Excesso de requisições em curto período',
            'privilege_escalation': 'Tentativa de acessar recursos sem permissão',
            'mass_deletion': 'Exclusão em massa de registros',
            'ip_change': 'Acesso de IP diferente do habitual',
            'suspicious_pattern': 'Padrão de comportamento suspeito detectado',
        }
        return descriptions.get(self.tipo, self.get_tipo_display())

    @classmethod
    def get_criticidade_automatica(cls, tipo):
        """
        Define criticidade automática baseada no tipo de violação

        Mapeamento:
        - brute_force: alta
        - rate_limit_exceeded: media
        - acesso_cross_tenant: critica
        - privilege_escalation: critica
        - mass_deletion: alta
        - ip_change: baixa
        - suspicious_pattern: media
        """
        mapeamento = {
            'brute_force': 'alta',
            'rate_limit_exceeded': 'media',
            'acesso_cross_tenant': 'critica',
            'privilege_escalation': 'critica',
            'mass_deletion': 'alta',
            'ip_change': 'baixa',
            'suspicious_pattern': 'media',
        }
        return mapeamento.get(tipo, 'media')




class EmailRetry(models.Model):
    """
    Modelo para gerenciar retry de emails falhados
    
    Quando um email falha ao ser enviado (ex.: senha provisória),
    este modelo armazena os dados para tentativas automáticas de reenvio.
    """
    destinatario = models.EmailField(help_text='Email do destinatário')
    assunto = models.CharField(max_length=255, help_text='Assunto do email')
    mensagem = models.TextField(help_text='Corpo do email')
    
    # Controle de tentativas
    tentativas = models.IntegerField(default=0, help_text='Número de tentativas realizadas')
    max_tentativas = models.IntegerField(default=3, help_text='Número máximo de tentativas')
    
    # Status
    enviado = models.BooleanField(default=False, help_text='Indica se o email foi enviado com sucesso')
    erro = models.TextField(blank=True, help_text='Último erro ocorrido ao tentar enviar')
    
    # Relacionamento
    loja = models.ForeignKey(
        'Loja', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='emails_retry',
        help_text='Loja relacionada ao email (se aplicável)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text='Data de criação do registro')
    updated_at = models.DateTimeField(auto_now=True, help_text='Data da última atualização')
    proxima_tentativa = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Data e hora da próxima tentativa de envio'
    )
    
    class Meta:
        verbose_name = 'Email para Retry'
        verbose_name_plural = 'Emails para Retry'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['enviado', 'tentativas'], name='email_retry_status_idx'),
            models.Index(fields=['proxima_tentativa'], name='email_retry_proxima_idx'),
            models.Index(fields=['loja', 'enviado'], name='email_retry_loja_idx'),
        ]
    
    def __str__(self):
        status = "✅ Enviado" if self.enviado else f"⏳ Tentativa {self.tentativas}/{self.max_tentativas}"
        return f"{status} - {self.destinatario} - {self.assunto[:50]}"
    
    def pode_retentar(self):
        """Verifica se ainda pode tentar reenviar o email"""
        return not self.enviado and self.tentativas < self.max_tentativas
    
    def atingiu_max_tentativas(self):
        """Verifica se atingiu o número máximo de tentativas"""
        return self.tentativas >= self.max_tentativas


# ============================================================================
# MODELOS DE BACKUP - v800
# ============================================================================

class ConfiguracaoBackup(models.Model):
    """
    Configuração de backup automático para cada loja.
    
    Responsabilidades:
    - Armazenar configurações de agendamento de backup
    - Controlar frequência e horário de envio
    - Manter histórico de execuções
    
    Boas práticas aplicadas:
    - Single Responsibility: Apenas configuração de backup
    - Validação de dados no método clean()
    - Choices bem definidos para campos de seleção
    """
    
    # Choices
    FREQUENCIA_CHOICES = [
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
    ]
    
    DIA_SEMANA_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    # Relacionamento
    loja = models.OneToOneField(
        Loja,
        on_delete=models.CASCADE,
        related_name='config_backup',
        help_text='Loja associada a esta configuração'
    )
    
    # Configuração de agendamento
    backup_automatico_ativo = models.BooleanField(
        default=False,
        help_text='Ativa ou desativa o backup automático'
    )
    horario_envio = models.TimeField(
        default='03:00:00',
        help_text='Horário para envio automático do backup (formato 24h)'
    )
    frequencia = models.CharField(
        max_length=20,
        choices=FREQUENCIA_CHOICES,
        default='semanal',
        help_text='Frequência de execução do backup automático'
    )
    dia_semana = models.IntegerField(
        null=True,
        blank=True,
        choices=DIA_SEMANA_CHOICES,
        help_text='Dia da semana para backup semanal (0=Segunda, 6=Domingo)'
    )
    dia_mes = models.IntegerField(
        null=True,
        blank=True,
        help_text='Dia do mês para backup mensal (1-28)'
    )
    
    # Histórico de execuções
    ultimo_backup = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data e hora do último backup realizado'
    )
    ultimo_envio_email = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data e hora do último envio de email com backup'
    )
    total_backups_realizados = models.IntegerField(
        default=0,
        help_text='Contador total de backups realizados'
    )
    
    # Configurações adicionais
    incluir_imagens = models.BooleanField(
        default=False,
        help_text='Incluir imagens no backup (aumenta significativamente o tamanho)'
    )
    manter_ultimos_n_backups = models.IntegerField(
        default=5,
        help_text='Quantidade de backups a manter armazenados no servidor'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'superadmin_configuracao_backup'
        verbose_name = 'Configuração de Backup'
        verbose_name_plural = 'Configurações de Backup'
        indexes = [
            models.Index(fields=['backup_automatico_ativo', 'horario_envio'], name='cfg_backup_ativo_idx'),
            models.Index(fields=['ultimo_backup'], name='cfg_backup_ultimo_idx'),
        ]
    
    def __str__(self):
        status = "✅ Ativo" if self.backup_automatico_ativo else "❌ Inativo"
        return f"{status} - {self.loja.nome} - {self.get_frequencia_display()}"
    
    def clean(self):
        """
        Validações customizadas.
        
        Garante consistência dos dados de agendamento.
        """
        from django.core.exceptions import ValidationError
        
        # Validar dia_semana para backup semanal
        if self.frequencia == 'semanal' and self.dia_semana is None:
            raise ValidationError({
                'dia_semana': 'Dia da semana é obrigatório para backup semanal'
            })
        
        # Validar dia_mes para backup mensal
        if self.frequencia == 'mensal':
            if self.dia_mes is None:
                raise ValidationError({
                    'dia_mes': 'Dia do mês é obrigatório para backup mensal'
                })
            if not (1 <= self.dia_mes <= 28):
                raise ValidationError({
                    'dia_mes': 'Dia do mês deve estar entre 1 e 28'
                })
        
        # Validar manter_ultimos_n_backups
        if self.manter_ultimos_n_backups < 1:
            raise ValidationError({
                'manter_ultimos_n_backups': 'Deve manter pelo menos 1 backup'
            })
        if self.manter_ultimos_n_backups > 30:
            raise ValidationError({
                'manter_ultimos_n_backups': 'Não é recomendado manter mais de 30 backups'
            })
    
    def save(self, *args, **kwargs):
        """Executa validações antes de salvar"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def deve_executar_backup_hoje(self):
        """
        Verifica se o backup deve ser executado hoje (data local conforme TIME_ZONE).
        
        Returns:
            bool: True se deve executar, False caso contrário
        """
        if not self.backup_automatico_ativo:
            return False
        
        now_local = timezone.localtime(timezone.now())
        
        if self.frequencia == 'diario':
            return True
        
        if self.frequencia == 'semanal':
            return now_local.weekday() == self.dia_semana
        
        if self.frequencia == 'mensal':
            return now_local.day == self.dia_mes
        
        return False
    
    def incrementar_contador(self):
        """Incrementa o contador de backups realizados"""
        self.total_backups_realizados += 1
        self.ultimo_backup = timezone.now()
        self.save(update_fields=['total_backups_realizados', 'ultimo_backup'])


class HistoricoBackup(models.Model):
    """
    Histórico de backups realizados.
    
    Responsabilidades:
    - Registrar cada backup executado
    - Armazenar metadados e estatísticas
    - Controlar status e erros
    
    Boas práticas aplicadas:
    - Auditoria completa de operações
    - Separação de concerns (status, email, arquivo)
    - Índices otimizados para queries comuns
    """
    
    # Choices
    TIPO_CHOICES = [
        ('manual', 'Manual'),
        ('automatico', 'Automático'),
    ]
    
    STATUS_CHOICES = [
        ('processando', 'Processando'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
    ]
    
    # Relacionamentos
    loja = models.ForeignKey(
        Loja,
        on_delete=models.CASCADE,
        related_name='historico_backups',
        help_text='Loja que teve backup realizado'
    )
    solicitado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backups_solicitados',
        help_text='Usuário que solicitou o backup (para backups manuais)'
    )
    
    # Tipo e status
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        db_index=True,
        help_text='Tipo de backup: manual ou automático'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='processando',
        db_index=True,
        help_text='Status atual do processamento do backup'
    )
    
    # Informações do arquivo
    arquivo_nome = models.CharField(
        max_length=255,
        help_text='Nome do arquivo de backup gerado'
    )
    arquivo_tamanho_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Tamanho do arquivo em megabytes'
    )
    arquivo_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Caminho do arquivo no storage (S3, filesystem, etc)'
    )
    
    # Estatísticas do backup
    total_registros = models.IntegerField(
        default=0,
        help_text='Total de registros incluídos no backup'
    )
    tabelas_incluidas = models.JSONField(
        default=dict,
        help_text='Dicionário com contagem de registros por tabela'
    )
    tempo_processamento_segundos = models.IntegerField(
        null=True,
        blank=True,
        help_text='Tempo total de processamento em segundos'
    )
    
    # Controle de erros
    erro_mensagem = models.TextField(
        blank=True,
        help_text='Mensagem de erro detalhada (se houver)'
    )
    
    # Controle de email
    email_enviado = models.BooleanField(
        default=False,
        help_text='Indica se o backup foi enviado por email'
    )
    email_enviado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data e hora do envio do email'
    )
    email_destinatario = models.EmailField(
        blank=True,
        help_text='Email do destinatário'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Data e hora de criação do registro'
    )
    concluido_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data e hora de conclusão do backup'
    )
    
    class Meta:
        db_table = 'superadmin_historico_backup'
        verbose_name = 'Histórico de Backup'
        verbose_name_plural = 'Histórico de Backups'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loja', '-created_at'], name='hist_backup_loja_idx'),
            models.Index(fields=['status', '-created_at'], name='hist_backup_status_idx'),
            models.Index(fields=['tipo', '-created_at'], name='hist_backup_tipo_idx'),
            models.Index(fields=['email_enviado'], name='hist_backup_email_idx'),
        ]
    
    def __str__(self):
        status_emoji = {
            'processando': '⏳',
            'concluido': '✅',
            'erro': '❌',
        }
        emoji = status_emoji.get(self.status, '❓')
        return f"{emoji} {self.loja.nome} - {self.get_tipo_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    def marcar_como_concluido(self, tamanho_mb: float, total_registros: int, tabelas: dict):
        """
        Marca o backup como concluído com sucesso.
        
        Args:
            tamanho_mb: Tamanho do arquivo em MB
            total_registros: Total de registros exportados
            tabelas: Dicionário com contagem por tabela
        """
        self.status = 'concluido'
        self.arquivo_tamanho_mb = tamanho_mb
        self.total_registros = total_registros
        self.tabelas_incluidas = tabelas
        self.concluido_em = timezone.now()
        
        # Calcular tempo de processamento
        if self.created_at:
            delta = self.concluido_em - self.created_at
            self.tempo_processamento_segundos = int(delta.total_seconds())
        
        self.save()
    
    def marcar_como_erro(self, erro_mensagem: str):
        """
        Marca o backup como erro.
        
        Args:
            erro_mensagem: Mensagem de erro detalhada
        """
        self.status = 'erro'
        self.erro_mensagem = erro_mensagem
        self.concluido_em = timezone.now()
        self.save()
    
    def marcar_email_enviado(self, destinatario: str):
        """
        Marca que o email foi enviado com sucesso.
        
        Args:
            destinatario: Email do destinatário
        """
        self.email_enviado = True
        self.email_enviado_em = timezone.now()
        self.email_destinatario = destinatario
        self.save(update_fields=['email_enviado', 'email_enviado_em', 'email_destinatario'])
    
    def get_tamanho_formatado(self):
        """
        Retorna o tamanho do arquivo formatado.
        
        Returns:
            str: Tamanho formatado (ex: "15.5 MB")
        """
        if self.arquivo_tamanho_mb < 1:
            return f"{self.arquivo_tamanho_mb * 1024:.1f} KB"
        return f"{self.arquivo_tamanho_mb:.2f} MB"
    
    def get_tempo_processamento_formatado(self):
        """
        Retorna o tempo de processamento formatado.
        
        Returns:
            str: Tempo formatado (ex: "2m 30s")
        """
        if not self.tempo_processamento_segundos:
            return "N/A"
        
        minutos = self.tempo_processamento_segundos // 60
        segundos = self.tempo_processamento_segundos % 60
        
        if minutos > 0:
            return f"{minutos}m {segundos}s"
        return f"{segundos}s"
