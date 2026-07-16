"""Envio de recibo de pagamento do salão (email / WhatsApp + PDF).

Layout alinhado ao recibo da Clínica da Beleza (cupom 80mm).
"""
from __future__ import annotations

import hashlib
import hmac
import io
import logging
import re
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings

from core.cpf_utils import eh_cnpj, eh_cpf, normalizar_cpf_cnpj
from core.phone_utils import telefone_exibicao_brasileiro

logger = logging.getLogger(__name__)

RECIBO_PDF_TOKEN_MAX_AGE = 600  # 10 min — Evolution pode demorar a buscar o PDF


def make_recibo_pdf_token(payment_id: int, loja_id: int) -> str:
    """Token assinado: payment_id-loja_id-ts-sig (regenerável sem cache)."""
    ts = int(time.time())
    payload = f"{payment_id}:{loja_id}:{ts}"
    sig = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:24]
    return f"{payment_id}-{loja_id}-{ts}-{sig}"


def parse_recibo_pdf_token(token: str, expected_payment_id: int) -> int | None:
    """Valida token e retorna loja_id, ou None se inválido/expirado."""
    parts = (token or "").split("-")
    if len(parts) != 4:
        return None
    try:
        payment_id = int(parts[0])
        loja_id = int(parts[1])
        ts = int(parts[2])
    except (TypeError, ValueError):
        return None
    sig = parts[3]
    if payment_id != expected_payment_id:
        return None
    if abs(int(time.time()) - ts) > RECIBO_PDF_TOKEN_MAX_AGE:
        return None
    payload = f"{payment_id}:{loja_id}:{ts}"
    expected = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:24]
    if not hmac.compare_digest(sig, expected):
        return None
    return loja_id


def gerar_pdf_recibo_payment(payment) -> bytes:
    """Gera PDF a partir do Payment (com relations carregadas)."""
    agendamento = payment.agendamento
    cliente = getattr(agendamento, "cliente", None) if agendamento else None
    if not agendamento or not cliente:
        raise ValueError("Pagamento sem agendamento/cliente")
    ctx = _obter_dados_contexto(payment, cliente, agendamento)
    return _gerar_pdf_recibo(ctx)


def enviar_recibo_pagamento(payment, *, canal: str) -> tuple[bool, str]:
    agendamento = payment.agendamento
    if not agendamento:
        return False, "Pagamento sem agendamento vinculado."
    cliente = getattr(agendamento, "cliente", None)
    if not cliente:
        return False, "Cliente não encontrado no agendamento."
    if canal == "email":
        return _enviar_recibo_email(payment, cliente, agendamento)
    if canal == "whatsapp":
        return _enviar_recibo_whatsapp(payment, cliente, agendamento)
    return False, f"Canal desconhecido: {canal}"


def _formatar_data_recibo(dt) -> str:
    """Formata data/hora no fuso America/Sao_Paulo."""
    if not dt:
        return "—"
    from django.utils import timezone as dj_tz

    if isinstance(dt, datetime) and dj_tz.is_aware(dt):
        dt = dj_tz.localtime(dt)
    if hasattr(dt, "strftime"):
        if isinstance(dt, datetime):
            return dt.strftime("%d/%m/%Y %H:%M")
        return dt.strftime("%d/%m/%Y")
    return str(dt)


def _label_documento_loja(cpf_cnpj: str) -> str:
    if eh_cpf(cpf_cnpj):
        return "CPF"
    if eh_cnpj(cpf_cnpj):
        return "CNPJ"
    return "CPF/CNPJ"


def _extrair_desconto(payment) -> float:
    try:
        d = float(payment.desconto or 0)
        if d > 0:
            return d
    except (TypeError, ValueError):
        pass
    notes = (getattr(payment, "notes", None) or "").strip()
    m = re.search(r"Desconto:\s*R\$\s*([\d.,]+)", notes, re.IGNORECASE)
    if not m:
        return 0.0
    raw = m.group(1).strip()
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return float(Decimal(raw))
    except (InvalidOperation, ValueError):
        return 0.0


