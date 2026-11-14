"""NFC-e da venda de produto. O recibo de pagamento continua separado."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class NfceConfig(LojaIsolationMixin, models.Model):
    """Liga o cupom fiscal quando a clínica informa regime, CSC e inscrição estadual."""

    REGIME_SIMPLES = "simples"
    REGIME_NORMAL = "normal"
    REGIME_CHOICES = (
        (REGIME_SIMPLES, "Simples Nacional"),
        (REGIME_NORMAL, "Regime normal"),
    )

    habilitada = models.BooleanField(default=False, verbose_name="Emitir NFC-e nas vendas de produto")
    regime = models.CharField(max_length=12, choices=REGIME_CHOICES, blank=True, default="")
    id_csc = models.CharField(max_length=6, blank=True, default="", verbose_name="ID do CSC")
    csc = models.CharField(max_length=500, blank=True, default="", verbose_name="CSC")
    inscricao_estadual = models.CharField(max_length=20, blank=True, default="")
    serie = models.PositiveSmallIntegerField(default=1)
    proximo_numero = models.PositiveIntegerField(default=1)
    proximo_numero_teste = models.PositiveIntegerField(default=1)
    ambiente_homologacao = models.BooleanField(
        default=True,
        verbose_name="Homologação",
        help_text="Ligado envia cupom de teste. Desligado envia NFC-e com valor fiscal.",
    )
    ncm_padrao = models.CharField(max_length=8, blank=True, default="")
    codigo_municipio = models.CharField(max_length=7, blank=True, default="", verbose_name="Código IBGE")
    aliquota_icms = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Configuração de NFC-e"
        constraints = [
            models.UniqueConstraint(fields=["loja_id"], name="cb_nfce_config_loja"),
        ]


class NfceCupom(LojaIsolationMixin, models.Model):
    """Uma NFC-e por venda de balcão. O número não volta atrás depois de reservado."""

    STATUS_PENDENTE = "pendente"
    STATUS_AUTORIZADA = "autorizada"
    STATUS_REJEITADA = "rejeitada"
    STATUS_CANCELADA = "cancelada"
    STATUS_CHOICES = (
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_AUTORIZADA, "Autorizada"),
        (STATUS_REJEITADA, "Rejeitada"),
        (STATUS_CANCELADA, "Cancelada"),
    )

    venda = models.OneToOneField(
        "clinica_beleza.VendaBalcao",
        on_delete=models.PROTECT,
        related_name="cupom_nfce",
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    numero = models.PositiveIntegerField()
    serie = models.PositiveSmallIntegerField(default=1)
    homologacao = models.BooleanField(default=True)
    chave = models.CharField(max_length=44, blank=True, default="")
    protocolo = models.CharField(max_length=20, blank=True, default="")
    qrcode = models.TextField(blank=True, default="")
    xml = models.TextField(blank=True, default="")
    motivo = models.TextField(blank=True, default="")
    emitida_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Cupom fiscal"
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "serie", "numero", "homologacao"],
                name="cb_nfce_cupom_numero",
            ),
        ]
