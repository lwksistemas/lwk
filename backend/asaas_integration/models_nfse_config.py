"""
Configuração de NFS-e do Superadmin (emissão de notas para assinaturas das lojas).
Permite escolher entre emitir via Asaas (intermediário) ou ISSNet direto.
"""
from django.db import models


class SuperadminNFSeConfig(models.Model):
    """
    Configuração de emissão de NFS-e para assinaturas das lojas.
    Singleton — apenas um registro.
    
    Quando uma loja paga a assinatura, o sistema emite NFS-e usando
    o certificado digital da empresa administradora (ex: LWK Sistemas).
    """
    singleton_key = models.CharField(max_length=10, default='config', unique=True)

    # Provedor de emissão
    PROVEDOR_CHOICES = [
        ('asaas', 'Asaas (Intermediário - emite via Asaas)'),
        ('issnet', 'ISSNet Ribeirão Preto (Direto - sem taxa)'),
        ('desabilitado', 'Desabilitado (não emite NFS-e)'),
    ]
    provedor_nfse = models.CharField(
        max_length=20,
        choices=PROVEDOR_CHOICES,
        default='asaas',
        verbose_name='Provedor de NFS-e',
        help_text='Como emitir notas fiscais das assinaturas das lojas'
    )

    # Emissão automática após pagamento
    emitir_automaticamente = models.BooleanField(
        default=True,
        verbose_name='Emitir automaticamente',
        help_text='Emitir NFS-e automaticamente quando pagamento é confirmado'
    )

    # === Dados do Prestador (empresa que emite as notas) ===
    prestador_cnpj = models.CharField(
        max_length=18, blank=True,
        verbose_name='CNPJ do Prestador',
        help_text='CNPJ da empresa que emite as notas (ex: LWK Sistemas)'
    )
    prestador_razao_social = models.CharField(
        max_length=200, blank=True,
        verbose_name='Razão Social',
    )
    prestador_inscricao_municipal = models.CharField(
        max_length=20, blank=True,
        verbose_name='Inscrição Municipal',
    )
    prestador_email = models.EmailField(
        blank=True,
        verbose_name='E-mail do Prestador',
        help_text='E-mail para receber notificações de NFS-e emitidas'
    )

    # Regime Especial de Tributação
    REGIME_ESPECIAL_CHOICES = [
        ('', '-'),
        ('1', 'Microempresa Municipal'),
        ('2', 'Estimativa'),
        ('3', 'Sociedade de Profissionais'),
        ('4', 'Cooperativa'),
        ('5', 'Microempresário Individual (MEI)'),
        ('6', 'Microempresário e Empresa de Pequeno Porte (ME EPP)'),
    ]
    regime_especial_tributacao = models.CharField(
        max_length=2, blank=True, default='',
        choices=REGIME_ESPECIAL_CHOICES,
        verbose_name='Regime Especial de Tributação',
        help_text='Identifica o regime de tributação da empresa. Simples Nacional geralmente usa Microempresa Municipal.'
    )

    # === Configurações ISSNet (quando provedor = issnet) ===
    issnet_usuario = models.CharField(
        max_length=100, blank=True,
        verbose_name='Usuário ISSNet',
    )
    issnet_senha = models.CharField(
        max_length=100, blank=True,
        verbose_name='Senha ISSNet',
    )
    issnet_certificado = models.BinaryField(
        blank=True, null=True,
        verbose_name='Certificado Digital A1 (.pfx)',
    )
    issnet_certificado_nome = models.CharField(
        max_length=255, blank=True,
        verbose_name='Nome do arquivo .pfx',
    )
    issnet_senha_certificado = models.CharField(
        max_length=100, blank=True,
        verbose_name='Senha do Certificado',
    )

    # === Dados fiscais ===
    codigo_servico_municipal = models.CharField(
        max_length=10, default='1401', blank=True,
        verbose_name='Código do Serviço Municipal',
    )
    descricao_servico_padrao = models.TextField(
        default='Licenciamento de uso de software SaaS',
        blank=True,
        verbose_name='Descrição Padrão do Serviço',
    )
    aliquota_iss = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00,
        verbose_name='Alíquota ISS (%)',
    )
    codigo_cnae = models.CharField(
        max_length=20, blank=True,
        verbose_name='Código CNAE',
    )
    optante_simples_nacional = models.BooleanField(
        default=True,
        verbose_name='Optante Simples Nacional',
    )
    incentivador_cultural = models.BooleanField(
        default=False,
        verbose_name='Incentivador Cultural',
        help_text='Se a empresa é incentivadora cultural'
    )

    # === Controle de RPS ===
    serie_rps = models.CharField(
        max_length=10, default='E', blank=True,
        verbose_name='Série do RPS',
    )
    ultimo_rps = models.IntegerField(
        default=0,
        verbose_name='Último RPS emitido',
        help_text='Próxima emissão usará este + 1'
    )

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'superadmin_nfse_config'
        verbose_name = 'Configuração NFS-e Superadmin'
        verbose_name_plural = 'Configurações NFS-e Superadmin'

    def __str__(self):
        return f"NFS-e Config - {self.get_provedor_nfse_display()}"

    @classmethod
    def get_config(cls):
        """Obtém ou cria configuração singleton."""
        obj, _ = cls.objects.using('default').get_or_create(
            singleton_key='config',
            defaults={'provedor_nfse': 'asaas'}
        )
        return obj

    def proximo_rps(self) -> int:
        """Retorna e incrementa o próximo número de RPS."""
        self.ultimo_rps += 1
        self.save(update_fields=['ultimo_rps', 'updated_at'])
        return self.ultimo_rps
