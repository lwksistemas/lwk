"""Seções reutilizáveis do PDF de proposta/contrato."""
import logging
from io import BytesIO
from xml.sax.saxutils import escape

from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily, stringWidth
from reportlab.platypus import HRFlowable, Image, Paragraph, Spacer, Table, TableStyle

from core.phone_utils import telefone_exibicao_brasileiro

from .formatters import (
    _formatar_endereco_lead,
    _formatar_nome_usuario,
    _formatar_timestamp_local,
    _formatar_valor,
    _html_to_paragraphs,
    _title_case_endereco,
    baixar_logo_pdf,
    blocos_formatados,
    descricoes_da_oportunidade,
    titulo_de_bloco,
)

logger = logging.getLogger(__name__)

FONTE = "DejaVu"
FONTE_NEGRITO = "DejaVu-Bold"
_pasta_fontes = Path(__file__).resolve().parent / "fonts"
if FONTE not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont(FONTE, str(_pasta_fontes / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONTE_NEGRITO, str(_pasta_fontes / "DejaVuSans-Bold.ttf")))
    registerFontFamily(FONTE, normal=FONTE, bold=FONTE_NEGRITO, italic=FONTE, boldItalic=FONTE_NEGRITO)


def nome_item_documento(nome, prestadora_nome="") -> str:
    """Nome do item na proposta, sem repetir o tipo nem a marca da prestadora."""
    texto = (nome or "").strip()
    marcas = []
    bruto = (prestadora_nome or "").strip()
    if bruto:
        principal = bruto.split("—")[0].split("–")[0].strip()
        if principal:
            marcas.append(principal)
            primeira = principal.split()[0]
            if primeira and primeira not in marcas:
                marcas.append(primeira)
    for marca in marcas:
        if texto.upper().startswith(marca.upper()):
            resto = texto[len(marca):].lstrip(" —-–")
            if resto:
                return resto
    return texto or "Item"

def _recorte_logo(conteudo: bytes) -> bytes:
    """Tira a margem branca ou transparente para as duas marcas ficarem do mesmo tamanho."""
    imagem = PILImage.open(BytesIO(conteudo))
    imagem.load()
    if "A" in imagem.getbands():
        caixa = imagem.getchannel("A").point(lambda alpha: 255 if alpha > 12 else 0).getbbox()
    else:
        caixa = imagem.convert("RGB").convert("L").point(lambda valor: 0 if valor > 242 else 255).getbbox()
    if not caixa:
        return conteudo
    recorte = imagem.crop(caixa)
    if recorte.size[0] < 8 or recorte.size[1] < 8:
        return conteudo
    saida = BytesIO()
    recorte.save(saida, format="PNG")
    return saida.getvalue()


def _imagem_cabecalho(conteudo, max_w, max_h):
    """Monta a logo no tamanho do cabeçalho, sem esticar."""
    conteudo = _recorte_logo(conteudo)
    pil_img = PILImage.open(BytesIO(conteudo))
    largura_px, altura_px = pil_img.size
    if not largura_px or not altura_px:
        return None
    proporcao = altura_px / float(largura_px)
    largura = max_w
    altura = largura * proporcao
    if altura > max_h:
        altura = max_h
        largura = altura / proporcao
    imagem = Image(BytesIO(conteudo), width=largura, height=altura)
    imagem.hAlign = "CENTER"
    return imagem


def _par_mesma_altura(esquerda: bytes, direita: bytes, titulo: str, largura_util=None):
    """As duas logos saem com a mesma altura e deixam o título em uma linha."""
    esquerda = _recorte_logo(esquerda)
    direita = _recorte_logo(direita)
    proporcoes = []
    for conteudo in (esquerda, direita):
        largura_px, altura_px = PILImage.open(BytesIO(conteudo)).size
        proporcoes.append(largura_px / float(altura_px))
    util = largura_util if largura_util is not None else A4[0] - 4 * cm
    reserva_titulo = stringWidth(titulo, "Helvetica-Bold", 14) + 2.2 * cm
    altura = 1.6 * cm
    if altura * sum(proporcoes) > util - reserva_titulo:
        altura = (util - reserva_titulo) / sum(proporcoes)
    imagens = []
    for conteudo, proporcao in zip((esquerda, direita), proporcoes, strict=True):
        imagem = Image(BytesIO(conteudo), width=altura * proporcao, height=altura)
        imagem.hAlign = "CENTER"
        imagens.append(imagem)
    return imagens[0], imagens[1]


def _build_cabecalho(elements, logo_url, titulo, logo_direita_url=None, largura=None):
    """Logo principal à esquerda, título no centro e a logo do login à direita."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HeaderTitle", parent=styles["Heading1"], fontSize=14,
        textColor=colors.HexColor("#0176d3"), alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=0, leading=16,
    )
    esquerda = baixar_logo_pdf(logo_url) if logo_url else None
    direita_url = (logo_direita_url or "").strip()
    if direita_url and direita_url == (logo_url or "").strip():
        direita_url = ""
    direita = baixar_logo_pdf(direita_url) if direita_url else None
    if not esquerda and not direita:
        elements.append(Paragraph(titulo, title_style))
        return
    if esquerda and direita:
        try:
            util = largura if largura is not None else A4[0] - 4 * cm
            img_esquerda, img_direita = _par_mesma_altura(esquerda, direita, titulo, util)
            folga = 0.7 * cm
            coluna_esquerda = img_esquerda.drawWidth + folga
            coluna_direita = img_direita.drawWidth + folga
            meio = util - coluna_esquerda - coluna_direita
            tabela = Table(
                [[img_esquerda, Paragraph(titulo, title_style), img_direita]],
                colWidths=[coluna_esquerda, meio, coluna_direita],
            )
            tabela.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), folga),
                ("LEFTPADDING", (1, 0), (1, 0), 4),
                ("RIGHTPADDING", (1, 0), (1, 0), 4),
                ("LEFTPADDING", (2, 0), (2, 0), folga),
                ("RIGHTPADDING", (2, 0), (2, 0), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(tabela)
            return
        except Exception as exc:
            logger.warning("Erro ao montar as duas logos da proposta: %s", exc)
    unico = esquerda or direita
    title_style.alignment = TA_LEFT
    try:
        img = _imagem_cabecalho(unico, 6 * cm, 3 * cm)
        if not img:
            raise ValueError("Logo não disponível")
        tabela = Table([[img, Paragraph(titulo, title_style)]], colWidths=[6.5 * cm, None])
        tabela.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(tabela)
    except Exception as exc:
        logger.warning("Erro ao adicionar logo no PDF: %s", exc)
        title_style.alignment = TA_CENTER
        elements.append(Paragraph(titulo, title_style))


def _build_secao_empresa(elements, loja_data, style, titulo="Dados da Empresa"):
    """Adiciona seção Dados da Empresa."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecEmpresa", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph(f"<b>{escape(titulo)}</b>", section))
    linhas = [f"<b>Nome:</b> {loja_data.get('nome') or '—'}"]
    if loja_data.get("endereco"):
        linhas.append(f"<b>Endereço:</b> {_title_case_endereco(loja_data['endereco'])}")
    if loja_data.get("cpf_cnpj"):
        linhas.append(f"<b>CPF/CNPJ:</b> {loja_data['cpf_cnpj']}")
    if loja_data.get("telefone"):
        tel_fmt = telefone_exibicao_brasileiro(loja_data["telefone"]) or loja_data["telefone"].strip()
        linhas.append(f"<b>Telefone:</b> {tel_fmt}")
    if loja_data.get("admin_nome"):
        linhas.append(f"<b>Responsável:</b> {loja_data['admin_nome']}")
    if loja_data.get("admin_email"):
        linhas.append(f"<b>Email:</b> {loja_data['admin_email']}")
    for ln in linhas:
        elements.append(Paragraph(ln, style))


