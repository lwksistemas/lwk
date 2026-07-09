"""Service para envio de recibo de pagamento por email ou WhatsApp."""
import logging

logger = logging.getLogger(__name__)


def enviar_recibo_pagamento(payment, *, canal: str) -> tuple[bool, str]:
    """
    Envia recibo de pagamento para o paciente.

    Args:
        payment: instância de Payment
        canal: 'email' ou 'whatsapp'

    Returns:
        (sucesso: bool, mensagem: str)
    """
    appointment = payment.appointment
    if not appointment:
        return False, 'Pagamento sem agendamento vinculado.'

    patient = getattr(appointment, 'patient', None)
    if not patient:
        return False, 'Paciente não encontrado no agendamento.'

    if canal == 'email':
        return _enviar_recibo_email(payment, patient)
    elif canal == 'whatsapp':
        return _enviar_recibo_whatsapp(payment, patient)
    return False, f'Canal desconhecido: {canal}'


def _enviar_recibo_email(payment, patient) -> tuple[bool, str]:
    """Envia recibo por email para o paciente."""
    email = (getattr(patient, 'email', '') or '').strip()
    if not email:
        return False, 'Paciente não possui email cadastrado.'

    try:
        from core.email_delivery import create_email_multipart, send_prepared
        from core.email_sync_context import email_sync_only

        assunto = f'Recibo de Pagamento — R$ {payment.amount:.2f}'
        corpo = _montar_corpo_recibo(payment, patient)

        msg = create_email_multipart(
            subject=assunto,
            body=corpo,
            to=[email],
            html=corpo,
        )
        token = email_sync_only.set(True)
        try:
            send_prepared(msg, fail_silently=False)
        finally:
            email_sync_only.reset(token)

        logger.info('Recibo enviado por email para %s (payment_id=%s)', email, payment.id)
        return True, f'Recibo enviado para {email}'
    except Exception as e:
        logger.warning('Falha ao enviar recibo email payment_id=%s: %s', payment.id, e)
        return False, f'Erro ao enviar email: {e}'


def _enviar_recibo_whatsapp(payment, patient) -> tuple[bool, str]:
    """Envia recibo por WhatsApp para o paciente."""
    telefone = (getattr(patient, 'telefone', '') or '').strip()
    if not telefone:
        return False, 'Paciente não possui telefone cadastrado.'

    try:
        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp

        loja_id = payment.loja_id
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        if not config or not getattr(config, 'whatsapp_ativo', False):
            return False, 'WhatsApp não está ativo. Configure em Configurações → WhatsApp.'

        mensagem = _montar_mensagem_whatsapp(payment, patient)
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if ok:
            logger.info('Recibo enviado por WhatsApp para %s (payment_id=%s)', telefone, payment.id)
            return True, f'Recibo enviado para {telefone}'
        return False, err or 'Erro ao enviar WhatsApp.'
    except Exception as e:
        logger.warning('Falha ao enviar recibo WhatsApp payment_id=%s: %s', payment.id, e)
        return False, f'Erro ao enviar WhatsApp: {e}'


def _montar_corpo_recibo(payment, patient) -> str:
    """Monta HTML do recibo para email."""
    from decimal import Decimal
    nome = getattr(patient, 'nome', 'Cliente')
    valor = Decimal(str(payment.amount or 0))
    metodo = payment.get_payment_method_display() if hasattr(payment, 'get_payment_method_display') else payment.payment_method
    data = payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else '—'

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:400px;margin:0 auto;padding:20px;">
      <h2 style="text-align:center;border-bottom:2px solid #333;padding-bottom:8px;">
        RECIBO DE PAGAMENTO
      </h2>
      <p><strong>Paciente:</strong> {nome}</p>
      <p><strong>Data:</strong> {data}</p>
      <p><strong>Forma de pagamento:</strong> {metodo}</p>
      <p style="font-size:18px;font-weight:bold;border-top:1px dashed #999;padding-top:12px;">
        Valor pago: R$ {valor:.2f}
      </p>
      <p style="text-align:center;font-size:11px;color:#666;margin-top:20px;">
        Documento não fiscal — gerado automaticamente.
      </p>
    </div>
    """


def _montar_mensagem_whatsapp(payment, patient) -> str:
    """Monta texto do recibo para WhatsApp."""
    from decimal import Decimal
    nome = getattr(patient, 'nome', 'Cliente')
    valor = Decimal(str(payment.amount or 0))
    metodo = payment.get_payment_method_display() if hasattr(payment, 'get_payment_method_display') else payment.payment_method
    data = payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else '—'

    return (
        f"*RECIBO DE PAGAMENTO*\n\n"
        f"Paciente: {nome}\n"
        f"Data: {data}\n"
        f"Forma: {metodo}\n"
        f"*Valor pago: R$ {valor:.2f}*\n\n"
        f"Obrigado pela preferência! 🙏"
    )
