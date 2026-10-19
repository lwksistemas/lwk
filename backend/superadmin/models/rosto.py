"""Credencial de rosto do aparelho (WebAuthn). Não guarda foto nem biometria."""

from django.contrib.auth.models import User
from django.db import models


class CredencialRosto(models.Model):
    """Chave pública do Face ID ou do desbloqueio facial deste aparelho."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="credenciais_rosto")
    escopo = models.CharField(max_length=80)
    credential_id = models.CharField(max_length=512, unique=True)
    public_key = models.TextField()
    sign_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "superadmin_credencial_rosto"
        indexes = [
            models.Index(fields=["user", "escopo"], name="rosto_user_escopo_idx"),
        ]

    def __str__(self):
        return f"rosto:{self.user_id}:{self.escopo}"
