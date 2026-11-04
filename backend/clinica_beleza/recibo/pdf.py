"""Geração de PDF do recibo de pagamento."""
import html
import io
import logging
import re

from .context import (
    _linha_documento_loja,
    _linha_tel_cep,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
    comprovante_sem_cobranca,
    cor_primaria_recibo,
    custeado_pela_clinica,
    linha_valor_com_desconto_recibo,
    linha_vencimento_recibo,
    linhas_local_convenio_recibo,
    linhas_protocolo_informativo,
    procedimentos_exibidos_recibo,
    produtos_exibidos_recibo,
    recebido_a_maior_recibo,
    reconciliar_conta_recibo,
    rotulo_forma_recibo,
    rotulo_numero_recibo,
    rotulo_subtotal_recibo,
    rotulo_total_recibo,
    situacao_comprovante_recibo,
    situacao_recibo,
    texto_cadastro_recibo,
    tinta_recibo,
    titulo_recibo,
)
from .moeda import formatar_moeda_recibo

logger = logging.getLogger(__name__)


def _texto_pdf(valor) -> str:
    """Texto de cadastro no Paragraph do ReportLab (sem interpretar tags)."""
    return html.escape(str(valor or ""), quote=True)


def logo_url_permitida_para_download(logo_url: str) -> bool:
    """Só baixa logo do servidor de mídia da loja (anti-SSRF)."""
    from clinica_beleza.pdf_common.logo import logo_url_permitida

    return logo_url_permitida(logo_url)


def _saldo_devedor_recibo(ctx: dict) -> float:
    """Saldo em aberto do recibo (a prazo ou pagamento parcial).

    Usa 'saldo_devedor' quando presente; senão, deriva de valor_total - valor_pago.
    """
    valor_pago = ctx.get("valor_pago", 0) or 0
    valor_total = ctx.get("valor_total", 0) or 0
    return ctx.get("saldo_devedor", max(valor_total - valor_pago, 0))


# Logo no topo do recibo.
_LOGO_RODAPE_MAX_W_MM = 58
_LOGO_RODAPE_MAX_H_MM = 28


def _logo_rodape_recibo(logo_url: str, mm_unit):
    """Baixa a logo da loja e retorna um Image do reportlab para o rodapé, ou None."""
    if not logo_url:
        return None
    if not logo_url_permitida_para_download(logo_url):
        logger.warning("Logo do recibo recusada (URL fora da mídia)")
        return None
    try:
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage

        from clinica_beleza.pdf_common.logo import baixar_logo

        conteudo = baixar_logo(logo_url, timeout=5)
        if not conteudo:
            return None
        raw = io.BytesIO(conteudo)
        pil = PILImage.open(raw)
        iw, ih = pil.size
        if not iw or not ih:
            return None
        max_w = _LOGO_RODAPE_MAX_W_MM * mm_unit
        max_h = _LOGO_RODAPE_MAX_H_MM * mm_unit
        ratio = min(max_w / iw, max_h / ih)
        raw.seek(0)
        img = RLImage(raw, width=iw * ratio, height=ih * ratio)
        img.hAlign = "CENTER"
        return img
    except Exception as e:
        logger.warning("Logo do rodapé do recibo indisponível: %s", e)
        return None


def _estilos_pdf():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import HRFlowable

    return {
        "s_center": ParagraphStyle("c", fontSize=8, alignment=TA_CENTER, leading=13, spaceAfter=1),
        "s_bold_center": ParagraphStyle(
            "bc", fontSize=11, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=15, spaceAfter=1,
        ),
        "s_title": ParagraphStyle("ti", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=13),
        "s_left": ParagraphStyle("l", fontSize=8, leading=13, spaceAfter=1),
        "s_bold": ParagraphStyle("b", fontSize=8, fontName="Helvetica-Bold", leading=13),
        "s_total": ParagraphStyle("t", fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=16),
        "s_aceite": ParagraphStyle(
            "aceite", fontSize=8, alignment=TA_CENTER, leading=11, textColor=colors.black,
        ),
        "s_footer": ParagraphStyle(
            "f", fontSize=7, alignment=TA_CENTER, leading=11, textColor=colors.HexColor("#666666"),
        ),
        "s_aviso": ParagraphStyle(
            "aviso", fontSize=9, alignment=TA_CENTER, leading=14, textColor=colors.HexColor("#333333"),
        ),
        "s_right": ParagraphStyle("r", fontSize=8, alignment=TA_RIGHT, leading=13),
        "hr": HRFlowable(width="100%", thickness=0.5, dash=[2, 2], spaceAfter=3, spaceBefore=3),
    }


