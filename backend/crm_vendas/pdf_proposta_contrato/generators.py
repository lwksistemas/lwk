"""Geração de PDF para proposta e contrato do CRM."""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from .formatters import _obter_dados_loja
from ..emitente_documento import obter_dados_emitente_documento
from .sections import (
    _build_cabecalho,
    _build_secao_assinaturas,
    _build_secao_cliente,
    _build_secao_conteudo,
    _build_secao_desconto,
    _build_secao_empresa,
    _build_secao_produtos,
)
from .watermark import _build_watermark_callback, _inserir_watermark_flowable


def gerar_pdf_proposta(proposta, incluir_assinaturas=True) -> BytesIO:
    """Gera PDF da proposta comercial."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.2 * cm, bottomMargin=0.5 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()
    compact = ParagraphStyle('Compact', parent=styles['Normal'], fontSize=9, spaceBefore=0, spaceAfter=1, leading=11)

    loja_id = getattr(proposta, 'loja_id', None)
    loja_data = obter_dados_emitente_documento(proposta)
    if loja_id and not loja_data.get('logo'):
        loja_data = {**loja_data, 'logo': (_obter_dados_loja(loja_id) or {}).get('logo')}
    logo_url = loja_data.get('logo')
    _build_cabecalho(elements, logo_url, 'PROPOSTA COMERCIAL')
    elements.append(Paragraph(f'<b>Título:</b> {proposta.titulo or "—"}', compact))

    if loja_data:
        _build_secao_empresa(elements, loja_data, compact)

    lead = proposta.oportunidade.lead if proposta.oportunidade and proposta.oportunidade.lead else None
    if lead:
        _build_secao_cliente(elements, lead, compact)

    _build_secao_produtos(elements, proposta.oportunidade, compact, incluir_recorrencia=True)
    _build_secao_desconto(elements, proposta, compact)
    _build_secao_conteudo(elements, proposta.conteudo, compact)

    vendedor = proposta.oportunidade.vendedor if proposta.oportunidade and getattr(proposta.oportunidade, 'vendedor', None) else None
    ass_v, ass_c = _build_secao_assinaturas(elements, proposta, lead, vendedor, compact, incluir_assinaturas, 'proposta')

    wm_data = _build_watermark_callback(logo_url, ass_v, ass_c)
    _inserir_watermark_flowable(elements, wm_data, max_wm_w_cm=7.5, max_wm_h_cm=5, y_factor=0.8)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_contrato(contrato, incluir_assinaturas=True) -> BytesIO:
    """Gera PDF do contrato."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * cm, bottomMargin=1 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()
    normal = styles['Normal']

    loja_id = getattr(contrato, 'loja_id', None)
    loja_data = obter_dados_emitente_documento(contrato)
    if loja_id and not loja_data.get('logo'):
        loja_data = {**loja_data, 'logo': (_obter_dados_loja(loja_id) or {}).get('logo')}
    logo_url = loja_data.get('logo')
    _build_cabecalho(elements, logo_url, 'CONTRATO')
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(f'<b>Número:</b> {contrato.numero or "—"}', normal))
    elements.append(Paragraph(f'<b>Título:</b> {contrato.titulo or "—"}', normal))

    _build_secao_desconto(elements, contrato, normal)
    elements.append(Spacer(1, 0.03 * cm))

    if loja_data:
        _build_secao_empresa(elements, loja_data, normal)

    lead = contrato.oportunidade.lead if contrato.oportunidade and contrato.oportunidade.lead else None
    if lead:
        _build_secao_cliente(elements, lead, normal)

    if contrato.oportunidade and contrato.oportunidade.itens.exists():
        _build_secao_produtos(elements, contrato.oportunidade, normal, incluir_recorrencia=False)
        elements.append(Spacer(1, 0.05 * cm))

    _build_secao_conteudo(elements, contrato.conteudo, normal)

    vendedor = contrato.oportunidade.vendedor if contrato.oportunidade and getattr(contrato.oportunidade, 'vendedor', None) else None
    ass_v, ass_c = _build_secao_assinaturas(elements, contrato, lead, vendedor, normal, incluir_assinaturas, 'contrato')

    wm_data = _build_watermark_callback(logo_url, ass_v, ass_c)
    _inserir_watermark_flowable(elements, wm_data, max_wm_w_cm=5.5, max_wm_h_cm=3.5, y_factor=1.0)

    doc.build(elements)
    buffer.seek(0)
    return buffer
