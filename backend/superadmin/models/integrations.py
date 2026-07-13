"""Modelos Super Admin."""

from django.db import models

from .loja import Loja


class GoogleCalendarConnection(models.Model):
    """
    Conexão OAuth com Google Calendar por loja (CRM Vendas).
    Armazenado no banco default para que o callback OAuth (sem tenant na URL) possa salvar.
    vendedor_id=None = conexão do proprietário; vendedor_id preenchido = conexão do vendedor.
    """
    loja = models.ForeignKey(
        Loja, on_delete=models.CASCADE, related_name='google_calendar_connections',
        db_column='loja_id',
    )
    vendedor_id = models.IntegerField(null=True, blank=True, db_index=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    calendar_id = models.CharField(max_length=255, default='primary')
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'superadmin_google_calendar_connection'
        verbose_name = 'Conexão Google Calendar (CRM)'
        verbose_name_plural = 'Conexões Google Calendar (CRM)'
        constraints = [
            models.UniqueConstraint(
                fields=['loja'],
                condition=models.Q(vendedor_id__isnull=True),
                name='gcal_loja_owner_uniq',
            ),
            models.UniqueConstraint(
                fields=['loja', 'vendedor_id'],
                condition=models.Q(vendedor_id__isnull=False),
                name='gcal_loja_vendedor_uniq',
            ),
        ]