def _formatar_cep(cep: str) -> str:
    if not cep:
        return ""
    d = re.sub(r"\D", "", str(cep))
    if len(d) == 8:
        return f"{d[:5]}-{d[5:]}"
    return str(cep).strip()


def _formatar_endereco_loja(loja) -> str:
    partes = []
    if getattr(loja, "logradouro", ""):
        end = loja.logradouro
        if getattr(loja, "numero", ""):
            end += f", {loja.numero}"
        partes.append(end)
    if getattr(loja, "bairro", ""):
        partes.append(loja.bairro)
    if getattr(loja, "cidade", ""):
        cidade = loja.cidade
        if getattr(loja, "uf", ""):
            cidade += f" - {loja.uf}"
        partes.append(cidade)
    return ", ".join(partes)


def _linha_tel_cep(telefone: str = "", cep: str = "") -> str:
    partes = []
    if telefone:
        partes.append(f"Tel: {telefone}")
    if cep:
        partes.append(f"CEP {cep}")
    return "  ·  ".join(partes)


def _linha_documento_loja(ctx: dict) -> str:
    doc = ctx.get("loja_documento") or ""
    if not doc:
        return ""
    label = ctx.get("loja_documento_label") or _label_documento_loja(doc)
    return f"{label}: {doc}"


def _formas_pagamento_texto(ctx: dict) -> str:
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        metodo = ctx.get("metodo", "")
        return f'  {metodo} — R$ {ctx.get("valor_pago", 0):.2f}\n'
    return "\n".join(f'  • {f["metodo"]} — R$ {f["valor"]:.2f}' for f in formas) + "\n"


def _formas_pagamento_html(ctx: dict) -> str:
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        metodo = ctx.get("metodo", "")
        return f'<li>{metodo} — R$ {ctx.get("valor_pago", 0):.2f}</li>'
    return "".join(f'<li>{f["metodo"]} — R$ {f["valor"]:.2f}</li>' for f in formas)


def _obter_dados_contexto(payment, cliente, agendamento) -> dict:
    from superadmin.models import Loja

    loja = Loja.objects.filter(id=payment.loja_id).first()
    profissional = getattr(agendamento, "profissional", None)
    servico = getattr(agendamento, "servico", None)
    desconto = _extrair_desconto(payment)
    valor_total = float(payment.valor_total_efetivo)
    valor_pago = float(payment.amount or 0)

    # Valor do serviço na linha: preço do atendimento (antes do desconto no total)
    valor_servico = float(getattr(agendamento, "valor", None) or payment.valor_total or valor_pago or 0)
    if desconto > 0 and valor_servico <= valor_pago + 0.009:
        valor_servico = valor_total + desconto

    servicos = []
    if servico:
        servicos.append({"nome": servico.nome, "valor": valor_servico})
    elif valor_servico > 0:
        servicos.append({"nome": "Atendimento", "valor": valor_servico})

    servicos_soma = sum(s["valor"] for s in servicos)
    subtotal = valor_total + desconto if desconto > 0 else servicos_soma

    doc_raw = (getattr(loja, "cpf_cnpj", "") or "") if loja else ""
    tel_raw = (getattr(loja, "owner_telefone", "") or "") if loja else ""
    cep_raw = (getattr(loja, "cep", "") or "") if loja else ""
    loja_telefone = telefone_exibicao_brasileiro(tel_raw)
    loja_cep = _formatar_cep(cep_raw)
    loja_email = (getattr(getattr(loja, "owner", None), "email", "") or "").strip() if loja else ""

    data_at = agendamento.data
    hora = agendamento.hora_inicio
    if data_at and hora:
        data_atendimento = f"{data_at.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
    elif data_at:
        data_atendimento = data_at.strftime("%d/%m/%Y")
    else:
        data_atendimento = "—"

    metodo = (
        payment.get_payment_method_display()
        if hasattr(payment, "get_payment_method_display")
        else payment.payment_method
    )

    return {
        "cliente_nome": getattr(cliente, "nome", "Cliente"),
        "cliente_email": (getattr(cliente, "email", "") or "").strip(),
        "cliente_telefone": telefone_exibicao_brasileiro(getattr(cliente, "telefone", "") or ""),
        "profissional_nome": getattr(profissional, "nome", "") if profissional else "",
        "loja_nome": getattr(loja, "nome", "") if loja else "",
        "loja_documento": normalizar_cpf_cnpj(doc_raw),
        "loja_documento_label": _label_documento_loja(doc_raw),
        "loja_endereco": _formatar_endereco_loja(loja) if loja else "",
        "loja_telefone": loja_telefone,
        "loja_cep": loja_cep,
        "loja_email": loja_email,
        "loja_tel_cep": _linha_tel_cep(loja_telefone, loja_cep),
        "servicos": servicos,
        "subtotal": float(subtotal),
        "desconto": desconto,
        "valor_total": valor_total,
        "valor_pago": valor_pago,
        "metodo": metodo,
        "formas_pagamento": [{"metodo": metodo, "valor": valor_pago}],
        "data": _formatar_data_recibo(payment.payment_date),
        "data_atendimento": data_atendimento,
    }


