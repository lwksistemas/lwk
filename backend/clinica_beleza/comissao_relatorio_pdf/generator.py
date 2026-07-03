from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from ..prontuario_pdf import _resolver_cabecalho
from .blocos import (
    _bloco_consultas_pdf,
    _bloco_procedimentos_pdf,
    _bloco_resumo_profissional,
    _bloco_totais_final,
)
from .constants import _COR_PRIMARIA, _CINZA
from .formatting import _fmt_data_br, _is_linha_consulta
from .timbrado import _logo_image, _merge_timbrado_fundo


def gerar_pdf_comissoes(
    *,
    resultado: dict,
    loja,
    data_inicio: date | None,
    data_fim: date | None,
    profissional_filtro_nome: str | None = None,
) -> BytesIO:
    """
    Gera PDF do relatório de comissões.
    resultado: retorno de calcular_comissoes (dict com profissionais e totais).
    """
    loja_id = loja.id
    tipo_cab, dados_cab = _resolver_cabecalho(loja_id)

    top_margin = 2 * cm
    if tipo_cab == 'timbrado':
        top_margin = 3.2 * cm

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=top_margin,
        bottomMargin=1.5 * cm,
    )

    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=13,
        textColor=_COR_PRIMARIA,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    subtitulo_style = ParagraphStyle(
        'Sub',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=_CINZA,
        spaceAfter=1,
    )
    prof_style = ParagraphStyle(
        'Prof',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.HexColor('#111827'),
        spaceAfter=4,
    )

    elements = []

    if tipo_cab == 'logo':
        img = _logo_image(dados_cab)
        if img:
            elements.append(img)
            elements.append(Spacer(1, 2 * mm))
    elif tipo_cab == 'texto' and dados_cab:
        elements.append(Paragraph(getattr(dados_cab, 'nome', '') or 'Clínica', titulo_style))
        elements.append(Spacer(1, 1 * mm))

    elements.append(Paragraph('Relatório de Comissões', titulo_style))
    periodo = f'Período: {_fmt_data_br(data_inicio)} a {_fmt_data_br(data_fim)}'
    elements.append(Paragraph(periodo, subtitulo_style))

    if profissional_filtro_nome:
        elements.append(Paragraph(f'Profissional: {profissional_filtro_nome}', prof_style))
    else:
        elements.append(Paragraph('Profissionais: todos', subtitulo_style))

    elements.append(Spacer(1, 2 * mm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 2 * mm))

    profissionais = resultado.get('profissionais') or []
    if not profissionais:
        elements.append(Paragraph('Nenhum dado encontrado no período.', styles['Normal']))
    else:
        for idx, p in enumerate(profissionais):
            if idx > 0:
                elements.append(Spacer(1, 4 * mm))
            if len(profissionais) > 1 or not profissional_filtro_nome:
                elements.append(Paragraph(p.get('nome', ''), ParagraphStyle(
                    'NomeProf',
                    parent=styles['Heading2'],
                    fontSize=10,
                    fontName='Helvetica-Bold',
                    textColor=_COR_PRIMARIA,
                    spaceBefore=2 * mm if idx > 0 else 0,
                    spaceAfter=1 * mm,
                )))

            detalhes = p.get('detalhes') or []
            linhas_c = [d for d in detalhes if _is_linha_consulta(d)]
            linhas_p = [d for d in detalhes if not _is_linha_consulta(d)]
            qtd_proc = sum(d.get('qtd', 0) for d in linhas_p)

            info = (
                f'{p.get("total_atendimentos", 0)} consulta(s) paga(s)'
                + (f' · {qtd_proc} procedimento(s)' if qtd_proc else '')
            )
            elements.append(Paragraph(info, subtitulo_style))
            elements.extend(_bloco_consultas_pdf(linhas_c, p))
            elements.extend(_bloco_procedimentos_pdf(linhas_p, p, qtd_proc))
            elements.extend(_bloco_resumo_profissional(p))

        if len(profissionais) > 1:
            totais = resultado.get('totais') or {}
            elements.extend(_bloco_totais_final(styles, totais, multi_prof=True))

    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    if tipo_cab == 'timbrado':
        pdf_bytes = _merge_timbrado_fundo(pdf_bytes, dados_cab)

    out = BytesIO(pdf_bytes)
    out.seek(0)
    return out