def _build_secao_cliente(elements, lead, style, titulo="Dados do Cliente"):
    """Adiciona seção Dados do Cliente."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecCliente", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph(f"<b>{escape(titulo)}</b>", section))
    conta = getattr(lead, "conta", None)
    if conta:
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", style))
        empresa_nome = conta.razao_social or conta.nome or ""
        if empresa_nome:
            elements.append(Paragraph(f"<b>Empresa:</b> {empresa_nome}", style))
    else:
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", style))
    if getattr(lead, "cpf_cnpj", ""):
        elements.append(Paragraph(f"<b>CPF/CNPJ:</b> {lead.cpf_cnpj}", style))
    if getattr(lead, "telefone", ""):
        tel_fmt = telefone_exibicao_brasileiro(lead.telefone) or (lead.telefone or "").strip()
        elements.append(Paragraph(f"<b>Telefone:</b> {tel_fmt}", style))
    if getattr(lead, "email", ""):
        elements.append(Paragraph(f"<b>Email:</b> {lead.email}", style))
    elements.append(Paragraph(f"<b>Endereço:</b> {_formatar_endereco_lead(lead)}", style))


def _build_secao_produtos(elements, oportunidade, style, incluir_recorrencia=True, titulo="Produtos e Serviços da Oportunidade"):
    """Adiciona seção Produtos e Serviços."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecProd", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph(f"<b>{escape(titulo)}</b>", section))
    itens = list(oportunidade.itens.select_related("produto_servico").all()) if oportunidade else []
    if not itens:
        elements.append(Paragraph("Nenhum item cadastrado.", style))
        return 0, 0, 0, 0, 0
    nome_style = ParagraphStyle("ItemNomePdf", fontName="Helvetica", fontSize=8, leading=10)
    if incluir_recorrencia:
        table_data = [["Item", "Recorrência", "Qtd", "Preço Unit.", "Subtotal"]]
    else:
        table_data = [["Item", "Qtd", "Preço Unit.", "Subtotal"]]
    valor_unico = 0
    valor_mensal = 0
    valor_trimestral = 0
    valor_semestral = 0
    valor_anual = 0
    for item in itens:
        ps = item.produto_servico
        prestadora = getattr(oportunidade, "empresa_prestadora", None)
        marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
        nome = Paragraph(escape(nome_item_documento(getattr(ps, "nome", ""), marca)), nome_style)
        recorrencia = getattr(ps, "recorrencia", "unico") or "unico"
        recorrencia_label = {
            "unico": "Único",
            "mensal": "Mensal",
            "trimestral": "Trimestral",
            "semestral": "Semestral",
            "anual": "Anual",
        }.get(recorrencia, recorrencia)
        qtd = str(item.quantidade) if item.quantidade is not None else "1"
        preco = _formatar_valor(item.preco_unitario)
        sub = item.quantidade * item.preco_unitario if item.quantidade and item.preco_unitario else 0
        subtotal = _formatar_valor(sub)
        if incluir_recorrencia:
            table_data.append([nome, recorrencia_label, qtd, preco, subtotal])
        else:
            table_data.append([nome, qtd, preco, subtotal])
        if recorrencia == "unico":
            valor_unico += float(sub)
        elif recorrencia == "mensal":
            valor_mensal += float(sub)
        elif recorrencia == "trimestral":
            valor_trimestral += float(sub)
        elif recorrencia == "semestral":
            valor_semestral += float(sub)
        elif recorrencia == "anual":
            valor_anual += float(sub)
    largura = A4[0] - 4 * cm
    if incluir_recorrencia:
        col_widths = [largura - 230, 70, 30, 65, 65]
    else:
        col_widths = [largura - 175, 40, 70, 65]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3f3ff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    t.hAlign = "LEFT"
    elements.append(t)
    return valor_unico, valor_mensal, valor_trimestral, valor_semestral, valor_anual


