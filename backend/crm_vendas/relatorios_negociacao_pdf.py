"""PDF dos clientes com oportunidade ganha e o histórico da negociação."""
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.cpf_utils import eh_cpf, label_empresa_lead, normalizar_cpf_cnpj, somente_digitos_documento
from core.phone_utils import telefone_exibicao_brasileiro

from .feedback_data import texto_tem_data
from .models import Oportunidade
from .periodo import calcular_intervalo_datas as calcular_periodo
from .periodo import filtro_fechamento_no_periodo as _filtro_datas_fechamento_ganho
from .relatorios_pdf_common import carregar_logo_relatorio, _obter_logo_loja

TITULO_RELATORIO = "Controle de qualidade"

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


def telefone_para_exibicao(oportunidade) -> str:
    """Telefone no padrão (DDD) 99999-9999, mesmo quando veio com o 55."""
    bruto = telefone_do_cliente(oportunidade)
    if not bruto:
        return ""
    return telefone_exibicao_brasileiro(bruto)


def empresa_da_oportunidade(oportunidade) -> str:
    """Empresa do cliente. CNPJ com razão social não usa o nome fantasia. CPF vira PESSOA FISICA."""
    from .relatorio_comissao_data import nome_da_conta

    lead = getattr(oportunidade, "lead", None)
    if lead is None:
        return "—"
    conta = getattr(lead, "conta", None) if getattr(lead, "conta_id", None) else None
    documento = getattr(lead, "cpf_cnpj", None)
    if conta is not None and not eh_cpf(documento) and (getattr(conta, "razao_social", "") or "").strip():
        return nome_da_conta(conta) or "—"
    conta_nome = getattr(conta, "nome", None) if conta is not None else None
    rotulo = label_empresa_lead(
        documento,
        empresa=getattr(lead, "empresa", None),
        conta_nome=conta_nome,
    )
    return (rotulo or "").strip() or "—"


def documento_da_oportunidade(oportunidade) -> str:
    """CPF ou CNPJ do cliente, formatado, para a coluna Oportunidade."""
    lead = getattr(oportunidade, "lead", None)
    if lead is None:
        return ""
    bruto = (getattr(lead, "cpf_cnpj", "") or "").strip()
    if len(somente_digitos_documento(bruto)) not in (11, 14) and getattr(lead, "conta_id", None):
        bruto = (getattr(getattr(lead, "conta", None), "cnpj", "") or "").strip()
    digitos = somente_digitos_documento(bruto)
    formatado = normalizar_cpf_cnpj(bruto)
    if len(digitos) == 11:
        return f"CPF {formatado}"
    if len(digitos) == 14:
        return f"CNPJ {formatado}"
    return ""


def linha_contato_empresa(oportunidade) -> str:
    """No CNPJ a faixa traz o contato e o telefone. No CPF fica só o nome."""
    if not documento_da_oportunidade(oportunidade).startswith("CNPJ"):
        return ""
    nome = nome_do_cliente(oportunidade)
    telefone = telefone_para_exibicao(oportunidade) or "Não informado"
    return f"Contato da empresa - {nome} - {telefone}"


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


def _estilos_cartao():
    base = getSampleStyleSheet()
    return {
        "nome": ParagraphStyle(
            "NegNome",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.white,
        ),
        "telefone": ParagraphStyle(
            "NegTel",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=TA_RIGHT,
            textColor=colors.white,
        ),
        "rotulo": ParagraphStyle(
            "NegRotulo",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#6b7280"),
        ),
        "valor": ParagraphStyle(
            "NegValor",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#111827"),
        ),
        "documento": ParagraphStyle(
            "NegDocumento",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#374151"),
        ),
        "nota": ParagraphStyle(
            "NegNota",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#111827"),
        ),
        "meta": ParagraphStyle(
            "NegMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#4b5563"),
        ),
        "vazio": ParagraphStyle(
            "NegVazio",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#6b7280"),
        ),
        "resumo": ParagraphStyle(
            "NegResumo",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#374151"),
        ),
    }


def _historico_flow(oportunidade, estilos, largura):
    linhas = []
    notas = list(oportunidade.notas_negociacao.all())
    feedback = (getattr(oportunidade, "feedback_pos_venda", "") or "").strip()
    if not notas and not feedback:
        linhas.append([Paragraph("Sem histórico de negociação.", estilos["vazio"])])
    else:
        linhas.append([Paragraph("HISTÓRICO DE NEGOCIAÇÃO", estilos["rotulo"])])
        for nota in notas:
            quando = getattr(nota, "created_at", None)
            if quando is not None and timezone.is_aware(quando):
                quando = timezone.localtime(quando)
            quando_txt = quando.strftime("%d/%m/%Y %H:%M") if quando else ""
            tipo = _TIPOS_NOTA.get(getattr(nota, "tipo", ""), "Registro")
            autor = (getattr(nota, "autor_nome", "") or "").strip()
            cabeca = " — ".join(parte for parte in (tipo, quando_txt, autor) if parte)
            linhas.append([Paragraph(escape(cabeca), estilos["meta"])])
            linhas.append([_paragrafo(getattr(nota, "texto", "") or "", estilos["nota"])])
        if feedback:
            linhas.append([Paragraph("OPINIÃO DO CLIENTE (PÓS-VENDA)", estilos["rotulo"])])
            if not texto_tem_data(feedback):
                atualizado = getattr(oportunidade, "updated_at", None)
                if atualizado is not None and timezone.is_aware(atualizado):
                    atualizado = timezone.localtime(atualizado)
                if atualizado:
                    linhas.append([Paragraph(
                        escape(f"Registrado em {atualizado.strftime('%d/%m/%Y %H:%M')}"),
                        estilos["meta"],
                    )])
            linhas.append([_paragrafo(feedback, estilos["nota"])])

    tabela = Table(linhas, colWidths=[largura])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return tabela


