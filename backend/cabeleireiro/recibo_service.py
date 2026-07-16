"""Envio de recibo de pagamento do salão (email / WhatsApp + PDF)."""
from __future__ import annotations

import hashlib
import io
import logging
import re
import time
from decimal import Decimal, InvalidOperation
from datetime import datetime

from core.cpf_utils import eh_cnpj, eh_cpf, normalizar_cpf_cnpj
from core.phone_utils import telefone_exibicao_brasileiro

logger = logging.getLogger(__name__)


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


def _obter_dados_contexto(payment, cliente, agendamento) -> dict:
    from superadmin.models import Loja

    loja = Loja.objects.filter(id=payment.loja_id).first()
    profissional = getattr(agendamento, "profissional", None)
    servico = getattr(agendamento, "servico", None)
    servicos = []
    if servico:
        servicos.append({"nome": servico.nome, "valor": float(agendamento.valor or payment.amount or 0)})
    elif float(payment.amount or 0) > 0:
        servicos.append({"nome": "Atendimento", "valor": float(payment.amount or 0)})

    doc_raw = (getattr(loja, "cpf_cnpj", "") or "") if loja else ""
    tel_raw = (getattr(loja, "owner_telefone", "") or "") if loja else ""
    cep_raw = (getattr(loja, "cep", "") or "") if loja else ""
    desconto = _extrair_desconto(payment)
    valor_total = float(payment.valor_total_efetivo)
    valor_pago = float(payment.amount or 0)
    subtotal = valor_total + desconto if desconto > 0 else sum(s["valor"] for s in servicos)
    loja_telefone = telefone_exibicao_brasileiro(tel_raw)
    loja_cep = _formatar_cep(cep_raw)
    data_at = agendamento.data
    hora = agendamento.hora_inicio
    if data_at and hora:
        data_atendimento = f"{data_at.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
    elif data_at:
        data_atendimento = data_at.strftime("%d/%m/%Y")
    else:
        data_atendimento = "—"

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
        "servicos": servicos,
        "subtotal": float(subtotal),
        "desconto": desconto,
        "valor_total": valor_total,
        "valor_pago": valor_pago,
        "metodo": payment.get_payment_method_display(),
        "data": _formatar_data_recibo(payment.payment_date),
        "data_atendimento": data_atendimento,
    }


