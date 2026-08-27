"""Gateway WhatsApp no SuperAdmin: clientes LWK/parceiros, instâncias e chaves."""
from django.db import models

from .loja import Loja


class WhatsappCustomer(models.Model):
    TIPO_LWK = "lwk_loja"
    TIPO_PARCEIRO = "parceiro"
    TIPO_CHOICES = [
        (TIPO_LWK, "Loja LWK"),
        (TIPO_PARCEIRO, "Parceiro (API)"),
    ]

    tipo = models.CharField(max_length=16, choices=TIPO_CHOICES, db_index=True)
    loja = models.OneToOneField(
        Loja,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="whatsapp_customer",
    )
    nome = models.CharField(max_length=200)
    documento = models.CharField(max_length=18, blank=True, default="", db_index=True)
    quota_numeros = models.PositiveSmallIntegerField(default=50)
    webhook_url = models.URLField(max_length=500, blank=True, default="")
    is_active = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "superadmin_whatsapp_customer"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["documento"],
                condition=models.Q(tipo="parceiro") & ~models.Q(documento=""),
                name="uniq_whatsapp_parceiro_documento",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} {self.nome}"


class WhatsappInstance(models.Model):
    STATUS_CONNECTED = "connected"
    STATUS_QR = "qr_pending"
    STATUS_OFF = "disconnected"
    STATUS_CHOICES = [
        (STATUS_CONNECTED, "Conectado"),
        (STATUS_QR, "Aguardando QR"),
        (STATUS_OFF, "Desconectado"),
    ]

    customer = models.ForeignKey(
        WhatsappCustomer,
        on_delete=models.CASCADE,
        related_name="instances",
    )
    instance_name = models.CharField(max_length=80, unique=True)
    rotulo = models.CharField(max_length=80, blank=True, default="")
    telefone = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OFF, db_index=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "superadmin_whatsapp_instance"
        ordering = ["customer_id", "id"]

    def __str__(self) -> str:
        return self.instance_name


class WhatsappApiKey(models.Model):
    customer = models.ForeignKey(
        WhatsappCustomer,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    nome = models.CharField(max_length=80, default="padrão")
    prefixo = models.CharField(max_length=40)
    key_hash = models.CharField(max_length=64, unique=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "superadmin_whatsapp_api_key"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.prefixo}… ({self.customer_id})"
