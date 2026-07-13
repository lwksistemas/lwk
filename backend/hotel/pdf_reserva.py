"""Geração de PDF para Confirmação de Reserva de Hotel.
Inclui: dados do hotel, hóspede, quarto, datas, regras/termos e assinaturas digitais.
"""
import logging
from io import BytesIO

import pytz
import requests as http_requests
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)

AZUL = colors.HexColor("#0176d3")
VERDE = colors.HexColor("#10b981")


def _ts_local(dt):
    if not dt:
        return "—"
    tz = pytz.timezone("America/Sao_Paulo")
    return dt.astimezone(tz).strftime("%d/%m/%Y %H:%M:%S")


def _fmt_brl(valor):
    if not valor:
        return "R$ 0,00"
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _hotel_pdf_styles(styles):
    """Retorna dict de ParagraphStyle para o PDF de reserva."""
    return {
        "title": ParagraphStyle("Title2", parent=styles["Heading1"], fontSize=20, textColor=AZUL, alignment=TA_CENTER, spaceAfter=6),
        "subtitle": ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey, alignment=TA_CENTER),
        "section": ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, textColor=AZUL, spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=4),
        "footer": ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER),
        "titulo": ParagraphStyle("HTitle", parent=styles["Heading1"], fontSize=18, textColor=AZUL, alignment=TA_LEFT, spaceBefore=0, spaceAfter=0, leading=22),
        "subtitulo": ParagraphStyle("HSub", parent=styles["Normal"], fontSize=10, textColor=colors.grey, alignment=TA_LEFT),
        "aceite": ParagraphStyle("Aceite", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#555555"), leading=13),
    }


def _hotel_pdf_logo_endereco(loja):
    """Monta string de endereço da loja para uso no cabeçalho."""
    if not loja:
        return ""
    rua = ", ".join(p for p in [loja.logradouro, loja.numero] if p and str(p).strip())
    if getattr(loja, "complemento", "") and str(loja.complemento).strip():
        rua = f"{rua}, {loja.complemento.strip()}" if rua else loja.complemento.strip()
    cidade_uf = " - ".join(p for p in [loja.cidade, loja.uf] if p and str(p).strip())
    cep_str = f"CEP {loja.cep}" if getattr(loja, "cep", "") and str(loja.cep).strip() else ""
    parts = [rua, loja.bairro, cidade_uf, cep_str]
    return ", ".join(p for p in parts if p and str(p).strip())


def _hotel_pdf_cabecalho(reserva, st):
    """Monta cabeçalho com logo/nome do hotel. Retorna lista de elements."""
    from superadmin.models import Loja
    loja = Loja.objects.using("default").filter(id=reserva.loja_id).first()
    nome_hotel = loja.nome if loja else "Hotel"
    logo_url = ""
    if loja:
        logo_url = (getattr(loja, "login_logo", "") or "") or (getattr(loja, "logo", "") or "")
    elements = []
    if logo_url:
        try:
            resp = http_requests.get(logo_url, timeout=5)
            if resp.status_code == 200:
                max_w, max_h = 6 * cm, 3 * cm
                img_buf = BytesIO(resp.content)
                pil_img = PILImage.open(img_buf)
                iw, ih = pil_img.size
                aspect = ih / float(iw)
                if iw > ih:
                    w = min(max_w, iw)
                    h = w * aspect
                    if h > max_h:
                        h = max_h
                        w = h / aspect
                else:
                    h = min(max_h, ih)
                    w = h / aspect
                    if w > max_w:
                        w = max_w
                        h = w * aspect
                img_buf.seek(0)
                logo_img = Image(img_buf, width=w, height=h)
                endereco = _hotel_pdf_logo_endereco(loja)
                info_col = [Paragraph(nome_hotel, st["titulo"])]
                if endereco:
                    info_col.append(Paragraph(endereco, st["subtitulo"]))
                cab = Table([[logo_img, info_col]], colWidths=[w + 0.5 * cm, None])
                cab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                elements.append(cab)
                logo_url = logo_url  # keep truthy
        except Exception:
            logo_url = ""
    if not logo_url:
        styles = getSampleStyleSheet()
        elements.append(Paragraph(nome_hotel, ParagraphStyle("LN", parent=styles["Normal"], fontSize=16, alignment=TA_CENTER, textColor=AZUL, spaceAfter=2)))
        if loja:
            endereco = _hotel_pdf_logo_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, st["subtitle"]))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph("CONFIRMAÇÃO DE RESERVA", st["title"]))
    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _hotel_pdf_dados_reserva(reserva):
    """Monta tabela com dados da reserva. Retorna Table."""
    hospede = reserva.hospede
    quarto = reserva.quarto
    diarias = (reserva.data_checkout - reserva.data_checkin).days if reserva.data_checkin and reserva.data_checkout else 0
    col1, col2 = 5.5 * cm, 11 * cm
    rows = [
        ["Hóspede", hospede.nome if hospede else "—"],
        ["Documento", hospede.documento if hospede and hospede.documento else "—"],
        ["Email", hospede.email if hospede and hospede.email else "—"],
        ["Telefone", hospede.telefone if hospede and hospede.telefone else "—"],
        ["Quarto", f'{quarto.numero} — {quarto.nome or quarto.tipo or ""}' if quarto else "—"],
        ["Check-in", reserva.data_checkin.strftime("%d/%m/%Y") if reserva.data_checkin else "—"],
        ["Check-out", reserva.data_checkout.strftime("%d/%m/%Y") if reserva.data_checkout else "—"],
        ["Diárias", str(diarias)],
        ["Hóspedes", f"{reserva.adultos} adulto(s)" + (f", {reserva.criancas} criança(s)" if reserva.criancas else "")],
        ["Valor Diária", _fmt_brl(reserva.valor_diaria)],
        ["Valor Total", _fmt_brl(reserva.valor_total)],
    ]
    if reserva.canal:
        rows.append(["Canal", reserva.canal])
    t = Table(rows, colWidths=[col1, col2])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#444444")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _hotel_pdf_termos(reserva, st):
    """Monta seção de termos/regras do hotel. Retorna lista de elements ou []."""
    conteudo = reserva.conteudo_confirmacao or ""
    if not conteudo.strip():
        try:
            from .models import ReservaTemplate
            tpl = ReservaTemplate.objects.filter(loja_id=reserva.loja_id, is_padrao=True, ativo=True).first()
            if tpl:
                conteudo = tpl.conteudo or ""
        except Exception:
            pass
    if not conteudo.strip():
        return []
    els = [Spacer(1, 0.5 * cm), Paragraph("Regras e Termos do Hotel", st["section"])]
    for line in conteudo.split("\n"):
        stripped = line.strip()
        els.append(Spacer(1, 0.15 * cm) if not stripped else Paragraph(stripped, st["body"]))
    return els


