"""
Geração de PDF para Proposta e Contrato do CRM.
Inclui: Dados da Loja, Dados do Cliente, Produtos e Serviços da Oportunidade.
Suporta assinaturas digitais com marca d'água (logo transparente).
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import re
import pytz
import logging
import requests
from PIL import Image as PILImage

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ═══════════════════════════════════════════════════════════════════════════════


def _formatar_timestamp_local(assinado_em):
    """Converte timestamp UTC para timezone local (Brasil)."""
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    return assinado_em.astimezone(tz_brasil).strftime('%d/%m/%Y %H:%M:%S')


def _formatar_valor(valor):
    """Formata valor monetário para exibição."""
    if valor is None:
        return '—'
    try:
        v = float(valor)
        return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (TypeError, ValueError):
        return '—'


def _formatar_endereco_lead(lead):
    """Monta string de endereço do lead."""
    if not lead:
        return '—'
    parts = [
        getattr(lead, 'logradouro', '') or '',
        f"nº {lead.numero}" if getattr(lead, 'numero', '') else '',
        getattr(lead, 'complemento', '') or '',
        getattr(lead, 'bairro', '') or '',
        (f"{lead.cidade}/{lead.uf}" if (getattr(lead, 'cidade', '') and getattr(lead, 'uf', ''))
         else (getattr(lead, 'cidade', '') or getattr(lead, 'uf', ''))),
        f"CEP {lead.cep}" if getattr(lead, 'cep', '') else '',
    ]
    return ', '.join(p for p in parts if p).strip() or '—'


def _formatar_nome_usuario(user):
    """Tenta montar um nome legível para o usuário (vendedor)."""
    if not user:
        return '—'
    first = getattr(user, 'first_name', '') or ''
    last = getattr(user, 'last_name', '') or ''
    full = f'{first} {last}'.strip()
    return full or getattr(user, 'nome', '') or getattr(user, 'username', '') or '—'


def _html_to_paragraphs(html):
    """Converte HTML/texto do conteúdo em lista de parágrafos para o PDF."""
    if not html:
        return ['Conteúdo não informado.']
    text = str(html)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|div|li|h[1-6])>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>', '• ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    lines = text.split('\n')
    paragraphs = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            paragraphs.append(stripped)
        elif paragraphs:
            paragraphs.append('')
    return paragraphs if paragraphs else ['Conteúdo não informado.']


def _obter_dados_loja(loja_id):
    """Obtém dados da loja do superadmin (nome, endereço, CPF/CNPJ, admin, logo)."""
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).select_related('owner').first()
        if not loja:
            return {}
        cidade = getattr(loja, 'cidade', '') or ''
        uf = getattr(loja, 'uf', '') or ''
        cidade_uf = f"{cidade}/{uf}" if (cidade and uf) else (cidade or uf)
        endereco_parts = [
            getattr(loja, 'logradouro', '') or '',
            getattr(loja, 'numero', '') or '',
            getattr(loja, 'complemento', '') or '',
            getattr(loja, 'bairro', '') or '',
            cidade_uf,
            f"CEP {loja.cep}" if getattr(loja, 'cep', '') else '',
        ]
        endereco = ', '.join(p for p in endereco_parts if p).strip() or None
        owner = getattr(loja, 'owner', None)
        admin_nome = None
        admin_email = None
        if owner:
            admin_nome = f"{getattr(owner, 'first_name', '') or ''} {getattr(owner, 'last_name', '') or ''}".strip() or getattr(owner, 'username', '') or None
            admin_email = getattr(owner, 'email', None) or None
        return {
            'nome': getattr(loja, 'nome', '') or '',
            'endereco': endereco,
            'cpf_cnpj': getattr(loja, 'cpf_cnpj', '') or None,
            'admin_nome': admin_nome,
            'admin_email': admin_email,
            'logo': getattr(loja, 'logo', '') or None,
        }
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÕES REUTILIZÁVEIS DO PDF
# ═══════════════════════════════════════════════════════════════════════════════


def _build_cabecalho(elements, logo_url, titulo):
    """Cria cabeçalho com logo à esquerda e título à direita."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'HeaderTitle', parent=styles['Heading1'], fontSize=16,
        textColor=colors.HexColor('#0176d3'), alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=0, leading=18,
    )
    if not logo_url:
        title_style.alignment = TA_CENTER
        elements.append(Paragraph(titulo, title_style))
        return
    try:
        response = requests.get(logo_url, timeout=5)
        if response.status_code != 200:
            raise ValueError('Logo não disponível')
        img_buffer = BytesIO(response.content)
        pil_img = PILImage.open(img_buffer)
        iw, ih = pil_img.size
        aspect = ih / float(iw)
        max_w, max_h = 6 * cm, 3 * cm
        width = min(max_w, iw)
        height = width * aspect
        if height > max_h:
            height = max_h
            width = height / aspect
        img_buffer.seek(0)
        img = Image(img_buffer, width=width, height=height)
        table = Table([[img, Paragraph(titulo, title_style)]], colWidths=[width + 0.5 * cm, None])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(table)
    except Exception as e:
        logger.warning(f"Erro ao adicionar logo no PDF: {e}")
        title_style.alignment = TA_CENTER
        elements.append(Paragraph(titulo, title_style))


