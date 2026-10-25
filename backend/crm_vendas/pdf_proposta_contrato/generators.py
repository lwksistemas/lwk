"""Geração de PDF para proposta e contrato do CRM."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from ..emitente_documento import obter_dados_emitente_documento
from .formatters import (
    _obter_dados_loja,
    conteudo_com_descricoes,
    conteudo_narrativo_da_proposta,
    dividir_folhas_marcadas,
    extrair_letra_do_template,
    extrair_pagamento_inicial,
    paragrafos_condicoes,
    partir_condicoes,
    titulo_e_corpo_da_primeira_folha,
    separar_subtitulo,
    subtitulo_da_versao,
)
from .sections import (
    _build_cabecalho,
    _build_faixa_logos,
    _build_identificacao_visual,
    _build_pagamento_inicial_visual,
    _build_recursos_visuais,
    _build_resumo_visual,
    _build_secao_assinaturas,
    _build_secao_cliente,
    _build_secao_conteudo,
    _build_secao_desconto,
    _build_secao_empresa,
    _build_secao_produtos,
    _build_tabela_investimento_visual,
    _descricoes_incluidas,
    _estilo_subtitulo_proposta,
    _itens_oportunidade,
    _estilo_titulo_proposta,
    _estilo_titulo_recursos,
    _linhas_implantacao,
    _par_logos,
)
from .watermark import _build_watermark_callback, _inserir_watermark_flowable


def _proposta_tem_as_duas_assinaturas(proposta) -> bool:
    """O quadro só entra na proposta depois que vendedor e cliente assinaram."""
    from ..models import AssinaturaDigital

    tipos = set(
        AssinaturaDigital.objects.filter(proposta=proposta, assinado=True).values_list("tipo", flat=True)
    )
    return "vendedor" in tipos and "cliente" in tipos


def _logo_prestadora(documento):
    """Logo da empresa prestadora vinculada à oportunidade. A logo do login fica só na tela de login."""
    oportunidade = getattr(documento, "oportunidade", None)
    prestadora = getattr(oportunidade, "empresa_prestadora", None) if oportunidade is not None else None
    if prestadora is None:
        return None
    logo = getattr(prestadora, "logo", None)
    if not isinstance(logo, str):
        return None
    logo = logo.strip()
    return logo or None


def _completar_logos(loja_data, loja_id):
    """A logo principal e a da tela de login ficam na loja, mesmo com emitente próprio."""
    dados = dict(loja_data or {})
    if not loja_id:
        return dados
    da_loja = _obter_dados_loja(loja_id) or {}
    if not dados.get("logo"):
        dados["logo"] = da_loja.get("logo")
    if not dados.get("login_logo"):
        dados["login_logo"] = da_loja.get("login_logo")
    return dados


def gerar_pdf_proposta(proposta, incluir_assinaturas=True) -> BytesIO:
    """Gera PDF da proposta comercial."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.15 * cm, bottomMargin=1.2 * cm, leftMargin=1.55 * cm, rightMargin=1.55 * cm)
    elements = []
    styles = getSampleStyleSheet()
    compact = ParagraphStyle("Compact", parent=styles["Normal"], fontSize=9, spaceBefore=0, spaceAfter=1, leading=11)

    loja_id = getattr(proposta, "loja_id", None)
    loja_data = _completar_logos(obter_dados_emitente_documento(proposta), loja_id)
    logo_url = loja_data.get("logo")
    logos = _par_logos(logo_url, _logo_prestadora(proposta))
    _build_faixa_logos(elements, *logos)
    elements.append(Paragraph("PROPOSTA COMERCIAL", _estilo_titulo_proposta()))

    lead = proposta.oportunidade.lead if proposta.oportunidade and proposta.oportunidade.lead else None
    conteudo, fonte_texto, fonte_negrito, tamanho_texto = extrair_letra_do_template(
        conteudo_narrativo_da_proposta(proposta),
    )
    paragrafos = paragrafos_condicoes(conteudo, proposta.oportunidade)
    marcado = dividir_folhas_marcadas(paragrafos)
    if marcado is not None:
        primeira, paragrafos = marcado
        titulo_banco, linhas_banco = titulo_e_corpo_da_primeira_folha(primeira)
        subtitulo_template, paragrafos = separar_subtitulo(paragrafos)
        intro, secoes = partir_condicoes(paragrafos)
    else:
        subtitulo_template, paragrafos = separar_subtitulo(paragrafos)
        intro, secoes = partir_condicoes(paragrafos)
        titulo_banco, linhas_banco, intro, secoes = extrair_pagamento_inicial(intro, secoes)
    subtitulo = subtitulo_da_versao(_itens_oportunidade(proposta.oportunidade)) or subtitulo_template
    if subtitulo:
        elements.append(Paragraph(escape(subtitulo), _estilo_subtitulo_proposta()))

    _build_identificacao_visual(elements, loja_data, lead)
    totais = _build_tabela_investimento_visual(elements, proposta.oportunidade)
    _build_resumo_visual(elements, proposta, totais)
    _build_pagamento_inicial_visual(
        elements, titulo_banco, linhas_banco, fonte_texto, fonte_negrito, tamanho_texto,
    )

    tem_recursos = (
        any(paragrafo for paragrafo in intro)
        or bool(secoes)
        or bool(_descricoes_incluidas(proposta.oportunidade))
        or bool(_linhas_implantacao(proposta.oportunidade))
    )
    if tem_recursos:
        elements.append(PageBreak())
        _build_faixa_logos(elements, *logos)
        elements.append(Paragraph("RECURSOS E CONDIÇÕES", _estilo_titulo_recursos()))
        _build_recursos_visuais(
            elements, proposta.oportunidade, intro, secoes, fonte_texto, fonte_negrito, tamanho_texto,
        )

    vendedor = proposta.oportunidade.vendedor if proposta.oportunidade and getattr(proposta.oportunidade, "vendedor", None) else None
    ass_v, ass_c = None, None
    if incluir_assinaturas and _proposta_tem_as_duas_assinaturas(proposta):
        ass_v, ass_c = _build_secao_assinaturas(elements, proposta, lead, vendedor, compact, True, "proposta")

    wm_data = _build_watermark_callback(logo_url, ass_v, ass_c)
    _inserir_watermark_flowable(elements, wm_data, preencher_quadro=True)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_contrato(contrato, incluir_assinaturas=True) -> BytesIO:
    """Gera PDF do contrato."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * cm, bottomMargin=1 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    loja_id = getattr(contrato, "loja_id", None)
    loja_data = _completar_logos(obter_dados_emitente_documento(contrato), loja_id)
    logo_url = loja_data.get("logo")
    _build_cabecalho(elements, logo_url, "CONTRATO", _logo_prestadora(contrato))
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

    _build_secao_conteudo(
        elements,
        conteudo_com_descricoes(contrato.conteudo, contrato.oportunidade),
        normal,
    )

    vendedor = contrato.oportunidade.vendedor if contrato.oportunidade and getattr(contrato.oportunidade, "vendedor", None) else None
    ass_v, ass_c = _build_secao_assinaturas(elements, contrato, lead, vendedor, normal, incluir_assinaturas, "contrato")

    wm_data = _build_watermark_callback(logo_url, ass_v, ass_c)
    _inserir_watermark_flowable(elements, wm_data, max_wm_w_cm=5.5, max_wm_h_cm=3.5, y_factor=1.0)

    doc.build(elements)
    buffer.seek(0)
    return buffer
