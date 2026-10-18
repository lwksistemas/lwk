"""PDF dos clientes com oportunidade ganha e o histórico da negociação."""
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from .models import Oportunidade
from .periodo import calcular_intervalo_datas as calcular_periodo
from .periodo import filtro_fechamento_no_periodo as _filtro_datas_fechamento_ganho
from .relatorios_pdf_common import _criar_cabecalho_relatorio, _obter_logo_loja

_TIPOS_NOTA = {
    "resposta_cliente": "Resposta do cliente",
    "nota_interna": "Nota interna",
}


def telefone_do_cliente(oportunidade) -> str:
    """Telefone do lead, depois do contato e da empresa."""
    lead = getattr(oportunidade, "lead", None)
    if lead is None:
        return ""
    candidatos = [getattr(lead, "telefone", "")]
    contato = getattr(lead, "contato", None)
    if contato is not None:
        candidatos.append(getattr(contato, "telefone", ""))
    conta = getattr(lead, "conta", None)
    if conta is not None:
        candidatos.append(getattr(conta, "telefone", ""))
    for valor in candidatos:
        texto = (valor or "").strip()
        if texto:
            return texto
    return ""


def nome_do_cliente(oportunidade) -> str:
    lead = getattr(oportunidade, "lead", None)
    nome = (getattr(lead, "nome", "") or "").strip() if lead is not None else ""
    if nome:
        return nome
    return (getattr(oportunidade, "titulo", "") or "").strip() or "Cliente"


def _data_ganho(oportunidade):
    return (
        getattr(oportunidade, "data_fechamento_ganho", None)
        or getattr(oportunidade, "data_fechamento", None)
    )


def _brl(valor) -> str:
    numero = f"{float(valor or 0):,.2f}"
    return "R$ " + numero.replace(",", "X").replace(".", ",").replace("X", ".")


def _paragrafo(texto: str, style) -> Paragraph:
    return Paragraph(escape(texto or "").replace("\n", "<br/>"), style)


def gerar_relatorio_negociacao_ganhos(
    loja_id: int,
    periodo: str,
    vendedor_id=None,
    empresa_prestadora_id=None,
    data_inicio_custom=None,
    data_fim_custom=None,
) -> BytesIO:
    """Clientes fichados com oportunidade ganha e o histórico da negociação."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "NegTitulo",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#0176d3"),
        spaceBefore=8,
        spaceAfter=4,
    )
    corpo = ParagraphStyle("NegCorpo", parent=styles["Normal"], fontSize=9, leading=12)
    nota_style = ParagraphStyle(
        "NegNota",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        leftIndent=8,
        spaceBefore=2,
    )
    meta = ParagraphStyle(
        "NegMeta",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#4b5563"),
        leftIndent=8,
    )

    data_inicio, data_fim = calcular_periodo(periodo)
    if data_inicio_custom and data_fim_custom:
        from datetime import date as date_type

        try:
            data_inicio = date_type.fromisoformat(str(data_inicio_custom))
            data_fim = date_type.fromisoformat(str(data_fim_custom))
        except (TypeError, ValueError):
            pass

    elements = [
        _criar_cabecalho_relatorio(_obter_logo_loja(loja_id), "Clientes fichados e ganhos"),
        Spacer(1, 0.2 * cm),
        Paragraph("Histórico de negociação", styles["Normal"]),
        Paragraph(
            f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
            styles["Normal"],
        ),
        Spacer(1, 0.3 * cm),
    ]

    oportunidades = (
        Oportunidade.objects.filter(loja_id=loja_id, etapa="closed_won")
        .filter(_filtro_datas_fechamento_ganho(data_inicio, data_fim))
        .select_related("lead", "lead__conta", "lead__contato", "vendedor")
        .prefetch_related("notas_negociacao")
    )
    if empresa_prestadora_id:
        oportunidades = oportunidades.filter(empresa_prestadora_id=empresa_prestadora_id)
    if vendedor_id:
        oportunidades = oportunidades.filter(vendedor_id=vendedor_id)
    oportunidades = oportunidades.order_by("lead__nome", "data_fechamento_ganho", "id")

    linhas = list(oportunidades)
    elements.append(Paragraph(f"Oportunidades ganhas: {len(linhas)}", corpo))

    if not linhas:
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(Paragraph("Nenhuma oportunidade ganha neste período.", corpo))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    for opp in linhas:
        elements.append(_paragrafo(nome_do_cliente(opp), titulo))
        telefone = telefone_do_cliente(opp) or "Não informado"
        elements.append(_paragrafo(f"Telefone: {telefone}", corpo))
        ganho = _data_ganho(opp)
        ganho_txt = ganho.strftime("%d/%m/%Y") if ganho else "—"
        vendedor = getattr(getattr(opp, "vendedor", None), "nome", "") or "—"
        elements.append(_paragrafo(
            f"{opp.titulo} · {_brl(opp.valor)} · Ganho em {ganho_txt} · {vendedor}",
            corpo,
        ))
        elements.append(Paragraph("Histórico de negociação", meta))
        notas = list(opp.notas_negociacao.all())
        if not notas:
            elements.append(Paragraph("Nenhum registro no histórico.", nota_style))
        for nota in notas:
            quando = getattr(nota, "created_at", None)
            if quando is not None and timezone.is_aware(quando):
                quando = timezone.localtime(quando)
            quando_txt = quando.strftime("%d/%m/%Y %H:%M") if quando else ""
            tipo = _TIPOS_NOTA.get(getattr(nota, "tipo", ""), "Registro")
            autor = (getattr(nota, "autor_nome", "") or "").strip()
            cabeca = " · ".join(parte for parte in (quando_txt, tipo, autor) if parte)
            elements.append(Paragraph(escape(cabeca), meta))
            elements.append(_paragrafo(getattr(nota, "texto", "") or "", nota_style))
        feedback = (getattr(opp, "feedback_pos_venda", "") or "").strip()
        if feedback:
            elements.append(Paragraph("Depois da venda", meta))
            elements.append(_paragrafo(feedback, nota_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