def _build_secao_desconto(elements, documento, style):
    """Adiciona resumo financeiro com tabela visual."""
    valor_total = documento.valor_total
    desconto_valor = getattr(documento, "desconto_valor", None) or 0
    has_desconto = desconto_valor and float(desconto_valor) > 0

    # Buscar valores de adesão/mensal/anual se disponíveis nos itens
    oportunidade = getattr(documento, "oportunidade", None)
    valor_unico = 0
    valor_mensal = 0
    valor_trimestral = 0
    valor_semestral = 0
    valor_anual = 0
    if oportunidade:
        try:
            for item in oportunidade.itens.select_related("produto_servico").all():
                ps = item.produto_servico
                recorrencia = getattr(ps, "recorrencia", "unico") or "unico"
                sub = float(item.quantidade * item.preco_unitario) if item.quantidade and item.preco_unitario else 0
                if recorrencia == "unico":
                    valor_unico += sub
                elif recorrencia == "mensal":
                    valor_mensal += sub
                elif recorrencia == "trimestral":
                    valor_trimestral += sub
                elif recorrencia == "semestral":
                    valor_semestral += sub
                elif recorrencia == "anual":
                    valor_anual += sub
        except Exception:
            pass

    # Montar tabela de resumo financeiro
    resumo_data = []
    if valor_unico > 0:
        resumo_data.append(["Adesão/Implantação:", _formatar_valor(valor_unico)])
    if valor_mensal > 0:
        resumo_data.append(["Valor Mensal:", f"{_formatar_valor(valor_mensal)}/mês"])
    if valor_trimestral > 0:
        resumo_data.append(["Valor Trimestral:", f"{_formatar_valor(valor_trimestral)}/trimestre"])
    if valor_semestral > 0:
        resumo_data.append(["Valor Semestral:", f"{_formatar_valor(valor_semestral)}/semestre"])
    if valor_anual > 0:
        resumo_data.append(["Valor Anual:", f"{_formatar_valor(valor_anual)}/ano"])
    resumo_data.append(["Valor Total:", _formatar_valor(valor_total)])
    if has_desconto:
        desconto_tipo = getattr(documento, "desconto_tipo", "percentual")
        if desconto_tipo == "percentual":
            resumo_data.append(["Desconto:", f"{desconto_valor}%"])
        else:
            resumo_data.append(["Desconto:", _formatar_valor(desconto_valor)])
        valor_final = getattr(documento, "valor_com_desconto", valor_total)
        resumo_data.append(["Valor com Desconto:", _formatar_valor(valor_final)])

    t = Table(resumo_data, colWidths=[5 * cm, 5 * cm])
    style_cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#0176d3")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e5e7eb")),
    ]
    # Destacar última linha (valor final)
    last = len(resumo_data) - 1
    style_cmds.append(("FONTNAME", (0, last), (-1, last), "Helvetica-Bold"))
    style_cmds.append(("FONTSIZE", (0, last), (-1, last), 10))
    style_cmds.append(("BACKGROUND", (0, last), (-1, last), colors.HexColor("#e0f2fe")))
    style_cmds.append(("TEXTCOLOR", (1, last), (1, last), colors.HexColor("#0176d3")))
    t.setStyle(TableStyle(style_cmds))
    t.hAlign = "LEFT"
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(t)
    elements.append(Spacer(1, 0.2 * cm))


def _build_resumo_investimento(elements, documento, totais, style):
    """Pagamento inicial e cobranças seguintes da proposta."""
    from .formatters import linhas_resumo_investimento

    unico, mensal, trimestral, semestral, anual = totais
    linhas, frase = linhas_resumo_investimento(
        unico=unico,
        mensal=mensal,
        trimestral=trimestral,
        semestral=semestral,
        anual=anual,
        valor_total=getattr(documento, "valor_total", None),
        desconto_valor=getattr(documento, "desconto_valor", None) or 0,
        desconto_tipo=getattr(documento, "desconto_tipo", "percentual") or "percentual",
        valor_com_desconto=getattr(documento, "valor_com_desconto", None),
    )
    if not linhas:
        return
    resumo_data = [[rotulo, valor] for rotulo, valor in linhas]
    t = Table(resumo_data, colWidths=[5.4 * cm, 5 * cm])
    style_cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#0176d3")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e5e7eb")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
    ]
    t.setStyle(TableStyle(style_cmds))
    t.hAlign = "LEFT"
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(t)
    if frase:
        nota = ParagraphStyle("NotaInvestimento", parent=style, fontSize=8, leading=11, spaceBefore=3, spaceAfter=2)
        elements.append(Paragraph(escape(frase), nota))
    elements.append(Spacer(1, 0.15 * cm))


def _build_secao_incluidos(elements, oportunidade, style):
    """Descrição cadastrada de cada serviço, fora do texto do template."""
    from .formatters import descricao_util_na_proposta

    if oportunidade is None:
        return
    relacao = getattr(oportunidade, "itens", None)
    if relacao is None:
        return
    itens = relacao.select_related("produto_servico").all() if hasattr(relacao, "select_related") else relacao
    prestadora = getattr(oportunidade, "empresa_prestadora", None)
    marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
    vistos = set()
    blocos = []
    for item in itens:
        produto = getattr(item, "produto_servico", None)
        texto = " ".join((getattr(produto, "descricao", None) or "").split())
        if not descricao_util_na_proposta(texto) or texto in vistos:
            continue
        vistos.add(texto)
        nome = nome_item_documento(getattr(produto, "nome", ""), marca)
        blocos.append((nome, texto))
    if not blocos:
        return
    section = ParagraphStyle("SecIncluidos", parent=style, fontSize=10, spaceBefore=4, spaceAfter=2)
    elements.append(Paragraph("<b>O que está incluído</b>", section))
    nome_style = ParagraphStyle("IncluidoNome", parent=style, fontName="Helvetica-Bold", fontSize=9, spaceBefore=3, spaceAfter=1)
    texto_style = ParagraphStyle(
        "IncluidoTexto",
        parent=style,
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        spaceBefore=0,
        spaceAfter=3,
    )
    for nome, texto in blocos:
        elements.append(Paragraph(escape(nome), nome_style))
        elements.append(Paragraph(escape(texto), texto_style))


def _build_secao_condicoes(elements, paragrafos, style):
    """Texto do template da prestadora: condições, prazo e pagamento."""
    if not paragrafos:
        return
    section = ParagraphStyle("SecCondicoes", parent=style, fontSize=10, spaceBefore=4, spaceAfter=2)
    elements.append(Paragraph("<b>Condições e pagamento</b>", section))
    conteudo_style = ParagraphStyle(
        "CondicoesTexto",
        parent=style,
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        spaceBefore=2,
        spaceAfter=4,
    )
    for paragrafo in paragrafos:
        if paragrafo == "":
            elements.append(Spacer(1, 0.15 * cm))
        else:
            elements.append(Paragraph(escape(paragrafo), conteudo_style))


def _build_secao_conteudo(elements, conteudo, style):
    """Adiciona seção Conteúdo."""
    section = ParagraphStyle("SecConteudo", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph("<b>Conteúdo</b>", section))
    styles = getSampleStyleSheet()
    conteudo_style = ParagraphStyle(
        "ConteudoJustificado",
        parent=styles["Normal"],
        fontSize=style.fontSize if hasattr(style, "fontSize") else 9,
        leading=style.leading if hasattr(style, "leading") else 11,
        alignment=TA_JUSTIFY,
        spaceBefore=2,
        spaceAfter=4,
    )
    for p in _html_to_paragraphs(conteudo)[:100]:
        if p == "":
            elements.append(Spacer(1, 0.2 * cm))
        else:
            elements.append(Paragraph(escape(p), conteudo_style))


COR_PROPOSTA = colors.HexColor("#1B365D")
COR_TEXTO = colors.HexColor("#1F2937")
COR_FAIXA = colors.HexColor("#F4F7FB")


def _par_logos(url_esquerda, url_direita):
    """Baixa cada logo uma vez. A segunda folha reutiliza os mesmos arquivos."""
    esquerda = baixar_logo_pdf(url_esquerda) if url_esquerda else None
    direita_url = (url_direita or "").strip()
    if direita_url and direita_url == (url_esquerda or "").strip():
        direita_url = ""
    direita = baixar_logo_pdf(direita_url) if direita_url else None
    return esquerda, direita


