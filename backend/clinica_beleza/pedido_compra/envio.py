"""Envio de pedido de compra por e-mail e WhatsApp."""
from __future__ import annotations

import logging

from django.conf import settings

from clinica_beleza.models.fornecedores import PedidoCompra
from clinica_beleza.pedido_compra.context import _loja_nome
from clinica_beleza.pedido_compra.errors import PedidoCompraError
from clinica_beleza.pedido_compra.formatters import _brl, _fmt_numero, nome_arquivo_pdf_pedido
from clinica_beleza.pedido_compra.service import clinica_assinou, finalizar_se_completo, pdf_bytes_pedido

logger = logging.getLogger(__name__)


def enviar_pedido_assinado(pedido: PedidoCompra, canais: list[str]) -> dict:
    if pedido.status == PedidoCompra.STATUS_CANCELADO:
        raise PedidoCompraError("Pedido cancelado.")
    if pedido.status == PedidoCompra.STATUS_RASCUNHO or not clinica_assinou(pedido):
        raise PedidoCompraError("Assine o pedido pela clínica antes de enviar ao fornecedor.")
    canais = [c for c in (canais or []) if c in ("email", "whatsapp")]
    if not canais:
        raise PedidoCompraError("Informe o canal: email ou whatsapp.")
    pdf = pdf_bytes_pedido(pedido)
    finalizar_se_completo(pedido)
    resultado: dict = {}
    if "email" in canais:
        resultado["email"] = _enviar_pdf_email(pedido, pdf)
    if "whatsapp" in canais:
        resultado["whatsapp"] = _enviar_pdf_whatsapp(pedido, pdf)
    if any(r.get("sucesso") for r in resultado.values()):
        pedido.status = PedidoCompra.STATUS_ENVIADO
        pedido.save(update_fields=["status", "updated_at"])
    return resultado


def _enviar_pdf_email(pedido: PedidoCompra, pdf_bytes: bytes) -> dict:
    email = (pedido.fornecedor.email or "").strip()
    if not email:
        return {"sucesso": False, "erro": "Fornecedor sem e-mail cadastrado."}
    try:
        from core.assinatura_service import _render_email_html
        from core.email_delivery import create_email_multipart, send_prepared

        clinica = _loja_nome(pedido.loja_id)
        forn = pedido.fornecedor
        numero = _fmt_numero(pedido.numero)
        total = _brl(pedido.valor_total)
        qtd_itens = pedido.itens.count()
        destinatario = (forn.nome_fantasia or forn.razao_social or "fornecedor").strip()
        corpo_txt = (
            f"Prezado(a) {destinatario},\n\n"
            f"Encaminhamos o pedido de compra nº {numero} da {clinica}, "
            f"já assinado pelo profissional responsável, para processamento.\n\n"
            f"Itens: {qtd_itens}\n"
            f"Valor total: {total}\n\n"
            f"A foto do pedido está no corpo deste e-mail.\n\n"
            f"Atenciosamente,\n{clinica}"
        )
        jpeg_bytes = _jpeg_do_pdf(pdf_bytes)
        foto_html = ""
        if jpeg_bytes:
            foto_html = (
                '<p style="text-align:center;margin:0 0 16px;">'
                '<img src="cid:pedido" alt="Pedido de compra" style="max-width:100%;height:auto;" />'
                "</p>"
            )
        corpo_html = f"""
<p style="color:#333;font-size:16px;line-height:1.6;margin:0 0 16px;">Prezado(a) <strong>{destinatario}</strong>,</p>
<p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 24px;">
A <strong>{clinica}</strong> encaminha o pedido de compra nº <strong>{numero}</strong>,
já assinado pelo profissional responsável, para processamento junto à sua empresa.
</p>
<table width="100%" style="background:#f8f9fa;border-left:4px solid #8B3D52;border-radius:4px;margin-bottom:24px;"><tr><td style="padding:20px;">
<p style="margin:0 0 8px;color:#666;font-size:13px;">Pedido de compra</p>
<p style="margin:0 0 12px;color:#333;font-size:22px;font-weight:700;">nº {numero}</p>
<p style="margin:0 0 4px;color:#666;font-size:13px;">{qtd_itens} {"item" if qtd_itens == 1 else "itens"}</p>
<p style="margin:0;color:#8B3D52;font-size:20px;font-weight:700;">{total}</p>
</td></tr></table>
{foto_html}
<p style="color:#555;font-size:14px;line-height:1.6;margin:0 0 8px;">A foto do pedido está acima.</p>
<p style="color:#888;font-size:13px;margin:0;">Em caso de dúvidas, responda a este e-mail ou entre em contato com a clínica.</p>
"""
        html = _render_email_html("Pedido de compra", "#8B3D52 0%, #6B2E3F 100%", corpo_html, clinica)
        msg = create_email_multipart(
            subject=f"Pedido de compra nº {numero} — {clinica}",
            body=corpo_txt,
            to=[email],
            html=html,
        )
        if jpeg_bytes:
            from core.email_delivery import attach_inline_jpeg

            attach_inline_jpeg(msg, jpeg_bytes, cid="pedido", filename=f"pedido_{numero}.jpg")
        else:
            msg.attach(nome_arquivo_pdf_pedido(pedido), pdf_bytes, "application/pdf")
        send_prepared(msg, fail_silently=False)
        return {"sucesso": True}
    except Exception as exc:
        logger.warning("Falha e-mail PDF pedido #%s: %s", pedido.numero, exc)
        return {"sucesso": False, "erro": str(exc)}


