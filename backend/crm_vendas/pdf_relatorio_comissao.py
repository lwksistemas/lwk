"""Geração de PDF do Relatório de Comissão com área de assinatura.
"""
import logging
from io import BytesIO

import requests
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)

_AZUL = colors.HexColor("#0176d3")
_CINZA = colors.HexColor("#f3f4f6")
_CINZA_ESCURO = colors.HexColor("#6b7280")
_VERDE = colors.HexColor("#059669")
_VERMELHO = colors.HexColor("#dc2626")


def _fmt_brl(valor) -> str:
    v = float(valor or 0)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_data(d) -> str:
    """Formata data/datetime para exibição no fuso de Brasília (UTC-3)."""
    if not d:
        return "—"
    if hasattr(d, "strftime"):
        if hasattr(d, "hour"):
            # Converter UTC → Brasília (UTC-3)
            try:
                import pytz
                tz_brasilia = pytz.timezone("America/Sao_Paulo")
                if d.tzinfo is not None:
                    d_local = d.astimezone(tz_brasilia)
                else:
                    # Sem tzinfo: assumir UTC e converter
                    import pytz as _pytz
                    d_local = _pytz.utc.localize(d).astimezone(tz_brasilia)
                return d_local.strftime("%d/%m/%Y %H:%M")
            except Exception:
                # Fallback: subtrair 3h manualmente
                from datetime import timedelta
                d_local = d - timedelta(hours=3)
                return d_local.strftime("%d/%m/%Y %H:%M")
        return d.strftime("%d/%m/%Y")
    return str(d)


def _build_pdf_styles(styles):
    """Retorna dict com todos os ParagraphStyle usados no PDF."""
    titulo = ParagraphStyle("RCTitulo", parent=styles["Heading1"], fontSize=16, textColor=_AZUL, alignment=TA_CENTER, spaceBefore=0, spaceAfter=6)
    secao = ParagraphStyle("RCSecao", parent=styles["Heading2"], fontSize=11, textColor=_AZUL, spaceBefore=12, spaceAfter=4)
    info = ParagraphStyle("RCInfo", parent=styles["Normal"], fontSize=9, spaceBefore=0, spaceAfter=2, leading=13)
    rodape = ParagraphStyle("RCRodape", parent=styles["Normal"], fontSize=7, textColor=_CINZA_ESCURO, alignment=TA_CENTER)
    ParagraphStyle("RCAssinLabel", parent=styles["Normal"], fontSize=8, textColor=_CINZA_ESCURO, alignment=TA_CENTER)
    assin_nome = ParagraphStyle("RCAssinNome", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER, spaceBefore=2)
    card = ParagraphStyle("RCCard", parent=styles["Normal"], fontSize=8.5, spaceBefore=0, spaceAfter=1, leading=12)
    card_email = ParagraphStyle("RCCardEmail", parent=styles["Normal"], fontSize=7.5, spaceBefore=0, spaceAfter=1, leading=11)
    card_title = ParagraphStyle("RCCardTitle", parent=styles["Normal"], fontSize=9, textColor=_AZUL, spaceBefore=0, spaceAfter=3, leading=12)
    return {"titulo": titulo, "secao": secao, "info": info, "rodape": rodape, "assin_nome": assin_nome, "card": card, "card_email": card_email, "card_title": card_title}


def _build_pdf_cabecalho(loja, titulo_style):
    """Retorna lista de elements para cabeçalho com logo + título."""
    elements = []
    logo_url = getattr(loja, "logo", "") or None
    if logo_url:
        try:
            resp = requests.get(logo_url, timeout=5)
            if resp.status_code == 200:
                img_buffer = BytesIO(resp.content)
                pil_img = PILImage.open(img_buffer)
                iw, ih = pil_img.size
                aspect = ih / float(iw)
                max_w, max_h = 6 * cm, 3 * cm
                width = min(max_w, iw)
                height = width * aspect
                if height > max_h:
                    height = max_h
                    width = height / aspect
                img_buffer.seek(0)
                img = Image(img_buffer, width=width, height=height)
                ht = Table([[img, Paragraph("RELATÓRIO DE COMISSÃO", titulo_style)]], colWidths=[width + 0.5 * cm, None])
                ht.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                elements.append(ht)
            else:
                elements.append(Paragraph("RELATÓRIO DE COMISSÃO", titulo_style))
        except Exception:
            elements.append(Paragraph("RELATÓRIO DE COMISSÃO", titulo_style))
    else:
        elements.append(Paragraph("RELATÓRIO DE COMISSÃO", titulo_style))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=_AZUL))
    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _build_pdf_vendedor(relatorio, loja):
    """Resolve o vendedor do relatório com fallback para VendedorUsuario."""
    v = relatorio.vendedor or getattr(relatorio.empresa_prestadora, "vendedor", None)
    if not v and getattr(loja, "owner", None):
        try:
            from superadmin.models import VendedorUsuario

            from .models import Vendedor
            vu = VendedorUsuario.objects.using("default").filter(user=loja.owner, loja=loja).first()
            if vu:
                v = Vendedor.objects.filter(id=vu.vendedor_id, loja_id=loja.id).first()
        except Exception:
            pass
    return v


