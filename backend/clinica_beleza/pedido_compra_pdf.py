"""PDF do pedido de compra — mesma estrutura da proposta do CRM Vendas."""
from io import BytesIO
from xml.sax.saxutils import escape

import pytz
import requests
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from clinica_beleza.pdf_common import finalize_pdf_com_timbrado, logo_image
from clinica_beleza.pedido_compra_service import _brl, _fmt_numero

VINHO = colors.HexColor("#8B3D52")
FUNDO_TABELA = colors.HexColor("#f8eef1")
FUNDO_TOTAL = colors.HexColor("#f8eef1")
BORDA = colors.HexColor("#e5e7eb")

WM_OPACIDADE = 0.50


def _ts_local(dt) -> str:
    if not dt:
        return "—"
    tz = pytz.timezone("America/Sao_Paulo")
    return dt.astimezone(tz).strftime("%d/%m/%Y %H:%M:%S")


def _tel(raw: str) -> str:
    if not raw:
        return ""
    try:
        from core.phone_utils import telefone_exibicao_brasileiro
        return telefone_exibicao_brasileiro(raw) or raw.strip()
    except Exception:
        return raw.strip()


def _endereco_fornecedor(forn) -> str:
    parts = [
        getattr(forn, "logradouro", "") or "",
        f"nº {forn.numero}" if getattr(forn, "numero", "") else "",
        getattr(forn, "complemento", "") or "",
        getattr(forn, "bairro", "") or "",
        (
            f"{forn.municipio}/{forn.uf}"
            if getattr(forn, "municipio", "") and getattr(forn, "uf", "")
            else (getattr(forn, "municipio", "") or getattr(forn, "uf", "") or "")
        ),
        f"CEP {forn.cep}" if getattr(forn, "cep", "") else "",
    ]
    return ", ".join(p for p in parts if p).strip()


def _styles():
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "PedCrmTitle",
            parent=base["Heading1"],
            fontSize=16,
            textColor=VINHO,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            leading=18,
        ),
        "Compact": ParagraphStyle(
            "PedCrmCompact",
            parent=base["Normal"],
            fontSize=9,
            spaceBefore=0,
            spaceAfter=1,
            leading=11,
        ),
        "Section": ParagraphStyle(
            "PedCrmSection",
            parent=base["Normal"],
            fontSize=10,
            spaceBefore=2,
            spaceAfter=1,
        ),
        "Validade": ParagraphStyle(
            "PedCrmValidade",
            parent=base["Normal"],
            fontSize=7,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER,
            spaceBefore=2,
        ),
    }


def _cabecalho(elements, logo_url: str, styles, titulo_txt: str):
    titulo = Paragraph(escape(titulo_txt), styles["Title"])
    logo = logo_image(logo_url, max_w=6 * cm, max_h=3 * cm) if logo_url else None
    if logo:
        tab = Table([[logo, titulo]], colWidths=[6.5 * cm, 10.5 * cm])
        tab.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(tab)
    else:
        styles["Title"].alignment = TA_CENTER
        elements.append(titulo)


def _linha(elements, texto: str, style):
    elements.append(Paragraph(texto, style))


def _watermark_bytes(logo_url: str) -> bytes | None:
    if not logo_url:
        return None
    try:
        resp = requests.get(logo_url, timeout=5)
        if resp.status_code != 200:
            return None
        pil_img = PILImage.open(BytesIO(resp.content)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * WM_OPACIDADE))
        pil_img.putalpha(alpha)
        out = BytesIO()
        pil_img.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return None


class QuadroAssinatura(Flowable):
    """Quadro da assinatura com a logo da clínica centralizada no fundo."""

    def __init__(self, table: Table, wm_bytes: bytes | None):
        Flowable.__init__(self)
        self.table = table
        self.wm_bytes = wm_bytes
        self.width = 16 * cm
        self.height = 0

    def wrap(self, availWidth, availHeight):
        w, h = self.table.wrap(availWidth, availHeight)
        self.width = w
        self.height = h
        return w, h

    def draw(self):
        if self.wm_bytes and self.width and self.height:
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(BytesIO(self.wm_bytes))
                iw, ih = img.getSize()
                if iw and ih:
                    max_w = self.width * 0.92
                    max_h = self.height * 0.88
                    wm_w = max_w
                    wm_h = wm_w * (ih / float(iw))
                    if wm_h > max_h:
                        wm_h = max_h
                        wm_w = wm_h / (ih / float(iw))
                    x = (self.width - wm_w) / 2
                    y = (self.height - wm_h) / 2
                    self.canv.drawImage(
                        img, x, y, width=wm_w, height=wm_h,
                        mask="auto", preserveAspectRatio=True,
                    )
            except Exception:
                pass
        self.table.drawOn(self.canv, 0, 0)