def _build_faixa_logos(elements, esquerda, direita):
    """Logos nas laterais, sem título no meio."""
    if not esquerda and not direita:
        return
    altura_max = 1.9 * cm
    util = A4[0] - 3.1 * cm

    def montar(conteudo):
        recorte = _recorte_logo(conteudo)
        largura_px, altura_px = PILImage.open(BytesIO(recorte)).size
        if not largura_px or not altura_px:
            return None
        proporcao = largura_px / float(altura_px)
        largura = min(altura_max * proporcao, util * 0.46)
        return Image(BytesIO(recorte), width=largura, height=largura / proporcao)

    img_esquerda = montar(esquerda) if esquerda else None
    img_direita = montar(direita) if direita else None
    if img_esquerda and img_direita:
        meio = max(util - img_esquerda.drawWidth - img_direita.drawWidth, 0.3 * cm)
        tabela = Table(
            [[img_esquerda, "", img_direita]],
            colWidths=[img_esquerda.drawWidth, meio, img_direita.drawWidth],
        )
        tabela.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(tabela)
    else:
        imagem = img_esquerda or img_direita
        imagem.hAlign = "LEFT" if img_esquerda else "RIGHT"
        elements.append(imagem)
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=COR_PROPOSTA, spaceBefore=1, spaceAfter=8))


def _estilo_titulo_proposta():
    return ParagraphStyle(
        "TituloPropostaVisual",
        fontName=FONTE_NEGRITO,
        fontSize=20,
        textColor=COR_PROPOSTA,
        alignment=TA_LEFT,
        leading=24,
        spaceBefore=2,
        spaceAfter=2,
    )


def _estilo_titulo_recursos():
    return ParagraphStyle(
        "TituloRecursosVisual",
        fontName=FONTE_NEGRITO,
        fontSize=18,
        textColor=COR_PROPOSTA,
        alignment=TA_LEFT,
        leading=22,
        spaceBefore=2,
        spaceAfter=8,
    )


def _estilo_subtitulo_proposta():
    return ParagraphStyle(
        "SubtituloPropostaVisual",
        fontName=FONTE,
        fontSize=10,
        textColor=colors.HexColor("#4B5563"),
        leading=13,
        spaceBefore=4,
        spaceAfter=8,
    )


def _estilo_secao_proposta(fonte=None, tamanho=11):
    nome = fonte or FONTE_NEGRITO
    return ParagraphStyle(
        f"SecaoProposta{nome}{tamanho}",
        fontName=nome,
        fontSize=tamanho,
        textColor=COR_PROPOSTA,
        leading=tamanho + 3,
        spaceBefore=0,
        spaceAfter=4,
    )


def _estilo_corpo_proposta(fonte=None, tamanho=9):
    nome = fonte or FONTE
    return ParagraphStyle(
        f"CorpoProposta{nome}{tamanho}",
        fontName=nome,
        fontSize=tamanho,
        textColor=COR_TEXTO,
        leading=tamanho + 4,
        spaceBefore=0,
        spaceAfter=0,
    )


def _titulo_numerado(elements, numero, titulo, estilo=None):
    elements.append(Paragraph(f"{numero:02d}  {escape(titulo)}", estilo or _estilo_secao_proposta()))


def _markup_linha(texto: str) -> str:
    bruto = " ".join((texto or "").split())
    if not bruto:
        return ""
    if bruto.lower().startswith("banco ") or "agência" in bruto.lower() or "agencia" in bruto.lower():
        return f"<b>{escape(bruto)}</b>"
    if ":" in bruto and "•" not in bruto.split(":", 1)[0]:
        lead, resto = bruto.split(":", 1)
        if 0 < len(lead) <= 80:
            return f"<b>{escape(lead)}:</b> {escape(resto.strip())}"
    return escape(bruto)


def _linha_cadastro(rotulo, valor, style):
    texto = " ".join(str(valor or "").split())
    if not texto or texto == "—":
        return None
    return Paragraph(f"<b>{escape(rotulo)}:</b> {escape(texto)}", style)


def _endereco_proposta(lead) -> str:
    texto = _formatar_endereco_lead(lead).replace("nº ", "")
    return "" if texto == "—" else texto


def _texto_cadastro(valor) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _rotulo_documento(valor) -> str:
    import re
    digits = re.sub(r"\D", "", _texto_cadastro(valor))
    if len(digits) == 11:
        return "CPF"
    if len(digits) == 14:
        return "CNPJ"
    return "CPF/CNPJ"


def _valor_da_conta(lead, campo) -> str:
    conta = getattr(lead, "conta", None)
    if conta is None:
        return ""
    return _texto_cadastro(getattr(conta, campo, None))


def _nomes_da_empresa(lead):
    """Razão social e nome fantasia. O nome da conta é o nome fantasia."""
    razao = _valor_da_conta(lead, "razao_social") or _texto_cadastro(getattr(lead, "empresa", None))
    fantasia = _valor_da_conta(lead, "nome")
    return razao, fantasia


def _documento_do_cliente(lead) -> str:
    documento = _texto_cadastro(getattr(lead, "cpf_cnpj", None))
    return documento or _valor_da_conta(lead, "cnpj")


def _pessoa_do_contato(lead, *nomes_empresa) -> str:
    contato = getattr(lead, "contato", None)
    pessoa = _texto_cadastro(getattr(contato, "nome", None)) if contato is not None else ""
    if not pessoa:
        pessoa = _texto_cadastro(getattr(lead, "nome", None))
    empresas = {nome.casefold() for nome in nomes_empresa if nome}
    if pessoa.casefold() in empresas:
        return ""
    return pessoa


