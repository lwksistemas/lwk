"""Modelos Super Admin."""

from django.contrib.auth.models import User
from django.db import models


class AuditLog(models.Model):
    """Audit log para ações sensíveis do sistema.
    Registra emissão/cancelamento de NFS-e, acesso a certificados,
    alterações de configuração, etc.
    """

    ACAO_CHOICES = [
        ("nfse_emitir_manual", "Emissão manual de NFS-e"),
        ("nfse_emitir_auto", "Emissão automática de NFS-e"),
        ("nfse_cancelar", "Cancelamento de NFS-e"),
        ("nfse_reenviar", "Reenvio de NFS-e por email"),
        ("config_certificado_upload", "Upload de certificado digital"),
        ("config_certificado_acesso", "Acesso a certificado digital"),
        ("config_alterar", "Alteração de configuração sensível"),
        ("config_issnet_test", "Teste de conexão ISSNet"),
        ("login_superadmin", "Login no superadmin"),
        ("outro", "Outra ação"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_logs",
    )
    usuario_email = models.CharField(max_length=200, blank=True)
    usuario_nome = models.CharField(max_length=200, blank=True)

    acao = models.CharField(max_length=50, choices=ACAO_CHOICES, db_index=True)
    descricao = models.CharField(max_length=500, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    sucesso = models.BooleanField(default=True)

    # Detalhes extras (JSON)
    detalhes = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "superadmin_audit_log"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["acao", "-created_at"], name="audit_acao_created_idx"),
            models.Index(fields=["user", "-created_at"], name="audit_user_created_idx"),
        ]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.acao} - {self.usuario_email}"
