"""PDF do quadro de pipeline, no mesmo padrão visual da proposta e do histórico."""
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models_config import CRMConfig
from .relatorio_comissao_data import nome_da_conta

TITULO = "PIPELINE DE VENDAS"


def _logo_da_loja(loja) -> str | None:
    logo = (getattr(loja, "logo", "") or getattr(loja, "login_logo", "") or "").strip()
    return logo or None


def _logo_direita(oportunidades, loja) -> str | None:
    """Uma prestadora no quadro usa a logo dela. Várias usam a logo de login da loja."""
    logos = []
    for oportunidade in oportunidades:
        prestadora = getattr(oportunidade, "empresa_prestadora", None)
        logo = getattr(prestadora, "logo", None) if prestadora is not None else None
        if isinstance(logo, str):
            logo = logo.strip()
            if logo and logo not in logos:
                logos.append(logo)
    if len(logos) == 1:
        return logos[0]
    login = (getattr(loja, "login_logo", "") or "").strip()
    return login or None


def _etapas_da_loja():
    config = CRMConfig.objects.order_by("id").first()
    brutas = config.etapas_pipeline if config and config.etapas_pipeline else CRMConfig.get_default_etapas()
    ativas = [etapa for etapa in brutas if isinstance(etapa, dict) and etapa.get("ativo", True) and etapa.get("key")]
    ativas.sort(key=lambda etapa: etapa.get("ordem") or 0)
    return [(etapa["key"], etapa.get("label") or etapa["key"]) for etapa in ativas]


def _nome_cliente(oportunidade) -> str:
    lead = getattr(oportunidade, "lead", None)
    nome = (getattr(lead, "nome", "") or "").strip() if lead is not None else ""
    if nome:
        return nome
    return (getattr(oportunidade, "titulo", "") or "").strip() or "—"


def _nome_prestadora(oportunidade) -> str:
    prestadora = getattr(oportunidade, "empresa_prestadora", None)
    if prestadora is None:
        return "—"
    return nome_da_conta(prestadora) or "—"


def _nome_vendedor(oportunidade) -> str:
    vendedor = getattr(oportunidade, "vendedor", None)
    return (getattr(vendedor, "nome", "") or "").strip() or "—"


def _brl(valor) -> str:
    if valor is None:
        return "—"
    numero = Decimal(valor).quantize(Decimal("0.01"))
    texto = f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _data_linha(oportunidade) -> str:
    if oportunidade.etapa == "closed_won":
        dia = oportunidade.data_fechamento_ganho or oportunidade.data_fechamento
    elif oportunidade.etapa == "closed_lost":
        dia = oportunidade.data_fechamento_perdido
    else:
        criado = getattr(oportunidade, "created_at", None)
        dia = timezone.localtime(criado).date() if criado else None
    if not dia:
        return "—"
    return dia.strftime("%d/%m/%Y")


def _telefone_linha(oportunidade) -> str:
    from .relatorios_negociacao_pdf import telefone_para_exibicao

    return telefone_para_exibicao(oportunidade) or "—"


def _periodo_texto(data_inicio, data_fim) -> str:
    def _dia(valor):
        texto = (valor or "").strip()[:10]
        if len(texto) == 10 and texto[4] == "-":
            ano, mes, dia = texto.split("-")
            return f"{dia}/{mes}/{ano}"
        return ""

    inicio = _dia(data_inicio)
    fim = _dia(data_fim)
    if inicio and fim:
        return f"Período: {inicio} até {fim}"
    if inicio:
        return f"Período: a partir de {inicio}"
    if fim:
        return f"Período: até {fim}"
    return "Período: todos"


def _estilos():
    base = getSampleStyleSheet()
    return {
        "meta": ParagraphStyle("PipeMeta", parent=base["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#374151")),
        "th": ParagraphStyle("PipeTh", parent=base["Normal"], fontSize=8, leading=10, textColor=colors.white, fontName="Helvetica-Bold"),
        "th_dir": ParagraphStyle("PipeThDir", parent=base["Normal"], fontSize=8, leading=10, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_RIGHT),
        "td": ParagraphStyle("PipeTd", parent=base["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#111827")),
        "td_dir": ParagraphStyle("PipeTdDir", parent=base["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#111827"), alignment=TA_RIGHT),
        "etapa": ParagraphStyle("PipeEtapa", parent=base["Normal"], fontSize=9, leading=11, textColor=colors.white, fontName="Helvetica-Bold"),
        "etapa_dir": ParagraphStyle("PipeEtapaDir", parent=base["Normal"], fontSize=9, leading=11, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_RIGHT),
        "vazio": ParagraphStyle("PipeVazio", parent=base["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#6b7280")),
    }


