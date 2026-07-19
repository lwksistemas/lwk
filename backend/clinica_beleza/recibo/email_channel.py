"""Envio de recibo por email e templates de mensagem."""
import logging

from .context import (
    _formas_pagamento_html,
    _formas_pagamento_texto,
    _linha_documento_loja,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
    _obter_dados_contexto,
)
from .pdf import _gerar_pdf_recibo

logger = logging.getLogger(__name__)


def _enviar_recibo_email(payment, patient, appointment) -> tuple[bool, str]:
    """Envia recibo por email com PDF em anexo."""
    email = (getattr(patient, "email", "") or "").strip()
    if not email:
        return False, "Paciente não possui email cadastrado."

    try:
        from core.email_delivery import create_email_multipart, send_prepared
        from core.email_sync_context import email_sync_only

        ctx = _obter_dados_contexto(payment, patient, appointment)
        pdf_bytes = _gerar_pdf_recibo(ctx)

        assunto = f'Recibo de Pagamento — {ctx["loja_nome"] or "Clínica"}'
        corpo_html = _montar_email_html(ctx)
        corpo_texto = _montar_email_texto(ctx)

        msg = create_email_multipart(
            subject=assunto,
            body=corpo_texto,
            to=[email],
            html=corpo_html,
        )
        msg.attach(f"recibo_{payment.id}.pdf", pdf_bytes, "application/pdf")

        token = email_sync_only.set(True)
        try:
            send_prepared(msg, fail_silently=False)
        finally:
            email_sync_only.reset(token)

        logger.info("Recibo PDF enviado por email para %s (payment_id=%s)", email, payment.id)
        return True, f"Recibo enviado para {email}"
    except Exception as e:
        logger.warning("Falha ao enviar recibo email payment_id=%s: %s", payment.id, e)
        return False, f"Erro ao enviar email: {e}"


def _montar_email_html(ctx: dict) -> str:
    """Email profissional com resumo completo — PDF vai em anexo."""
    procs_html = "".join(
        f"<li>{label} — R$ {valor:.2f}</li>"
        for label, valor in _linhas_taxa_consulta_recibo(ctx)
    )
    procs_html += "".join(
        f'<li>{p["nome"]} — R$ {p["valor"]:.2f}</li>' for p in ctx["procedimentos"]
    )
    doc_line = _linha_documento_loja(ctx)
    descontos = _linhas_descontos_recibo(ctx)
    desconto_html = ""
    if descontos:
        linhas_desc = "".join(
            f'<p style="margin:4px 0;"><strong>{label}:</strong> - R$ {valor:.2f}</p>'
            for label, valor in descontos
        )
        desconto_html = (
            f'<p style="margin:4px 0;"><strong>Subtotal:</strong> R$ {ctx.get("subtotal", 0):.2f}</p>'
            f"{linhas_desc}"
        )
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;color:#333;">
      <div style="text-align:center;border-bottom:2px solid #8B3D52;padding-bottom:12px;margin-bottom:16px;">
        <h2 style="margin:0;color:#8B3D52;">{ctx['loja_nome'] or 'Clínica'}</h2>
        {f'<p style="margin:4px 0;font-size:12px;color:#666;">{doc_line}</p>' if doc_line else ''}
        {f'<p style="margin:4px 0;font-size:12px;color:#666;">{ctx["loja_endereco"]}</p>' if ctx['loja_endereco'] else ''}
        {f'<p style="margin:4px 0;font-size:12px;color:#666;">{ctx.get("loja_tel_cep") or (("Tel: " + ctx["loja_telefone"]) if ctx.get("loja_telefone") else "")}</p>' if (ctx.get('loja_tel_cep') or ctx.get('loja_telefone')) else ''}
      </div>

      <p>Olá <strong>{ctx['paciente_nome']}</strong>,</p>
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
        {f'<p style="margin:12px 0 0;font-size:12px;color:#555;">{ctx["retorno_aviso"]}</p>' if (ctx.get("retorno_aviso") or "").strip() else ''}
      </div>

      <p style="font-size:12px;color:#666;">
        O recibo completo está em anexo (PDF). Guarde para seus registros.
      </p>

      <p style="margin-top:20px;">Atenciosamente,<br><strong>{ctx['loja_nome']}</strong></p>
      {f'<p style="font-size:11px;color:#999;">Tel: {ctx["loja_telefone"]}</p>' if ctx['loja_telefone'] else ''}
    </div>
    """


def _montar_email_texto(ctx: dict) -> str:
    """Versão texto puro do email."""
    procs_lines = [
        f"  • {label} — R$ {valor:.2f}"
        for label, valor in _linhas_taxa_consulta_recibo(ctx)
    ]
    procs_lines.extend(f'  • {p["nome"]} — R$ {p["valor"]:.2f}' for p in ctx["procedimentos"])
    procs = "\n".join(procs_lines) or "  —"
    doc_line = _linha_documento_loja(ctx)
    descontos = _linhas_descontos_recibo(ctx)
    desconto_lines = ""
    if descontos:
        linhas_desc = "".join(f"{label}: - R$ {valor:.2f}\n" for label, valor in descontos)
        desconto_lines = (
            f'Subtotal: R$ {ctx.get("subtotal", 0):.2f}\n'
            f"{linhas_desc}"
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
        f'{ctx["loja_nome"] or "Clínica"}\n'
        f'{header_extra}\n'
        f'Olá {ctx["paciente_nome"]},\n\n'
        f'Segue o resumo do seu atendimento e o recibo em PDF anexo.\n\n'
        f'Data do pagamento: {ctx["data"]}\n'
        f'Profissional: {ctx["profissional_nome"] or "—"}\n'
        f'Data/Hora do atendimento: {ctx.get("data_atendimento") or "—"}\n'
        f'Serviços:\n{procs}\n'
        f'{desconto_lines}'
        f'Total: R$ {ctx["valor_total"]:.2f}\n'
        f'Forma(s) de pagamento:\n{_formas_pagamento_texto(ctx)}'
        f'Valor pago: R$ {ctx["valor_pago"]:.2f}\n'
        f'{((ctx.get("retorno_aviso") or "").strip() + "\n") if (ctx.get("retorno_aviso") or "").strip() else ""}'
        f'\nAtenciosamente,\n{ctx["loja_nome"]}\n'
    )
