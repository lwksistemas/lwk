"""Envio de recibo por WhatsApp e templates de mensagem."""
import logging

from .context import (
    _formas_pagamento_texto,
    _linhas_descontos_recibo,
    linha_valor_com_desconto_recibo,
    linhas_protocolo_informativo,
    rotulo_subtotal_recibo,
    rotulo_total_recibo,
    _linhas_taxa_consulta_recibo,
    _obter_dados_contexto,
    custeado_pela_clinica,
    linha_vencimento_recibo,
    procedimentos_exibidos_recibo,
    recebido_a_maior_recibo,
    saldo_aberto_recibo,
    reconciliar_conta_recibo,
    situacao_recibo,
    titulo_recibo,
)
from .moeda import formatar_moeda_recibo
from .pdf import _gerar_pdf_recibo

logger = logging.getLogger(__name__)


def _enviar_recibo_whatsapp(payment, patient, appointment, *, somente_foto=False) -> tuple[bool, str]:
    """Envia só a foto do recibo. Cliente, valores e formas ficam na imagem."""
    telefone = (getattr(patient, "telefone", "") or "").strip()
    if not telefone:
        return False, "Paciente não possui telefone cadastrado."

    try:
        from django.conf import settings

        from whatsapp.models import WhatsAppConfig

        loja_id = payment.loja_id
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return False, "WhatsApp não está ativo. Configure em Configurações → WhatsApp."

        ctx = _obter_dados_contexto(payment, patient, appointment)

        try:
            from clinica_beleza.public_pdf import PREFIX_RECIBO, gravar_pdf_publico
            from clinica_beleza.recibo.imagem import pdf_para_jpeg

            pdf_bytes = _gerar_pdf_recibo(ctx)
            from clinica_beleza.media_docs_service import arquivar_pdf_gerado
            arquivar_pdf_gerado(
                getattr(payment, "loja_id", None),
                patient,
                pdf_bytes,
                f"recibo_{payment.id}.pdf",
            )
            jpeg_bytes = None
            try:
                jpeg_bytes = pdf_para_jpeg(pdf_bytes)
            except Exception as conv_err:
                logger.warning("Conversão do recibo em foto falhou: %s", conv_err)

            payload = {"payment_id": payment.id, "pdf": pdf_bytes}
            if jpeg_bytes:
                payload["imagem"] = jpeg_bytes
            token = gravar_pdf_publico(PREFIX_RECIBO, payload)

            api_base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
            if jpeg_bytes:
                from whatsapp.services import _send_whatsapp_image_evolution

                img_url = f"{api_base}/api/clinica-beleza/payments/{payment.id}/recibo-img/{token}/"
                ok_img, err_img = _send_whatsapp_image_evolution(
                    telefone, img_url, f"recibo_{payment.id}.jpg",
                    caption=None, config=config,
                )
                if not ok_img:
                    logger.warning("Foto do recibo via WhatsApp falhou, tentando PDF: %s", err_img)
                    from whatsapp.services import _send_whatsapp_document_evolution

                    pdf_url = f"{api_base}/api/clinica-beleza/payments/{payment.id}/recibo-pdf/{token}/"
                    _send_whatsapp_document_evolution(
                        telefone, pdf_url, f"recibo_{payment.id}.pdf",
                        caption=None, config=config,
                    )
            else:
                from whatsapp.services import _send_whatsapp_document_evolution

                pdf_url = f"{api_base}/api/clinica-beleza/payments/{payment.id}/recibo-pdf/{token}/"
                _send_whatsapp_document_evolution(
                    telefone, pdf_url, f"recibo_{payment.id}.pdf",
                    caption=None, config=config,
                )
        except Exception as pdf_err:
            logger.warning("Foto do recibo via WhatsApp falhou: %s", pdf_err)
            return False, "Não foi possível enviar a foto do recibo."

        logger.info("Recibo enviado por WhatsApp para %s (payment_id=%s)", telefone, payment.id)
        return True, f"Recibo enviado para {telefone}"
    except Exception as e:
        logger.warning("Falha ao enviar recibo WhatsApp payment_id=%s: %s", payment.id, e)
        return False, f"Erro ao enviar WhatsApp: {e}"