def _linhas_do_cliente(lead, style):
    """Empresa: razão social e nome fantasia, com a pessoa no contato. Pessoa física continua Cliente."""
    razao, fantasia = _nomes_da_empresa(lead)
    documento = _documento_do_cliente(lead)
    pessoa = _texto_cadastro(getattr(lead, "nome", None))
    empresa = _rotulo_documento(documento) == "CNPJ" or bool(razao or fantasia)
    if empresa and not razao and not fantasia:
        razao = pessoa
    linhas = []
    if empresa:
        if razao:
            linhas.append(_linha_cadastro("Razão social", razao, style))
        if fantasia:
            linhas.append(_linha_cadastro("Nome fantasia", fantasia, style))
        contato = _pessoa_do_contato(lead, razao, fantasia)
    else:
        linhas.append(_linha_cadastro("Cliente", pessoa, style))
        contato = ""
    linhas.append(_linha_cadastro(_rotulo_documento(documento), documento, style))
    linhas.append(_linha_cadastro("Endereço", _endereco_proposta(lead), style))
    telefone = _texto_cadastro(getattr(lead, "telefone", None))
    if telefone:
        telefone = telefone_exibicao_brasileiro(telefone) or telefone
    email = _texto_cadastro(getattr(lead, "email", None))
    if contato:
        partes = [contato]
        if telefone:
            partes.append(telefone)
        if email:
            partes.append(email)
        linhas.append(_linha_cadastro("Contato", " • ".join(partes), style))
    elif telefone and email:
        linhas.append(_linha_cadastro("Contato", f"{telefone} • {email}", style))
    elif telefone:
        linhas.append(_linha_cadastro("Contato", telefone, style))
    else:
        linhas.append(_linha_cadastro("E-mail", email, style))
    return linhas


def _build_identificacao_visual(elements, loja_data, lead):
    """Representante e cliente em linhas curtas, com os dados do cadastro."""
    style = _estilo_corpo_proposta()
    _titulo_numerado(elements, 1, "Identificação")
    loja_data = loja_data or {}
    linhas = []
    if loja_data.get("nome"):
        linhas.append(_linha_cadastro("Representante", loja_data.get("nome"), style))
    documento = loja_data.get("cpf_cnpj") or ""
    linhas.append(_linha_cadastro(_rotulo_documento(documento), documento, style))
    linhas.append(_linha_cadastro("Endereço", loja_data.get("endereco"), style))
    responsavel = _texto_cadastro(loja_data.get("admin_nome"))
    telefone = _texto_cadastro(loja_data.get("telefone"))
    if telefone:
        telefone = telefone_exibicao_brasileiro(telefone) or telefone
    if responsavel and telefone:
        linhas.append(_linha_cadastro("Responsável", f"{responsavel} • {telefone}", style))
    else:
        linhas.append(_linha_cadastro("Responsável", responsavel, style))
        linhas.append(_linha_cadastro("Telefone", telefone, style))
    linhas.append(_linha_cadastro("E-mail", loja_data.get("admin_email"), style))
    for linha in linhas:
        if linha is not None:
            elements.append(linha)
    if lead is None:
        return
    elements.append(Spacer(1, 0.22 * cm))
    for linha in _linhas_do_cliente(lead, style):
        if linha is not None:
            elements.append(linha)


def _itens_oportunidade(oportunidade):
    if oportunidade is None:
        return []
    relacao = getattr(oportunidade, "itens", None)
    if relacao is None:
        return []
    if hasattr(relacao, "select_related"):
        return list(relacao.select_related("produto_servico").all())
    return list(relacao)


def _build_tabela_investimento_visual(elements, oportunidade):
    """Tabela Serviço, Quantidade, Cobrança e Valor. O valor já multiplica a quantidade."""
    _titulo_numerado(elements, 2, "Investimento")
    itens = _itens_oportunidade(oportunidade)
    if not itens:
        elements.append(Paragraph("Nenhum item cadastrado.", _estilo_corpo_proposta()))
        return 0, 0, 0, 0, 0
    prestadora = getattr(oportunidade, "empresa_prestadora", None)
    marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
    header_style = ParagraphStyle(
        "HeadInvestimento",
        fontName=FONTE_NEGRITO,
        fontSize=8,
        textColor=colors.white,
        leading=10,
    )
    header_centro = ParagraphStyle("HeadInvestimentoCentro", parent=header_style, alignment=TA_CENTER)
    header_direita = ParagraphStyle("HeadInvestimentoDireita", parent=header_style, alignment=TA_RIGHT)
    nome_style = ParagraphStyle("NomeInvestimento", fontName=FONTE, fontSize=8, leading=10, textColor=COR_TEXTO)
    celula = ParagraphStyle("CelulaInvestimento", fontName=FONTE, fontSize=8, leading=10, textColor=COR_TEXTO, alignment=TA_CENTER)
    valor_style = ParagraphStyle("ValorInvestimento", fontName=FONTE, fontSize=8, leading=10, textColor=COR_TEXTO, alignment=TA_RIGHT)
    mostra_unitario = _mostra_valor_unitario(itens)
    cabecalhos = [
        Paragraph("Serviço", header_style),
        Paragraph("Qtd", header_centro),
        Paragraph("Cobrança", header_centro),
    ]
    if mostra_unitario:
        cabecalhos.append(Paragraph("Valor un.", header_direita))
        cabecalhos.append(Paragraph("Total", header_direita))
    else:
        cabecalhos.append(Paragraph("Valor", header_direita))
    table_data = [cabecalhos]
    totais = {"unico": 0, "mensal": 0, "trimestral": 0, "semestral": 0, "anual": 0}
    rotulos = {
        "unico": "Única",
        "mensal": "Mensal",
        "trimestral": "Trimestral",
        "semestral": "Semestral",
        "anual": "Anual",
    }
    for item in itens:
        produto = getattr(item, "produto_servico", None)
        nome = nome_item_documento(getattr(produto, "nome", ""), marca)
        quantidade = getattr(item, "quantidade", 1)
        recorrencia = getattr(produto, "recorrencia", "unico") or "unico"
        subtotal = _subtotal_item(item)
        totais[recorrencia] = totais.get(recorrencia, 0) + subtotal
        linha = [
            Paragraph(escape(nome), nome_style),
            Paragraph(_quantidade_texto(quantidade), celula),
            Paragraph(rotulos.get(recorrencia, recorrencia), celula),
        ]
        if mostra_unitario:
            linha.append(Paragraph(_formatar_valor(_preco_unitario_item(item)), valor_style))
        linha.append(Paragraph(_formatar_valor(subtotal), valor_style))
        table_data.append(linha)
    largura = A4[0] - 3.1 * cm
    if mostra_unitario:
        colunas = [largura - 10.6 * cm, 1.6 * cm, 2.8 * cm, 3.1 * cm, 3.1 * cm]
        alinhamento_valor = ("ALIGN", (3, 0), (4, -1), "RIGHT")
    else:
        colunas = [largura - 8.2 * cm, 1.8 * cm, 3.2 * cm, 3.2 * cm]
        alinhamento_valor = ("ALIGN", (3, 0), (3, -1), "RIGHT")
    tabela = Table(table_data, colWidths=colunas)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PROPOSTA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_FAIXA]),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        alinhamento_valor,
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    tabela.hAlign = "LEFT"
    elements.append(tabela)
    return totais["unico"], totais["mensal"], totais["trimestral"], totais["semestral"], totais["anual"]


