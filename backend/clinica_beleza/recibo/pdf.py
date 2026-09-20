"""Geração de PDF do recibo de pagamento."""
import io
import logging

from .context import (
    _linha_documento_loja,
    _linha_tel_cep,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
)

logger = logging.getLogger(__name__)

# Marca d'água da logo no recibo (cupom 80mm). Opacidade baixa para não competir
# com o texto; tamanho máximo ajustado à largura estreita do cupom.
_WM_OPACIDADE_RECIBO = 0.22
_WM_MAX_W_MM = 55
_WM_MAX_H_MM = 55

# Logo (imagem nítida) no rodapé do recibo — parte branca, aparece em todo recibo.
_LOGO_RODAPE_MAX_W_MM = 32
_LOGO_RODAPE_MAX_H_MM = 20


def _logo_rodape_recibo(logo_url: str, mm_unit):
    """Baixa a logo da loja e retorna um Image do reportlab para o rodapé, ou None."""
    if not logo_url:
        return None
    try:
        import requests as http_requests
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage

        resp = http_requests.get(logo_url, timeout=5)
        if resp.status_code != 200:
            return None
        raw = io.BytesIO(resp.content)
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


def _marca_dagua_bytes_recibo(logo_url: str) -> bytes | None:
    """Baixa a logo e aplica opacidade baixa para uso como marca d'água de fundo."""
    if not logo_url:
        return None
    try:
        import requests as http_requests
        from PIL import Image as PILImage

        resp = http_requests.get(logo_url, timeout=5)
        if resp.status_code != 200:
            return None
        pil_img = PILImage.open(io.BytesIO(resp.content)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * _WM_OPACIDADE_RECIBO))
        pil_img.putalpha(alpha)
        out_buf = io.BytesIO()
        pil_img.save(out_buf, format="PNG")
        return out_buf.getvalue()
    except Exception as e:
        logger.warning("Marca d'água do recibo indisponível: %s", e)
        return None


def _marca_dagua_flowable_base():
    """Classe Flowable que desenha a logo (marca d'água) abaixo do bloco de assinatura."""
    from reportlab.lib.pagesizes import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Flowable

    class _MarcaDaguaAssinaturaReciboImpl(Flowable):
        """Desenha a logo semitransparente ocupando a largura do cupom, sem empurrar o texto seguinte."""

        def __init__(self, wm_bytes: bytes):
            Flowable.__init__(self)
            self._wm_bytes = wm_bytes
            self.width = 0
            self.height = 0  # não ocupa altura no fluxo; desenha "atrás" do texto abaixo

        def draw(self):
            try:
                img = ImageReader(io.BytesIO(self._wm_bytes))
                iw, ih = img.getSize()
                if not iw or not ih:
                    return
                max_w = _WM_MAX_W_MM * mm
                max_h = _WM_MAX_H_MM * mm
                ratio = min(max_w / iw, max_h / ih)
                wm_w = iw * ratio
                wm_h = ih * ratio
                # Centralizada na largura do cupom; desenhada logo abaixo (para trás) do nome/CPF.
                avail = getattr(self, "_frame_width", 72 * mm) or 72 * mm
                x = (avail - wm_w) / 2
                self.canv.saveState()
                self.canv.drawImage(
                    img, x, -wm_h, width=wm_w, height=wm_h,
                    mask="auto", preserveAspectRatio=True,
                )
                self.canv.restoreState()
            except Exception as e:
                logger.warning("Falha ao desenhar marca d'água do recibo: %s", e)

        def wrap(self, avail_w, avail_h):
            self._frame_width = avail_w
            return (avail_w, 0)

    return _MarcaDaguaAssinaturaReciboImpl


