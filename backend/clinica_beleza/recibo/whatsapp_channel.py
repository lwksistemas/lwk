"""Envio de recibo por WhatsApp e templates de mensagem."""
import hashlib
import logging
import time

from .context import (
    _formas_pagamento_texto,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
    _obter_dados_contexto,
)
from .pdf import _gerar_pdf_recibo

logger = logging.getLogger(__name__)


def _enviar_recibo_whatsapp(payment, patient, appointment) -> tuple[bool, str]:
    """Envia recibo por WhatsApp: mensagem de texto + PDF se possível."""
    telefone = (getattr(patient, "telefone", "") or "").strip()
    if not telefone:
        return False, "Paciente não possui telefone cadastrado."

    try:
        from django.conf import settings
        from django.core.cache import cache as django_cache

        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp

        loja_id = payment.loja_id
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return False, "WhatsApp não está ativo. Configure em Configurações → WhatsApp."

        ctx = _obter_dados_contexto(payment, patient, appointment)
        mensagem = _montar_mensagem_whatsapp(ctx)

        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if not ok:
            return False, err or "Erro ao enviar WhatsApp."

        try:
            ts = str(int(time.time()))
            token_raw = f"recibo-{payment.id}-{ts}-{settings.SECRET_KEY[:16]}"
            token = hashlib.sha256(token_raw.encode()).hexdigest()[:32]

            pdf_bytes = _gerar_pdf_recibo(ctx)
            django_cache.set(
                f"recibo_pdf_{token}",
                {"payment_id": payment.id, "pdf": pdf_bytes},
                300,
            )

            api_base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
            pdf_url = f"{api_base}/api/clinica-beleza/payments/{payment.id}/recibo-pdf/{token}/"

            from whatsapp.services import _send_whatsapp_document_evolution
            _send_whatsapp_document_evolution(
                telefone, pdf_url, f"recibo_{payment.id}.pdf",
                caption="Recibo de Pagamento", config=config,
            )
        except Exception as pdf_err:
            logger.warning("PDF via WhatsApp falhou (texto já enviado): %s", pdf_err)

        logger.info("Recibo enviado por WhatsApp para %s (payment_id=%s)", telefone, payment.id)
        return True, f"Recibo enviado para {telefone}"
    except Exception as e:
        logger.warning("Falha ao enviar recibo WhatsApp payment_id=%s: %s", payment.id, e)
        return False, f"Erro ao enviar WhatsApp: {e}"


def _montar_mensagem_whatsapp(ctx: dict) -> str:
    """Mensagem profissional formatada para WhatsApp."""
    procs_lines = []
    for label, valor in _linhas_taxa_consulta_recibo(ctx):
        procs_lines.append(f"  • {label} ......... R$ {valor:.2f}")
    for p in ctx["procedimentos"]:
        nome = p["nome"][:35]
        val = f'{p["valor"]:.2f}'
        procs_lines.append(f"  • {nome} ... R$ {val}")
    procs = "\n".join(procs_lines)
    prof_line = f'👩‍⚕️ *Profissional:* {ctx["profissional_nome"]}\n' if ctx["profissional_nome"] else ""
    valor_pago = f'{ctx["valor_pago"]:.2f}'
    descontos = _linhas_descontos_recibo(ctx)
    desconto_block = ""
    if descontos:
        linhas_desc = "\n".join(
            f"🏷️ *{label}:* - R$ {valor:.2f}" for label, valor in descontos
        )
        desconto_block = (
            f'🧾 *Subtotal:* R$ {ctx.get("subtotal", 0):.2f}\n'
            f"{linhas_desc}\n"
            f'💵 *Total:* R$ {ctx.get("valor_total", 0):.2f}\n'
        )
    return (
        f'🏥 *{ctx["loja_nome"] or "Clínica"}*\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'✅ *RECIBO DE PAGAMENTO*\n'
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
        f'💰 *Valor pago: R$ {valor_pago}*\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'{("ℹ️ " + ctx["retorno_aviso"] + "\n\n") if (ctx.get("retorno_aviso") or "").strip() else ""}'
        f'_O recibo completo em PDF segue em anexo._\n'
        f'Agradecemos pela confiança! 🙏'
    )