def _secao_assinatura_recibo_pdf(ctx, styles, mm_unit):
    """Bloco de assinatura digital do recibo (paciente), com valor jurídico.

    Só é incluído quando o ctx traz 'assinatura_recibo' (dict com nome/ip/assinado_em/email).
    """
    from reportlab.platypus import Paragraph, Spacer

    assinatura = ctx.get("assinatura_recibo") or {}
    if not assinatura:
        return []

    s_title = styles["s_title"]
    s_center = styles["s_center"]
    s_aceite = styles["s_aceite"]
    hr = styles["hr"]

    # Título e dados do cliente centralizados para alinhar todo o bloco de assinatura.
    story = [Spacer(1, 2 * mm_unit), hr, Paragraph("ACEITE DO CLIENTE", s_title), Spacer(1, 1 * mm_unit)]
    nome = (assinatura.get("nome") or ctx.get("paciente_nome") or "").strip().upper() or "—"
    # Nome e CPF centralizados para alinhar com o restante do bloco (email/IP/data e texto jurídico).
    story.append(Paragraph(f"<b>Cliente:</b> {_texto_pdf(nome)}", s_center))
    cpf = (assinatura.get("cpf") or ctx.get("paciente_cpf") or "").strip()
    if cpf:
        story.append(Paragraph(f"<b>CPF:</b> {_texto_pdf(cpf)}", s_center))

    # Declaração de reconhecimento de dívida — só quando há saldo em aberto
    # (pagamento a prazo ou parcial). Dá força ao documento como base de cobrança.
    saldo = _saldo_devedor_recibo(ctx)
    if saldo > 0.009:
        vencimento = (ctx.get("vencimento") or "").strip()
        if vencimento:
            declaracao = (
                f"Declaro que recebi o(s) serviço(s)/atendimento(s) descrito(s) acima e "
                f"reconheço o saldo devedor de {formatar_moeda_recibo(saldo)}, "
                f"com vencimento em {_texto_pdf(vencimento)}."
            )
        else:
            declaracao = (
                f"Declaro que recebi o(s) serviço(s)/atendimento(s) descrito(s) acima e "
                f"reconheço o saldo devedor de {formatar_moeda_recibo(saldo)}, "
                f"sem vencimento combinado."
            )
        story.append(Spacer(1, 1 * mm_unit))
        story.append(Paragraph(declaracao, s_aceite))
        story.append(Spacer(1, 1 * mm_unit))
    elif assinatura.get("assinado_em"):
        story.append(Spacer(1, 1 * mm_unit))
        story.append(Paragraph(
            f"Aceite do saldo em aberto registrado em {_texto_pdf(assinatura['assinado_em'])}. "
            "Não confirma pagamentos feitos depois deste registro.",
            s_aceite,
        ))
        story.append(Spacer(1, 1 * mm_unit))

    if assinatura.get("email"):
        story.append(Paragraph(f"E-mail: {_texto_pdf(assinatura['email'])}", s_aceite))
    if assinatura.get("assinado_em"):
        story.append(Paragraph(
            f"Aceite registrado em: {_texto_pdf(assinatura['assinado_em'])}",
            s_aceite,
        ))
    if assinatura.get("ip"):
        story.append(Paragraph(f"IP: {_texto_pdf(assinatura['ip'])}", s_aceite))
    story.append(Spacer(1, 1 * mm_unit))
    story.append(Paragraph(
        "Registro do aceite do cliente: nome, data, hora e endereço IP.",
        s_aceite,
    ))
    return story



