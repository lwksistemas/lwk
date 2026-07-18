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
from .constants import _CINZA, _COR_PRIMARIA
from .formatting import _fmt_data_br, _is_linha_consulta
from ..pdf_common import logo_image as _logo_image
from ..pdf_common import merge_timbrado_fundo as _merge_timbrado_fundo


def _styles_comissoes(styles):
    titulo_style = ParagraphStyle(
        "Titulo",
        parent=styles["Heading1"],
        fontSize=13,
        textColor=_COR_PRIMARIA,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    subtitulo_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=_CINZA,
        spaceAfter=1,
    )
    prof_style = ParagraphStyle(
        "Prof",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=4,
    )
    return titulo_style, subtitulo_style, prof_style


def _cabecalho_elements(tipo_cab, dados_cab, titulo_style):
    elements = []
    if tipo_cab == "logo":
        img = _logo_image(dados_cab)
        if img:
            elements.append(img)
            elements.append(Spacer(1, 2 * mm))
    elif tipo_cab == "texto" and dados_cab:
        elements.append(Paragraph(getattr(dados_cab, "nome", "") or "Clínica", titulo_style))
        elements.append(Spacer(1, 1 * mm))
    return elements


def _titulo_periodo_elements(
    titulo_style,
    subtitulo_style,
    prof_style,
    *,
    data_inicio,
    data_fim,
    profissional_filtro_nome,
):
    elements = [
        Paragraph("Relatório de Comissões", titulo_style),
        Paragraph(
            f"Período: {_fmt_data_br(data_inicio)} a {_fmt_data_br(data_fim)}",
            subtitulo_style,
        ),
    ]
    if profissional_filtro_nome:
        elements.append(Paragraph(f"Profissional: {profissional_filtro_nome}", prof_style))
    else:
        elements.append(Paragraph("Profissionais: todos", subtitulo_style))
    elements.append(Spacer(1, 2 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
    elements.append(Spacer(1, 2 * mm))
    return elements


def _nome_profissional_style(styles, idx: int):
    return ParagraphStyle(
        "NomeProf",
        parent=styles["Heading2"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=_COR_PRIMARIA,
        spaceBefore=2 * mm if idx > 0 else 0,
        spaceAfter=1 * mm,
    )


def _bloco_um_profissional(p, idx, *, multi_ou_sem_filtro, styles, subtitulo_style):
    elements = []
    if idx > 0:
        elements.append(Spacer(1, 4 * mm))
    if multi_ou_sem_filtro:
        elements.append(Paragraph(p.get("nome", ""), _nome_profissional_style(styles, idx)))

    detalhes = p.get("detalhes") or []
    linhas_c = [d for d in detalhes if _is_linha_consulta(d)]
    linhas_p = [d for d in detalhes if not _is_linha_consulta(d)]
    qtd_proc = sum(d.get("qtd", 0) for d in linhas_p)
    info = (
        f'{p.get("total_atendimentos", 0)} consulta(s) paga(s)'
        + (f" · {qtd_proc} procedimento(s)" if qtd_proc else "")
    )
    elements.append(Paragraph(info, subtitulo_style))
    elements.extend(_bloco_consultas_pdf(linhas_c, p))
    elements.extend(_bloco_procedimentos_pdf(linhas_p, p, qtd_proc))
    elements.extend(_bloco_resumo_profissional(p))
    return elements


def _corpo_profissionais(resultado, *, profissional_filtro_nome, styles, subtitulo_style):
    profissionais = resultado.get("profissionais") or []
    if not profissionais:
        return [Paragraph("Nenhum dado encontrado no período.", styles["Normal"])]

    multi_ou_sem_filtro = len(profissionais) > 1 or not profissional_filtro_nome
    elements = []
    for idx, p in enumerate(profissionais):
        elements.extend(
            _bloco_um_profissional(
                p,
                idx,
                multi_ou_sem_filtro=multi_ou_sem_filtro,
                styles=styles,
                subtitulo_style=subtitulo_style,
            )
        )
    if len(profissionais) > 1:
        totais = resultado.get("totais") or {}
        elements.extend(_bloco_totais_final(styles, totais, multi_prof=True))
    return elements


def gerar_pdf_comissoes(
    *,
    resultado: dict,
    loja,
    data_inicio: date | None,
    data_fim: date | None,
    profissional_filtro_nome: str | None = None,
) -> BytesIO:
    """Gera PDF do relatório de comissões.
    resultado: retorno de calcular_comissoes (dict com profissionais e totais).
    """
    loja_id = loja.id
    tipo_cab, dados_cab = _resolver_cabecalho(loja_id)
    top_margin = 3.2 * cm if tipo_cab == "timbrado" else 2 * cm

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    titulo_style, subtitulo_style, prof_style = _styles_comissoes(styles)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=top_margin,
        bottomMargin=1.5 * cm,
    )

    elements = []
    elements.extend(_cabecalho_elements(tipo_cab, dados_cab, titulo_style))
    elements.extend(
        _titulo_periodo_elements(
            titulo_style,
            subtitulo_style,
            prof_style,
            data_inicio=data_inicio,
            data_fim=data_fim,
            profissional_filtro_nome=profissional_filtro_nome,
        )
    )
    elements.extend(
        _corpo_profissionais(
            resultado,
            profissional_filtro_nome=profissional_filtro_nome,
            styles=styles,
            subtitulo_style=subtitulo_style,
        )
    )

    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    if tipo_cab == "timbrado":
        pdf_bytes = _merge_timbrado_fundo(pdf_bytes, dados_cab)

    out = BytesIO(pdf_bytes)
    out.seek(0)
    return out
