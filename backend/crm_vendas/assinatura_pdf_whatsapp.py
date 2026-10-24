"""Envia o PDF já assinado por WhatsApp, para o cliente e para o vendedor."""
import logging
import re

logger = logging.getLogger(__name__)


def nome_arquivo_pdf_assinado(tipo_doc: str, documento) -> str:
    titulo = (getattr(documento, "titulo", None) or "").strip()
    seguro = re.sub(r"[^\w]+", "_", titulo, flags=re.UNICODE).strip("_")
    base = (tipo_doc or "documento").lower()
    if seguro:
        return f"{base}_{documento.id}_{seguro}_assinado.pdf"
    return f"{base}_{documento.id}_assinado.pdf"


def telefones_pdf_assinado(documento) -> list[str]:
    oportunidade = getattr(documento, "oportunidade", None)
    lead = getattr(oportunidade, "lead", None) if oportunidade else None
    vendedor = getattr(oportunidade, "vendedor", None) if oportunidade else None
    brutos = [
        getattr(lead, "telefone", None),
        getattr(vendedor, "telefone", None),
    ]
    vistos = []
    chaves = set()
    for bruto in brutos:
        texto = (bruto or "").strip()
        chave = re.sub(r"\D", "", texto)
        if len(chave) < 10 or chave in chaves:
            continue
        chaves.add(chave)
        vistos.append(texto)
    return vistos


def enviar_whatsapp_pdf_assinado(documento, loja_id, pdf_bytes: bytes, tipo_doc: str) -> tuple[bool, str | None]:
    """Manda o PDF como documento do WhatsApp. O e-mail segue o caminho dele."""
    from core.public_urls import get_public_api_base_url
    from whatsapp.assinatura_whatsapp import whatsapp_envio_permitido
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp_document
    from whatsapp.sync_context import whatsapp_sync_only

    from .pdf_publico_whatsapp import gravar_pdf_assinado

    telefones = telefones_pdf_assinado(documento)
    if not telefones or not pdf_bytes:
        return False, None

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    is_proposta = tipo_doc == "Proposta"
    ok_cfg, err_cfg = whatsapp_envio_permitido(
        config,
        proposta=is_proposta,
        contrato=not is_proposta,
    )
    if not ok_cfg:
        logger.info(
            "PDF assinado sem WhatsApp: %s#%s %s",
            documento.__class__.__name__,
            getattr(documento, "id", None),
            err_cfg,
        )
        return False, err_cfg

    filename = nome_arquivo_pdf_assinado(tipo_doc, documento)
    token = gravar_pdf_assinado(pdf_bytes, filename)
    pdf_url = f"{get_public_api_base_url()}/api/crm-vendas/documento-assinado/{token}/"
    participio = "assinada" if is_proposta else "assinado"
    titulo = (getattr(documento, "titulo", None) or "").strip()
    caption = f"{tipo_doc} {participio}"
    if titulo:
        caption = f"{caption}: {titulo}"

    enviou = False
    erros = []
    for telefone in telefones:
        marca = whatsapp_sync_only.set(True)
        try:
            ok, err = send_whatsapp_document(
                telefone=telefone,
                document_url=pdf_url,
                filename=filename,
                caption=caption[:1024],
                config=config,
            )
        finally:
            whatsapp_sync_only.reset(marca)
        if ok:
            enviou = True
            logger.info(
                "PDF assinado enviado por WhatsApp: %s#%s arquivo=%s",
                documento.__class__.__name__,
                getattr(documento, "id", None),
                filename,
            )
        else:
            erros.append(err or "falha no envio")
            logger.warning(
                "PDF assinado por WhatsApp falhou: %s#%s erro=%s",
                documento.__class__.__name__,
                getattr(documento, "id", None),
                err,
            )
    return enviou, "; ".join(erros) or None