def _build_pdf_cards(relatorio, loja, st):
    """Monta tabela com cards de Prestador, Contratante e Vendedor."""
    v = _build_pdf_vendedor(relatorio, loja)
    card_style, card_email_style, card_title_style = st["card"], st["card_email"], st["card_title"]
    prestador_lines = [Paragraph("<b>Prestador de Serviços</b>", card_title_style), Paragraph(f'{loja.nome or "—"}'  , card_style)]
    if getattr(loja, "cpf_cnpj", ""):
        prestador_lines.append(Paragraph(f'<font color="#6b7280">CNPJ:</font> {loja.cpf_cnpj}', card_style))
    prestador_email = getattr(loja, "owner", None) and getattr(loja.owner, "email", "")
    if prestador_email:
        prestador_lines.append(Paragraph(f"{prestador_email}", card_email_style))
    ep = relatorio.empresa_prestadora
    contratante_lines = [Paragraph("<b>Empresa Contratante</b>", card_title_style), Paragraph(f'{ep.nome or "—"}'  , card_style)]
    if ep.cnpj:
        contratante_lines.append(Paragraph(f'<font color="#6b7280">CNPJ:</font> {ep.cnpj}', card_style))
    if ep.email:
        contratante_lines.append(Paragraph(f"{ep.email}", card_email_style))
    vendedor_lines = []
    if v:
        vendedor_lines = [Paragraph("<b>Vendedor Responsável</b>", card_title_style), Paragraph(f"{v.nome}", card_style)]
        if v.email:
            vendedor_lines.append(Paragraph(f"{v.email}", card_email_style))
    ct = Table([[prestador_lines, contratante_lines, vendedor_lines]], colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    ct.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#d1d5db")), ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#d1d5db")), ("BOX", (2, 0), (2, 0), 0.5, colors.HexColor("#d1d5db")),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f9fafb")), ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f9fafb")), ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#f9fafb")),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return ct, v


def _build_pdf_resumo(relatorio):
    """Monta tabela de Resumo Financeiro."""
    resumo_data = [
        ["Descrição", "Valor"],
        ["Quantidade de Vendas", str(relatorio.quantidade_vendas)],
        ["Total de Vendas", _fmt_brl(relatorio.valor_total_vendas)],
        ["Total de Comissão", _fmt_brl(relatorio.valor_total_comissao)],
    ]
    t = Table(resumo_data, colWidths=[10 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("BACKGROUND", (0, 1), (-1, -1), _CINZA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CINZA]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("TEXTCOLOR", (1, -1), (1, -1), _VERDE),
    ]))
    return t