def _texto_saldo_whatsapp(ctx: dict) -> str:
    saldo = saldo_aberto_recibo(ctx)
    if saldo <= 0:
        return ""
    return (
        f"Saldo a pagar: {formatar_moeda_recibo(saldo)}\n"
        f"{linha_vencimento_recibo(ctx)}\n"
    )


def _montar_mensagem_whatsapp(ctx: dict) -> str:
    """Mensagem profissional formatada para WhatsApp."""
    ctx = reconciliar_conta_recibo(ctx)
    procs_lines = []
    for label, valor in _linhas_taxa_consulta_recibo(ctx):
        procs_lines.append(f"  • {label} ......... {formatar_moeda_recibo(valor)}")
    for nome, valor in procedimentos_exibidos_recibo(ctx):
        procs_lines.append(f"  • {nome} ... {formatar_moeda_recibo(valor)}")
    procs = "\n".join(procs_lines)
    prof_line = f'👩‍⚕️ *Profissional:* {ctx["profissional_nome"]}\n' if ctx["profissional_nome"] else ""
    descontos = _linhas_descontos_recibo(ctx)
    desconto_block = ""
    if descontos:
        linhas_desc = "\n".join(
            f"🏷️ *{label}:* - {formatar_moeda_recibo(valor)}" for label, valor in descontos
        )
        desconto_block = (
            f'🧾 *{rotulo_subtotal_recibo(ctx)}:* {formatar_moeda_recibo(ctx.get("subtotal", 0))}\n'
            f"{linhas_desc}\n"
        )
    valor_com_desconto = linha_valor_com_desconto_recibo(ctx)
    if valor_com_desconto:
        desconto_block += f'*{valor_com_desconto[0]}:* {formatar_moeda_recibo(valor_com_desconto[1])}\n'
    protocolo_info = linhas_protocolo_informativo(ctx)
    if protocolo_info:
        linhas_proto = "\n".join(
            f"*{label}:* {formatar_moeda_recibo(valor)}" for label, valor in protocolo_info
        )
        desconto_block += f"*Protocolo*\n{linhas_proto}\n"
    if descontos or protocolo_info:
        desconto_block += (
            f'💵 *{rotulo_total_recibo(ctx)}:* {formatar_moeda_recibo(ctx.get("valor_total", 0))}\n'
        )
    extra = recebido_a_maior_recibo(ctx)
    extra_linha = (
        f"Recebido a maior: {formatar_moeda_recibo(extra)}\n" if extra > 0.009 else ""
    )
    if situacao_recibo(ctx) == "quitado" and custeado_pela_clinica(ctx):
        valor_pago_linha = ""
    else:
        valor_pago_linha = (
            f'💰 *Valor pago: {formatar_moeda_recibo(ctx.get("valor_pago", 0))}*\n'
        )
    return (
        f'🏥 *{ctx["loja_nome"] or "Clínica"}*\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'✅ *{titulo_recibo(ctx)[0]}*\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'👤 *Cliente:* {ctx["paciente_nome"]}\n'
        f'📅 *Data do pagamento:* {ctx["data"]}\n'
        f'{prof_line}'
        f'📅 *Data/Hora do atendimento:* {ctx.get("data_atendimento") or "—"}\n\n'
        f'📋 *Serviços realizados:*\n'
        f'{procs}\n\n'
        f'{desconto_block}'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'💳 *Forma de pagamento:*\n'
        f'{_formas_pagamento_texto(ctx)}'
        f'{valor_pago_linha}'
        f'{_texto_saldo_whatsapp(ctx)}'
        f'{extra_linha}'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'{("ℹ️ " + ctx["retorno_aviso"] + "\n\n") if (ctx.get("retorno_aviso") or "").strip() else ""}'
        f'_O recibo segue como foto nesta conversa._\n'
        f'Agradecemos pela confiança! 🙏'
    )
