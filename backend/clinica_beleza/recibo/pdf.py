"""Geração de PDF do recibo de pagamento."""
import html
import io
import logging

from .context import (
    _linha_documento_loja,
    _linha_tel_cep,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
    linhas_local_convenio_recibo,
    recebido_a_maior_recibo,
    reconciliar_conta_recibo,
    situacao_recibo,
    titulo_recibo,
)
from .moeda import formatar_moeda_recibo

logger = logging.getLogger(__name__)


def _texto_pdf(valor) -> str:
    """Texto de cadastro no Paragraph do ReportLab (sem interpretar tags)."""
    return html.escape(str(valor or ""), quote=True)


def logo_url_permitida_para_download(logo_url: str) -> bool:
    """Só baixa logo do servidor de mídia da loja (anti-SSRF)."""
    from clinica_beleza.pdf_common.logo import logo_url_permitida

    return logo_url_permitida(logo_url)


def _saldo_devedor_recibo(ctx: dict) -> float:
    """Saldo em aberto do recibo (a prazo ou pagamento parcial).

    Usa 'saldo_devedor' quando presente; senão, deriva de valor_total - valor_pago.
    """
    valor_pago = ctx.get("valor_pago", 0) or 0
    valor_total = ctx.get("valor_total", 0) or 0
    return ctx.get("saldo_devedor", max(valor_total - valor_pago, 0))


# Logo (imagem nítida) no rodapé do recibo — parte branca, aparece em todo recibo.
_LOGO_RODAPE_MAX_W_MM = 48
_LOGO_RODAPE_MAX_H_MM = 30


def _logo_rodape_recibo(logo_url: str, mm_unit):
    """Baixa a logo da loja e retorna um Image do reportlab para o rodapé, ou None."""
    if not logo_url:
        return None
    if not logo_url_permitida_para_download(logo_url):
        logger.warning("Logo do recibo recusada (URL fora da mídia)")
        return None
    try:
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage

        from clinica_beleza.pdf_common.logo import baixar_logo

        conteudo = baixar_logo(logo_url, timeout=5)
        if not conteudo:
            return None
        raw = io.BytesIO(conteudo)
        pil = PILImage.open(raw)
        iw, ih = pil.size
        if not iw or not ih:
            return None
        max_w = _LOGO_RODAPE_MAX_W_MM * mm_unit
        max_h = _LOGO_RODAPE_MAX_H_MM * mm_unit
        ratio = min(max_w / iw, max_h / ih)
        raw.seek(0)
        img = RLImage(raw, width=iw * ratio, height=ih * ratio)
        img.hAlign = "CENTER"
        return img
    except Exception as e:
        logger.warning("Logo do rodapé do recibo indisponível: %s", e)
        return None


def _estilos_pdf():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import HRFlowable

    return {
        "s_center": ParagraphStyle("c", fontSize=8, alignment=TA_CENTER, leading=11),
        "s_bold_center": ParagraphStyle("bc", fontSize=11, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=14),
        "s_title": ParagraphStyle("ti", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12),
        "s_left": ParagraphStyle("l", fontSize=8, leading=11),
        "s_bold": ParagraphStyle("b", fontSize=8, fontName="Helvetica-Bold", leading=11),
        "s_total": ParagraphStyle("t", fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=15),
        "s_footer": ParagraphStyle(
            "f", fontSize=7, alignment=TA_CENTER, leading=10, textColor=colors.HexColor("#666666"),
        ),
        "s_aviso": ParagraphStyle(
            "aviso", fontSize=9, alignment=TA_CENTER, leading=12, textColor=colors.HexColor("#333333"),
        ),
        "s_right": ParagraphStyle("r", fontSize=8, alignment=TA_RIGHT, leading=11),
        "hr": HRFlowable(width="100%", thickness=0.5, dash=[2, 2], spaceAfter=3, spaceBefore=3),
    }


