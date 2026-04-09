"""
Modelos para armazenar NFS-e emitidas pelas lojas
"""
from django.db import models
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class NFSe(LojaIsolationMixin, models.Model):
    """
    Registro de NFS-e emitida pela loja.
    
    Armazena informações de notas fiscais emitidas através de qualquer provedor
    (Asaas, ISSNet, API Nacional, etc).
    """
    
    # Número da NFS-e (gerado pela prefeitura)
    numero_nf = models.CharField(
        max_length=50,
        verbose_name='Número da NFS-e',
        help_text='Número da nota fiscal gerado pela prefeitura'
    )
    
    # Número do RPS (gerado pela loja)
    numero_rps = models.IntegerField(
        default=0,
        verbose_name='Número do RPS',
        help_text='Número do Recibo Provisório de Serviços'
    )
    
    # Código de verificação
    codigo_verificacao = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Código de Verificação',
        help_text='Código para verificar autenticidade da NF no portal da prefeitura'
    )
    
    # Datas
    data_emissao = models.DateTimeField(
        verbose_name='Data de Emissão',
        help_text='Data e hora em que a NF foi emitida'
    )
    
    data_cancelamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Cancelamento',
        help_text='Data e hora em que a NF foi cancelada'
    )
    
    # Valores
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor Total',
        help_text='Valor total dos serviços'
    )
    
    valor_iss = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Valor ISS',
        help_text='Valor do ISS retido'
    )
    
    aliquota_iss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Alíquota ISS (%)',
        help_text='Alíquota do ISS aplicada'
    )
    
    # Tomador (cliente)
    tomador_cpf_cnpj = models.CharField(
        max_length=18,
        blank=True,
        verbose_name='CPF/CNPJ do Tomador',
        help_text='CPF ou CNPJ do cliente'
    )
    
    tomador_nome = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nome do Tomador',
        help_text='Nome ou razão social do cliente'
    )
    
    tomador_email = models.EmailField(
        blank=True,
        verbose_name='Email do Tomador',
        help_text='Email do cliente'
    )
    
    # Serviço
    servico_codigo = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Código do Serviço',
        help_text='Código do serviço municipal'
    )
    
    servico_descricao = models.TextField(
        blank=True,
        verbose_name='Descrição do Serviço',
        help_text='Descrição do serviço prestado'
    )
    
    # Provedor
    PROVEDOR_CHOICES = [
        ('asaas', 'Asaas'),
        ('issnet', 'ISSNet - Ribeirão Preto'),
        ('nacional', 'API Nacional NFS-e'),
        ('manual', 'Manual'),
    ]
    
    provedor = models.CharField(
        max_length=20,
        choices=PROVEDOR_CHOICES,
        default='asaas',
        verbose_name='Provedor',
        help_text='Sistema usado para emitir a NF'
    )
    
    # Status
    STATUS_CHOICES = [
        ('emitida', 'Emitida'),
        ('cancelada', 'Cancelada'),
        ('erro', 'Erro na Emissão'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='emitida',
        verbose_name='Status',
        help_text='Status atual da NF'
    )
    
    # XMLs
    xml_rps = models.TextField(
        blank=True,
        verbose_name='XML do RPS',
        help_text='XML do Recibo Provisório de Serviços'
    )
    
    xml_nfse = models.TextField(
        blank=True,
        verbose_name='XML da NFS-e',
        help_text='XML da Nota Fiscal de Serviço Eletrônica'
    )
    
    # URLs
    pdf_url = models.URLField(
        blank=True,
        verbose_name='URL do PDF',
        help_text='URL para download do PDF da NF'
    )
    
    xml_url = models.URLField(
        blank=True,
        verbose_name='URL do XML',
        help_text='URL para download do XML da NF'
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações',
        help_text='Observações internas sobre a NF'
    )
    
    # Erro (se houver)
    erro = models.TextField(
        blank=True,
        verbose_name='Erro',
        help_text='Mensagem de erro se a emissão falhou'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()
    
    class Meta:
        db_table = 'nfse_integration_nfse'
        verbose_name = 'NFS-e'
        verbose_name_plural = 'NFS-e'
        ordering = ['-data_emissao']
        indexes = [
            models.Index(fields=['loja_id', '-data_emissao'], name='nfse_loja_data_idx'),
            models.Index(fields=['numero_nf'], name='nfse_numero_idx'),
            models.Index(fields=['numero_rps'], name='nfse_rps_idx'),
            models.Index(fields=['status'], name='nfse_status_idx'),
            models.Index(fields=['tomador_cpf_cnpj'], name='nfse_tomador_idx'),
        ]
        # Garantir que número de NF é único por loja
        unique_together = [['loja_id', 'numero_nf']]
    
    def __str__(self):
        return f'NFS-e {self.numero_nf} - {self.loja.nome if self.loja_id else "N/A"}'
    
    def get_valor_liquido(self):
        """Retorna valor líquido (valor - ISS)."""
        return self.valor - self.valor_iss
    
    def is_cancelada(self):
        """Verifica se a NF está cancelada."""
        return self.status == 'cancelada'
    
    def pode_cancelar(self):
        """Verifica se a NF pode ser cancelada."""
        return self.status == 'emitida'
