"""Configuração de NFS-e individual por loja (Clínica da Beleza).
Cada loja tem suas próprias credenciais, certificado e dados fiscais.
"""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class ClinicaBelezaNFSeConfig(LojaIsolationMixin, models.Model):
    """Configuração de emissão de NFS-e para clientes da clínica.
    Uma por loja — isolamento automático via LojaIsolationMixin.
    """

    PROVEDOR_NF_CHOICES = [
        ("asaas", "Asaas (Intermediário - Padrão)"),
        ("issnet", "ISSNet - Ribeirão Preto (Direto)"),
        ("nacional", "API Nacional NFS-e (Direto)"),
        ("manual", "Emissão Manual (Sem integração)"),
    ]

    provedor_nf = models.CharField(
        max_length=20,
        choices=PROVEDOR_NF_CHOICES,
        default="asaas",
        verbose_name="Provedor de Nota Fiscal",
        help_text="Sistema usado para emitir notas fiscais de serviço",
    )

    # === Credenciais ISSNet ===
    issnet_usuario = models.CharField(
        max_length=100, blank=True,
        verbose_name="Usuário ISSNet",
    )
    issnet_senha = models.CharField(
        max_length=100, blank=True,
        verbose_name="Senha ISSNet",
    )
    issnet_certificado = models.BinaryField(
        blank=True, null=True,
        verbose_name="Certificado Digital A1 (.pfx)",
    )
    issnet_certificado_nome = models.CharField(
        max_length=255, blank=True,
        verbose_name="Nome do arquivo .pfx",
    )
    issnet_senha_certificado = models.CharField(
        max_length=100, blank=True,
        verbose_name="Senha do Certificado",
    )
    issnet_ambiente_homologacao = models.BooleanField(
        default=False,
        verbose_name="ISSNet homologação (teste)",
    )

    # === Informações do Prestador ===
    inscricao_municipal = models.CharField(
        max_length=20, blank=True,
        verbose_name="Inscrição Municipal",
    )
    codigo_cnae = models.CharField(
        max_length=20, blank=True,
        verbose_name="Código CNAE",
    )
    optante_simples_nacional = models.BooleanField(
        default=True,
        verbose_name="Optante pelo Simples Nacional",
    )
    regime_especial_tributacao = models.CharField(
        max_length=2, blank=True, default="0",
        verbose_name="Regime Especial de Tributação",
    )
    incentivador_cultural = models.BooleanField(
        default=False,
        verbose_name="Incentivador Cultural",
    )
    item_lista_servico = models.CharField(
        max_length=10, blank=True,
        verbose_name="Item da Lista de Serviços (LC 116)",
    )
    codigo_nbs = models.CharField(
        max_length=20, blank=True,
        verbose_name="Código NBS",
    )

    # === RPS / Série ===
    issnet_serie_rps = models.CharField(
        max_length=10, blank=True, default="",
        verbose_name="Série do RPS",
    )
    issnet_ultimo_rps_conhecido = models.IntegerField(
        default=0,
        verbose_name="Último RPS emitido",
    )
    issnet_numero_lote = models.IntegerField(
        default=0,
        verbose_name="Número do Lote",
    )

    # === Dados do Serviço ===
    codigo_servico_municipal = models.CharField(
        max_length=10, default="0601",
        verbose_name="Código do Serviço Municipal",
    )
    descricao_servico_padrao = models.TextField(
        default="Serviços de estética, saúde e bem-estar",
        verbose_name="Descrição Padrão do Serviço",
    )
    aliquota_iss = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00,
        verbose_name="Alíquota ISS (%)",
    )
    emitir_nf_automaticamente = models.BooleanField(
        default=False,
        verbose_name="Emitir NF Automaticamente",
        help_text="Desligado por padrão. Só emite NFS-e ao finalizar consulta se a clínica ativar.",
    )

    # === Asaas da loja (conta própria) ===
    asaas_api_key = models.CharField(
        max_length=255, blank=True,
        verbose_name="API Key Asaas (loja)",
    )
    asaas_sandbox = models.BooleanField(
        default=False,
        verbose_name="Asaas sandbox (homologação)",
    )
    asaas_webhook_token = models.TextField(
        blank=True, default="",
        verbose_name="Token webhook Asaas (loja)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_nfse_config"
        verbose_name = "Configuração NFS-e (Clínica)"
        verbose_name_plural = "Configurações NFS-e (Clínicas)"

    def __str__(self):
        return f"NFS-e Config (loja_id={self.loja_id})"