def _build_secao_empresa(elements, loja_data, style):
    """Adiciona seção Dados da Empresa."""
    section = ParagraphStyle('SecEmpresa', parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph('<b>Dados da Empresa</b>', section))
    linhas = [f"<b>Nome:</b> {loja_data.get('nome') or '—'}"]
    if loja_data.get('endereco'):
        linhas.append(f"<b>Endereço:</b> {loja_data['endereco']}")
    if loja_data.get('cpf_cnpj'):
        linhas.append(f"<b>CPF/CNPJ:</b> {loja_data['cpf_cnpj']}")
    if loja_data.get('admin_nome'):
        linhas.append(f"<b>Administrador:</b> {loja_data['admin_nome']}")
    if loja_data.get('admin_email'):
        linhas.append(f"<b>Email do administrador:</b> {loja_data['admin_email']}")
    for ln in linhas:
        elements.append(Paragraph(ln, style))


def _build_secao_cliente(elements, lead, style):
    """Adiciona seção Dados do Cliente."""
    section = ParagraphStyle('SecCliente', parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph('<b>Dados do Cliente</b>', section))
    conta = getattr(lead, 'conta', None)
    if conta:
        elements.append(Paragraph(f"<b>Nome de contato:</b> {lead.nome}", style))
        empresa_nome = conta.razao_social or conta.nome or ''
        if empresa_nome:
            elements.append(Paragraph(f"<b>Empresa:</b> {empresa_nome}", style))
    else:
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", style))
    if getattr(lead, 'cpf_cnpj', ''):
        elements.append(Paragraph(f"<b>CPF/CNPJ:</b> {lead.cpf_cnpj}", style))
    if getattr(lead, 'email', ''):
        elements.append(Paragraph(f"<b>Email:</b> {lead.email}", style))
    if getattr(lead, 'telefone', ''):
        elements.append(Paragraph(f"<b>Telefone:</b> {lead.telefone}", style))
    elements.append(Paragraph(f"<b>Endereço:</b> {_formatar_endereco_lead(lead)}", style))