def _formatar_cpf(cpf: str) -> str:
    d = "".join(c for c in (cpf or "") if c.isdigit())
    if len(d) != 11:
        return (cpf or "").strip()
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def _linhas_profissional(ass_cli, loja) -> list[str]:
    prof = getattr(ass_cli, "profissional", None) if ass_cli else None
    nome = (
        (getattr(prof, "nome", None) if prof else None)
        or (ass_cli.nome_assinante if ass_cli else "")
        or loja.get("nome")
        or "Clínica"
    ).strip().upper() or "—"
    linhas = [f"Profissional: {escape(nome)}"]

    cpf = (getattr(prof, "cpf", None) if prof else None) or (ass_cli.cpf_assinante if ass_cli else "")
    if cpf:
        linhas.append(f"<font size='8'>CPF: {escape(_formatar_cpf(cpf))}</font>")

    conselho = ""
    if prof and hasattr(prof, "formatar_conselho"):
        conselho = (prof.formatar_conselho() or "").strip()
    if not conselho and ass_cli:
        conselho = (ass_cli.conselho_display or "").strip()
    if conselho:
        linhas.append(f"<font size='8'>Conselho: {escape(conselho)}</font>")

    especialidade = (getattr(prof, "especialidade", "") or "").strip() if prof else ""
    if especialidade:
        linhas.append(f"<font size='8'>Especialidade: {escape(especialidade)}</font>")

    email = (
        (getattr(prof, "email", "") or "").strip() if prof else ""
    ) or (ass_cli.email_assinante if ass_cli else "") or loja.get("email") or ""
    if email:
        linhas.append(f"<font size='8'>Email: {escape(email)}</font>")

    telefone = (getattr(prof, "telefone", "") or "").strip() if prof else ""
    if telefone:
        linhas.append(f"<font size='8'>Telefone: {escape(_tel(telefone))}</font>")

    if ass_cli and ass_cli.assinado:
        linhas.append(f"<font size='8'>Assinado em: {_ts_local(ass_cli.assinado_em)}</font>")
        linhas.append(f"<font size='8'>IP: {escape(str(ass_cli.ip_address or '—'))}</font>")
        linhas.append("<font size='8'>Assinado digitalmente</font>")
    return linhas


def _secao_assinaturas(elements, pedido, loja, styles, wm_bytes=None):
    from .models.fornecedores import PedidoCompraAssinatura

    compact = styles["Compact"]
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph("<b>Assinatura</b>", styles["Section"]))

    ass_cli = pedido.assinaturas.select_related("profissional").filter(
        tipo=PedidoCompraAssinatura.TIPO_CLINICA, assinado=True,
    ).first()

    clinica_info = _linhas_profissional(ass_cli, loja)
    rows = [[Paragraph(linha, compact)] for linha in clinica_info]
    tab = Table(rows, colWidths=[16 * cm])
    tab.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("BOX", (0, 0), (0, -1), 0.5, BORDA),
    ]))
    elements.append(QuadroAssinatura(tab, wm_bytes if ass_cli else None))
    elements.append(Spacer(1, 0.1 * cm))
    elements.append(Paragraph(
        "Este documento possui validade jurídica e contém a assinatura digital do profissional responsável, "
        "com registro de data, hora e endereço IP.",
        styles["Validade"],
    ))
    return ass_cli


