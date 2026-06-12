from django.db import models

from core.mixins import LojaIsolationMixin, LojaIsolationManager

class Conta(LojaIsolationMixin, models.Model):
    """Conta (empresa)."""
    TIPO_CHOICES = [
        ('cliente', 'Cliente'),
        ('prestadora', 'Prestadora de Serviço'),
        ('ambos', 'Cliente e Prestadora'),
    ]

    nome = models.CharField(max_length=255, help_text='Nome fantasia da empresa')
    razao_social = models.CharField(max_length=255, blank=True, help_text='Razão social da empresa')
    cnpj = models.CharField(max_length=18, blank=True, help_text='CNPJ da empresa (formato: 00.000.000/0000-00)')
    inscricao_estadual = models.CharField(max_length=20, blank=True, help_text='Inscrição estadual')
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='cliente',
        help_text='Tipo da empresa: cliente, prestadora de serviço ou ambos',
    )
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
            models.Index(fields=['loja_id', 'tipo'], name='crm_conta_loja_tipo_idx'),
        ]

    def __str__(self):
        return self.nome