def _quantidade_numero(quantidade) -> float:
    if quantidade is None or quantidade == "":
        return 1.0
    try:
        return float(quantidade)
    except (TypeError, ValueError):
        return 1.0


def _mostra_valor_unitario(itens) -> bool:
    """A coluna do valor por unidade só entra quando alguma quantidade passa de 1."""
    return any(_quantidade_numero(getattr(item, "quantidade", 1)) > 1 for item in itens or [])


def _quantidade_texto(quantidade) -> str:
    numero = _quantidade_numero(quantidade)
    if numero.is_integer():
        return str(int(numero))
    return f"{numero:.2f}".replace(".", ",")


def _preco_unitario_item(item) -> float:
    preco = getattr(item, "preco_unitario", 0) or 0
    try:
        return float(preco)
    except (TypeError, ValueError):
        return 0


def _subtotal_item(item) -> float:
    quantidade = getattr(item, "quantidade", 0) or 0
    preco = getattr(item, "preco_unitario", 0) or 0
    try:
        return float(quantidade) * float(preco)
    except (TypeError, ValueError):
        return 0


def _build_resumo_visual(elements, documento, totais):
    """Pagamento inicial, o que ele inclui e as cobranças seguintes, em linhas."""
    from .formatters import linhas_resumo_investimento, texto_resumo_visual

    unico, mensal, trimestral, semestral, anual = totais
    linhas, frase = linhas_resumo_investimento(
        unico=unico,
        mensal=mensal,
        trimestral=trimestral,
        semestral=semestral,
        anual=anual,
        valor_total=getattr(documento, "valor_total", None),
        desconto_valor=getattr(documento, "desconto_valor", None) or 0,
        desconto_tipo=getattr(documento, "desconto_tipo", "percentual") or "percentual",
        valor_com_desconto=getattr(documento, "valor_com_desconto", None),
    )
    blocos = texto_resumo_visual(linhas, frase)
    if not blocos:
        return
    elements.append(Spacer(1, 0.35 * cm))
    forte = ParagraphStyle(
        "ResumoForte",
        fontName=FONTE_NEGRITO,
        fontSize=15,
        textColor=COR_PROPOSTA,
        leading=18,
        spaceBefore=2,
        spaceAfter=1,
    )
    seguinte = ParagraphStyle(
        "ResumoSeguinte",
        fontName=FONTE_NEGRITO,
        fontSize=12,
        textColor=COR_PROPOSTA,
        leading=15,
        spaceBefore=4,
        spaceAfter=1,
    )
    nota = ParagraphStyle(
        "ResumoNota",
        fontName=FONTE,
        fontSize=9,
        textColor=COR_TEXTO,
        leading=13,
        spaceBefore=1,
        spaceAfter=1,
    )
    primeiro_negrito = True
    for texto, negrito in blocos:
        if not negrito:
            elements.append(Paragraph(escape(texto), nota))
            continue
        elements.append(Paragraph(escape(texto), forte if primeiro_negrito else seguinte))
        primeiro_negrito = False


def _build_pagamento_inicial_visual(elements, titulo, linhas, fonte=None, fonte_negrito=None, tamanho=9):
    """Texto da primeira folha, abaixo de Mensalidades seguintes."""
    linhas = list(linhas or [])
    if not titulo and not any(_markup_linha(linha) for linha in linhas):
        return
    elements.append(Spacer(1, 0.22 * cm))
    titulo_tamanho = min(tamanho + 2, 16)
    if titulo:
        elements.append(Paragraph(f"<b>{escape(titulo)}</b>", ParagraphStyle(
            f"TituloPagamentoInicial{fonte_negrito or FONTE_NEGRITO}{titulo_tamanho}",
            fontName=fonte_negrito or FONTE_NEGRITO,
            fontSize=titulo_tamanho,
            textColor=COR_PROPOSTA,
            leading=titulo_tamanho + 3,
            spaceBefore=10,
            spaceAfter=4,
        )))
    corpo = _estilo_corpo_proposta(fonte, tamanho)
    for linha in linhas:
        if not " ".join((linha or "").split()):
            elements.append(Spacer(1, 0.35 * cm))
            continue
        markup = _markup_linha(linha)
        if markup:
            elements.append(Paragraph(markup, corpo))


def _descricoes_incluidas(oportunidade):
    from .formatters import descricao_util_na_proposta

    vistos = set()
    blocos = []
    prestadora = getattr(oportunidade, "empresa_prestadora", None) if oportunidade is not None else None
    marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
    for item in _itens_oportunidade(oportunidade):
        produto = getattr(item, "produto_servico", None)
        recorrencia = getattr(produto, "recorrencia", "unico") or "unico"
        if recorrencia == "unico":
            continue
        texto = " ".join((getattr(produto, "descricao", None) or "").split())
        if not descricao_util_na_proposta(texto) or texto in vistos:
            continue
        vistos.add(texto)
        nome = nome_item_documento(getattr(produto, "nome", ""), marca)
        blocos.append((nome, texto))
    return blocos


def _linhas_implantacao(oportunidade):
    from .formatters import descricao_util_na_proposta

    prestadora = getattr(oportunidade, "empresa_prestadora", None) if oportunidade is not None else None
    marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
    linhas = []
    for item in _itens_oportunidade(oportunidade):
        produto = getattr(item, "produto_servico", None)
        recorrencia = getattr(produto, "recorrencia", "unico") or "unico"
        if recorrencia != "unico":
            continue
        nome = nome_item_documento(getattr(produto, "nome", ""), marca)
        valor = _formatar_valor(_subtotal_item(item))
        texto = " ".join((getattr(produto, "descricao", None) or "").split())
        if descricao_util_na_proposta(texto):
            linhas.append(f"{nome} — {valor}: {texto}")
        else:
            linhas.append(f"{nome} — {valor}")
    return linhas


def _sem_acento(texto: str) -> str:
    import unicodedata
    base = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(letra for letra in base if unicodedata.category(letra) != "Mn")


def _estilo_paragrafo_proposta(fonte=None, tamanho=9):
    nome = fonte or FONTE
    return ParagraphStyle(
        f"ParagrafoProposta{nome}{tamanho}",
        fontName=nome,
        fontSize=tamanho,
        textColor=COR_TEXTO,
        leading=tamanho + 4,
        spaceBefore=1,
        spaceAfter=6,
    )