def _recortar_pdf_apos_conteudo(pdf_bytes: bytes, y_conteudo: float | None, mm_unit) -> bytes:
    """Corta a folha alta logo abaixo da logomarca, sem faixa branca no fim."""
    if y_conteudo is None:
        return pdf_bytes
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(pdf_bytes))
    if not reader.pages:
        return pdf_bytes
    page = reader.pages[0]
    llx, _lly, urx, ury = (float(v) for v in page.mediabox)
    corte = max(0.0, float(y_conteudo) - 3 * mm_unit)
    if corte >= ury - 20 * mm_unit:
        return pdf_bytes
    page.mediabox.lower_left = (llx, corte)
    page.mediabox.upper_right = (urx, ury)
    page.cropbox.lower_left = (llx, corte)
    page.cropbox.upper_right = (urx, ury)
    writer = PdfWriter()
    writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _icone_pdf(nome: str, cor, lado: float = 13):
    """Desenho de linha na cor da clínica, no mesmo lugar do exemplo."""
    from reportlab.graphics.shapes import Circle, Drawing, Group, Path
    from reportlab.lib.colors import white

    desenho = Drawing(lado, lado)
    grupo = Group()
    escala = lado / 24.0
    grupo.transform = (escala, 0, 0, -escala, 0, lado)

    def traco(comandos, preenchimento=None, cor_traco=cor, largura=1.7):
        caminho = Path(
            strokeColor=cor_traco,
            fillColor=preenchimento,
            strokeWidth=largura,
            strokeLineCap=1,
            strokeLineJoin=1,
        )
        for comando in comandos:
            op = comando[0]
            if op == "M":
                caminho.moveTo(comando[1], comando[2])
            elif op == "L":
                caminho.lineTo(comando[1], comando[2])
            elif op == "C":
                caminho.curveTo(comando[1], comando[2], comando[3], comando[4], comando[5], comando[6])
            elif op == "Z":
                caminho.closePath()
        return caminho

    def caixa_arredondada(x, y, w, h, raio):
        return traco([
            ("M", x + raio, y),
            ("L", x + w - raio, y),
            ("C", x + w, y, x + w, y, x + w, y + raio),
            ("L", x + w, y + h - raio),
            ("C", x + w, y + h, x + w, y + h, x + w - raio, y + h),
            ("L", x + raio, y + h),
            ("C", x, y + h, x, y + h, x, y + h - raio),
            ("L", x, y + raio),
            ("C", x, y, x, y, x + raio, y),
            ("Z",),
        ])

    if nome == "pessoa":
        grupo.add(Circle(12, 8, 3.1, strokeColor=cor, fillColor=None, strokeWidth=1.7))
        grupo.add(traco([
            ("M", 5.6, 19.4),
            ("C", 6.4, 16.1, 8.6, 14.6, 12, 14.6),
            ("C", 15.4, 14.6, 17.6, 16.1, 18.4, 19.4),
        ]))
    elif nome == "cpf":
        grupo.add(caixa_arredondada(3.5, 5, 17, 14, 2))
        grupo.add(Circle(8.8, 11.2, 1.7, strokeColor=cor, fillColor=None, strokeWidth=1.5))
        grupo.add(traco([
            ("M", 6.6, 15.7),
            ("C", 7.1, 14.4, 7.9, 13.8, 8.8, 13.8),
            ("C", 9.7, 13.8, 10.5, 14.4, 11, 15.7),
        ]))
        grupo.add(traco([("M", 13.4, 9.6), ("L", 18.6, 9.6)]))
        grupo.add(traco([("M", 13.4, 12.4), ("L", 18.6, 12.4)]))
        grupo.add(traco([("M", 13.4, 15.2), ("L", 16.6, 15.2)]))
    elif nome == "calendario":
        grupo.add(caixa_arredondada(4, 5, 16, 15, 2))
        grupo.add(traco([("M", 8, 3.5), ("L", 8, 7.5)]))
        grupo.add(traco([("M", 16, 3.5), ("L", 16, 7.5)]))
        grupo.add(traco([("M", 4, 10), ("L", 20, 10)]))
    elif nome == "pin":
        grupo.add(traco([
            ("M", 12, 21),
            ("C", 12, 21, 18.2, 15.6, 18.2, 10.8),
            ("C", 18.2, 7.4, 15.4, 4.6, 12, 4.6),
            ("C", 8.6, 4.6, 5.8, 7.4, 5.8, 10.8),
            ("C", 5.8, 15.6, 12, 21, 12, 21),
            ("Z",),
        ]))
        grupo.add(Circle(12, 10.7, 2, strokeColor=cor, fillColor=None, strokeWidth=1.6))
    elif nome == "telefone":
        grupo.add(caixa_arredondada(8, 3, 8, 18, 1.8))
        grupo.add(traco([("M", 10.4, 6.2), ("L", 13.6, 6.2)]))
    elif nome == "email":
        grupo.add(caixa_arredondada(3, 6, 18, 12, 2))
        grupo.add(traco([("M", 4, 7.6), ("L", 12, 13), ("L", 20, 7.6)]))
    elif nome == "cartao":
        grupo.add(caixa_arredondada(2.5, 5.5, 19, 13, 2))
        grupo.add(traco([("M", 2.5, 10), ("L", 21.5, 10)]))
    elif nome == "caixa":
        grupo.add(traco([
            ("M", 8, 8),
            ("L", 8, 6.8),
            ("C", 8, 5.6, 8.8, 5.2, 10, 5.2),
            ("L", 14, 5.2),
            ("C", 15.2, 5.2, 16, 5.6, 16, 6.8),
            ("L", 16, 8),
        ]))
        grupo.add(caixa_arredondada(3.5, 8, 17, 11, 2))
        grupo.add(traco([("M", 7, 12.3), ("L", 11, 12.3)]))
        grupo.add(traco([("M", 7, 15.3), ("L", 15, 15.3)]))
    elif nome == "ok":
        grupo.add(Circle(12, 12, 10, strokeColor=None, fillColor=cor, strokeWidth=0))
        grupo.add(traco([
            ("M", 7.2, 12.4),
            ("L", 10.3, 15.5),
            ("L", 16.8, 8.6),
        ], cor_traco=white, largura=2.2))
    desenho.add(grupo)
    return desenho


