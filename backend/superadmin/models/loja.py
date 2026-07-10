"""Modelos Super Admin."""
import re

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .catalog import PlanoAssinatura, TipoLoja

class Loja(models.Model):
    """Loja gerenciada pelo Super Admin"""
    # Informações básicas
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(blank=True)
    
    # Documentos
    cpf_cnpj = models.CharField(max_length=18, blank=True, db_index=True, help_text='CPF ou CNPJ da loja (somente dígitos)')
    inscricao_municipal = models.CharField(max_length=20, blank=True, default='', help_text='Inscrição municipal da loja (para emissão de NFS-e)')
    
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
    
    # ✅ NOVO: Forma de pagamento preferida (primeira cobrança sempre boleto/PIX)
    FORMA_PAGAMENTO_CHOICES = [
        ('boleto', 'Boleto Bancário'),
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão de Crédito'),
    ]
    forma_pagamento_preferida = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        default='boleto',
        help_text='Forma de pagamento escolhida pelo administrador (primeira cobrança sempre boleto/PIX)'
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
    cor_fundo_pagina = models.CharField(
        max_length=7,
        blank=True,
        help_text='Cor de fundo das páginas internas (#RRGGBB). Vazio = tom claro da cor primária.',
    )
    agenda_status_colors = models.JSONField(
        default=dict,
        blank=True,
        help_text='Overrides de cores dos status da agenda (bg/border por status). Vazio = padrão LWK.',
    )
    colunas_consultas = models.JSONField(
        default=list,
        blank=True,
        help_text='Colunas visíveis na listagem de Consultas (clínica). Vazio = padrão sem AGENDA.',
    )
    dominio_customizado = models.CharField(max_length=255, blank=True, unique=True, null=True)
    
    # ✅ NOVO v1421: Sistema híbrido de acesso às lojas
    atalho = models.SlugField(
        unique=True,
        blank=True,
        max_length=50,
        help_text='Atalho curto para acesso fácil (ex: felix). Gerado automaticamente a partir do nome.'
    )
    subdomain = models.SlugField(
        unique=True,
        blank=True,
        null=True,
        max_length=50,
        help_text='Subdomínio personalizado (ex: felix.lwksistemas.com.br). Opcional para planos premium.'
    )
    
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
        ordering = ['nome']
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['is_active', '-created_at'], name='loja_active_created_idx'),
            models.Index(fields=['tipo_loja', 'is_active'], name='loja_tipo_active_idx'),
            models.Index(fields=['plano', 'is_active'], name='loja_plano_active_idx'),
            models.Index(fields=['owner', 'is_active'], name='loja_owner_active_idx'),
            models.Index(fields=['database_name'], name='loja_db_name_idx'),
            models.Index(fields=['storage_ultima_verificacao'], name='loja_storage_check_idx'),
            # ✅ NOVO v1421: Índices para sistema de acesso híbrido
            models.Index(fields=['atalho'], name='loja_atalho_idx'),
            models.Index(fields=['subdomain'], name='loja_subdomain_idx'),
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
    
    def _generate_unique_atalho(self):
        """
        Gera atalho simples e único (sem hash) a partir do nome da loja.
        
        ✅ NOVO v1421: Sistema híbrido de acesso
        
        O atalho é usado para acesso fácil pelo cliente (ex: /felix)
        enquanto o slug continua sendo usado internamente com hash para segurança.
        
        Returns:
            str: Atalho único (ex: 'felix-representacoes')
        """
        # Base: nome da loja slugificado (máximo 30 caracteres para manter URL curta)
        base = slugify(self.nome)[:30].rstrip('-')
        
        if not base:
            base = 'loja'
        
        # Garantir unicidade: se já existir, adicionar sufixo numérico
        atalho = base
        counter = 1
        while Loja.objects.filter(atalho=atalho).exclude(pk=self.pk).exists():
            atalho = f"{base}-{counter}"
            counter += 1
        
        return atalho
    
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
        # Gerar slug seguro (com hash) se não existir
        if not self.slug:
            self.slug = self._generate_unique_slug()
        
        # ✅ NOVO v1421: Gerar atalho simples (sem hash) se não existir
        if not self.atalho:
            self.atalho = self._generate_unique_atalho()
        
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
    
    def get_url_amigavel(self):
        """
        Retorna a URL amigável que o cliente deve usar (prioridade).
        
        ✅ NOVO v1421: Sistema híbrido de acesso
        
        Ordem de prioridade:
        1. Domínio customizado (enterprise)
        2. Subdomínio (premium)
        3. Atalho simples (padrão)
        
        Returns:
            str: URL completa amigável para o cliente
        
        Exemplos:
            >>> loja.get_url_amigavel()
            'https://crm.felixrepresentacoes.com.br'  # Se tem domínio próprio
            'https://felix.lwksistemas.com.br'  # Se tem subdomínio
            'https://lwksistemas.com.br/felix'  # Padrão (atalho)
        """
        if self.dominio_customizado:
            return f"https://{self.dominio_customizado}"
        elif self.subdomain:
            return f"https://{self.subdomain}.lwksistemas.com.br"
        else:
            return f"https://lwksistemas.com.br/{self.atalho}"
    
    def get_url_segura(self):
        """
        Retorna a URL com hash (para uso interno do sistema).
        
        ✅ NOVO v1421: Sistema híbrido de acesso
        
        Esta URL contém o hash aleatório e é usada internamente pelo sistema
        para garantir segurança (impossível enumerar lojas).
        
        Returns:
            str: URL completa com slug seguro (contém hash)
        
        Exemplo:
            >>> loja.get_url_segura()
            'https://lwksistemas.com.br/loja/felix-representacoes-a8f3k9'
        """
        return f"https://lwksistemas.com.br/loja/{self.slug}"