def _build_pdf_detalhamento(relatorio, secao_style):
    """Monta seção de detalhamento das vendas. Retorna lista de elements ou []."""
    oportunidades = relatorio.dados_oportunidades or []
    if not oportunidades:
        return []
    det_data = [["Data", "Cliente", "Valor Venda", "Comissão"]]
    for op in oportunidades:
        det_data.append([op.get("data", "—"), (op.get("cliente", "—") or "—")[:35], _fmt_brl(op.get("valor", 0)), _fmt_brl(op.get("comissao", 0))])
    t = Table(det_data, colWidths=[2.5 * cm, 7 * cm, 3.5 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CINZA]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [Paragraph("<b>Detalhamento das Vendas</b>", secao_style), t, Spacer(1, 0.4 * cm)]


def _build_pdf_assinaturas(relatorio, loja, v, st, incluir_assinaturas):
    """Monta bloco de assinaturas (realizadas ou em branco)."""
    elements = []
    ep = relatorio.empresa_prestadora
    if incluir_assinaturas:
        elements += [HRFlowable(width="100%", thickness=0.5, color=_CINZA_ESCURO), Spacer(1, 0.3 * cm), Paragraph("<b>Registro de Assinaturas Digitais</b>", st["secao"])]
        assin_rows = []
        if relatorio.empresa_aprovado_em:
            assin_rows.append(["Empresa Contratante", relatorio.empresa_aprovado_nome or ep.nome, _fmt_data(relatorio.empresa_aprovado_em), relatorio.empresa_aprovado_ip or "—", "Aprovado ✓"])
        elif relatorio.empresa_reprovado_em:
            assin_rows.append(["Empresa Contratante", ep.nome, _fmt_data(relatorio.empresa_reprovado_em), "—", "Reprovado ✗"])
        if relatorio.vendedor_assinado_em:
            vendedor_assin_nome = relatorio.vendedor_assinado_nome
            if v and (not vendedor_assin_nome or vendedor_assin_nome == "—" or vendedor_assin_nome == loja.nome):
                vendedor_assin_nome = v.nome
            elif not vendedor_assin_nome:
                vendedor_assin_nome = "—"
            assin_rows.append(["Vendedor", vendedor_assin_nome, _fmt_data(relatorio.vendedor_assinado_em), relatorio.vendedor_assinado_ip or "—", "Assinado ✓"])
        if assin_rows:
            ta = Table([["Parte", "Nome", "Data/Hora", "IP", "Status"]] + assin_rows, colWidths=[3 * cm, 5 * cm, 3 * cm, 3.5 * cm, 2.5 * cm])
            ta.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CINZA]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(ta)
        elements.append(Spacer(1, 0.4 * cm))
    else:
        nome_vendedor_assin = v.nome if v else "Vendedor"
        linha_assin = "_" * 45
        assin_table_data = [[Paragraph(f'{linha_assin}<br/><br/><b>{ep.nome}</b><br/><font size="8" color="grey">Empresa Contratante</font>', st["assin_nome"]), Paragraph(f'{linha_assin}<br/><br/><b>{nome_vendedor_assin}</b><br/><font size="8" color="grey">Vendedor Responsável</font>', st["assin_nome"])]]
        ta = Table(assin_table_data, colWidths=[8 * cm, 8 * cm])
        ta.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        elements += [
            Spacer(1, 0.5 * cm), HRFlowable(width="100%", thickness=0.5, color=_CINZA_ESCURO),
            Spacer(1, 0.3 * cm), Paragraph("<b>Assinaturas</b>", st["secao"]), Spacer(1, 0.2 * cm),
            ta, Spacer(1, 0.3 * cm),
            Paragraph("Data: _____ / _____ / _________", ParagraphStyle("data", parent=getSampleStyleSheet()["Normal"], fontSize=9, alignment=TA_CENTER)),
        ]
    return elements


def _build_pdf_rodape(relatorio, rodape_style):
    """Monta rodapé com data de geração e número do relatório."""
    from django.utils import timezone
    try:
        import pytz
        agora_brasilia = timezone.now().astimezone(pytz.timezone("America/Sao_Paulo"))
    except Exception:
        from datetime import timedelta
        agora_brasilia = timezone.now() - timedelta(hours=3)
    return Paragraph(f'Documento gerado em {agora_brasilia.strftime("%d/%m/%Y às %H:%M")} | Nº {relatorio.numero} | LWK Sistemas', rodape_style)


def gerar_pdf_relatorio_comissao(relatorio, loja, incluir_assinaturas: bool = False) -> BytesIO:
    """Gera PDF do relatório de comissão.

    Args:
        relatorio: instância de RelatorioComissao
        loja: instância de Loja (prestador)
        incluir_assinaturas: se True, inclui bloco com dados das assinaturas já realizadas

    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    st = _build_pdf_styles(styles)

    elements = _build_pdf_cabecalho(loja, st["titulo"])

    card_table, v = _build_pdf_cards(relatorio, loja, st)
    elements.append(card_table)
    elements.append(Spacer(1, 0.4 * cm))

    elements.append(Paragraph("<b>Resumo Financeiro</b>", st["secao"]))
    elements.append(_build_pdf_resumo(relatorio))
    elements.append(Spacer(1, 0.4 * cm))

    elements.extend(_build_pdf_detalhamento(relatorio, st["secao"]))

    elements.extend(_build_pdf_assinaturas(relatorio, loja, v, st, incluir_assinaturas))

    if relatorio.observacoes:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("<b>Observações</b>", st["secao"]))
        elements.append(Paragraph(relatorio.observacoes, st["info"]))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=_CINZA_ESCURO))
    elements.append(Spacer(1, 0.1 * cm))
    elements.append(_build_pdf_rodape(relatorio, st["rodape"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
