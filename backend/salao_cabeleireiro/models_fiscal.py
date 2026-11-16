"""Nota de serviço e cupom de produto do salão. Cada loja grava o próprio certificado."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class SalaoNFSeConfig(LojaIsolationMixin, models.Model):
    """Configuração da NFS-e dos serviços deste salão."""

    PROVEDOR_NF_CHOICES = [
        ("asaas", "Asaas (conta da sua loja)"),
        ("issnet", "ISSNet — Padrão Nacional (DPS / RTC)"),
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
        max_length=500, blank=True,
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
        max_length=500, blank=True,
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
        max_length=10, default="0602",
        verbose_name="Código do Serviço Municipal",
    )
    descricao_servico_padrao = models.TextField(
        default="Serviços de cabeleireiro",
        verbose_name="Descrição Padrão do Serviço",
    )
    aliquota_iss = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00,
        verbose_name="Alíquota ISS (%)",
    )
    emitir_nf_automaticamente = models.BooleanField(
        default=False,
        verbose_name="Emitir NF Automaticamente",
        help_text="Desligado por padrão. O salão só emite a nota de serviço quando esta opção está ligada.",
    )

    # === Padrão Nacional ISSNet (RTC/DPS) ===
    issnet_usar_padrao_nacional = models.BooleanField(
        default=True,
        verbose_name="Usar padrão Nacional (DPS/RTC)",
        help_text="Se True, emite via webservice Nacional ISSNet (DPS/RTC).",
    )
    codigo_tributacao_nacional = models.CharField(
        max_length=10,
        blank=True,
        default="",
        verbose_name="Código de Tributação Nacional (cTribNac)",
    )
    codigo_tributacao_municipal = models.CharField(
        max_length=10,
        blank=True,
        default="",
        verbose_name="Código de Tributação Municipal (cTribMun)",
    )
    nacional_codigo_municipio = models.CharField(
        max_length=7,
        blank=True,
        default="",
        verbose_name="Código IBGE do município (API Nacional)",
    )
    indicador_operacao = models.CharField(
        max_length=2,
        blank=True,
        default="",
        verbose_name="Indicador da Operação (IBS/CBS)",
    )
    cst_ibscbs = models.CharField(
        max_length=3,
        blank=True,
        default="",
        verbose_name="Situação Tributária IBS/CBS (CST)",
    )
    cclass_trib_ibscbs = models.CharField(
        max_length=6,
        blank=True,
        default="",
        verbose_name="Classificação Tributária IBS/CBS (cClassTrib)",
    )
    p_tot_trib_sn = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="% Total de Tributos (Simples Nacional)",
    )

    # === Asaas da loja (conta própria) ===
    asaas_api_key = models.TextField(
        blank=True,
        default="",
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
        db_table = "salao_nfse_config"
        verbose_name = "Configuração NFS-e (Salão)"
        verbose_name_plural = "Configurações NFS-e (Salões)"
        constraints = [
            models.UniqueConstraint(fields=["loja_id"], name="salao_nfse_config_loja"),
        ]

    def __str__(self):
        return f"NFS-e Config (loja_id={self.loja_id})"


class SalaoNfceConfig(LojaIsolationMixin, models.Model):
    """Liga o cupom fiscal de produto quando o salão informa regime, CSC e inscrição estadual."""

    REGIME_CHOICES = (
        ("simples", "Simples Nacional"),
        ("normal", "Regime normal"),
    )

    habilitada = models.BooleanField(default=False, verbose_name="Emitir NFC-e nas vendas de produto")
    regime = models.CharField(max_length=12, choices=REGIME_CHOICES, blank=True, default="")
    id_csc = models.CharField(max_length=6, blank=True, default="", verbose_name="ID do CSC")
    csc = models.CharField(max_length=500, blank=True, default="")
    inscricao_estadual = models.CharField(max_length=20, blank=True, default="")
    serie = models.PositiveSmallIntegerField(default=1)
    proximo_numero = models.PositiveIntegerField(default=1)
    proximo_numero_teste = models.PositiveIntegerField(default=1)
    ambiente_homologacao = models.BooleanField(default=True, verbose_name="Homologação")
    ncm_padrao = models.CharField(max_length=8, blank=True, default="")
    codigo_municipio = models.CharField(max_length=7, blank=True, default="")
    aliquota_icms = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = LojaIsolationManager()

    class Meta:
        db_table = "salao_nfce_config"
        verbose_name = "Configuração NFC-e (Salão)"
        constraints = [
            models.UniqueConstraint(fields=["loja_id"], name="salao_nfce_config_loja"),
        ]