def _cartao_cliente(oportunidade, estilos, largura):
    nome = nome_do_cliente(oportunidade)
    telefone = telefone_para_exibicao(oportunidade) or "Não informado"
    contato = linha_contato_empresa(oportunidade)
    ganho = _data_ganho(oportunidade)
    ganho_txt = ganho.strftime("%d/%m/%Y") if ganho else "—"
    vendedor = getattr(getattr(oportunidade, "vendedor", None), "nome", "") or "—"
    empresa = empresa_da_oportunidade(oportunidade)
    documento = documento_da_oportunidade(oportunidade)
    oportunidade_celula = [Paragraph("OPORTUNIDADE", estilos["rotulo"]), _paragrafo(empresa, estilos["valor"])]
    if documento:
        oportunidade_celula.append(_paragrafo(documento, estilos["documento"]))

    if contato:
        faixa = Table(
            [[_paragrafo(contato, estilos["nome"])]],
            colWidths=[largura],
        )
    else:
        faixa = Table(
            [[_paragrafo(nome, estilos["nome"]), _paragrafo(telefone, estilos["telefone"])]],
            colWidths=[largura * 0.62, largura * 0.38],
        )
    faixa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0176d3")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    dados = Table(
        [[
            oportunidade_celula,
            [Paragraph("VALOR", estilos["rotulo"]), _paragrafo(_brl(oportunidade.valor), estilos["valor"])],
            [Paragraph("GANHO EM", estilos["rotulo"]), _paragrafo(ganho_txt, estilos["valor"])],
            [Paragraph("VENDEDOR", estilos["rotulo"]), _paragrafo(vendedor, estilos["valor"])],
        ]],
        colWidths=[largura * 0.40, largura * 0.18, largura * 0.16, largura * 0.26],
    )
    dados.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (1, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    moldura = Table(
        [[faixa], [dados], [_historico_flow(oportunidade, estilos, largura)]],
        colWidths=[largura],
    )
    moldura.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#d1d5db")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return KeepTogether([moldura, Spacer(1, 0.28 * cm)])


def _montar_pagina(logo):
    """Logo centralizada no topo de cada página e o número no rodapé."""

    def _pagina(canvas, doc):
        canvas.saveState()
        if logo:
            dados, largura_img, altura_img = logo
            x = (A4[0] - largura_img) / 2
            y = A4[1] - 0.55 * cm - altura_img
            canvas.drawImage(
                ImageReader(BytesIO(dados)),
                x,
                y,
                width=largura_img,
                height=altura_img,
                preserveAspectRatio=True,
                mask="auto",
            )
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawString(1.4 * cm, 0.9 * cm, TITULO_RELATORIO)
        canvas.drawRightString(A4[0] - 1.4 * cm, 0.9 * cm, f"Página {doc.page}")
        canvas.restoreState()

    return _pagina


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
    logo = carregar_logo_relatorio(_obter_logo_loja(loja_id))
    margem_topo = 1.4 * cm
    if logo:
        margem_topo = 0.55 * cm + logo[2] + 0.35 * cm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=margem_topo,
        bottomMargin=1.6 * cm,
    )
    pagina = _montar_pagina(logo)
    estilos = _estilos_cartao()
    titulo = ParagraphStyle(
        "TituloControle",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0176d3"),
        spaceAfter=4,
    )
    largura = A4[0] - 2.8 * cm

    data_inicio, data_fim = calcular_periodo(periodo)
    if data_inicio_custom and data_fim_custom:
        from datetime import date as date_type

        try:
            data_inicio = date_type.fromisoformat(str(data_inicio_custom))
            data_fim = date_type.fromisoformat(str(data_fim_custom))
        except (TypeError, ValueError):
            pass

    elements = [
        Paragraph(TITULO_RELATORIO, titulo),
        Spacer(1, 0.15 * cm),
        Paragraph(
            f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
            estilos["resumo"],
        ),
        Spacer(1, 0.25 * cm),
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
    quantidade = len(linhas)
    resumo_qtd = "1 oportunidade ganha" if quantidade == 1 else f"{quantidade} oportunidades ganhas"
    elements.append(Paragraph(resumo_qtd, estilos["resumo"]))
    elements.append(Spacer(1, 0.35 * cm))

    if not linhas:
        elements.append(Paragraph("Nenhuma oportunidade ganha neste período.", estilos["resumo"]))
        doc.build(elements, onFirstPage=pagina, onLaterPages=pagina)
        buffer.seek(0)
        return buffer

    for opp in linhas:
        elements.append(_cartao_cliente(opp, estilos, largura))

    doc.build(elements, onFirstPage=pagina, onLaterPages=pagina)
    buffer.seek(0)
    return buffer