def _build_recursos_visuais(elements, oportunidade, intro, secoes, fonte=None, fonte_negrito=None, tamanho=9):
    """Segunda folha: o que está incluído e as seções escritas no template."""
    corpo = _estilo_paragrafo_proposta(fonte, tamanho)
    estilo_titulo = _estilo_secao_proposta(fonte_negrito, min(tamanho + 2, 16))
    numero = 3
    incluidos = _descricoes_incluidas(oportunidade)
    if incluidos:
        _titulo_numerado(elements, numero, "O que está incluído", estilo_titulo)
        numero += 1
        for nome, texto in incluidos:
            if ":" in texto:
                elements.append(Paragraph(_markup_linha(texto), corpo))
            else:
                elements.append(Paragraph(f"<b>{escape(nome)}:</b> {escape(texto)}", corpo))
    for texto in intro:
        if texto == "":
            elements.append(Spacer(1, 0.12 * cm))
            continue
        elements.append(Paragraph(_markup_linha(texto), corpo))
    implantacao = _linhas_implantacao(oportunidade)
    if implantacao and not any("implant" in _sem_acento(secao["titulo"]) for secao in secoes):
        secoes = list(secoes) + [{"titulo": "Implantação e liberação", "paragrafos": implantacao}]
    for secao in secoes:
        _titulo_numerado(elements, numero, secao["titulo"], estilo_titulo)
        numero += 1
        paragrafos = list(secao["paragrafos"])
        for paragrafo in paragrafos:
            if paragrafo == "":
                elements.append(Spacer(1, 0.12 * cm))
                continue
            elements.append(Paragraph(_markup_linha(paragrafo), corpo))


