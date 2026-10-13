"""Credencial da conta Cora da LWK para boletos de assinatura."""

from django.db import models

from core.encryption import decrypt_value, encrypt_value, is_encrypted


class CoraConfig(models.Model):
    """Certificado e client-id da Integração Direta (conta da LWK)."""

    singleton_key = models.CharField(max_length=10, default="config", unique=True)
    client_id = models.CharField(max_length=80, blank=True)
    certificate_pem = models.TextField(blank=True)
    private_key_pem = models.TextField(blank=True)
    enabled = models.BooleanField(default=False)
    use_for_boletos = models.BooleanField(
        default=False,
        help_text="Se ativo, novas lojas nascem com boleto da Cora.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "superadmin_cora_config"
        verbose_name = "Configuração Cora"

    def __str__(self):
        return "Cora habilitada" if self.enabled else "Cora desabilitada"

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(singleton_key="config", defaults={"enabled": False})
        return obj

    def gravar_segredo(self, campo: str, texto: str) -> None:
        bruto = (texto or "").strip()
        if not bruto:
            return
        setattr(self, campo, bruto if is_encrypted(bruto) else encrypt_value(bruto))

    def certificado(self) -> str:
        return decrypt_value(self.certificate_pem or "")

    def chave_privada(self) -> str:
        return decrypt_value(self.private_key_pem or "")

    @property
    def credencial_pronta(self) -> bool:
        return bool((self.client_id or "").strip() and self.certificate_pem and self.private_key_pem)
