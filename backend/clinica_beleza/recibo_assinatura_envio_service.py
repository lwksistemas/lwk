"""Envio de recibo para assinatura digital e da foto do recibo assinado (email/WhatsApp)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

CANAIS_ENVIO_VALIDOS = ("email", "whatsapp")


def normalizar_canal_envio(canal: str | None) -> str | None:
    valor = (canal or "email").strip().lower()
    return valor if valor in CANAIS_ENVIO_VALIDOS else None


def enviar_recibo_para_assinatura(*, payment, adapter, loja_id: int, canal: str, request) -> tuple[bool, str]:
    """Cria a assinatura pendente e envia o link para o paciente por email ou WhatsApp.

    Retorna (sucesso, mensagem).
    """
    from core.assinatura_service import criar_assinatura, enviar_email_parte1
    from whatsapp.assinatura_whatsapp import enviar_whatsapp_link_assinatura

    if canal == "whatsapp":
        telefone = adapter.get_telefone_parte1(payment)
        if not telefone:
            return False, "Paciente não possui telefone cadastrado."
    else:
        _, email = adapter.get_destinatario_parte1(payment)
        if not email:
            return False, "Paciente não possui e-mail cadastrado."

    # Remove pendências antigas e cria uma nova assinatura para o paciente.
    adapter.deletar_assinaturas_pendentes(payment, "paciente")
    assinatura = criar_assinatura(adapter, payment, "paciente", loja_id)
    adapter.atualizar_status_assinatura(payment, "aguardando_paciente")

    if canal == "whatsapp":
        ok, err = enviar_whatsapp_link_assinatura(
            adapter, payment, assinatura, loja_id,
            telefone=adapter.get_telefone_parte1(payment),
            user=getattr(request, "user", None),
        )
    else:
        ok, err = enviar_email_parte1(adapter, payment, assinatura, loja_id)
        err = err or "erro no e-mail"

    if ok:
        return True, "Recibo enviado para assinatura."

    adapter.atualizar_status_assinatura(payment, "rascunho")
    assinatura.delete()
    return False, err or "Falha ao enviar o recibo para assinatura."


def enviar_recibo_assinado(*, payment, adapter, loja_id: int, user=None) -> None:
    """Envia só a foto do recibo assinado, sem repetir o resumo do atendimento.

    A assinatura já está gravada, então a foto inclui a seção de assinatura digital.
    Chamado quando a assinatura conclui. Não levanta — registra a falha no log.
    """
    appointment = adapter._appointment(payment)
    patient = adapter._patient(payment)
    if patient is None or appointment is None:
        logger.warning(
            "Recibo assinado sem paciente (payment %s, loja %s)",
            getattr(payment, "id", None),
            loja_id,
        )
        return

    try:
        from clinica_beleza.recibo.email_channel import _enviar_recibo_email

        ok, err = _enviar_recibo_email(payment, patient, appointment, somente_foto=True)
        if not ok:
            logger.warning(
                "Recibo assinado por e-mail não enviado (payment %s): %s",
                getattr(payment, "id", None),
                err,
            )
    except Exception:
        logger.exception(
            "Falha ao enviar recibo assinado por e-mail (payment %s)",
            getattr(payment, "id", None),
        )

    try:
        from clinica_beleza.recibo.whatsapp_channel import _enviar_recibo_whatsapp

        ok, err = _enviar_recibo_whatsapp(payment, patient, appointment, somente_foto=True)
        if not ok:
            logger.warning(
                "Recibo assinado por WhatsApp não enviado (payment %s, user=%s): %s",
                getattr(payment, "id", None),
                getattr(user, "id", None),
                err,
            )
    except Exception:
        logger.exception(
            "Falha ao enviar recibo assinado por WhatsApp (payment %s)",
            getattr(payment, "id", None),
        )