def _build_secao_produtos(elements, oportunidade, style, incluir_recorrencia=True):
    """Adiciona seção Produtos e Serviços."""
    section = ParagraphStyle('SecProd', parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph('<b>Produtos e Serviços da Oportunidade</b>', section))
    itens = list(oportunidade.itens.select_related('produto_servico').all()) if oportunidade else []
    if not itens:
        elements.append(Paragraph('Nenhum item cadastrado.', style))
        return 0, 0
    if incluir_recorrencia:
        table_data = [['Item', 'Recorrência', 'Qtd', 'Preço Unit.', 'Subtotal']]
    else:
        table_data = [['Item', 'Qtd', 'Preço Unit.', 'Subtotal']]
    valor_unico = 0
    valor_mensal = 0
    for item in itens:
        ps = item.produto_servico
        tipo_ps = ps.get_tipo_display() if hasattr(ps, 'get_tipo_display') else getattr(ps, 'tipo', '')
        nome = f"{tipo_ps}: {ps.nome}" if tipo_ps else ps.nome
        recorrencia = getattr(ps, 'recorrencia', 'unico') or 'unico'
        recorrencia_label = {'unico': 'Único', 'mensal': 'Mensal', 'trimestral': 'Trimestral', 'anual': 'Anual'}.get(recorrencia, recorrencia)
        qtd = str(item.quantidade) if item.quantidade is not None else '1'
        preco = _formatar_valor(item.preco_unitario)
        sub = item.quantidade * item.preco_unitario if item.quantidade and item.preco_unitario else 0
        subtotal = _formatar_valor(sub)
        if incluir_recorrencia:
            table_data.append([nome, recorrencia_label, qtd, preco, subtotal])
        else:
            table_data.append([nome, qtd, preco, subtotal])
        if recorrencia == 'unico':
            valor_unico += float(sub)
        else:
            valor_mensal += float(sub)
    if incluir_recorrencia:
        col_widths = [None, 60, 35, 65, 65]
    else:
        col_widths = [None, 40, 70, 70]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f3ff')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t.hAlign = 'LEFT'
    elements.append(t)
    return valor_unico, valor_mensal


def _build_secao_desconto(elements, documento, style):
    """Adiciona resumo financeiro com tabela visual."""
    valor_total = documento.valor_total
    desconto_valor = getattr(documento, 'desconto_valor', None) or 0
    has_desconto = desconto_valor and float(desconto_valor) > 0

    # Buscar valores de adesão/mensal se disponíveis nos itens
    oportunidade = getattr(documento, 'oportunidade', None)
    valor_unico = 0
    valor_mensal = 0
    if oportunidade:
        try:
            for item in oportunidade.itens.select_related('produto_servico').all():
                ps = item.produto_servico
                recorrencia = getattr(ps, 'recorrencia', 'unico') or 'unico'
                sub = float(item.quantidade * item.preco_unitario) if item.quantidade and item.preco_unitario else 0
                if recorrencia == 'unico':
                    valor_unico += sub
                else:
                    valor_mensal += sub
        except Exception:
            pass

    # Montar tabela de resumo financeiro
    resumo_data = []
    if valor_unico > 0:
        resumo_data.append(['Adesão/Implantação:', _formatar_valor(valor_unico)])
    if valor_mensal > 0:
        resumo_data.append(['Valor Mensal:', f'{_formatar_valor(valor_mensal)}/mês'])
    resumo_data.append(['Valor Total:', _formatar_valor(valor_total)])
    if has_desconto:
        desconto_tipo = getattr(documento, 'desconto_tipo', 'percentual')
        if desconto_tipo == 'percentual':
            resumo_data.append(['Desconto:', f'{desconto_valor}%'])
        else:
            resumo_data.append(['Desconto:', _formatar_valor(desconto_valor)])
        valor_final = getattr(documento, 'valor_com_desconto', valor_total)
        resumo_data.append(['Valor com Desconto:', _formatar_valor(valor_final)])

    t = Table(resumo_data, colWidths=[5 * cm, 5 * cm])
    style_cmds = [
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#0176d3')),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, colors.HexColor('#e5e7eb')),
    ]
    # Destacar última linha (valor final)
    last = len(resumo_data) - 1
    style_cmds.append(('FONTNAME', (0, last), (-1, last), 'Helvetica-Bold'))
    style_cmds.append(('FONTSIZE', (0, last), (-1, last), 10))
    style_cmds.append(('BACKGROUND', (0, last), (-1, last), colors.HexColor('#e0f2fe')))
    style_cmds.append(('TEXTCOLOR', (1, last), (1, last), colors.HexColor('#0176d3')))
    t.setStyle(TableStyle(style_cmds))
    t.hAlign = 'LEFT'
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(t)
    elements.append(Spacer(1, 0.2 * cm))