def gerar_pdf_pedido_compra(pedido) -> bytes:
    from .pedido_compra_service import _dados_loja
    from .prontuario_pdf.header import _resolver_cabecalho

    loja = _dados_loja(pedido.loja_id)
    styles = _styles()
    compact = styles["Compact"]
    section = styles["Section"]
    tipo_cab, dados_cab = _resolver_cabecalho(pedido.loja_id)
    top_margin = 3.2 * cm if tipo_cab == "timbrado" else 0.2 * cm
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=top_margin,
        bottomMargin=0.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    elements = []
    logo_url = loja.get("logo") or ""
    titulo_txt = f"PEDIDO DE COMPRA Nº {_fmt_numero(pedido.numero)}"
    if tipo_cab == "timbrado":
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(escape(titulo_txt), styles["Title"]))
    else:
        _cabecalho(elements, logo_url, styles, titulo_txt)

    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph("<b>Dados da Empresa</b>", section))
    _linha(elements, f"<b>Nome:</b> {escape(loja.get('nome') or '—')}", compact)
    if loja.get("endereco"):
        _linha(elements, f"<b>Endereço:</b> {escape(loja['endereco'])}", compact)
    if loja.get("cnpj"):
        _linha(elements, f"<b>CPF/CNPJ:</b> {escape(loja['cnpj'])}", compact)
    if loja.get("telefone"):
        _linha(elements, f"<b>Telefone:</b> {escape(_tel(loja['telefone']))}", compact)
    from .models.fornecedores import PedidoCompraAssinatura
    ass_cli = pedido.assinaturas.filter(
        tipo=PedidoCompraAssinatura.TIPO_CLINICA, assinado=True,
    ).first()
    if ass_cli and ass_cli.nome_assinante:
        resp = escape(ass_cli.nome_assinante)
        extras = []
        if ass_cli.cpf_assinante:
            extras.append(f"CPF {_formatar_cpf(ass_cli.cpf_assinante)}")
        if ass_cli.conselho_display:
            extras.append(ass_cli.conselho_display)
        if extras:
            resp += f" — {escape(' · '.join(extras))}"
        _linha(elements, f"<b>Responsável:</b> {resp}", compact)
    if loja.get("email"):
        _linha(elements, f"<b>Email:</b> {escape(loja['email'])}", compact)

    forn = pedido.fornecedor
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph("<b>Dados do Fornecedor</b>", section))
    _linha(elements, f"<b>Nome:</b> {escape(forn.razao_social or '—')}", compact)
    if forn.nome_fantasia and forn.nome_fantasia != forn.razao_social:
        _linha(elements, f"<b>Nome fantasia:</b> {escape(forn.nome_fantasia)}", compact)
    if forn.cnpj:
        _linha(elements, f"<b>CPF/CNPJ:</b> {escape(forn.cnpj)}", compact)
    if forn.telefone:
        _linha(elements, f"<b>Telefone:</b> {escape(_tel(forn.telefone))}", compact)
    if forn.email:
        _linha(elements, f"<b>Email:</b> {escape(forn.email)}", compact)
    end_forn = _endereco_fornecedor(forn)
    if end_forn:
        _linha(elements, f"<b>Endereço:</b> {escape(end_forn)}", compact)

    pacientes = list(pedido.pacientes.all())
    if pacientes:
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph("<b>Pacientes</b>", section))
        for idx, pac in enumerate(pacientes, start=1):
            linha = f"{idx}. {escape(pac.nome or '—')}"
            if pac.cpf:
                linha += f" — CPF {escape(_formatar_cpf(pac.cpf))}"
            _linha(elements, linha, compact)

    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph("<b>Itens do Pedido</b>", section))
    rows = [["Item", "Código", "Un.", "Qtd", "Preço Unit.", "Subtotal"]]
    for item in pedido.itens.all():
        rows.append([
            Paragraph(escape(item.nome), compact),
            escape(item.codigo or ""),
            escape(item.unidade or "un"),
            f"{item.quantidade:g}".replace(".", ","),
            _brl(item.preco),
            _brl(item.subtotal),
        ])
    tabela = Table(rows, colWidths=[6.2 * cm, 2.4 * cm, 1.4 * cm, 1.4 * cm, 2.3 * cm, 2.3 * cm])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FUNDO_TABELA),
        ("TEXTCOLOR", (0, 0), (-1, 0), VINHO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    tabela.hAlign = "LEFT"
    elements.append(tabela)

    resumo = Table([["Valor Total:", _brl(pedido.valor_total)]], colWidths=[5 * cm, 5 * cm])
    resumo.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), FUNDO_TOTAL),
        ("BOX", (0, 0), (-1, -1), 0.5, VINHO),
        ("TEXTCOLOR", (1, 0), (1, 0), VINHO),
    ]))
    resumo.hAlign = "LEFT"
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(resumo)

    if pedido.observacoes:
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph("<b>Conteúdo</b>", section))
        elements.append(Paragraph(escape(pedido.observacoes), compact))

    wm = _watermark_bytes(logo_url) if logo_url else None
    _secao_assinaturas(elements, pedido, loja, styles, wm_bytes=wm)

    doc.build(elements)
    return finalize_pdf_com_timbrado(buf, tipo_cab, dados_cab).getvalue()
