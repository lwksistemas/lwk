"""Service para envio de recibo de pagamento por email ou WhatsApp."""
from .email_channel import _enviar_recibo_email
from .whatsapp_channel import _enviar_recibo_whatsapp


def enviar_recibo_pagamento(payment, *, canal: str) -> tuple[bool, str]:
    """Envia recibo de pagamento para o paciente.

    Args:
        payment: instância de Payment (com select_related appointment__patient)
        canal: 'email' ou 'whatsapp'

    Returns:
        (sucesso: bool, mensagem: str)

    """
    appointment = payment.appointment
    if not appointment:
        return False, "Pagamento sem agendamento vinculado."

    patient = getattr(appointment, "patient", None)
    if not patient:
        return False, "Paciente não encontrado no agendamento."

    if canal == "email":
        return _enviar_recibo_email(payment, patient, appointment)
    if canal == "whatsapp":
        return _enviar_recibo_whatsapp(payment, patient, appointment)
    return False, f"Canal desconhecido: {canal}"
