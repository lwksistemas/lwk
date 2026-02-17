"""
Modelos para WhatsApp (ETAPA 4): auditoria e configuração por loja.
"""
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class WhatsAppConfig(models.Model):
    """
    Configuração de envio WhatsApp por loja (respeitado pelo motor de regras).
    LGPD: opt-out por paciente é campo allow_whatsapp no Patient (clinica_beleza).
    """
    loja = models.OneToOneField(
        'superadmin.Loja',
        on_delete=models.CASCADE,
        related_name='whatsapp_config',
    )
    enviar_confirmacao = models.BooleanField(default=True, verbose_name='Enviar confirmação de agendamento')
    enviar_lembrete_24h = models.BooleanField(default=True, verbose_name='Enviar lembrete 24h antes')
    enviar_lembrete_2h = models.BooleanField(default=True, verbose_name='Enviar lembrete 2h antes')
    enviar_cobranca = models.BooleanField(default=True, verbose_name='Enviar cobrança financeiro')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'whatsapp'
        verbose_name = 'Configuração WhatsApp'
        verbose_name_plural = 'Configurações WhatsApp'

    def __str__(self):
        return f"WhatsApp config - {self.loja.nome}"


class WhatsAppLog(models.Model):
    """Log de cada mensagem enviada via WhatsApp (LGPD / auditoria)."""
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('falhou', 'Falhou'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_logs',
    )
    telefone = models.CharField(max_length=20)
    mensagem = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'whatsapp'
        ordering = ['-created_at']
        verbose_name = 'Log WhatsApp'
        verbose_name_plural = 'Logs WhatsApp'

    def __str__(self):
        return f"{self.telefone} - {self.status} - {self.created_at}"