_FACES_SELECAO = {
    "padrao": ("DejaVu", "DejaVu-Bold"),
    "times": ("Times-Roman", "Times-Bold"),
    "helvetica": ("Helvetica", "Helvetica-Bold"),
    "courier": ("Courier", "Courier-Bold"),
}
_ALINHAR = {"left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT, "justify": TA_JUSTIFY}
_estilo_formatado_seq = 0


def _face_selecionada(tipo, negrito, fonte_padrao, fonte_negrito):
    if tipo in _FACES_SELECAO:
        normal, bold = _FACES_SELECAO[tipo]
        return bold if negrito else normal
    return fonte_negrito if negrito else fonte_padrao


def _estilo_formatado(fonte, tamanho, alinhamento, cor, espaco_depois):
    global _estilo_formatado_seq
    _estilo_formatado_seq += 1
    return ParagraphStyle(
        f"TplFmt{_estilo_formatado_seq}",
        fontName=fonte,
        fontSize=tamanho,
        textColor=cor,
        leading=tamanho + 4,
        alignment=_ALINHAR.get(alinhamento, TA_LEFT),
        spaceBefore=1,
        spaceAfter=espaco_depois,
    )


def _markup_trechos(bloco, fonte_padrao, fonte_negrito, tamanho_padrao, negrito=False):
    partes = []
    for trecho in bloco["trechos"]:
        texto = trecho.get("texto") or ""
        if texto == "":
            continue
        face = _face_selecionada(trecho.get("fonte"), negrito or bool(trecho.get("negrito")), fonte_padrao, fonte_negrito)
        size = trecho.get("tamanho") or tamanho_padrao
        miolo = escape(texto).replace("\n", "<br/>")
        partes.append(f'<font face="{face}" size="{size}">{miolo}</font>')
    return "".join(partes)


def _flowable_bloco(bloco, fonte, fonte_negrito, tamanho, negrito=False, espaco_depois=2):
    texto = (bloco.get("texto") or "").strip()
    if not texto:
        return Spacer(1, 0.35 * cm)
    tem_fonte = any(
        trecho.get("fonte") or trecho.get("tamanho") or trecho.get("negrito")
        for trecho in bloco["trechos"] if trecho.get("texto")
    )
    tamanho_bloco = next((trecho.get("tamanho") for trecho in bloco["trechos"] if trecho.get("tamanho")), None)
    if negrito:
        tamanho_efetivo = tamanho_bloco or min(tamanho + 2, 16)
        fonte_efetiva = _face_selecionada(bloco["trechos"][0].get("fonte") if bloco["trechos"] else None, True, fonte, fonte_negrito)
        cor = COR_PROPOSTA
    else:
        tamanho_efetivo = tamanho_bloco or tamanho
        fonte_efetiva = fonte
        cor = COR_TEXTO
    estilo = _estilo_formatado(fonte_efetiva, tamanho_efetivo, bloco.get("align") or "left", cor, espaco_depois)
    if tem_fonte or negrito:
        markup = _markup_trechos(bloco, fonte, fonte_negrito, tamanho_efetivo, negrito)
    else:
        markup = _markup_linha(texto) or escape(texto)
    if not markup:
        return Spacer(1, 0.12 * cm)
    return Paragraph(markup, estilo)


def _sem_descricao_de_produto(blocos, oportunidade):
    descricoes = {" ".join(texto.split()) for texto in descricoes_da_oportunidade(oportunidade)}
    if not descricoes:
        return blocos
    return [bloco for bloco in blocos if " ".join((bloco.get("texto") or "").split()) not in descricoes]


def _titulo_formatado(bloco):
    texto = " ".join((bloco.get("texto") or "").split())
    return bool(texto) and "\n" not in (bloco.get("texto") or "") and bool(titulo_de_bloco(texto))


def desenhar_primeira_folha_formatada(elements, blocos, fonte, fonte_negrito, tamanho):
    """Primeira folha escrita no template, com a letra e o alinhamento de cada trecho."""
    blocos = [bloco for bloco in blocos if bloco.get("texto") is not None]
    while blocos and not (blocos[0].get("texto") or "").strip():
        blocos.pop(0)
    if not blocos:
        return
    elements.append(Spacer(1, 0.22 * cm))
    inicio = 0
    if _titulo_formatado(blocos[0]):
        elements.append(_flowable_bloco(blocos[0], fonte, fonte_negrito, tamanho, negrito=True, espaco_depois=4))
        inicio = 1
    for bloco in blocos[inicio:]:
        elements.append(_flowable_bloco(bloco, fonte, fonte_negrito, tamanho, espaco_depois=1))


def desenhar_recursos_formatados(elements, oportunidade, blocos, fonte, fonte_negrito, tamanho):
    """Segunda folha: incluídos da oportunidade e o texto do template já formatado."""
    blocos = _sem_descricao_de_produto(list(blocos or []), oportunidade)
    corpo = _estilo_paragrafo_proposta(fonte, tamanho)
    estilo_titulo = _estilo_secao_proposta(fonte_negrito, min(tamanho + 2, 16))
    numero = 3
    incluidos = _descricoes_incluidas(oportunidade)
    if incluidos:
        _titulo_numerado(elements, numero, "O que está incluído", estilo_titulo)
        numero += 1
        for nome, texto in incluidos:
            if ":" in texto:
                elements.append(Paragraph(_markup_linha(texto), corpo))
            else:
                elements.append(Paragraph(f"<b>{escape(nome)}:</b> {escape(texto)}", corpo))
    implantacao = _linhas_implantacao(oportunidade)
    if implantacao and not any("implant" in _sem_acento(bloco.get("texto") or "") for bloco in blocos):
        blocos.append({"align": "left", "trechos": [{"texto": "Implantação e liberação", "fonte": None, "tamanho": None}], "texto": "Implantação e liberação"})
        for linha in implantacao:
            blocos.append({"align": "left", "trechos": [{"texto": linha, "fonte": None, "tamanho": None}], "texto": linha})
    for bloco in blocos:
        if not (bloco.get("texto") or "").strip():
            elements.append(Spacer(1, 0.12 * cm))
            continue
        if _titulo_formatado(bloco):
            prefixo = f"{numero:02d}  "
            numero += 1
            titulo = {
                "align": bloco.get("align") or "left",
                "trechos": [{"texto": prefixo + (bloco["trechos"][0].get("texto") or "").lstrip(), "fonte": bloco["trechos"][0].get("fonte"), "tamanho": bloco["trechos"][0].get("tamanho")}] + bloco["trechos"][1:],
                "texto": prefixo + (bloco.get("texto") or "").lstrip(),
            }
            elements.append(_flowable_bloco(titulo, fonte, fonte_negrito, tamanho, negrito=True, espaco_depois=4))
            continue
        if "implant" in _sem_acento(bloco.get("texto") or "") and bloco.get("texto", "").strip() == "Implantação e liberação":
            elements.append(_flowable_bloco(bloco, fonte, fonte_negrito, tamanho, negrito=True, espaco_depois=4))
            continue
        elements.append(_flowable_bloco(bloco, fonte, fonte_negrito, tamanho, espaco_depois=4))


def _build_secao_assinaturas(elements, documento, lead, vendedor, style, incluir_assinaturas=True, tipo_doc="proposta"):
    """Adiciona seção Assinaturas com dados digitais."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    proposta = tipo_doc == "proposta"
    elements.append(Spacer(1, 0.15 * cm if proposta else 0.35 * cm))
    if proposta:
        style = ParagraphStyle(
            "AssinaturaProposta",
            fontName=FONTE,
            fontSize=8,
            leading=10,
            textColor=COR_TEXTO,
        )
        section = ParagraphStyle(
            "SecAssinProposta",
            fontName=FONTE_NEGRITO,
            fontSize=11,
            textColor=COR_PROPOSTA,
            leading=13,
            spaceBefore=0,
            spaceAfter=2,
        )
        coluna = (A4[0] - 3.1 * cm) / 2
    else:
        section = ParagraphStyle("SecAssin", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
        coluna = 8 * cm
    elements.append(Paragraph("Assinaturas", section))

    nome_vendedor = getattr(documento, "nome_vendedor_assinatura", None) or ""
    nome_cliente = getattr(documento, "nome_cliente_assinatura", None) or ""
    lead_email = getattr(lead, "email", "") or "" if lead else ""
    vendedor_email = getattr(vendedor, "email", "") or "" if vendedor else ""

    assinatura_vendedor = None
    assinatura_cliente = None
    if incluir_assinaturas:
        from ..models import AssinaturaDigital
        filtro = {"assinado": True}
        if tipo_doc == "proposta":
            filtro["proposta"] = documento
        else:
            filtro["contrato"] = documento
        for ass in AssinaturaDigital.objects.filter(**filtro).order_by("assinado_em"):
            if ass.tipo == "vendedor":
                assinatura_vendedor = ass
            elif ass.tipo == "cliente":
                assinatura_cliente = ass

    vendedor_nome_fmt = (nome_vendedor or _formatar_nome_usuario(vendedor)).strip().upper() or "—"
    cliente_nome_fmt = (nome_cliente or getattr(lead, "nome", "") or "—").strip().upper() or "—"

    vendedor_info = [f"Vendedor: {vendedor_nome_fmt}"]
    if vendedor_email:
        vendedor_info.append(f"<font size='8'>Email: {vendedor_email}</font>")
    if assinatura_vendedor:
        ts = _formatar_timestamp_local(assinatura_vendedor.assinado_em)
        vendedor_info.append(f'<font size="8">Assinado em: {ts}</font>')
        vendedor_info.append(f'<font size="8">IP: {assinatura_vendedor.ip_address}</font>')
        vendedor_info.append('<font size="8">Assinado digitalmente</font>')

    cliente_info = [f"Cliente: {cliente_nome_fmt}"]
    if lead_email:
        cliente_info.append(f"<font size='8'>Email: {lead_email}</font>")
    if assinatura_cliente:
        ts = _formatar_timestamp_local(assinatura_cliente.assinado_em)
        cliente_info.append(f'<font size="8">Assinado em: {ts}</font>')
        cliente_info.append(f'<font size="8">IP: {assinatura_cliente.ip_address}</font>')
        cliente_info.append('<font size="8">Assinado digitalmente</font>')

    assinatura_data = []
    max_rows = max(len(vendedor_info), len(cliente_info))
    for i in range(max_rows):
        v_text = Paragraph(vendedor_info[i], style) if i < len(vendedor_info) else ""
        c_text = Paragraph(cliente_info[i], style) if i < len(cliente_info) else ""
        assinatura_data.append([v_text, c_text])

    t = Table(assinatura_data, colWidths=[coluna, coluna])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 if proposta else 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 if proposta else 6),
        ("TOPPADDING", (0, 0), (-1, -1), 1 if proposta else 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0 if proposta else 1),
        ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("BOX", (1, 0), (1, -1), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.05 * cm if proposta else 0.1 * cm))

    # Mensagem de validade jurídica
    validade = ParagraphStyle(
        "Validade",
        parent=style,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceBefore=0 if proposta else 2,
    )
    elements.append(Paragraph(
        "Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, "
        "com registro de data, hora e endereço IP.", validade))

    return assinatura_vendedor, assinatura_cliente


def _build_watermark_callback(logo_url, assinatura_vendedor, assinatura_cliente):
    """Prepara dados da marca d'água (logo transparente) para uso nas assinaturas.
    Retorna bytes PNG da imagem com transparência, ou None.
    """
    if not (assinatura_vendedor or assinatura_cliente) or not logo_url:
        return None
    try:
        conteudo = baixar_logo_pdf(logo_url)
        if not conteudo:
            return None
        pil_img = PILImage.open(BytesIO(conteudo)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.25))
        pil_img.putalpha(alpha)
        out_buf = BytesIO()
        pil_img.save(out_buf, format="PNG")
        return out_buf.getvalue()
    except Exception:
        return None
