"""Resolução e construção de cabeçalho dos PDFs."""
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from ..models import MemedTimbrado
from ..pdf_common import logo_image
from .constants import MARGIN, PAGE_WIDTH


def _buscar_timbrado(loja_id):
    """Timbrado da loja pelo manager (com loja_id no contexto). Sem all_without_filter."""
    from tenants.middleware import get_current_loja_id, get_current_tenant_db, set_current_loja_id

    if not loja_id:
        return None
    anterior = get_current_loja_id()
    try:
        set_current_loja_id(loja_id)
        qs = MemedTimbrado.objects.filter(loja_id=loja_id)
        tenant_db = get_current_tenant_db()
        if tenant_db and tenant_db != "default":
            qs = qs.using(tenant_db)
        return qs.first()
    finally:
        set_current_loja_id(anterior)


def _resolver_cabecalho(loja_id):
    """Resolve qual cabeçalho usar no PDF.

    Prioridade:
        1. MemedTimbrado.pdf (se configurado para a loja)
        2. Loja.logo (se tem logo)
        3. Texto simples (nome da clínica + endereço + CNPJ)

    Retorna tupla:
        ('timbrado', bytes) | ('logo', url_string) | ('texto', loja_instance)
    """
    timbrado = _buscar_timbrado(loja_id)
    if timbrado and timbrado.pdf:
        return ("timbrado", bytes(timbrado.pdf))

    # 2. Logo da clínica
    from superadmin.models import Loja
    loja = Loja.objects.filter(id=loja_id).first()
    if loja and loja.logo:
        return ("logo", loja.logo)

    # 3. Texto simples (fallback)
    return ("texto", loja)


def _resolver_cabecalho_relatorio(loja_id):
    """Cabeçalho para relatórios (ex.: comissões): logo da loja; sem logo, timbrado Memed.
    """
    from superadmin.models import Loja

    loja = Loja.objects.filter(id=loja_id).first()
    logo_url = ""
    if loja:
        logo_url = (loja.logo or "").strip() or (getattr(loja, "login_logo", "") or "").strip()
    if logo_url:
        return ("logo", logo_url)

    timbrado = _buscar_timbrado(loja_id)
    if timbrado and timbrado.pdf:
        return ("timbrado", bytes(timbrado.pdf))

    return ("texto", loja)


def get_top_margin(loja_id):
    """Margem superior conforme tipo de cabeçalho (timbrado precisa de mais espaço)."""
    tipo, _ = _resolver_cabecalho(loja_id)
    return 3.2 * cm if tipo == "timbrado" else MARGIN


def _logo_image_flowable(logo_url: str, max_w=4 * cm, max_h=2.5 * cm):
    """Carrega logo por URL e retorna flowable ReportLab."""
    return logo_image(logo_url, max_w=max_w, max_h=max_h)


# ---------------------------------------------------------------------------
# Construção de elementos do PDF
# ---------------------------------------------------------------------------

def _build_header_elements(loja_id, styles):
    """Constrói elementos do cabeçalho para o PDF."""
    tipo, dados = _resolver_cabecalho(loja_id)
    elements = []

    if tipo == "timbrado":
        # Fundo timbrado é mesclado após gerar o PDF; apenas reserva espaço no topo.
        elements.append(Spacer(1, 6 * mm))

    elif tipo == "logo":
        img = _logo_image_flowable(dados)
        if img:
            elements.append(img)
        from superadmin.models import Loja
        loja = Loja.objects.filter(id=loja_id).first()
        if loja:
            elements.append(Paragraph(loja.nome, styles["ClinicaHeader"]))
            endereco = _formatar_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, styles["ClinicaSubHeader"]))
        elements.append(Spacer(1, 4 * mm))

    else:
        # Texto simples
        loja = dados
        if loja:
            elements.append(Paragraph(loja.nome, styles["ClinicaHeader"]))
            endereco = _formatar_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, styles["ClinicaSubHeader"]))
        elements.append(Spacer(1, 4 * mm))

    # Linha separadora
    elements.append(_linha_separadora())
    elements.append(Spacer(1, 4 * mm))

    return elements


def _formatar_endereco(loja) -> str:
    """Formata endereço da loja para exibição no cabeçalho."""
    partes = []
    if loja.logradouro:
        endereco = loja.logradouro
        if loja.numero:
            endereco += f", {loja.numero}"
        if loja.bairro:
            endereco += f" - {loja.bairro}"
        if loja.cidade and loja.uf:
            endereco += f" · {loja.cidade}/{loja.uf}"
        partes.append(endereco)
    if loja.cpf_cnpj:
        partes.append(f"CNPJ: {loja.cpf_cnpj}")
    return " · ".join(partes) if partes else ""


def _linha_separadora():
    """Cria uma linha horizontal separadora."""
    t = Table([[""]],
              colWidths=[PAGE_WIDTH - 2 * MARGIN],
              rowHeights=[1])
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.grey),
    ]))
    return t