_MarcaDaguaAssinaturaRecibo = _marca_dagua_flowable_base()


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
    story.append(Spacer(1, 3 * mm_unit))
    story.append(hr)
    story.append(Paragraph("RECIBO DE PAGAMENTO", s_title))
    story.append(Paragraph(f"Emitido em {ctx.get('data_emissao') or ctx['data']}", s_center))
    story.append(hr)

    story.append(Paragraph(f"<b>Cliente:</b> {ctx['paciente_nome']}", s_left))
    if ctx.get("paciente_cpf"):
        story.append(Paragraph(f"<b>CPF:</b> {ctx['paciente_cpf']}", s_left))
    if ctx["profissional_nome"]:
        story.append(Paragraph(f"<b>Profissional:</b> {ctx['profissional_nome']}", s_left))
    if ctx.get("data_atendimento"):
        story.append(Paragraph(f"<b>Data/Hora do atendimento:</b> {ctx['data_atendimento']}", s_left))
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
            Paragraph(label, s_left),
            Paragraph(f"R$ {valor:.2f}", s_right),
        ])
    for p in ctx["procedimentos"]:
        nome_lower = (p["nome"] or "").strip().lower()
        if taxa_exibida > 0 and float(p["valor"]) == 0.0 and nome_lower in ("consulta", "taxa de consulta"):
            continue
        svc_data.append([
            Paragraph(f'• {p["nome"]}', s_left),
            Paragraph(f'R$ {p["valor"]:.2f}', s_right),
        ])

    if not svc_data:
        return None
    svc_table = Table(svc_data, colWidths=[col_w * 0.65, col_w * 0.35])
    svc_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
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
            Paragraph(f'R$ {ctx.get("subtotal", ctx["valor_total"]):.2f}', s_right),
        ])
        for label, valor in descontos:
            totals_data.append([
                Paragraph(label, s_left),
                Paragraph(f"- R$ {valor:.2f}", s_right),
            ])
    totals_data.append([
        Paragraph("<b>Total</b>", s_bold),
        Paragraph(f'<b>R$ {ctx["valor_total"]:.2f}</b>', s_right),
    ])

    formas = ctx.get("formas_pagamento", [])
    valor_pago = ctx.get("valor_pago", 0)
    if formas:
        totals_data.append([Paragraph("<b>Formas de pagamento:</b>", s_bold), Paragraph("", s_right)])
        for f in formas:
            totals_data.append([
                Paragraph(f'  {f["metodo"]}', s_left),
                Paragraph(f'R$ {f["valor"]:.2f}', s_right),
            ])
    elif valor_pago > 0:
        metodo = ctx.get("metodo", "")
        totals_data.append([Paragraph(metodo, s_left), Paragraph(f'R$ {valor_pago:.2f}', s_right)])

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

    s_bold = styles["s_bold"]
    s_left = styles["s_left"]
    s_footer = styles["s_footer"]
    hr = styles["hr"]

    story = [Spacer(1, 2 * mm_unit), hr, Paragraph("<b>ASSINATURA DIGITAL</b>", s_bold), Spacer(1, 1 * mm_unit)]
    nome = (assinatura.get("nome") or ctx.get("paciente_nome") or "").strip().upper() or "—"
    story.append(Paragraph(f"Cliente: {nome}", s_left))
    cpf = (assinatura.get("cpf") or ctx.get("paciente_cpf") or "").strip()
    if cpf:
        story.append(Paragraph(f"CPF: {cpf}", s_left))

    # Marca d'água da logo logo abaixo do nome e do CPF (mesma ideia do termo de consentimento).
    wm_bytes = _marca_dagua_bytes_recibo((ctx.get("logo_url") or "").strip())
    if wm_bytes:
        story.append(_MarcaDaguaAssinaturaRecibo(wm_bytes))

    if assinatura.get("email"):
        story.append(Paragraph(f"Email: {assinatura['email']}", s_footer))
    if assinatura.get("assinado_em"):
        story.append(Paragraph(f"Assinado em: {assinatura['assinado_em']}", s_footer))
    if assinatura.get("ip"):
        story.append(Paragraph(f"IP: {assinatura['ip']}", s_footer))
    story.append(Paragraph("Assinado digitalmente", s_footer))
    story.append(Spacer(1, 1 * mm_unit))
    story.append(Paragraph(
        "Este documento possui validade jurídica e contém a assinatura digital do cliente, "
        "com registro de data, hora e endereço IP.",
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
    saldo = ctx.get("saldo_devedor", max(ctx.get("valor_total", 0) - valor_pago, 0))
    vencimento = (ctx.get("vencimento") or "").strip()
    story.append(Paragraph(f"VALOR PAGO: R$ {valor_pago:.2f}", s_total))
    if saldo > 0.009:
        story.append(Spacer(1, 1 * mm_unit))
        saldo_txt = f"SALDO A PAGAR: R$ {saldo:.2f}"
        if vencimento:
            saldo_txt += f" — vencimento {vencimento}"
        story.append(Paragraph(saldo_txt, s_center))
    elif valor_pago >= ctx.get("valor_total", 0) and ctx.get("valor_total", 0) >= 0:
        story.append(Spacer(1, 1 * mm_unit))
        story.append(Paragraph("<b>Quitado</b>", s_center))
    story.append(Spacer(1, 2 * mm_unit))
    story.append(hr)

    aviso = (ctx.get("retorno_aviso") or "").strip()
    if aviso:
        story.append(Spacer(1, 2 * mm_unit))
        story.append(Paragraph(aviso, s_footer))

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


def _gerar_pdf_recibo(ctx: dict) -> bytes:
    """Gera PDF do recibo em formato cupom fiscal com layout profissional."""
    from reportlab.lib.pagesizes import mm
    from reportlab.platypus import SimpleDocTemplate, Spacer

    buf = io.BytesIO()
    page_w = 80 * mm
    page_h = 240 * mm
    doc = SimpleDocTemplate(
        buf, pagesize=(page_w, page_h),
        leftMargin=4 * mm, rightMargin=4 * mm,
        topMargin=6 * mm, bottomMargin=6 * mm,
    )

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

    doc.build(story)
    return buf.getvalue()
