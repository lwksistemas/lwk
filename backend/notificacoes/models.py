from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Notification(models.Model):
    CANAL_CHOICES = (
        ('in_app', 'In App'),
        ('push', 'Push'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
    )

    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('enviado', 'Enviado'),
        ('falhou', 'Falhou'),
        ('lido', 'Lido'),
    )

    TIPO_CHOICES = (
        ('agendamento', 'Agendamento'),
        ('cancelamento', 'Cancelamento'),
        ('lembrete', 'Lembrete'),
        ('financeiro', 'Financeiro'),
        ('tarefa', 'Tarefa'),
        ('sistema', 'Sistema'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    titulo = models.CharField(max_length=120)
    mensagem = models.TextField()
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES, default='in_app')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'

    def __str__(self):
        return f"{self.titulo} - {self.user}"