def _build_secao_conteudo(elements, conteudo, style):
    """Adiciona seção Conteúdo."""
    section = ParagraphStyle('SecConteudo', parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph('<b>Conteúdo</b>', section))
    styles = getSampleStyleSheet()
    for p in _html_to_paragraphs(conteudo)[:100]:
        if p == '':
            elements.append(Spacer(1, 0.2 * cm))
        else:
            elements.append(Paragraph(p[:500], styles['Normal']))


def _build_secao_assinaturas(elements, documento, lead, vendedor, style, incluir_assinaturas=True, tipo_doc='proposta'):
    """Adiciona seção Assinaturas com dados digitais."""
    section = ParagraphStyle('SecAssin', parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph('<b>Assinaturas</b>', section))

    nome_vendedor = getattr(documento, 'nome_vendedor_assinatura', None) or ''
    nome_cliente = getattr(documento, 'nome_cliente_assinatura', None) or ''
    lead_email = getattr(lead, 'email', '') or '' if lead else ''
    vendedor_email = getattr(vendedor, 'email', '') or '' if vendedor else ''

    assinatura_vendedor = None
    assinatura_cliente = None
    if incluir_assinaturas:
        from .models import AssinaturaDigital
        filtro = {'assinado': True}
        if tipo_doc == 'proposta':
            filtro['proposta'] = documento
        else:
            filtro['contrato'] = documento
        for ass in AssinaturaDigital.objects.filter(**filtro).order_by('assinado_em'):
            if ass.tipo == 'vendedor':
                assinatura_vendedor = ass
            elif ass.tipo == 'cliente':
                assinatura_cliente = ass

    vendedor_nome_fmt = (nome_vendedor or _formatar_nome_usuario(vendedor)).strip().upper() or '—'
    cliente_nome_fmt = (nome_cliente or getattr(lead, 'nome', '') or '—').strip().upper() or '—'

    vendedor_info = [f"Vendedor: {vendedor_nome_fmt}"]
    if vendedor_email:
        vendedor_info.append(f"<font size='8'>Email: {vendedor_email}</font>")
    if assinatura_vendedor:
        ts = _formatar_timestamp_local(assinatura_vendedor.assinado_em)
        vendedor_info.append(f'<font size="8">Assinado em: {ts}</font>')
        vendedor_info.append(f'<font size="8">IP: {assinatura_vendedor.ip_address}</font>')
        vendedor_info.append(f'<font size="8">Assinado digitalmente</font>')

    cliente_info = [f"Cliente: {cliente_nome_fmt}"]
    if lead_email:
        cliente_info.append(f"<font size='8'>Email: {lead_email}</font>")
    if assinatura_cliente:
        ts = _formatar_timestamp_local(assinatura_cliente.assinado_em)
        cliente_info.append(f'<font size="8">Assinado em: {ts}</font>')
        cliente_info.append(f'<font size="8">IP: {assinatura_cliente.ip_address}</font>')
        cliente_info.append(f'<font size="8">Assinado digitalmente</font>')

    assinatura_data = []
    max_rows = max(len(vendedor_info), len(cliente_info))
    for i in range(max_rows):
        v_text = Paragraph(vendedor_info[i], style) if i < len(vendedor_info) else ''
        c_text = Paragraph(cliente_info[i], style) if i < len(cliente_info) else ''
        assinatura_data.append([v_text, c_text])

    t = Table(assinatura_data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('BOX', (0, 0), (0, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('BOX', (1, 0), (1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.1 * cm))

    # Mensagem de validade jurídica
    validade = ParagraphStyle('Validade', parent=style, fontSize=7,
                              textColor=colors.HexColor('#666666'), alignment=TA_CENTER, spaceBefore=2)
    elements.append(Paragraph(
        'Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, '
        'com registro de data, hora e endereço IP.', validade))

    return assinatura_vendedor, assinatura_cliente


def _build_watermark_callback(logo_url, assinatura_vendedor, assinatura_cliente):
    """Prepara dados da marca d'água (logo transparente) para uso nas assinaturas.
    Retorna bytes PNG da imagem com transparência, ou None.
    """
    if not (assinatura_vendedor or assinatura_cliente) or not logo_url:
        return None
    try:
        resp = requests.get(logo_url, timeout=5)
        if resp.status_code != 200:
            return None
        pil_img = PILImage.open(BytesIO(resp.content)).convert('RGBA')
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.25))
        pil_img.putalpha(alpha)
        out_buf = BytesIO()
        pil_img.save(out_buf, format='PNG')
        return out_buf.getvalue()
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES PÚBLICAS
# ═══════════════════════════════════════════════════════════════════════════════


def gerar_pdf_proposta(proposta, incluir_assinaturas=True) -> BytesIO:
    """Gera PDF da proposta comercial."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.2 * cm, bottomMargin=0.5 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()
    compact = ParagraphStyle('Compact', parent=styles['Normal'], fontSize=9, spaceBefore=0, spaceAfter=1, leading=11)

    # Cabeçalho
    loja_id = getattr(proposta, 'loja_id', None)
    loja_data = _obter_dados_loja(loja_id) if loja_id else {}
    logo_url = loja_data.get('logo')
    _build_cabecalho(elements, logo_url, 'PROPOSTA COMERCIAL')
    elements.append(Paragraph(f'<b>Título:</b> {proposta.titulo or "—"}', compact))

    # Dados da Empresa
    if loja_data:
        _build_secao_empresa(elements, loja_data, compact)

    # Dados do Cliente
    lead = proposta.oportunidade.lead if proposta.oportunidade and proposta.oportunidade.lead else None
    if lead:
        _build_secao_cliente(elements, lead, compact)

    # Produtos e Serviços
    _build_secao_produtos(elements, proposta.oportunidade, compact, incluir_recorrencia=True)

    # Valor total e desconto
    _build_secao_desconto(elements, proposta, compact)

    # Conteúdo
    _build_secao_conteudo(elements, proposta.conteudo, compact)

    # Assinaturas
    vendedor = proposta.oportunidade.vendedor if proposta.oportunidade and getattr(proposta.oportunidade, 'vendedor', None) else None
    ass_v, ass_c = _build_secao_assinaturas(elements, proposta, lead, vendedor, compact, incluir_assinaturas, 'proposta')

    # Build com marca d'água
    wm_data = _build_watermark_callback(logo_url, ass_v, ass_c)
    if wm_data:
        # Inserir marca d'água como flowable antes da tabela de assinaturas
        from reportlab.platypus import Flowable

        class WatermarkFlowable(Flowable):
            """Desenha marca d'água no canvas na posição atual do fluxo."""
            def __init__(self, wm_bytes):
                Flowable.__init__(self)
                self.wm_bytes = wm_bytes
                self.width = 16 * cm
                self.height = 0  # não ocupa espaço vertical

            def draw(self):
                try:
                    from reportlab.lib.utils import ImageReader
                    img = ImageReader(BytesIO(self.wm_bytes))
                    iw, ih = img.getSize()
                    wm_w = 5.5 * cm
                    wm_h = wm_w * (ih / float(iw))
                    if wm_h > 3.5 * cm:
                        wm_h = 3.5 * cm
                        wm_w = wm_h / (ih / float(iw))
                    # Topo da marca d'água alinhado com a linha do email (row 1)
                    y_offset = -(0.35 * cm + wm_h)
                    x_left = (8 * cm - wm_w) / 2
                    x_right = 8 * cm + (8 * cm - wm_w) / 2
                    self.canv.drawImage(img, x_left, y_offset, width=wm_w, height=wm_h, mask='auto', preserveAspectRatio=True)
                    self.canv.drawImage(img, x_right, y_offset, width=wm_w, height=wm_h, mask='auto', preserveAspectRatio=True)
                except Exception:
                    pass

        # Encontrar a tabela de assinaturas (última Table) e inserir watermark antes dela
        insert_idx = None
        for i in range(len(elements) - 1, -1, -1):
            if isinstance(elements[i], Table):
                insert_idx = i
                break
        if insert_idx is not None:
            elements.insert(insert_idx, WatermarkFlowable(wm_data))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_contrato(contrato, incluir_assinaturas=True) -> BytesIO:
    """Gera PDF do contrato."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * cm, bottomMargin=1 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()
    normal = styles['Normal']

    # Cabeçalho
    loja_id = getattr(contrato, 'loja_id', None)
    loja_data = _obter_dados_loja(loja_id) if loja_id else {}
    logo_url = loja_data.get('logo')
    _build_cabecalho(elements, logo_url, 'CONTRATO')
    elements.append(Spacer(1, 0.01 * cm))
    elements.append(Paragraph(f'<b>Número:</b> {contrato.numero or "—"}', normal))
    elements.append(Paragraph(f'<b>Título:</b> {contrato.titulo or "—"}', normal))

    # Valor total e desconto
    _build_secao_desconto(elements, contrato, normal)
    elements.append(Spacer(1, 0.03 * cm))

    # Dados da Empresa
    if loja_data:
        _build_secao_empresa(elements, loja_data, normal)

    # Dados do Cliente
    lead = contrato.oportunidade.lead if contrato.oportunidade and contrato.oportunidade.lead else None
    if lead:
        _build_secao_cliente(elements, lead, normal)

    # Produtos e Serviços
    if contrato.oportunidade and contrato.oportunidade.itens.exists():
        _build_secao_produtos(elements, contrato.oportunidade, normal, incluir_recorrencia=False)
        elements.append(Spacer(1, 0.05 * cm))

    # Conteúdo
    _build_secao_conteudo(elements, contrato.conteudo, normal)

    # Assinaturas
    vendedor = contrato.oportunidade.vendedor if contrato.oportunidade and getattr(contrato.oportunidade, 'vendedor', None) else None
    ass_v, ass_c = _build_secao_assinaturas(elements, contrato, lead, vendedor, normal, incluir_assinaturas, 'contrato')

    # Build com marca d'água
    wm_data = _build_watermark_callback(logo_url, ass_v, ass_c)
    if wm_data:
        from reportlab.platypus import Flowable

        class WatermarkFlowable(Flowable):
            def __init__(self, wm_bytes):
                Flowable.__init__(self)
                self.wm_bytes = wm_bytes
                self.width = 16 * cm
                self.height = 0

            def draw(self):
                try:
                    from reportlab.lib.utils import ImageReader
                    img = ImageReader(BytesIO(self.wm_bytes))
                    iw, ih = img.getSize()
                    wm_w = 5.5 * cm
                    wm_h = wm_w * (ih / float(iw))
                    if wm_h > 3.5 * cm:
                        wm_h = 3.5 * cm
                        wm_w = wm_h / (ih / float(iw))
                    y_offset = -(0.35 * cm + wm_h)
                    x_left = (8 * cm - wm_w) / 2
                    x_right = 8 * cm + (8 * cm - wm_w) / 2
                    self.canv.drawImage(img, x_left, y_offset, width=wm_w, height=wm_h, mask='auto', preserveAspectRatio=True)
                    self.canv.drawImage(img, x_right, y_offset, width=wm_w, height=wm_h, mask='auto', preserveAspectRatio=True)
                except Exception:
                    pass

        insert_idx = None
        for i in range(len(elements) - 1, -1, -1):
            if isinstance(elements[i], Table):
                insert_idx = i
                break
        if insert_idx is not None:
            elements.insert(insert_idx, WatermarkFlowable(wm_data))

    doc.build(elements)
    buffer.seek(0)
    return buffer