def _gerar_pdf_recibo(ctx: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    page_w = 80 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=(page_w, 220 * mm),
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
    if ctx["loja_documento"]:
        story.append(Paragraph(f'{ctx["loja_documento_label"]}: {ctx["loja_documento"]}', s_center))
    if ctx["loja_endereco"]:
        story.append(Paragraph(ctx["loja_endereco"], s_center))
    if ctx["loja_telefone"] or ctx["loja_cep"]:
        partes = []
        if ctx["loja_telefone"]:
            partes.append(f'Tel: {ctx["loja_telefone"]}')
        if ctx["loja_cep"]:
            partes.append(f'CEP {ctx["loja_cep"]}')
        story.append(Paragraph("  ·  ".join(partes), s_center))
    story.append(Spacer(1, 3 * mm))
    story.append(hr)
    story.append(Paragraph("RECIBO DE PAGAMENTO", s_title))
    story.append(Paragraph(ctx["data"], s_center))
    story.append(hr)
    story.append(Paragraph(f"<b>Cliente:</b> {ctx['cliente_nome']}", s_left))
    if ctx["profissional_nome"]:
        story.append(Paragraph(f"<b>Profissional:</b> {ctx['profissional_nome']}", s_left))
    story.append(Paragraph(f"<b>Data/Hora:</b> {ctx['data_atendimento']}", s_left))
    story.append(hr)
    story.append(Paragraph("<b>SERVIÇOS</b>", s_bold))
    svc_data = [
        [Paragraph(f'• {s["nome"]}', s_left), Paragraph(f'R$ {s["valor"]:.2f}', s_right)]
        for s in ctx["servicos"]
    ]
    if svc_data:
        t = Table(svc_data, colWidths=[col_w * 0.65, col_w * 0.35])
        t.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(t)
    story.append(hr)
    totals = []
    if ctx.get("desconto", 0) > 0:
        totals.append([Paragraph("Subtotal", s_left), Paragraph(f'R$ {ctx["subtotal"]:.2f}', s_right)])
        totals.append([Paragraph("Desconto", s_left), Paragraph(f'- R$ {ctx["desconto"]:.2f}', s_right)])
    totals.append([Paragraph("<b>Total</b>", s_bold), Paragraph(f'<b>R$ {ctx["valor_total"]:.2f}</b>', s_right)])
    totals.append([Paragraph(ctx["metodo"], s_left), Paragraph(f'R$ {ctx["valor_pago"]:.2f}', s_right)])
    tt = Table(totals, colWidths=[col_w * 0.55, col_w * 0.45])
    tt.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(tt)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(f"VALOR PAGO: R$ {ctx['valor_pago']:.2f}", s_total))
    story.append(Paragraph("<b>Quitado</b>", s_center))
    story.append(hr)
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
        servicos = "".join(f'<li>{s["nome"]} — R$ {s["valor"]:.2f}</li>' for s in ctx["servicos"])
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;color:#333;">
          <h2 style="color:#4A3042;">{ctx['loja_nome'] or 'Salão'}</h2>
          <p>Olá <strong>{ctx['cliente_nome']}</strong>,</p>
          <p>Segue o recibo do seu atendimento em PDF anexo.</p>
          <ul>{servicos or '<li>—</li>'}</ul>
          <p><strong>Total pago:</strong> R$ {ctx['valor_pago']:.2f} ({ctx['metodo']})</p>
          <p>Atenciosamente,<br><strong>{ctx['loja_nome']}</strong></p>
        </div>
        """
        texto = (
            f'{ctx["loja_nome"] or "Salão"}\n'
            f'Olá {ctx["cliente_nome"]},\n'
            f'Recibo de pagamento — R$ {ctx["valor_pago"]:.2f} ({ctx["metodo"]}).\n'
            f'PDF em anexo.\n'
        )
        msg = create_email_multipart(
            subject=f'Recibo de Pagamento — {ctx["loja_nome"] or "Salão"}',
            body=texto,
            to=[email],
            html=html,
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
        from django.conf import settings
        from django.core.cache import cache as django_cache

        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp

        config = WhatsAppConfig.objects.filter(loja_id=payment.loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return False, "WhatsApp não está ativo. Configure em Configurações → WhatsApp."

        ctx = _obter_dados_contexto(payment, cliente, agendamento)
        servicos = "\n".join(f'  • {s["nome"]} — R$ {s["valor"]:.2f}' for s in ctx["servicos"])
        mensagem = (
            f'*{ctx["loja_nome"] or "Salão"}*\n'
            f'RECIBO DE PAGAMENTO\n\n'
            f'Cliente: {ctx["cliente_nome"]}\n'
            f'Data: {ctx["data"]}\n'
            f'Atendimento: {ctx["data_atendimento"]}\n'
            f'{servicos}\n'
            f'Forma: {ctx["metodo"]}\n'
            f'*Valor pago: R$ {ctx["valor_pago"]:.2f}*\n\n'
            f'_PDF segue em anexo._'
        )
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if not ok:
            return False, err or "Erro ao enviar WhatsApp."

        try:
            ts = str(int(time.time()))
            token_raw = f"recibo-salao-{payment.id}-{ts}-{settings.SECRET_KEY[:16]}"
            token = hashlib.sha256(token_raw.encode()).hexdigest()[:32]
            pdf_bytes = _gerar_pdf_recibo(ctx)
            django_cache.set(
                f"recibo_pdf_salao_{token}",
                {"payment_id": payment.id, "pdf": pdf_bytes},
                300,
            )
            api_base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
            # Em beta/staging o frontend aponta para a API correspondente; API_BASE_URL costuma estar certo.
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
