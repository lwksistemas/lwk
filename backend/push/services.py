"""
Envio de push notifications via Web Push (VAPID).
"""
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_push(user, title, body, url='/'):
    """
    Envia uma notificação push para todos os dispositivos inscritos do usuário.

    Args:
        user: instância de User
        title: título da notificação
        body: texto da mensagem
        url: URL para abrir ao clicar (path relativo ao frontend, ex: /loja/slug/agenda)
    """
    try:
        from pywebpush import webpush
    except ImportError:
        logger.warning('pywebpush não instalado; push não enviado.')
        return

    vapid_private = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    if not vapid_private:
        logger.warning('VAPID_PRIVATE_KEY não configurada; push não enviado.')
        return

    from .models import PushSubscription
    subs = PushSubscription.objects.filter(user=user)
    payload = json.dumps({'title': title, 'body': body, 'url': url})

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': sub.keys,
                },
                data=payload,
                vapid_private_key=vapid_private,
                vapid_claims={
                    'sub': getattr(settings, 'VAPID_CLAIM_MAILTO', 'mailto:admin@lwksistemas.com.br'),
                },
            )
        except Exception as e:
            logger.warning('Falha ao enviar push para %s: %s', sub.endpoint[:50], e)
            # Opcional: remover inscrição inválida
            # sub.delete()