def _paragrafo(texto, estilo):
    return Paragraph(escape(texto or "—"), estilo)


def gerar_pdf_pipeline(
    oportunidades,
    loja,
    *,
    data_inicio="",
    data_fim="",
    vendedor_nome="",
    etapas=None,
) -> bytes:
    """Quadro filtrado do pipeline, com a logo da loja e a da prestadora quando houver uma só."""
    from .pdf_proposta_contrato.sections import _build_cabecalho

    etapas = list(etapas) if etapas is not None else _etapas_da_loja()
    linhas = list(oportunidades)
    por_etapa = {}
    for oportunidade in linhas:
        por_etapa.setdefault(oportunidade.etapa, []).append(oportunidade)
    chaves = [chave for chave, _rotulo in etapas]
    for chave in por_etapa:
        if chave not in chaves:
            etapas.append((chave, chave))

    pagina = landscape(A4)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagina,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.6 * cm,
        title="Pipeline de vendas",
    )
    estilos = _estilos()
    elements = []
    largura = pagina[0] - 2.8 * cm
    _build_cabecalho(elements, _logo_da_loja(loja), TITULO, _logo_direita(linhas, loja), largura)
    elements.append(Spacer(1, 0.35 * cm))
    elements.append(Paragraph(escape(_periodo_texto(data_inicio, data_fim)), estilos["meta"]))
    if (vendedor_nome or "").strip():
        elements.append(Paragraph(escape(f"Vendedor: {vendedor_nome.strip()}"), estilos["meta"]))

    total = sum((Decimal(item.valor or 0) for item in linhas), Decimal("0"))
    quantidade = len(linhas)
    resumo = "1 oportunidade" if quantidade == 1 else f"{quantidade} oportunidades"
    elements.append(Paragraph(escape(f"{resumo} · {_brl(total)}"), estilos["meta"]))
    elements.append(Spacer(1, 0.35 * cm))

    colunas = [
        largura * 0.24,
        largura * 0.22,
        largura * 0.16,
        largura * 0.11,
        largura * 0.15,
        largura * 0.12,
    ]
    if not linhas:
        elements.append(Paragraph("Nenhuma oportunidade neste período.", estilos["vazio"]))
    else:
        for chave, rotulo in etapas:
            grupo = por_etapa.get(chave) or []
            if not grupo:
                continue
            grupo.sort(key=lambda item: _nome_cliente(item).upper())
            soma = sum((Decimal(item.valor or 0) for item in grupo), Decimal("0"))
            qtd = "1 oportunidade" if len(grupo) == 1 else f"{len(grupo)} oportunidades"
            cabeca = [
                _paragrafo("Cliente", estilos["th"]),
                _paragrafo("Prestadora", estilos["th"]),
                _paragrafo("Vendedor", estilos["th"]),
                _paragrafo("Valor", estilos["th_dir"]),
                _paragrafo("Telefone", estilos["th"]),
                _paragrafo("Data", estilos["th_dir"]),
            ]
            dados = [[_paragrafo(f"{rotulo} · {qtd} · {_brl(soma)}", estilos["etapa"]), "", "", "", "", ""], cabeca]
            for oportunidade in grupo:
                dados.append([
                    _paragrafo(_nome_cliente(oportunidade), estilos["td"]),
                    _paragrafo(_nome_prestadora(oportunidade), estilos["td"]),
                    _paragrafo(_nome_vendedor(oportunidade), estilos["td"]),
                    _paragrafo(_brl(oportunidade.valor), estilos["td_dir"]),
                    _paragrafo(_telefone_linha(oportunidade), estilos["td"]),
                    _paragrafo(_data_linha(oportunidade), estilos["td_dir"]),
                ])
            tabela = Table(dados, colWidths=colunas, repeatRows=2)
            tabela.setStyle(TableStyle([
                ("SPAN", (0, 0), (-1, 0)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0176d3")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#1e3a5f")),
                ("BACKGROUND", (0, 2), (-1, -1), colors.HexColor("#f8fafc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 1), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, 0), 5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                ("TOPPADDING", (0, 1), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
            ]))
            elements.append(tabela)
            elements.append(Spacer(1, 0.35 * cm))

    def _rodape(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        gerado = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
        canvas.drawString(1.4 * cm, 0.9 * cm, f"Pipeline de vendas · gerado em {gerado}")
        canvas.drawRightString(pagina[0] - 1.4 * cm, 0.9 * cm, f"Página {documento.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=_rodape, onLaterPages=_rodape)
    return buffer.getvalue()
