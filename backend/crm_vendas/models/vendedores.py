from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class Vendedor(LojaIsolationMixin, models.Model):
    """Vendedor da loja (equipe de vendas)."""

    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, default="Vendedor")
    comissao_padrao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Porcentagem de comissão padrão (ex: 5.00 para 5%)",
    )
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    config_acesso = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuração de grupo/permissões (grupo_id, permissoes_ids) para acesso ao CRM",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_vendedor"
        ordering = ["nome"]
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"
        indexes = [
            models.Index(fields=["loja_id", "is_active"], name="crm_vend_loja_active_idx"),
            models.Index(fields=["loja_id", "email"], name="crm_vend_loja_email_idx"),
        ]

    def __str__(self):
        return self.nome