def _cabecalho_recibo_pdf(ctx, styles, col_w, mm_unit):
    from reportlab.platypus import Paragraph, Spacer

    s_center = styles["s_center"]
    s_bold_center = styles["s_bold_center"]
    s_title = styles["s_title"]
    s_left = styles["s_left"]
    s_bold = styles["s_bold"]
    hr = styles["hr"]
    story = []

    if ctx["loja_nome"]:
        story.append(Paragraph(_texto_pdf(ctx["loja_nome"].upper()), s_bold_center))
    doc_line = _linha_documento_loja(ctx)
    if doc_line:
        story.append(Paragraph(_texto_pdf(doc_line), s_center))
    if ctx["loja_endereco"]:
        story.append(Paragraph(_texto_pdf(ctx["loja_endereco"]), s_center))
    tel_cep = ctx.get("loja_tel_cep") or _linha_tel_cep(ctx.get("loja_telefone", ""), ctx.get("loja_cep", ""))
    if tel_cep:
        story.append(Paragraph(_texto_pdf(tel_cep), s_center))
    if ctx.get("loja_email"):
        story.append(Paragraph(_texto_pdf(ctx["loja_email"]), s_center))
    story.append(Spacer(1, 3 * mm_unit))
    story.append(hr)
    titulo_doc, subtitulo_doc = titulo_recibo(ctx)
    story.append(Paragraph(titulo_doc, s_title))
    if subtitulo_doc:
        story.append(Paragraph(_texto_pdf(subtitulo_doc), s_center))
    story.append(Paragraph(f"Emitido em {_texto_pdf(ctx.get('data_emissao') or ctx['data'])}", s_center))
    numero = ctx.get("recibo_numero")
    if numero:
        story.append(Paragraph(f"Recibo nº {_texto_pdf(numero)}", s_center))
    story.append(hr)

    story.append(Paragraph(f"<b>Cliente:</b> {_texto_pdf(ctx['paciente_nome'])}", s_left))
    if ctx.get("paciente_cpf"):
        story.append(Paragraph(f"<b>CPF:</b> {_texto_pdf(ctx['paciente_cpf'])}", s_left))
    if ctx["profissional_nome"]:
        story.append(Paragraph(f"<b>Profissional:</b> {_texto_pdf(ctx['profissional_nome'])}", s_left))
    if ctx.get("data_atendimento"):
        story.append(Paragraph(f"<b>Data/Hora do atendimento:</b> {_texto_pdf(ctx['data_atendimento'])}", s_left))
    story.append(hr)
    story.append(Paragraph("<b>SERVIÇOS</b>", s_bold))
    story.append(Spacer(1, 1 * mm_unit))
    return story


def _tabela_servicos_recibo_pdf(ctx, styles, col_w):
    from reportlab.platypus import Paragraph, Table, TableStyle

    s_left = styles["s_left"]
    s_right = styles["s_right"]

    svc_data = []
    linhas_taxa = _linhas_taxa_consulta_recibo(ctx)
    taxa_exibida = linhas_taxa[0][1] if linhas_taxa else 0.0
    for label, valor in linhas_taxa:
        svc_data.append([
            Paragraph(_texto_pdf(label), s_left),
            Paragraph(formatar_moeda_recibo(valor), s_right),
        ])
    for p in ctx["procedimentos"]:
        nome_lower = (p["nome"] or "").strip().lower()
        if taxa_exibida > 0 and float(p["valor"]) == 0.0 and nome_lower in ("consulta", "taxa de consulta"):
            continue
        svc_data.append([
            Paragraph(f'• {_texto_pdf(p["nome"])}', s_left),
            Paragraph(formatar_moeda_recibo(p["valor"]), s_right),
        ])
    spans = []
    for label, valor in linhas_local_convenio_recibo(ctx):
        row = len(svc_data)
        svc_data.append([
            Paragraph(f"{_texto_pdf(label)} {_texto_pdf(valor)}", s_left),
            Paragraph("", s_right),
        ])
        spans.append(("SPAN", (0, row), (-1, row)))

    if not svc_data:
        return None
    svc_table = Table(svc_data, colWidths=[col_w * 0.65, col_w * 0.35])
    svc_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        *spans,
    ]))
    return svc_table


def _tabela_totais_recibo_pdf(ctx, styles, col_w):
    from reportlab.platypus import Paragraph, Table, TableStyle

    s_left = styles["s_left"]
    s_bold = styles["s_bold"]
    s_right = styles["s_right"]

    totals_data = []
    descontos = _linhas_descontos_recibo(ctx)
    if descontos:
        totals_data.append([
            Paragraph("Subtotal", s_left),
            Paragraph(formatar_moeda_recibo(ctx.get("subtotal", ctx["valor_total"])), s_right),
        ])
        for label, valor in descontos:
            totals_data.append([
                Paragraph(_texto_pdf(label), s_left),
                Paragraph(f"- {formatar_moeda_recibo(valor)}", s_right),
            ])
    totals_data.append([
        Paragraph("<b>Total</b>", s_bold),
        Paragraph(f"<b>{formatar_moeda_recibo(ctx['valor_total'])}</b>", s_right),
    ])

    formas = [
        f for f in (ctx.get("formas_pagamento") or [])
        if float(f.get("valor") or 0) > 0.009
    ]
    valor_pago = ctx.get("valor_pago", 0)
    if formas:
        totals_data.append([Paragraph("<b>Formas de pagamento:</b>", s_bold), Paragraph("", s_right)])
        for f in formas:
            totals_data.append([
                Paragraph(f'  {_texto_pdf(f["metodo"])}', s_left),
                Paragraph(formatar_moeda_recibo(f["valor"]), s_right),
            ])
    elif valor_pago > 0:
        metodo = ctx.get("metodo", "")
        totals_data.append([Paragraph(_texto_pdf(metodo), s_left), Paragraph(formatar_moeda_recibo(valor_pago), s_right)])
    extra = recebido_a_maior_recibo(ctx)
    if extra > 0.009:
        totals_data.append([
            Paragraph("Recebido a maior", s_left),
            Paragraph(formatar_moeda_recibo(extra), s_right),
        ])

    totals_table = Table(totals_data, colWidths=[col_w * 0.55, col_w * 0.45])
    totals_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return totals_table


