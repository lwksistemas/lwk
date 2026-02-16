"""
Helper para criar notificações a partir do código (ex.: ao criar agendamento).
"""
from django.utils.timezone import now

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

    Exemplo:
        from notificacoes.services import notify
        notify(
            user=agendamento.profissional.user,
            titulo='Novo atendimento',
            mensagem='Você tem um novo atendimento hoje.',
            tipo='agendamento',
        )
    """
    return Notification.objects.create(
        user=user,
        titulo=titulo,
        mensagem=mensagem,
        tipo=tipo,
        canal=canal,
        metadata=metadata,
    )
