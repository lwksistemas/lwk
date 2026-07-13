"""
Modelo de Relatório de Comissão com workflow de assinatura e pagamento.

Fluxo:
  1. Admin gera relatório → status 'pendente_aprovacao'
  2. Empresa prestadora recebe PDF por email → aprova ou reprova
  3. Se aprovado → vendedor assina → status 'aguardando_pagamento'
  4. Boleto gerado automaticamente no Asaas
  5. Pagamento confirmado → NFS-e emitida automaticamente → status 'concluido'
"""
import logging
import uuid

from django.db import connections, models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

logger = logging.getLogger(__name__)


class RelatorioComissao(LojaIsolationMixin, models.Model):
    """
    Relatório de comissão de uma empresa prestadora em um período.
    Controla o workflow: geração → aprovação → assinatura → boleto → NFS-e.
    """

    STATUS_CHOICES = [
        ('pendente_aprovacao', 'Aguardando aprovação da empresa'),
        ('reprovado', 'Reprovado pela empresa'),
        ('aprovado', 'Aprovado — aguardando assinatura do vendedor'),
        ('aguardando_pagamento', 'Aguardando pagamento'),
        ('pago', 'Pago'),
        ('nfse_emitida', 'NFS-e emitida'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    # Identificação
    numero = models.CharField(
        max_length=20,
        blank=True,
        help_text='Número sequencial do relatório (ex: RC-2024-001)',
    )
    titulo = models.CharField(
        max_length=255,
        help_text='Título descritivo (ex: Comissões Maio/2024 — Felix Representações)',
    )

    # Empresa prestadora (Conta com tipo='prestadora')
    empresa_prestadora = models.ForeignKey(
        'Conta',
        on_delete=models.PROTECT,
        related_name='relatorios_comissao',
        help_text='Empresa prestadora que receberá o relatório para aprovação',
    )

    # Vendedor responsável (assina após aprovação da empresa)
    vendedor = models.ForeignKey(
        'Vendedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relatorios_comissao',
        help_text='Vendedor que assina o relatório após aprovação da empresa',
    )

    # Período do relatório
    periodo_inicio = models.DateField(help_text='Data de início do período')
    periodo_fim = models.DateField(help_text='Data de fim do período')
    periodo_descricao = models.CharField(
        max_length=100,
        blank=True,
        help_text='Descrição legível do período (ex: Maio/2024)',
    )

    # Valores
    valor_total_vendas = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Soma total das vendas no período',
    )
    valor_total_comissao = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Valor total da comissão a pagar',
    )
    quantidade_vendas = models.IntegerField(
        default=0,
        help_text='Número de vendas fechadas no período',
    )

    # Status do workflow
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pendente_aprovacao',
        db_index=True,
    )

    # Tokens de assinatura (UUID simples, sem expiração complexa)
    token_empresa = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='Token para a empresa prestadora aprovar/reprovar',
    )
    token_vendedor = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='Token para o vendedor assinar',
    )

    # Dados de aprovação da empresa
    empresa_aprovado_em = models.DateTimeField(null=True, blank=True)
    empresa_aprovado_ip = models.GenericIPAddressField(null=True, blank=True)
    empresa_aprovado_nome = models.CharField(max_length=200, blank=True)

    # Dados de reprovação
    empresa_reprovado_em = models.DateTimeField(null=True, blank=True)
    empresa_reprovado_motivo = models.TextField(blank=True)

    # Dados de assinatura do vendedor
    vendedor_assinado_em = models.DateTimeField(null=True, blank=True)
    vendedor_assinado_ip = models.GenericIPAddressField(null=True, blank=True)
    vendedor_assinado_nome = models.CharField(max_length=200, blank=True)

    # Boleto Asaas
    asaas_payment_id = models.CharField(
        max_length=100, blank=True,
        help_text='ID da cobrança no Asaas (pay_xxxxx)',
    )
    asaas_customer_id = models.CharField(
        max_length=100, blank=True,
        help_text='ID do cliente no Asaas (cus_xxxxx)',
    )
    boleto_url = models.URLField(blank=True, help_text='URL do boleto para pagamento')
    boleto_vencimento = models.DateField(null=True, blank=True)
    pago_em = models.DateTimeField(null=True, blank=True)

    # NFS-e
    nfse_numero = models.CharField(max_length=100, blank=True)
    nfse_emitida_em = models.DateTimeField(null=True, blank=True)

    # Observações
    observacoes = models.TextField(blank=True)

    # Dados das oportunidades incluídas (snapshot JSON para o PDF)
    dados_oportunidades = models.JSONField(
        default=list,
        help_text='Lista de oportunidades incluídas no relatório (snapshot)',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_relatorio_comissao'
        ordering = ['-created_at']
        verbose_name = 'Relatório de Comissão'
        verbose_name_plural = 'Relatórios de Comissão'
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='rc_loja_status_idx'),
            models.Index(fields=['loja_id', 'empresa_prestadora'], name='rc_loja_empresa_idx'),
            models.Index(fields=['loja_id', '-created_at'], name='rc_loja_created_idx'),
            models.Index(fields=['token_empresa'], name='rc_token_empresa_idx'),
            models.Index(fields=['token_vendedor'], name='rc_token_vendedor_idx'),
            models.Index(fields=['asaas_payment_id'], name='rc_asaas_pay_idx'),
        ]

    def __str__(self):
        return f'{self.numero or self.titulo} — {self.get_status_display()}'

    def save(self, *args, **kwargs):
        """Gera número sequencial automaticamente. Cria tabela se não existir."""
        if not self.numero and self.loja_id:
            from django.utils import timezone
            ano = timezone.now().year
            try:
                ultimo = (
                    RelatorioComissao.objects.filter(
                        loja_id=self.loja_id,
                        numero__startswith=f'RC-{ano}-',
                    )
                    .order_by('-numero')
                    .first()
                )
            except Exception:
                # Tabela não existe — criar agora
                self._criar_tabela_se_necessario(kwargs.get('using'))
                ultimo = None

            if ultimo and ultimo.numero:
                try:
                    seq = int(ultimo.numero.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.numero = f'RC-{ano}-{seq:03d}'
        super().save(*args, **kwargs)

    @classmethod
    def _criar_tabela_se_necessario(cls, using=None):
        """Cria a tabela via SQL raw se não existir (fallback para multi-tenant)."""
        db = using or 'default'
        sql = """
        CREATE TABLE IF NOT EXISTS crm_relatorio_comissao (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            numero VARCHAR(20) DEFAULT '',
            titulo VARCHAR(255) NOT NULL DEFAULT '',
            empresa_prestadora_id BIGINT NOT NULL,
            vendedor_id BIGINT NULL,
            periodo_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
            periodo_fim DATE NOT NULL DEFAULT CURRENT_DATE,
            periodo_descricao VARCHAR(100) DEFAULT '',
            valor_total_vendas NUMERIC(12,2) DEFAULT 0,
            valor_total_comissao NUMERIC(12,2) DEFAULT 0,
            quantidade_vendas INTEGER DEFAULT 0,
            status VARCHAR(30) DEFAULT 'pendente_aprovacao',
            token_empresa UUID NOT NULL DEFAULT gen_random_uuid(),
            token_vendedor UUID NOT NULL DEFAULT gen_random_uuid(),
            empresa_aprovado_em TIMESTAMPTZ NULL,
            empresa_aprovado_ip INET NULL,
            empresa_aprovado_nome VARCHAR(200) DEFAULT '',
            empresa_reprovado_em TIMESTAMPTZ NULL,
            empresa_reprovado_motivo TEXT DEFAULT '',
            vendedor_assinado_em TIMESTAMPTZ NULL,
            vendedor_assinado_ip INET NULL,
            vendedor_assinado_nome VARCHAR(200) DEFAULT '',
            asaas_payment_id VARCHAR(100) DEFAULT '',
            asaas_customer_id VARCHAR(100) DEFAULT '',
            boleto_url VARCHAR(200) DEFAULT '',
            boleto_vencimento DATE NULL,
            pago_em TIMESTAMPTZ NULL,
            nfse_numero VARCHAR(100) DEFAULT '',
            nfse_emitida_em TIMESTAMPTZ NULL,
            observacoes TEXT DEFAULT '',
            dados_oportunidades JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS rc_token_empresa_uniq ON crm_relatorio_comissao(token_empresa);
        CREATE UNIQUE INDEX IF NOT EXISTS rc_token_vendedor_uniq ON crm_relatorio_comissao(token_vendedor);
        CREATE INDEX IF NOT EXISTS rc_loja_status_idx ON crm_relatorio_comissao(loja_id, status);
        """
        try:
            conn = connections[db]
            with conn.cursor() as cursor:
                cursor.execute(sql)
            logger.info('Tabela crm_relatorio_comissao criada em %s', db)
        except Exception as e:
            logger.warning('Erro ao criar tabela crm_relatorio_comissao: %s', e)

    @property
    def pode_aprovar(self):
        return self.status == 'pendente_aprovacao'

    @property
    def pode_reprovar(self):
        return self.status == 'pendente_aprovacao'

    @property
    def pode_vendedor_assinar(self):
        return self.status == 'aprovado'

    @property
    def pode_gerar_boleto(self):
        return self.status == 'aprovado' and not self.asaas_payment_id
