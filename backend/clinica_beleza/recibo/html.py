"""Cupom HTML do recibo — mesmo contexto do PDF (Imprimir)."""
from __future__ import annotations

import html

from .context import (
    _linha_documento_loja,
    _linha_tel_cep,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
    _obter_dados_contexto,
    aplicar_valor_consulta_do_local,
    linhas_local_convenio_recibo,
)


def _t(valor) -> str:
    return html.escape(str(valor or ""), quote=True)


def _saldo(ctx: dict) -> float:
    valor_pago = ctx.get("valor_pago", 0) or 0
    valor_total = ctx.get("valor_total", 0) or 0
    return float(ctx.get("saldo_devedor", max(valor_total - valor_pago, 0)))


def gerar_html_recibo(ctx: dict) -> str:
    """Monta o cupom de impressão a partir do mesmo ctx do PDF."""
    ctx = aplicar_valor_consulta_do_local(ctx)
    saldo = _saldo(ctx)
    retorno_sem_valor = bool(ctx.get("retorno_gratuito")) and float(ctx.get("valor_total") or 0) <= 0.009
    if retorno_sem_valor:
        titulo = "RECIBO DE RETORNO"
    elif saldo > 0.009:
        titulo = "COMPROVANTE DE ATENDIMENTO"
    else:
        titulo = "RECIBO DE PAGAMENTO"
    doc_line = _linha_documento_loja(ctx)
    tel_cep = ctx.get("loja_tel_cep") or _linha_tel_cep(
        ctx.get("loja_telefone", ""), ctx.get("loja_cep", ""),
    )
    data_emissao = ctx.get("data_emissao") or ctx.get("data") or "—"
    data_atend = ctx.get("data_atendimento") or "—"

    linhas_taxa = _linhas_taxa_consulta_recibo(ctx)
    taxa_exibida = linhas_taxa[0][1] if linhas_taxa else 0.0
    servicos = []
    for label, valor in linhas_taxa:
        servicos.append(
            f"<tr><td>{_t(label)}</td>"
            f'<td style="text-align:right">R$ {valor:.2f}</td></tr>'
        )
    for p in ctx.get("procedimentos") or []:
        nome = p.get("nome") or ""
        valor = float(p.get("valor") or 0)
        nome_lower = nome.strip().lower()
        if taxa_exibida > 0 and valor == 0.0 and nome_lower in ("consulta", "taxa de consulta"):
            continue
        servicos.append(
            f'<tr><td style="padding-left:8px">• {_t(nome)}</td>'
            f'<td style="text-align:right">R$ {valor:.2f}</td></tr>'
        )
    for label, valor in linhas_local_convenio_recibo(ctx):
        servicos.append(
            f"<tr><td>{_t(label)}</td>"
            f'<td style="text-align:right">{_t(valor)}</td></tr>'
        )

    descontos = _linhas_descontos_recibo(ctx)
    subtotal = float(ctx.get("subtotal", ctx.get("valor_total") or 0))
    descontos_html = "".join(
        f"<tr><td>{_t(label)}</td>"
        f'<td style="text-align:right">- R$ {valor:.2f}</td></tr>'
        for label, valor in descontos
    )
    if descontos:
        totais = (
            f'<tr><td><strong>Subtotal</strong></td>'
            f'<td style="text-align:right"><strong>R$ {subtotal:.2f}</strong></td></tr>'
            f"{descontos_html}"
        )
    else:
        totais = ""
    totais += (
        f'<tr><td><strong>Total</strong></td>'
        f'<td style="text-align:right"><strong>R$ {float(ctx.get("valor_total") or 0):.2f}</strong></td></tr>'
    )

    valor_pago = float(ctx.get("valor_pago") or 0)
    formas = ctx.get("formas_pagamento") or []
    if formas:
        formas_html = "".join(
            f"<tr><td>{_t(f.get('metodo'))}</td>"
            f'<td style="text-align:right">R$ {float(f.get("valor") or 0):.2f}</td></tr>'
            for f in formas
        )
    elif valor_pago > 0:
        formas_html = (
            f"<tr><td>{_t(ctx.get('metodo') or 'Pagamento')}</td>"
            f'<td style="text-align:right">R$ {valor_pago:.2f}</td></tr>'
        )
    elif ctx.get("retorno_gratuito"):
        formas_html = (
            '<tr><td>Isento — retorno</td>'
            '<td style="text-align:right">R$ 0.00</td></tr>'
        )
    else:
        formas_html = ""

    vencimento = (ctx.get("vencimento") or "").strip()
    if saldo > 0.009:
        saldo_bloco = (
            f'<div class="total" style="font-size:12px;">SALDO A PAGAR: R$ {saldo:.2f}'
            f"{f' — vencimento {_t(vencimento)}' if vencimento else ''}</div>"
        )
    elif ctx.get("retorno_gratuito") and valor_pago <= 0.009:
        saldo_bloco = (
            '<div class="footer" style="border-top:none;margin-top:0;">'
            '<p style="font-weight:bold;color:#333;">Retorno isento</p></div>'
        )
    else:
        saldo_bloco = (
            '<div class="footer" style="border-top:none;margin-top:0;">'
            '<p style="font-weight:bold;color:#333;">Quitado</p></div>'
        )

    aviso = (ctx.get("retorno_aviso") or "").strip()
    nome_loja = (ctx.get("loja_nome") or "CLÍNICA").upper()

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Recibo de Pagamento</title>
<style>
  @page {{ size: 80mm auto; margin: 4mm; }}
  body {{ font-family: 'Courier New', monospace; width: 72mm; margin: 0 auto; padding: 8px; font-size: 11px; line-height: 1.4; }}
  .header {{ text-align: center; border-bottom: 1px dashed #333; padding-bottom: 6px; margin-bottom: 8px; }}
  .header h1 {{ font-size: 13px; margin: 0 0 2px; }}
  .header p {{ margin: 1px 0; font-size: 10px; color: #444; }}
  .section {{ margin: 6px 0; }}
  .section-title {{ font-weight: bold; font-size: 10px; text-transform: uppercase; border-bottom: 1px dotted #aaa; margin-bottom: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
  td {{ padding: 2px 0; vertical-align: top; }}
  .divider {{ border-top: 1px dashed #333; margin: 8px 0; }}
  .total {{ font-size: 14px; font-weight: bold; text-align: center; margin: 8px 0; }}
  .footer {{ text-align: center; font-size: 9px; color: #666; margin-top: 10px; border-top: 1px dashed #333; padding-top: 6px; }}
  @media print {{ body {{ margin: 0; width: 72mm; }} }}
</style>
</head><body>
<div class="header">
  <h1>{_t(nome_loja)}</h1>
  {f'<p>{_t(doc_line)}</p>' if doc_line else ''}
  {f'<p>{_t(ctx.get("loja_endereco"))}</p>' if ctx.get("loja_endereco") else ''}
  {f'<p>{_t(tel_cep)}</p>' if tel_cep else ''}
  {f'<p>{_t(ctx.get("loja_email"))}</p>' if ctx.get("loja_email") else ''}
  <p style="margin-top:4px;font-weight:bold">{titulo}</p>
  <p>Emitido em {_t(data_emissao)}</p>
</div>

<div class="section">
  <div class="section-title">Cliente</div>
  <table><tr><td>{_t(ctx.get("paciente_nome"))}</td></tr></table>
</div>

<div class="section">
  <div class="section-title">Profissional</div>
  <table><tr><td>{_t(ctx.get("profissional_nome") or "—")}</td></tr></table>
</div>

<div class="section">
  <div class="section-title">Data/Hora do atendimento</div>
  <table><tr><td>{_t(data_atend)}</td></tr></table>
</div>

<div class="section">
  <div class="section-title">Serviços</div>
  <table>
    {''.join(servicos)}
  </table>
</div>

<div class="divider"></div>
<table>
  {totais}
</table>

<div class="section">
  <div class="section-title">Formas de pagamento:</div>
  <table>
    {formas_html}
  </table>
</div>

<div class="total">VALOR PAGO: R$ {valor_pago:.2f}</div>
{saldo_bloco}

<div class="footer">
  {f'<p style="color:#333;margin-bottom:6px;">{_t(aviso)}</p>' if aviso else ''}
  <p>Agradecemos pela confiança!</p>
  <p>Documento não fiscal — gerado pelo sistema.</p>
  <button onclick="window.print()" style="margin-top:8px;padding:6px 16px;font-size:12px;cursor:pointer;border:1px solid #333;border-radius:4px;background:#fff;">Imprimir</button>
</div>
</body></html>"""


def gerar_html_recibo_do_payment(payment) -> str:
    """Carrega o mesmo contexto do PDF e devolve o cupom HTML."""
    appointment = payment.appointment
    if not appointment:
        raise ValueError("Pagamento sem agendamento vinculado.")
    try:
        from clinica_beleza.models import Appointment

        appointment = (
            Appointment.objects.select_related(
                "patient",
                "procedure",
                "professional",
                "local_atendimento",
                "convenio",
                "consulta",
                "consulta__local_atendimento",
                "consulta__convenio",
            )
            .prefetch_related("appointment_procedures__procedure")
            .get(pk=appointment.pk)
        )
    except Exception:
        pass
    patient = getattr(appointment, "patient", None)
    if not patient:
        raise ValueError("Paciente não encontrado no agendamento.")
    return gerar_html_recibo(_obter_dados_contexto(payment, patient, appointment))
