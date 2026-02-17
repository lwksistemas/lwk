"""
Regras de notificação: avisar profissional, paciente (in-app / push / WhatsApp).
"""
from notificacoes.services import notify


def _user_do_profissional(professional):
    """Obtém o User vinculado ao Professional (ProfissionalUsuario), se existir."""
    from tenants.middleware import get_current_loja_id

    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    try:
        from superadmin.models import ProfissionalUsuario

        pu = (
            ProfissionalUsuario.objects.using("default")
            .filter(loja_id=loja_id, professional_id=professional.id)
            .select_related("user")
            .first()
        )
        return pu.user if pu else None
    except Exception:
        return None


def notificar_profissional_novo_agendamento(contexto):
    """
    Ao criar agendamento, notifica o profissional (in-app + push se tiver dispositivo).
    contexto: profissional, appointment (opcional, para link)
    """
    profissional = contexto.get("profissional")
    appointment = contexto.get("appointment")
    if not profissional:
        return

    user = _user_do_profissional(profissional)
    if not user:
        return

    titulo = "Novo agendamento"
    mensagem = "Você tem um novo agendamento na agenda."
    if appointment:
        data_str = appointment.date.strftime("%d/%m/%Y %H:%M") if hasattr(appointment.date, "strftime") else ""
        mensagem = f"Novo agendamento para {data_str}."

    try:
        notify(
            user=user,
            titulo=titulo,
            mensagem=mensagem,
            tipo="agendamento",
            canal="in_app",
            metadata={"url": "/agenda"},
        )
        notify(
            user=user,
            titulo=titulo,
            mensagem=mensagem,
            tipo="agendamento",
            canal="push",
            metadata={"url": "/agenda"},
        )
    except Exception:
        pass  # Notificação é best-effort; não falha o agendamento


regras_notificacao = [
    {
        "evento": "AGENDAMENTO_CRIADO",
        "acao": notificar_profissional_novo_agendamento,
        "ativa": True,
    },
]
