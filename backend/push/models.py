from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class PushSubscription(models.Model):
    """Inscrição de um usuário para receber push notifications (VAPID)."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
    )
    endpoint = models.TextField()
    keys = models.JSONField(help_text='p256dh e auth')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inscrição Push'
        verbose_name_plural = 'Inscrições Push'

    def __str__(self):
        return f"Push {self.user_id} - {self.endpoint[:50]}..."
