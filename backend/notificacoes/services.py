"""
Helper para criar notificações a partir do código (ex.: ao criar agendamento).
Quando canal='push', também envia push real via push.services.send_push.
"""
from .models import Notification


def notify(
    *,
    user,
    titulo,
    mensagem,
    tipo,
    canal='in_app',
    metadata=None,
):
    """
    Cria uma notificação para o usuário.
    Se canal='push', envia também a notificação push (dispositivo/celular).

    Exemplo:
        from notificacoes.services import notify
        notify(
            user=agendamento.profissional.user,
            titulo='Novo atendimento',
            mensagem='Você tem um novo atendimento hoje.',
            tipo='agendamento',
            canal='push',
            metadata={'url': '/loja/minha-loja/agenda'},
        )
    """
    notif = Notification.objects.create(
        user=user,
        titulo=titulo,
        mensagem=mensagem,
        tipo=tipo,
        canal=canal,
        metadata=metadata or {},
    )
    if canal == 'push':
        try:
            from push.services import send_push
            url = (metadata or {}).get('url') or '/'
            send_push(user=user, title=titulo, body=mensagem, url=url)
        except Exception:
            pass  # Push é best-effort; não falha a notificação in-app
    if canal == 'whatsapp':
        try:
            telefone = (metadata or {}).get('telefone')
            if telefone:
                from whatsapp.services import send_whatsapp
                send_whatsapp(telefone=telefone, mensagem=mensagem, user=user)
        except Exception:
            pass  # WhatsApp é best-effort; não falha a notificação in-app
    return notif