def _gerar_pdf_recibo(ctx: dict) -> bytes:
    """PDF cupom 80mm — mesmo layout da clínica."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    page_w = 80 * mm
    page_h = 240 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=(page_w, page_h),
        leftMargin=4 * mm,
        rightMargin=4 * mm,
        topMargin=6 * mm,
        bottomMargin=6 * mm,
    )

    s_center = ParagraphStyle("c", fontSize=8, alignment=TA_CENTER, leading=11)
    s_bold_center = ParagraphStyle("bc", fontSize=11, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=14)
    s_title = ParagraphStyle("ti", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12)
    s_left = ParagraphStyle("l", fontSize=8, leading=11)
    s_bold = ParagraphStyle("b", fontSize=8, fontName="Helvetica-Bold", leading=11)
    s_total = ParagraphStyle("t", fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=15)
    s_footer = ParagraphStyle("f", fontSize=7, alignment=TA_CENTER, leading=10, textColor=colors.HexColor("#666666"))
    s_right = ParagraphStyle("r", fontSize=8, alignment=TA_RIGHT, leading=11)

    hr = HRFlowable(width="100%", thickness=0.5, dash=[2, 2], spaceAfter=3, spaceBefore=3)
    col_w = page_w - 8 * mm
    story = []

    if ctx["loja_nome"]:
        story.append(Paragraph(ctx["loja_nome"].upper(), s_bold_center))
    doc_line = _linha_documento_loja(ctx)
    if doc_line:
        story.append(Paragraph(doc_line, s_center))
    if ctx["loja_endereco"]:
        story.append(Paragraph(ctx["loja_endereco"], s_center))
    tel_cep = ctx.get("loja_tel_cep") or _linha_tel_cep(ctx.get("loja_telefone", ""), ctx.get("loja_cep", ""))
    if tel_cep:
        story.append(Paragraph(tel_cep, s_center))
    if ctx.get("loja_email"):
        story.append(Paragraph(ctx["loja_email"], s_center))
    story.append(Spacer(1, 3 * mm))
    story.append(hr)
    story.append(Paragraph("RECIBO DE PAGAMENTO", s_title))
    story.append(Paragraph(ctx["data"], s_center))
    story.append(hr)

    story.append(Paragraph(f"<b>Cliente:</b> {ctx['cliente_nome']}", s_left))
    if ctx["profissional_nome"]:
        story.append(Paragraph(f"<b>Profissional:</b> {ctx['profissional_nome']}", s_left))
    if ctx.get("data_atendimento"):
        story.append(Paragraph(f"<b>Data/Hora do atendimento:</b> {ctx['data_atendimento']}", s_left))
    story.append(hr)

    story.append(Paragraph("<b>SERVIÇOS</b>", s_bold))
    story.append(Spacer(1, 1 * mm))
    svc_data = [
        [Paragraph(f'• {s["nome"]}', s_left), Paragraph(f'R$ {s["valor"]:.2f}', s_right)]
        for s in ctx["servicos"]
    ]
    if svc_data:
        svc_table = Table(svc_data, colWidths=[col_w * 0.65, col_w * 0.35])
        svc_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(svc_table)

    story.append(hr)

    totals_data = []
    if ctx.get("desconto", 0) > 0:
        totals_data.append([
            Paragraph("Subtotal", s_left),
            Paragraph(f'R$ {ctx.get("subtotal", ctx["valor_total"] + ctx["desconto"]):.2f}', s_right),
        ])
        totals_data.append([
            Paragraph("Desconto", s_left),
            Paragraph(f'- R$ {ctx["desconto"]:.2f}', s_right),
        ])
    totals_data.append([
        Paragraph("<b>Total</b>", s_bold),
        Paragraph(f'<b>R$ {ctx["valor_total"]:.2f}</b>', s_right),
    ])
    formas = ctx.get("formas_pagamento", [])
    if formas:
        totals_data.append([Paragraph("<b>Formas de pagamento:</b>", s_bold), Paragraph("", s_right)])
        for f in formas:
            totals_data.append([
                Paragraph(f'  {f["metodo"]}', s_left),
                Paragraph(f'R$ {f["valor"]:.2f}', s_right),
            ])
    else:
        metodo = ctx.get("metodo", "")
        totals_data.append([Paragraph(metodo, s_left), Paragraph(f'R$ {ctx["valor_pago"]:.2f}', s_right)])

    totals_table = Table(totals_data, colWidths=[col_w * 0.55, col_w * 0.45])
    totals_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(totals_table)

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(f"VALOR PAGO: R$ {ctx['valor_pago']:.2f}", s_total))
    if ctx.get("valor_pago", 0) >= ctx.get("valor_total", 0) and ctx.get("valor_total", 0) > 0:
        story.append(Spacer(1, 1 * mm))
        story.append(Paragraph("<b>Quitado</b>", s_center))
    story.append(Spacer(1, 2 * mm))
    story.append(hr)
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Agradecemos pela confiança!", s_footer))
    story.append(Paragraph("Documento não fiscal — gerado pelo sistema.", s_footer))

    doc.build(story)
    return buf.getvalue()


def _enviar_recibo_email(payment, cliente, agendamento) -> tuple[bool, str]:
    email = (getattr(cliente, "email", "") or "").strip()
    if not email:
        return False, "Cliente não possui email cadastrado."
    try:
        from core.email_delivery import create_email_multipart, send_prepared
        from core.email_sync_context import email_sync_only

        ctx = _obter_dados_contexto(payment, cliente, agendamento)
        pdf_bytes = _gerar_pdf_recibo(ctx)
        msg = create_email_multipart(
            subject=f'Recibo de Pagamento — {ctx["loja_nome"] or "Salão"}',
            body=_montar_email_texto(ctx),
            to=[email],
            html=_montar_email_html(ctx),
        )
        msg.attach(f"recibo_{payment.id}.pdf", pdf_bytes, "application/pdf")
        token = email_sync_only.set(True)
        try:
            send_prepared(msg, fail_silently=False)
        finally:
            email_sync_only.reset(token)
        return True, f"Recibo enviado para {email}"
    except Exception as e:
        logger.warning("Falha recibo email salão payment_id=%s: %s", payment.id, e)
        return False, f"Erro ao enviar email: {e}"


def _enviar_recibo_whatsapp(payment, cliente, agendamento) -> tuple[bool, str]:
    telefone = (getattr(cliente, "telefone", "") or "").strip()
    if not telefone:
        return False, "Cliente não possui telefone cadastrado."
    try:
        from django.core.cache import cache as django_cache

        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp

        config = WhatsAppConfig.objects.filter(loja_id=payment.loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return False, "WhatsApp não está ativo. Configure em Configurações → WhatsApp."

        ctx = _obter_dados_contexto(payment, cliente, agendamento)
        mensagem = _montar_mensagem_whatsapp(ctx)
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if not ok:
            return False, err or "Erro ao enviar WhatsApp."

        try:
            from core.public_urls import get_public_api_base_url

            token = make_recibo_pdf_token(payment.id, payment.loja_id)
            pdf_bytes = _gerar_pdf_recibo(ctx)
            django_cache.set(
                f"recibo_pdf_salao_{token}",
                {"payment_id": payment.id, "pdf": pdf_bytes},
                RECIBO_PDF_TOKEN_MAX_AGE,
            )
            api_base = get_public_api_base_url()
            pdf_url = f"{api_base}/api/cabeleireiro/payments/{payment.id}/recibo-pdf/{token}/"
            from whatsapp.services import _send_whatsapp_document_evolution

            _send_whatsapp_document_evolution(
                telefone,
                pdf_url,
                f"recibo_{payment.id}.pdf",
                caption="Recibo de Pagamento",
                config=config,
            )
        except Exception as pdf_err:
            logger.warning("PDF WhatsApp salão falhou (texto ok): %s", pdf_err)

        return True, f"Recibo enviado para {telefone}"
    except Exception as e:
        logger.warning("Falha recibo WhatsApp salão payment_id=%s: %s", payment.id, e)
        return False, f"Erro ao enviar WhatsApp: {e}"


def _montar_email_html(ctx: dict) -> str:
    """Email no mesmo padrão da clínica — PDF em anexo."""
    procs_html = "".join(
        f'<li>{s["nome"]} — R$ {s["valor"]:.2f}</li>' for s in ctx["servicos"]
    )
    doc_line = _linha_documento_loja(ctx)
    desconto_html = ""
    if ctx.get("desconto", 0) > 0:
        desconto_html = (
            f'<p style="margin:4px 0;"><strong>Subtotal:</strong> R$ {ctx.get("subtotal", 0):.2f}</p>'
            f'<p style="margin:4px 0;"><strong>Desconto:</strong> - R$ {ctx["desconto"]:.2f}</p>'
        )
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;color:#333;">
      <div style="text-align:center;border-bottom:2px solid #4A3042;padding-bottom:12px;margin-bottom:16px;">
        <h2 style="margin:0;color:#4A3042;">{ctx['loja_nome'] or 'Salão'}</h2>
        {f'<p style="margin:4px 0;font-size:12px;color:#666;">{doc_line}</p>' if doc_line else ''}
        {f'<p style="margin:4px 0;font-size:12px;color:#666;">{ctx["loja_endereco"]}</p>' if ctx['loja_endereco'] else ''}
        {f'<p style="margin:4px 0;font-size:12px;color:#666;">{ctx.get("loja_tel_cep") or (("Tel: " + ctx["loja_telefone"]) if ctx.get("loja_telefone") else "")}</p>' if (ctx.get('loja_tel_cep') or ctx.get('loja_telefone')) else ''}
      </div>

      <p>Olá <strong>{ctx['cliente_nome']}</strong>,</p>
      <p>Segue o resumo do seu atendimento e o recibo em PDF anexo.</p>

      <div style="background:#f8f8f8;border-radius:8px;padding:16px;margin:16px 0;">
        <p style="margin:4px 0;"><strong>Data do pagamento:</strong> {ctx['data']}</p>
        {f'<p style="margin:4px 0;"><strong>Profissional:</strong> {ctx["profissional_nome"]}</p>' if ctx['profissional_nome'] else ''}
        {f'<p style="margin:4px 0;"><strong>Data/Hora do atendimento:</strong> {ctx["data_atendimento"]}</p>' if ctx.get('data_atendimento') else ''}
        <p style="margin:4px 0;"><strong>Serviços:</strong></p>
        <ul style="margin:4px 0;padding-left:20px;">{procs_html or '<li>—</li>'}</ul>
        {desconto_html}
        <p style="margin:4px 0;"><strong>Total:</strong> R$ {ctx['valor_total']:.2f}</p>
        <p style="margin:4px 0;"><strong>Forma(s) de pagamento:</strong></p>
        <ul style="margin:4px 0;padding-left:20px;">{_formas_pagamento_html(ctx)}</ul>
        <p style="margin:12px 0 0;font-size:16px;font-weight:bold;color:#2e7d32;">
          Valor pago: R$ {ctx['valor_pago']:.2f}
        </p>
      </div>

      <p style="font-size:12px;color:#666;">
        O recibo completo está em anexo (PDF). Guarde para seus registros.
      </p>

      <p style="margin-top:20px;">Atenciosamente,<br><strong>{ctx['loja_nome']}</strong></p>
      {f'<p style="font-size:11px;color:#999;">Tel: {ctx["loja_telefone"]}</p>' if ctx['loja_telefone'] else ''}
    </div>
    """


