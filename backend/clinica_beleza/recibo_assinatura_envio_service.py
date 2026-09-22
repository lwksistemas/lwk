"""Envio de recibo para assinatura digital e do PDF assinado (email/WhatsApp)."""
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
    """Envia o recibo já assinado por email (PDF anexado) e WhatsApp (documento).

    Chamado quando a assinatura conclui. Não levanta — registra a falha no log.
    """
    try:
        from core.assinatura_service import enviar_pdf_final

        enviar_pdf_final(adapter, payment, loja_id)
    except Exception:
        logger.exception(
            "Falha ao enviar recibo assinado por e-mail (payment %s)",
            getattr(payment, "id", None),
        )

    try:
        _enviar_recibo_assinado_whatsapp(payment=payment, adapter=adapter, loja_id=loja_id, user=user)
    except Exception:
        logger.exception(
            "Falha ao enviar recibo assinado por WhatsApp (payment %s)",
            getattr(payment, "id", None),
        )


def _enviar_recibo_assinado_whatsapp(*, payment, adapter, loja_id: int, user=None) -> tuple[bool, str]:
    """Envia o PDF do recibo assinado via WhatsApp (usa URL pública, igual ao recibo)."""
    from django.conf import settings

    from clinica_beleza.public_pdf import PREFIX_RECIBO, gravar_pdf_publico
    from whatsapp.assinatura_whatsapp import whatsapp_envio_permitido
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp, send_whatsapp_document

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    ok_cfg, err_cfg = whatsapp_envio_permitido(config, termo=True)
    if not ok_cfg:
        return False, err_cfg or "WhatsApp indisponível."

    telefone = adapter.get_telefone_parte1(payment)
    if not telefone:
        return False, "Paciente não possui telefone cadastrado."

    nome_paciente, _ = adapter.get_destinatario_parte1(payment)
    mensagem = (
        f"Olá {nome_paciente or 'cliente'}! Segue o PDF do recibo assinado "
        f"({adapter.get_titulo(payment)})."
    )
    ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config, user=user)
    if not ok:
        return False, err or "Erro ao enviar WhatsApp."

    pdf_buffer = adapter.gerar_pdf(payment, incluir_assinaturas=True)
    pdf_bytes = pdf_buffer.getvalue() if hasattr(pdf_buffer, "getvalue") else bytes(pdf_buffer)
    if not pdf_bytes:
        return False, "Não foi possível gerar o PDF do recibo assinado."

    token = gravar_pdf_publico(PREFIX_RECIBO, {"payment_id": payment.id, "pdf": pdf_bytes})
    api_base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
    pdf_url = f"{api_base}/api/clinica-beleza/payments/{payment.id}/recibo-pdf/{token}/"

    ok_doc, err_doc = send_whatsapp_document(
        telefone=telefone,
        document_url=pdf_url,
        filename=f"recibo_{payment.id}_assinado.pdf",
        caption="Recibo Assinado",
        config=config,
        user=user,
    )
    if not ok_doc:
        logger.warning("PDF do recibo assinado via WhatsApp falhou payment=%s: %s", payment.id, err_doc)
        return False, err_doc or "Erro ao enviar o documento."
    return True, f"Recibo assinado enviado por WhatsApp para {telefone}"