def _enviar_pdf_whatsapp(pedido: PedidoCompra, pdf_bytes: bytes) -> dict:
    telefone = (pedido.fornecedor.telefone or "").strip()
    if not telefone:
        return {"sucesso": False, "erro": "Fornecedor sem telefone cadastrado."}
    try:
        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import (
            _send_whatsapp_document_evolution,
            _send_whatsapp_image_evolution,
            send_whatsapp,
        )

        config = WhatsAppConfig.objects.filter(loja_id=pedido.loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return {"sucesso": False, "erro": "WhatsApp não está ativo. Configure em Configurações → WhatsApp."}
        clinica = _loja_nome(pedido.loja_id)
        numero = _fmt_numero(pedido.numero)
        mensagem = (
            f"{clinica} encaminha o pedido de compra nº {numero}, "
            f"assinado pelo profissional responsável. A foto segue nesta conversa."
        )
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if not ok:
            return {"sucesso": False, "erro": err or "Erro ao enviar WhatsApp."}
        from clinica_beleza.public_pdf import PREFIX_PEDIDO, gravar_pdf_publico

        jpeg_bytes = _jpeg_do_pdf(pdf_bytes)
        payload = {"pedido_id": pedido.id, "pdf": pdf_bytes}
        if jpeg_bytes:
            payload["imagem"] = jpeg_bytes
        token = gravar_pdf_publico(PREFIX_PEDIDO, payload)
        api_base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
        try:
            if jpeg_bytes:
                img_url = f"{api_base}/api/clinica-beleza/estoque/pedidos/{pedido.id}/img-public/{token}/"
                ok_img, err_img = _send_whatsapp_image_evolution(
                    telefone, img_url, f"pedido_{numero}.jpg",
                    caption=f"Pedido de compra nº {numero} — {clinica}", config=config,
                )
                if not ok_img:
                    logger.warning("Foto do pedido via WhatsApp falhou, tentando PDF: %s", err_img)
                    pdf_url = f"{api_base}/api/clinica-beleza/estoque/pedidos/{pedido.id}/pdf-public/{token}/"
                    _send_whatsapp_document_evolution(
                        telefone, pdf_url, nome_arquivo_pdf_pedido(pedido),
                        caption=f"Pedido de compra nº {numero} — {clinica}", config=config,
                    )
            else:
                pdf_url = f"{api_base}/api/clinica-beleza/estoque/pedidos/{pedido.id}/pdf-public/{token}/"
                _send_whatsapp_document_evolution(
                    telefone, pdf_url, nome_arquivo_pdf_pedido(pedido),
                    caption=f"Pedido de compra nº {numero} — {clinica}", config=config,
                )
        except Exception as pdf_err:
            logger.warning("PDF pedido via WhatsApp falhou (texto já enviado): %s", pdf_err)
        return {"sucesso": True}
    except Exception as exc:
        logger.warning("Falha WhatsApp PDF pedido #%s: %s", pedido.numero, exc)
        return {"sucesso": False, "erro": str(exc)}


def pdf_publico_cache(pedido_id: int, token: str) -> bytes | None:
    from clinica_beleza.public_pdf import PREFIX_PEDIDO, ler_pdf_publico

    cached = ler_pdf_publico(PREFIX_PEDIDO, token) or {}
    if cached.get("pedido_id") != pedido_id:
        return None
    return cached.get("pdf")


def _jpeg_do_pdf(pdf_bytes: bytes) -> bytes | None:
    try:
        from clinica_beleza.recibo.imagem import pdf_para_jpeg

        return pdf_para_jpeg(pdf_bytes)
    except Exception as exc:
        logger.warning("Conversão do pedido em foto falhou: %s", exc)
        return None


def imagem_publica_cache(pedido_id: int, token: str) -> bytes | None:
    from clinica_beleza.public_pdf import PREFIX_PEDIDO, ler_pdf_publico

    cached = ler_pdf_publico(PREFIX_PEDIDO, token) or {}
    if cached.get("pedido_id") != pedido_id:
        return None
    return cached.get("imagem")