def _montar_email_texto(ctx: dict) -> str:
    procs = "\n".join(f'  • {s["nome"]} — R$ {s["valor"]:.2f}' for s in ctx["servicos"]) or "  —"
    doc_line = _linha_documento_loja(ctx)
    desconto_lines = ""
    if ctx.get("desconto", 0) > 0:
        desconto_lines = (
            f'Subtotal: R$ {ctx.get("subtotal", 0):.2f}\n'
            f'Desconto: - R$ {ctx["desconto"]:.2f}\n'
        )
    header_extra = ""
    if doc_line:
        header_extra += f"{doc_line}\n"
    if ctx.get("loja_endereco"):
        header_extra += f'{ctx["loja_endereco"]}\n'
    tel_cep = ctx.get("loja_tel_cep") or ""
    if not tel_cep and ctx.get("loja_telefone"):
        tel_cep = f'Tel: {ctx["loja_telefone"]}'
    if tel_cep:
        header_extra += f"{tel_cep}\n"
    return (
        f'{ctx["loja_nome"] or "Salão"}\n'
        f'{header_extra}\n'
        f'Olá {ctx["cliente_nome"]},\n\n'
        f'Segue o resumo do seu atendimento e o recibo em PDF anexo.\n\n'
        f'Data do pagamento: {ctx["data"]}\n'
        f'Profissional: {ctx["profissional_nome"] or "—"}\n'
        f'Data/Hora do atendimento: {ctx.get("data_atendimento") or "—"}\n'
        f'Serviços:\n{procs}\n'
        f'{desconto_lines}'
        f'Total: R$ {ctx["valor_total"]:.2f}\n'
        f'Forma(s) de pagamento:\n{_formas_pagamento_texto(ctx)}'
        f'Valor pago: R$ {ctx["valor_pago"]:.2f}\n\n'
        f'Atenciosamente,\n{ctx["loja_nome"]}\n'
    )


def _montar_mensagem_whatsapp(ctx: dict) -> str:
    """Mesmo padrão visual da clínica (texto + PDF em anexo)."""
    procs_lines = []
    for s in ctx["servicos"]:
        nome = s["nome"][:35]
        val = f'{s["valor"]:.2f}'
        procs_lines.append(f"  • {nome} ... R$ {val}")
    procs = "\n".join(procs_lines)
    prof_line = f'✂️ *Profissional:* {ctx["profissional_nome"]}\n' if ctx["profissional_nome"] else ""
    valor_pago = f'{ctx["valor_pago"]:.2f}'
    desconto_block = ""
    if ctx.get("desconto", 0) > 0:
        desconto_block = (
            f'🧾 *Subtotal:* R$ {ctx.get("subtotal", 0):.2f}\n'
            f'🏷️ *Desconto:* - R$ {ctx["desconto"]:.2f}\n'
        )
    return (
        f'💇 *{ctx["loja_nome"] or "Salão"}*\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'✅ *RECIBO DE PAGAMENTO*\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'👤 *Cliente:* {ctx["cliente_nome"]}\n'
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
        f'_O recibo completo em PDF segue em anexo._\n'
        f'Agradecemos pela confiança! 🙏'
    )
