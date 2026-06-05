"""Resolução e construção de cabeçalho dos PDFs."""
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

from .constants import MARGIN, PAGE_WIDTH, logger
from ..models import MemedTimbrado

def _resolver_cabecalho(loja_id):
    """
    Resolve qual cabeçalho usar no PDF.

    Prioridade:
        1. MemedTimbrado.pdf (se configurado para a loja)
        2. Loja.logo (se tem logo)
        3. Texto simples (nome da clínica + endereço + CNPJ)

    Retorna tupla:
        ('timbrado', bytes) | ('logo', url_string) | ('texto', loja_instance)
    """
    # 1. Timbrado PDF (prioridade máxima)
    timbrado = MemedTimbrado.objects.filter(loja_id=loja_id).first()
    if timbrado and timbrado.pdf:
        return ('timbrado', bytes(timbrado.pdf))

    # 2. Logo da clínica
    from superadmin.models import Loja
    loja = Loja.objects.filter(id=loja_id).first()
    if loja and loja.logo:
        return ('logo', loja.logo)

    # 3. Texto simples (fallback)
    return ('texto', loja)


def _resolver_cabecalho_relatorio(loja_id):
    """
    Cabeçalho para relatórios (ex.: comissões): logo da loja; sem logo, timbrado Memed.
    """
    from superadmin.models import Loja

    loja = Loja.objects.filter(id=loja_id).first()
    logo_url = ''
    if loja:
        logo_url = (loja.logo or '').strip() or (getattr(loja, 'login_logo', '') or '').strip()
    if logo_url:
        return ('logo', logo_url)

    timbrado = MemedTimbrado.objects.filter(loja_id=loja_id).first()
    if timbrado and timbrado.pdf:
        return ('timbrado', bytes(timbrado.pdf))

    return ('texto', loja)


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------

def _get_styles():
    """Retorna estilos customizados para os PDFs do prontuário."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ClinicaHeader',
        parent=styles['Normal'],
        fontSize=14,
        leading=18,
        alignment=1,  # center
        spaceAfter=2 * mm,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'ClinicaSubHeader',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=1,
        spaceAfter=4 * mm,
        textColor=colors.grey,
    ))
    styles.add(ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontSize=12,
        leading=15,
        fontName='Helvetica-Bold',
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        'DocFooter',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        spaceAfter=2 * mm,
        textColor=colors.HexColor('#444444'),
    ))
    styles.add(ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=13,
        leading=16,
        fontName='Helvetica-Bold',
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
        textColor=colors.HexColor('#333333'),
    ))
    return styles


# ---------------------------------------------------------------------------
# Construção de elementos do PDF
# ---------------------------------------------------------------------------

def _build_header_elements(loja_id, styles):
    """Constrói elementos do cabeçalho para o PDF."""
    tipo, dados = _resolver_cabecalho(loja_id)
    elements = []

    if tipo == 'timbrado':
        # Para timbrado PDF completo, usamos apenas um espaço reservado
        # O timbrado é um PDF de fundo — na implementação simplificada,
        # exibimos o nome da clínica como fallback legível.
        from superadmin.models import Loja
        loja = Loja.objects.filter(id=loja_id).first()
        if loja:
            elements.append(Paragraph(loja.nome, styles['ClinicaHeader']))
            endereco = _formatar_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, styles['ClinicaSubHeader']))
        elements.append(Spacer(1, 4 * mm))

    elif tipo == 'logo':
        # Logo da clínica (URL) — tentamos carregar a imagem
        try:
            logo_url = dados
            img = Image(logo_url, width=4 * cm, height=2 * cm)
            img.hAlign = 'CENTER'
            elements.append(img)
        except Exception as e:
            logger.warning('Falha ao carregar logo para PDF: %s', e)

        from superadmin.models import Loja
        loja = Loja.objects.filter(id=loja_id).first()
        if loja:
            elements.append(Paragraph(loja.nome, styles['ClinicaHeader']))
            endereco = _formatar_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, styles['ClinicaSubHeader']))
        elements.append(Spacer(1, 4 * mm))

    else:
        # Texto simples
        loja = dados
        if loja:
            elements.append(Paragraph(loja.nome, styles['ClinicaHeader']))
            endereco = _formatar_endereco(loja)
            if endereco:
                elements.append(Paragraph(endereco, styles['ClinicaSubHeader']))
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
            endereco += f', {loja.numero}'
        if loja.bairro:
            endereco += f' - {loja.bairro}'
        if loja.cidade and loja.uf:
            endereco += f' · {loja.cidade}/{loja.uf}'
        partes.append(endereco)
    if loja.cpf_cnpj:
        partes.append(f'CNPJ: {loja.cpf_cnpj}')
    return ' · '.join(partes) if partes else ''


def _linha_separadora():
    """Cria uma linha horizontal separadora."""
    t = Table([['']],
              colWidths=[PAGE_WIDTH - 2 * MARGIN],
              rowHeights=[1])
    t.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.grey),
    ]))
    return t