def _hotel_pdf_politicas(reserva, st):
    """Monta seção de horários e políticas. Retorna lista de elements ou []."""
    try:
        from .models import ConfiguracaoHotel
        cfg = ConfiguracaoHotel.objects.filter(loja_id=reserva.loja_id).first()
        if not cfg:
            return []
        els = [Spacer(1, 0.5 * cm), Paragraph("Horários e Políticas", st["section"])]
        col1, col2 = 5.5 * cm, 11 * cm
        def fmt(t):
            return t.strftime("%H:%M") if t else "—"
        th = Table([["Check-in a partir de", fmt(cfg.horario_checkin)], ["Check-out até", fmt(cfg.horario_checkout)]], colWidths=[col1, col2])
        th.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10), ("ALIGN", (0, 0), (-1, -1), "LEFT"), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fa")), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
        els.append(th)
        styles = getSampleStyleSheet()
        subsec_style = ParagraphStyle("SubSec", parent=styles["Heading3"], fontSize=11, textColor=AZUL, spaceBefore=4, spaceAfter=4)
        if cfg.politica_cancelamento and cfg.politica_cancelamento.strip():
            els += [Spacer(1, 0.3 * cm), Paragraph("Política de Cancelamento", subsec_style)]
            els += [Paragraph(linha.strip(), st["body"]) for linha in cfg.politica_cancelamento.split("\n") if linha.strip()]
        if cfg.informacoes_adicionais and cfg.informacoes_adicionais.strip():
            els += [Spacer(1, 0.3 * cm), Paragraph("Informações Adicionais", ParagraphStyle("SubSec2", parent=styles["Heading3"], fontSize=11, textColor=AZUL, spaceBefore=4, spaceAfter=4))]
            els += [Paragraph(linha.strip(), st["body"]) for linha in cfg.informacoes_adicionais.split("\n") if linha.strip()]
        return els
    except Exception:
        return []


def _hotel_pdf_assinaturas(reserva, st):
    """Monta seção de assinaturas digitais. Retorna lista de elements ou []."""
    from .models import ReservaAssinatura
    assinaturas = ReservaAssinatura.objects.filter(reserva=reserva, assinado=True).order_by("tipo")
    if not assinaturas.exists():
        return []
    col1, col2 = 5.5 * cm, 11 * cm
    els = [Spacer(1, 0.6 * cm), Paragraph("Assinaturas Digitais", st["section"])]
    for a in assinaturas:
        tipo_label = "HÓSPEDE" if a.tipo == "hospede" else "FUNCIONÁRIO DO HOTEL"
        ta = Table([[f"Assinatura Digital — {tipo_label}", ""], ["Nome", a.nome_assinante], ["Email", a.email_assinante], ["Data/Hora", _ts_local(a.assinado_em)], ["Endereço IP", a.ip_address or "—"]], colWidths=[col1, col2])
        ta.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), VERDE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")), ("SPAN", (0, 0), (-1, 0)), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f0fdf4"))]))
        els.append(ta)
        els.append(Spacer(1, 0.3 * cm))
    return els


def gerar_pdf_reserva(reserva, incluir_assinaturas: bool = False) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    st = _hotel_pdf_styles(styles)

    elements = _hotel_pdf_cabecalho(reserva, st)
    elements.append(Paragraph("Dados da Reserva", st["section"]))
    elements.append(_hotel_pdf_dados_reserva(reserva))
    elements.extend(_hotel_pdf_termos(reserva, st))
    elements.extend(_hotel_pdf_politicas(reserva, st))

    if reserva.observacoes and reserva.observacoes.strip():
        elements += [Spacer(1, 0.4 * cm), Paragraph("Observações", st["section"]), Paragraph(reserva.observacoes, st["body"])]

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(
        "Ao assinar digitalmente este documento, o hóspede declara ter lido e aceito "
        "todas as regras, termos e condições do hotel, bem como os dados da reserva informados.",
        st["aceite"],
    ))

    if incluir_assinaturas:
        elements.extend(_hotel_pdf_assinaturas(reserva, st))

    from django.utils import timezone as tz
    elements += [
        Spacer(1, 1 * cm),
        Paragraph("Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de data, hora e endereço IP.", st["footer"]),
        Paragraph(f'Gerado em {tz.now().strftime("%d/%m/%Y às %H:%M")}', st["footer"]),
    ]

    doc.build(elements)
    buf.seek(0)
    return buf