def _secao_assinatura_recibo_pdf(ctx, styles, mm_unit):
    """Bloco de assinatura digital do recibo (paciente), com valor jurídico.

    Só é incluído quando o ctx traz 'assinatura_recibo' (dict com nome/ip/assinado_em/email).
    """
    from reportlab.platypus import Paragraph, Spacer

    assinatura = ctx.get("assinatura_recibo") or {}
    if not assinatura:
        return []

    s_title = styles["s_title"]
    s_center = styles["s_center"]
    s_footer = styles["s_footer"]
    hr = styles["hr"]

    # Título e dados do cliente centralizados para alinhar todo o bloco de assinatura.
    story = [Spacer(1, 2 * mm_unit), hr, Paragraph("ACEITE DO CLIENTE", s_title), Spacer(1, 1 * mm_unit)]
    nome = (assinatura.get("nome") or ctx.get("paciente_nome") or "").strip().upper() or "—"
    # Nome e CPF centralizados para alinhar com o restante do bloco (email/IP/data e texto jurídico).
    story.append(Paragraph(f"<b>Cliente:</b> {_texto_pdf(nome)}", s_center))
    cpf = (assinatura.get("cpf") or ctx.get("paciente_cpf") or "").strip()
    if cpf:
        story.append(Paragraph(f"<b>CPF:</b> {_texto_pdf(cpf)}", s_center))

    # Declaração de reconhecimento de dívida — só quando há saldo em aberto
    # (pagamento a prazo ou parcial). Dá força ao documento como base de cobrança.
    saldo = _saldo_devedor_recibo(ctx)
    if saldo > 0.009:
        vencimento = (ctx.get("vencimento") or "").strip()
        if vencimento:
            declaracao = (
                f"Declaro que recebi o(s) serviço(s)/atendimento(s) descrito(s) acima e "
                f"reconheço o saldo devedor de {formatar_moeda_recibo(saldo)}, "
                f"com vencimento em {_texto_pdf(vencimento)}."
            )
        else:
            declaracao = (
                f"Declaro que recebi o(s) serviço(s)/atendimento(s) descrito(s) acima e "
                f"reconheço o saldo devedor de {formatar_moeda_recibo(saldo)}."
            )
        story.append(Spacer(1, 1 * mm_unit))
        story.append(Paragraph(declaracao, s_footer))
        story.append(Spacer(1, 1 * mm_unit))
    elif assinatura.get("assinado_em"):
        story.append(Spacer(1, 1 * mm_unit))
        story.append(Paragraph(
            f"Aceite do saldo em aberto registrado em {_texto_pdf(assinatura['assinado_em'])}. "
            "Não confirma pagamentos feitos depois deste registro.",
            s_footer,
        ))
        story.append(Spacer(1, 1 * mm_unit))

    if assinatura.get("email"):
        story.append(Paragraph(f"Email: {_texto_pdf(assinatura['email'])}", s_footer))
    if assinatura.get("assinado_em"):
        story.append(Paragraph(
            f"Aceite registrado em: {_texto_pdf(assinatura['assinado_em'])}",
            s_footer,
        ))
    if assinatura.get("ip"):
        story.append(Paragraph(f"IP: {_texto_pdf(assinatura['ip'])}", s_footer))
    story.append(Spacer(1, 1 * mm_unit))
    story.append(Paragraph(
        "Registro do aceite do cliente: nome, data, hora e endereço IP.",
        s_footer,
    ))
    return story


