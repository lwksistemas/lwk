from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class AssinaturaDigital(LojaIsolationMixin, models.Model):
    """Registro de assinatura digital para Propostas e Contratos.
    Armazena dados de assinatura: IP, timestamp, token único.
    """

    TIPO_CHOICES = [
        ("cliente", "Cliente"),
        ("vendedor", "Vendedor"),
    ]

    # Relacionamento direto (proposta OU contrato)
    # Usar ForeignKey direto ao invés de GenericForeignKey para evitar problemas cross-database
    proposta = models.ForeignKey(
        "Proposta",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assinaturas",
        help_text="Proposta sendo assinada",
    )
    contrato = models.ForeignKey(
        "Contrato",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assinaturas",
        help_text="Contrato sendo assinado",
    )

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, help_text="Tipo de assinante")
    nome_assinante = models.CharField(max_length=200, help_text="Nome completo do assinante")
    email_assinante = models.EmailField(help_text="Email do assinante")

    # Dados de segurança da assinatura
    ip_address = models.GenericIPAddressField(help_text="Endereço IP do assinante")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Data/hora de criação do token")
    user_agent = models.TextField(blank=True, help_text="User agent do navegador")

    # Token único para esta assinatura
    token = models.CharField(max_length=255, unique=True, db_index=True, help_text="Token único de assinatura")
    token_expira_em = models.DateTimeField(help_text="Data/hora de expiração do token")

    # Status da assinatura
    assinado = models.BooleanField(default=False, help_text="Se o documento foi assinado")
    assinado_em = models.DateTimeField(null=True, blank=True, help_text="Data/hora da assinatura")
    link_enviado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando o link de assinatura foi enviado ao assinante (e-mail/WhatsApp)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_assinatura_digital"
        ordering = ["-created_at"]
        verbose_name = "Assinatura Digital"
        verbose_name_plural = "Assinaturas Digitais"
        indexes = [
            models.Index(fields=["loja_id", "token"], name="crm_assin_loja_token_idx"),
            models.Index(fields=["loja_id", "tipo", "assinado"], name="crm_assin_loja_tipo_idx"),
            models.Index(fields=["proposta"], name="crm_assin_proposta_idx"),
            models.Index(fields=["contrato"], name="crm_assin_contrato_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(proposta__isnull=False, contrato__isnull=True) |
                    models.Q(proposta__isnull=True, contrato__isnull=False)
                ),
                name="crm_assin_proposta_ou_contrato",
            ),
        ]

    def __str__(self):
        status = "Assinado" if self.assinado else "Pendente"
        return f"{self.get_tipo_display()} - {self.nome_assinante} ({status})"

    @property
    def documento(self):
        """Retorna o documento (proposta ou contrato) para compatibilidade."""
        return self.proposta or self.contrato

    def is_expirado(self):
        """Verifica se o token está expirado."""
        from django.utils import timezone
        return timezone.now() > self.token_expira_em