def _hora_pdf(valor: str) -> str:
    texto = (valor or "").strip()
    if re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", texto):
        return texto.replace(" ", " às ", 1)
    return texto


def _cartao_recibo_pdf(ctx, col_w, mm_unit):
    """O mesmo cartão da prévia: faixa, quadro do cliente, tabela e total em destaque."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    cor_hex = cor_primaria_recibo(ctx.get("cor_primaria") or "")
    cor = colors.HexColor(cor_hex)
    fundo = colors.HexColor(tinta_recibo(cor_hex, 0.9))
    fundo_tabela = colors.HexColor(tinta_recibo(cor_hex, 0.82))
    cinza = colors.HexColor("#5C5562")
    verde = colors.HexColor("#1B8A45")
    tinta = colors.HexColor("#2B2430")

    def estilo(nome, **kwargs):
        base = dict(fontName="Helvetica", fontSize=9, leading=12, textColor=tinta)
        base.update(kwargs)
        return ParagraphStyle(nome, **base)

    s_centro = estilo("centro", alignment=TA_CENTER, textColor=cinza, spaceAfter=1)
    s_faixa = estilo("faixa", fontName="Helvetica-Bold", fontSize=12, leading=15, alignment=TA_CENTER, textColor=colors.white)
    s_cliente = estilo("cliente", fontSize=10, leading=12, spaceBefore=0, spaceAfter=0)
    s_secao = estilo("secao", fontName="Helvetica-Bold", fontSize=10, textColor=cor)
    s_th = estilo("th", fontName="Helvetica-Bold", fontSize=8, leading=11)
    s_th_r = estilo("thr", fontName="Helvetica-Bold", fontSize=8, leading=11, alignment=TA_RIGHT)
    s_td = estilo("td", fontSize=9, leading=11, spaceBefore=0, spaceAfter=0)
    s_td_r = estilo("tdr", fontSize=9, leading=11, alignment=TA_RIGHT, spaceBefore=0, spaceAfter=0)
    s_esq = estilo("esq", alignment=TA_RIGHT, textColor=cinza)
    s_dir = estilo("dir", fontName="Helvetica-Bold", alignment=TA_RIGHT)
    s_rotulo = estilo("rotulo", fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=cor)
    s_pill = estilo("pill", fontName="Helvetica-Bold", fontSize=13, leading=16, alignment=TA_CENTER, textColor=colors.white)
    s_ok = estilo("ok", fontName="Helvetica-Bold", fontSize=10, alignment=TA_RIGHT, textColor=verde)
    s_aviso_sit = estilo("aviso_sit", fontName="Helvetica-Bold", fontSize=10, alignment=TA_RIGHT, textColor=colors.HexColor("#A15C00"))
    s_neutro = estilo("neutro", fontName="Helvetica-Bold", fontSize=10, alignment=TA_RIGHT, textColor=cinza)
    s_obrigado = estilo("obrigado", fontName="Helvetica-BoldOblique", fontSize=11, leading=14, alignment=TA_CENTER, textColor=cor)
    s_nota = estilo("nota", fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor("#6D6572"))

    def caixa(conteudo, fundo_caixa, raios=(8, 8, 8, 8), paddings=(8, 8, 10, 10)):
        tabela = Table(conteudo, colWidths=[col_w])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), fundo_caixa),
            ("ROUNDEDCORNERS", raios),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), paddings[0]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), paddings[1]),
            ("LEFTPADDING", (0, 0), (-1, -1), paddings[2]),
            ("RIGHTPADDING", (0, 0), (-1, -1), paddings[3]),
        ]))
        return tabela

    story = []
    logo = _logo_rodape_recibo((ctx.get("logo_url") or "").strip(), mm_unit)
    if logo is not None:
        story.append(logo)
    elif ctx.get("loja_nome"):
        story.append(Paragraph(_texto_pdf(str(ctx["loja_nome"]).upper()), estilo(
            "marca", fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=TA_CENTER,
            textColor=cor, spaceAfter=4,
        )))
    doc_line = _linha_documento_loja(ctx)
    if doc_line:
        story.append(Paragraph(_texto_pdf(doc_line), s_centro))
    from reportlab.pdfbase.pdfmetrics import stringWidth

    s_contato = estilo("contato", fontSize=9, leading=11, textColor=cinza)

    def linha_icone(nome, texto, cor_icone=cor, estilo_texto=s_cliente, largura=None, folga=0):
        largura = largura or (col_w - 28)
        tabela = Table(
            [[_icone_pdf(nome, cor_icone), Paragraph(texto, estilo_texto)]],
            colWidths=[16, max(largura - 16, 20)],
        )
        tabela.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), folga),
            ("BOTTOMPADDING", (0, 0), (-1, -1), folga),
        ]))
        return tabela

    contato_itens = []
    if ctx.get("loja_endereco"):
        contato_itens.append(("pin", texto_cadastro_recibo(ctx["loja_endereco"])))
    if ctx.get("loja_telefone"):
        contato_itens.append(("telefone", ctx["loja_telefone"]))
    if ctx.get("loja_email"):
        contato_itens.append(("email", ctx["loja_email"]))
    for icone, texto in contato_itens:
        largura_texto = min(col_w - 24, max(stringWidth(str(texto), "Helvetica", 9) + 8, 40))
        linha = Table(
            [[_icone_pdf(icone, cor), Paragraph(_texto_pdf(texto), s_contato)]],
            colWidths=[18, largura_texto],
        )
        linha.hAlign = "CENTER"
        linha.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        story.append(linha)
    if not contato_itens and not ctx.get("loja_telefone"):
        tel_cep = ctx.get("loja_tel_cep") or _linha_tel_cep(ctx.get("loja_telefone", ""), ctx.get("loja_cep", ""))
        if tel_cep:
            story.append(Paragraph(_texto_pdf(tel_cep), s_centro))

    titulo, subtitulo = titulo_recibo(ctx)
    story.append(Spacer(1, 3 * mm_unit))
    story.append(caixa(
        [[Paragraph(f"<b>{_texto_pdf(titulo)}</b>", s_faixa)]],
        cor, raios=(8, 8, 8, 8), paddings=(8, 8, 6, 6),
    ))
    data_emissao = _hora_pdf(ctx.get("data_emissao") or ctx.get("data") or "—")
    numero = ctx.get("recibo_numero")
    meta = f"Emitido em {_texto_pdf(data_emissao)}"
    if numero:
        meta = f"{rotulo_numero_recibo(ctx)} nº {_texto_pdf(numero)}  |  {meta}"
    story.append(Spacer(1, 2 * mm_unit))
    story.append(Paragraph(meta, s_centro))
    if subtitulo:
        story.append(Paragraph(_texto_pdf(subtitulo), s_centro))

    somente = bool(ctx.get("somente_produtos"))
    rotulo_pessoa = "Cliente" if somente else "Paciente"
    folga_cliente = 2
    linhas_cliente = [linha_icone(
        "pessoa", f"<b>{rotulo_pessoa}:</b> {_texto_pdf(ctx.get('paciente_nome'))}",
        folga=folga_cliente,
    )]
    if ctx.get("paciente_cpf"):
        linhas_cliente.append(linha_icone(
            "cpf", f"<b>CPF:</b> {_texto_pdf(ctx['paciente_cpf'])}", folga=folga_cliente,
        ))
    if not somente:
        data_atend = _hora_pdf(ctx.get("data_atendimento") or "")
        if data_atend:
            linhas_cliente.append(linha_icone(
                "calendario", f"<b>Data do atendimento:</b> {_texto_pdf(data_atend)}",
                folga=folga_cliente,
            ))
        if ctx.get("profissional_nome"):
            linhas_cliente.append(linha_icone(
                "pessoa", f"<b>Profissional:</b> {_texto_pdf(ctx['profissional_nome'])}",
                folga=folga_cliente,
            ))
    story.append(Spacer(1, 2 * mm_unit))
    story.append(caixa([[linhas_cliente]], fundo, paddings=(6, 6, 10, 10)))

    situacao = situacao_recibo(ctx)
    custeio = situacao == "quitado" and custeado_pela_clinica(ctx)
    comprovante = comprovante_sem_cobranca(ctx)
    produtos = produtos_exibidos_recibo(ctx)
    servicos = []
    for label, valor in _linhas_taxa_consulta_recibo(ctx):
        servicos.append((f"• {label}", valor, "1"))
    for nome, valor in procedimentos_exibidos_recibo(ctx):
        quantidade = "1" if valor > 0.009 else "—"
        servicos.append((nome, valor, quantidade))
    titulo_tabela = "Produtos" if somente or (produtos and not servicos) else (
        "Procedimentos, serviços e produtos" if produtos and servicos else "Serviços / procedimentos"
    )
    story.append(Spacer(1, 3 * mm_unit))
    story.append(Paragraph(_texto_pdf(titulo_tabela.upper()), s_secao))

    dados = [[
        Paragraph("<b>Descrição</b>", s_th),
        Paragraph("<b>Qtd.</b>", s_th_r),
        Paragraph("<b>Unitário</b>", s_th_r),
        Paragraph("<b>Subtotal</b>", s_th_r),
    ]]
    for nome, valor, quantidade in servicos:
        unitario = formatar_moeda_recibo(valor) if quantidade == "1" else "—"
        dados.append([
            Paragraph(_texto_pdf(nome), s_td),
            Paragraph(quantidade, s_td_r),
            Paragraph(unitario, s_td_r),
            Paragraph(formatar_moeda_recibo(valor), s_td_r),
        ])
    for label, valor in linhas_local_convenio_recibo(ctx):
        dados.append([
            Paragraph(f"{_texto_pdf(label)} {_texto_pdf(valor)}", s_td),
            "", "", "",
        ])
    for item in produtos:
        nome = _texto_pdf(item["nome"])
        if item["desconto"] > 0.009:
            nome += f"<br/>desc. {formatar_moeda_recibo(item['desconto'])}"
        dados.append([
            Paragraph(nome, s_td),
            Paragraph(_texto_pdf(item["quantidade"]), s_td_r),
            Paragraph(formatar_moeda_recibo(item["preco_unitario"]), s_td_r),
            Paragraph(formatar_moeda_recibo(item["subtotal"]), s_td_r),
        ])
    tabela = Table(dados, colWidths=[col_w * 0.52, col_w * 0.12, col_w * 0.18, col_w * 0.18])
    estilo_tabela = [
        ("BACKGROUND", (0, 0), (-1, 0), fundo_tabela),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#EEEEEE")),
    ]
    tabela.setStyle(TableStyle(estilo_tabela))
    story.append(tabela)

    s_resumo = estilo("resumo_esq", fontName="Helvetica-Bold", fontSize=9, leading=12)

    def linha_valor(rotulo, valor, negativo=False):
        prefixo = "- " if negativo else ""
        tabela = Table(
            [[
                Paragraph(_texto_pdf(rotulo), s_resumo),
                Paragraph(f"{prefixo}{formatar_moeda_recibo(valor)}", s_dir),
            ]],
            colWidths=[col_w * 0.62, col_w * 0.38],
        )
        tabela.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 4),
            ("RIGHTPADDING", (0, 0), (0, 0), 0),
            ("LEFTPADDING", (1, 0), (1, 0), 0),
            ("RIGHTPADDING", (1, 0), (1, 0), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        return tabela

    subtotal = float(ctx.get("subtotal", ctx.get("valor_total") or 0))
    descontos = _linhas_descontos_recibo(ctx)
    story.append(Spacer(1, 2 * mm_unit))
    if not comprovante or descontos:
        story.append(linha_valor(rotulo_subtotal_recibo(ctx), subtotal))
    for label, valor in descontos:
        story.append(linha_valor(label, valor, negativo=True))
    protocolo = linhas_protocolo_informativo(ctx)
    if protocolo:
        story.append(Paragraph("<b>Protocolo</b>", s_secao))
        for label, valor in protocolo:
            story.append(linha_valor(label, valor))
    valor_com_desconto = linha_valor_com_desconto_recibo(ctx)
    if valor_com_desconto:
        story.append(linha_valor(valor_com_desconto[0], valor_com_desconto[1]))
    valor_pago = float(ctx.get("valor_pago") or 0)
    saldo = float(_saldo_devedor_recibo(ctx) or 0)
    if situacao == "parcial" and valor_pago > 0.009:
        story.append(linha_valor("PAGO", valor_pago))
    extra = recebido_a_maior_recibo(ctx)
    if extra > 0.009:
        story.append(linha_valor("Recebido a maior", extra))
    if not custeio and saldo > 0.009:
        story.append(linha_valor("SALDO A PAGAR", saldo))
        story.append(Paragraph(_texto_pdf(linha_vencimento_recibo(ctx)), s_nota))
    if comprovante:
        story.append(linha_valor("Valor do procedimento", float(ctx.get("valor_total") or 0)))

    rotulo = rotulo_total_recibo(ctx)
    if comprovante:
        rotulo_destaque = "Valor pago pelo paciente"
        valor_destaque = 0
    elif situacao == "quitado" and not custeio and rotulo == "Total":
        rotulo_destaque = "TOTAL PAGO"
        valor_destaque = float(ctx.get("valor_total") or 0)
    elif rotulo == "Total":
        rotulo_destaque = "TOTAL"
        valor_destaque = float(ctx.get("valor_total") or 0)
    else:
        rotulo_destaque = rotulo
        valor_destaque = float(ctx.get("valor_total") or 0)
    destaque = Table(
        [[
            Paragraph(f"<b>{_texto_pdf(rotulo_destaque)}</b>", s_rotulo),
            Paragraph(f"<b>{formatar_moeda_recibo(valor_destaque)}</b>", s_pill),
        ]],
        colWidths=[col_w * 0.72, col_w * 0.28],
    )
    destaque.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), fundo),
        ("BACKGROUND", (1, 0), (1, 0), cor),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, 0), 12),
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
    ]))
    story.append(Spacer(1, 2 * mm_unit))
    story.append(destaque)

    if comprovante:
        story.append(Paragraph(
            f"<b>Situação:</b> {_texto_pdf(situacao_comprovante_recibo(ctx))}",
            s_cliente,
        ))
    else:
        formas = [f for f in (ctx.get("formas_pagamento") or []) if float(f.get("valor") or 0) > 0.009]
        if not formas and valor_pago > 0.009:
            formas = [{"metodo": ctx.get("metodo") or "Pagamento", "valor": valor_pago}]
        if len(formas) > 1:
            formas_texto = " · ".join(
                f"{rotulo_forma_recibo(f.get('metodo') or '')} {formatar_moeda_recibo(f.get('valor') or 0)}"
                for f in formas
            )
        elif formas:
            formas_texto = rotulo_forma_recibo(formas[0].get("metodo") or "")
        else:
            formas_texto = (ctx.get("condicao_cobranca") or "").strip()
        rotulo_forma = "Formas de pagamento" if len(formas) > 1 else "Forma de pagamento"
        if situacao == "sem_saldo":
            situacao_txt, sit_style = subtitulo or "Sem valor a pagar", s_neutro
        elif situacao == "parcial":
            situacao_txt, sit_style = "Pagamento parcial", s_aviso_sit
        elif situacao == "em_aberto":
            situacao_txt, sit_style = "Em aberto", s_aviso_sit
        elif situacao == "quitado":
            situacao_txt, sit_style = "Quitado", s_ok
        else:
            situacao_txt, sit_style = "", s_neutro
        if formas_texto:
            forma_flow = linha_icone(
                "cartao",
                f"<b>{_texto_pdf(rotulo_forma)}:</b> {_texto_pdf(formas_texto)}",
                largura=col_w * 0.66,
            )
        else:
            forma_flow = Paragraph("", s_cliente)
        if situacao == "quitado":
            s_ok_esq = estilo("ok_esq", fontName="Helvetica-Bold", fontSize=10, textColor=verde)
            selo = Table(
                [[_icone_pdf("ok", verde, 14), Paragraph("Quitado", s_ok_esq)]],
                colWidths=[16, 58],
            )
            selo.hAlign = "RIGHT"
            selo.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ]))
        else:
            selo = Paragraph(_texto_pdf(situacao_txt), sit_style)
        pagamento = Table(
            [[forma_flow, selo]],
            colWidths=[col_w * 0.68, col_w * 0.32],
        )
        pagamento.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(pagamento)

    operacional = []
    tem_caixa = bool(ctx.get("caixa_nome"))
    tem_recebedor = bool(ctx.get("operador_nome"))
    largura_ops = (col_w / 2) - 28 if tem_caixa and tem_recebedor else (col_w - 36)
    if ctx.get("caixa_nome"):
        operacional.append(linha_icone(
            "caixa", f"<b>Caixa:</b> {_texto_pdf(ctx['caixa_nome'])}", largura=largura_ops,
        ))
    if ctx.get("operador_nome"):
        operacional.append(linha_icone(
            "pessoa", f"<b>Recebido por:</b> {_texto_pdf(ctx['operador_nome'])}", largura=largura_ops,
        ))
    if operacional:
        story.append(Spacer(1, 1 * mm_unit))
        if len(operacional) == 1:
            story.append(caixa([[operacional[0]]], fundo))
        else:
            meio_ops = col_w / 2
            ops = Table([operacional[:2]], colWidths=[meio_ops, meio_ops])
            ops.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), fundo),
                ("ROUNDEDCORNERS", [8, 8, 8, 8]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBEFORE", (1, 0), (1, 0), 0.6, colors.HexColor("#D8CEDF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(ops)

    aviso = (ctx.get("retorno_aviso") or "").strip()
    if aviso:
        story.append(Spacer(1, 2 * mm_unit))
        story.append(Paragraph(_texto_pdf(aviso), s_nota))
    if somente:
        nota = "Recibo comercial de produto · Documento não fiscal"
    elif comprovante:
        nota = "Comprovante de atendimento · Documento não fiscal."
    else:
        nota = "Recibo de prestação de serviços · Documento não fiscal."
    story.append(Spacer(1, 3 * mm_unit))
    story.append(caixa([
        [Paragraph("Agradecemos pela preferência!", s_obrigado)],
        [Paragraph(_texto_pdf(nota), s_nota)],
    ], fundo, paddings=(10, 8, 8, 8)))
    story.extend(_secao_assinatura_recibo_pdf(ctx, _estilos_pdf(), mm_unit))
    return story


def _gerar_pdf_recibo(ctx: dict, *, para_whatsapp: bool = False) -> bytes:
    """Gera o cartão do recibo. No WhatsApp, a largura é a do cupom antigo (150 mm)."""
    ctx = reconciliar_conta_recibo(ctx)
    from reportlab.lib.pagesizes import A4, mm
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

    margem_x = 4 * mm if para_whatsapp else 12 * mm
    margem_y = 6 * mm if para_whatsapp else 12 * mm

    class _ReciboDoc(BaseDocTemplate):
        def __init__(self, buffer, pagesize):
            super().__init__(
                buffer,
                pagesize=pagesize,
                leftMargin=margem_x,
                rightMargin=margem_x,
                topMargin=margem_y,
                bottomMargin=margem_y,
            )
            self.y_conteudo = None
            frame = Frame(
                self.leftMargin,
                self.bottomMargin,
                self.width,
                self.height,
                id="recibo",
                showBoundary=0,
            )
            self.addPageTemplates([PageTemplate(id="recibo", frames=[frame])])

        def afterFlowable(self, flowable):
            self.y_conteudo = self.frame._y

    buf = io.BytesIO()
    page_w = 150 * mm if para_whatsapp else A4[0]
    page_h = 900 * mm
    col_w = page_w - (2 * margem_x)
    story = _cartao_recibo_pdf(ctx, col_w, mm)

    doc = _ReciboDoc(buf, pagesize=(page_w, page_h))
    doc.build(story)
    return _recortar_pdf_apos_conteudo(buf.getvalue(), doc.y_conteudo, mm)


def gerar_pdf_recibo_da_consulta(consulta):
    """PDF oficial do recibo. Sem pagamento gravado (retorno a R$ 0), usa o mesmo gerador."""
    from decimal import Decimal

    from ..models import Payment
    from ..recibo_assinatura_adapter import ReciboAssinaturaAdapter

    adapter = ReciboAssinaturaAdapter()
    payment = (
        Payment.objects.filter(appointment_id=consulta.appointment_id)
        .order_by("-id")
        .first()
    )
    if payment is not None:
        assinado = payment.status_assinatura_recibo == "concluido"
        return adapter.gerar_pdf(payment, incluir_assinaturas=assinado)

    stub = Payment(
        loja_id=consulta.loja_id,
        appointment=consulta.appointment,
        amount=Decimal("0"),
        valor_total=Decimal("0"),
        desconto=Decimal("0"),
        payment_method="CASH",
        status="PENDING",
    )
    stub._prefetched_objects_cache = {"parcelas": []}
    return adapter.gerar_pdf(stub, incluir_assinaturas=False)