def _rodape_recibo_pdf(ctx, styles, mm_unit):
    from reportlab.platypus import Paragraph, Spacer

    s_total = styles["s_total"]
    s_center = styles["s_center"]
    s_footer = styles["s_footer"]
    hr = styles["hr"]

    story = []
    valor_pago = ctx.get("valor_pago", 0)
    saldo = _saldo_devedor_recibo(ctx)
    vencimento = (ctx.get("vencimento") or "").strip()
    situacao = situacao_recibo(ctx)
    condicao = (ctx.get("condicao_cobranca") or "").strip()
    if condicao and not ctx.get("formas_pagamento"):
        story.append(Paragraph(f"Condição de cobrança: {_texto_pdf(condicao)}", s_center))
        story.append(Spacer(1, 1 * mm_unit))
    if situacao == "sem_saldo":
        _, subtitulo = titulo_recibo(ctx)
        story.append(Paragraph(f"<b>{_texto_pdf(subtitulo)}</b>", s_center))
    else:
        rotulo_pago = "PAGO" if situacao == "parcial" else "VALOR PAGO"
        story.append(Paragraph(f"{rotulo_pago}: {formatar_moeda_recibo(valor_pago)}", s_total))
        if saldo > 0.009:
            story.append(Spacer(1, 1 * mm_unit))
            saldo_txt = f"SALDO A PAGAR: {formatar_moeda_recibo(saldo)}"
            if vencimento:
                saldo_txt += f" — vencimento {_texto_pdf(vencimento)}"
            story.append(Paragraph(saldo_txt, s_center))
        elif situacao == "quitado":
            story.append(Spacer(1, 1 * mm_unit))
            story.append(Paragraph("<b>Quitado</b>", s_center))
    story.append(Spacer(1, 2 * mm_unit))
    story.append(hr)

    aviso = (ctx.get("retorno_aviso") or "").strip()
    if aviso:
        story.append(Spacer(1, 2 * mm_unit))
        story.append(Paragraph(_texto_pdf(aviso), styles["s_aviso"]))

    story.extend(_secao_assinatura_recibo_pdf(ctx, styles, mm_unit))

    story.append(Spacer(1, 2 * mm_unit))
    story.append(Paragraph("Agradecemos pela confiança!", s_footer))
    story.append(Paragraph("Documento não fiscal — gerado pelo sistema.", s_footer))

    # Logo da clínica no rodapé (parte branca) — aparece em todo recibo, com ou sem assinatura.
    logo = _logo_rodape_recibo((ctx.get("logo_url") or "").strip(), mm_unit)
    if logo is not None:
        story.append(Spacer(1, 3 * mm_unit))
        story.append(logo)
    return story


def _recortar_pdf_apos_conteudo(pdf_bytes: bytes, y_conteudo: float | None, mm_unit) -> bytes:
    """Corta a folha alta logo abaixo da logomarca, sem faixa branca no fim."""
    if y_conteudo is None:
        return pdf_bytes
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(pdf_bytes))
    if not reader.pages:
        return pdf_bytes
    page = reader.pages[0]
    llx, _lly, urx, ury = (float(v) for v in page.mediabox)
    corte = max(0.0, float(y_conteudo) - 3 * mm_unit)
    if corte >= ury - 20 * mm_unit:
        return pdf_bytes
    page.mediabox.lower_left = (llx, corte)
    page.mediabox.upper_right = (urx, ury)
    page.cropbox.lower_left = (llx, corte)
    page.cropbox.upper_right = (urx, ury)
    writer = PdfWriter()
    writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _gerar_pdf_recibo(ctx: dict) -> bytes:
    """Gera PDF do recibo em formato cupom fiscal com layout profissional."""
    ctx = reconciliar_conta_recibo(ctx)
    from reportlab.lib.pagesizes import mm
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Spacer

    class _ReciboDoc(BaseDocTemplate):
        def __init__(self, buffer, pagesize):
            super().__init__(
                buffer,
                pagesize=pagesize,
                leftMargin=4 * mm,
                rightMargin=4 * mm,
                topMargin=6 * mm,
                bottomMargin=6 * mm,
            )
            self.y_conteudo = None
            frame = Frame(
                self.leftMargin,
                self.bottomMargin,
                self.width,
                self.height,
                id="recibo",
                showBoundary=0,
            )
            self.addPageTemplates([PageTemplate(id="recibo", frames=[frame])])

        def afterFlowable(self, flowable):
            self.y_conteudo = self.frame._y

    buf = io.BytesIO()
    page_w = 80 * mm
    # Folha alta de uma página só; o corte final tira o branco depois da logo.
    page_h = 900 * mm
    styles = _estilos_pdf()
    col_w = page_w - 8 * mm
    story = _cabecalho_recibo_pdf(ctx, styles, col_w, mm)

    svc_table = _tabela_servicos_recibo_pdf(ctx, styles, col_w)
    if svc_table:
        story.append(svc_table)

    story.append(styles["hr"])
    story.append(_tabela_totais_recibo_pdf(ctx, styles, col_w))
    story.append(Spacer(1, 3 * mm))
    story.extend(_rodape_recibo_pdf(ctx, styles, mm))

    doc = _ReciboDoc(buf, pagesize=(page_w, page_h))
    doc.build(story)
    return _recortar_pdf_apos_conteudo(buf.getvalue(), doc.y_conteudo, mm)
