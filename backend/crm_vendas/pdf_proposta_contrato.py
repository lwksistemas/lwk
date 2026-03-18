"""
Geração de PDF para Proposta e Contrato do CRM.
Inclui: Dados da Loja, Dados do Cliente, Produtos e Serviços da Oportunidade.
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
import re


def _strip_html(html):
    """Remove tags HTML e retorna texto limpo."""
    if not html:
        return ''
    text = re.sub(r'<[^>]+>', ' ', str(html))
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _formatar_valor(valor):
    """Formata valor monetário para exibição."""
    if valor is None:
        return '—'
    try:
        v = float(valor)
        return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (TypeError, ValueError):
        return '—'


def _obter_dados_loja(loja_id):
    """Obtém dados da loja do superadmin (nome, endereço, CPF/CNPJ, admin)."""
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
        }
    except Exception:
        return {}


def _formatar_endereco_lead(lead):
    """Monta string de endereço do lead."""
    if not lead:
        return '—'
    parts = [
        getattr(lead, 'logradouro', '') or '',
        getattr(lead, 'numero', '') and f"nº {lead.numero}" or '',
        getattr(lead, 'complemento', '') or '',
        getattr(lead, 'bairro', '') or '',
        (f"{lead.cidade}/{lead.uf}" if (getattr(lead, 'cidade', '') and getattr(lead, 'uf', '')) else (getattr(lead, 'cidade', '') or getattr(lead, 'uf', ''))),
        getattr(lead, 'cep', '') and f"CEP {lead.cep}" or '',
    ]
    return ', '.join(p for p in parts if p).strip() or '—'


def gerar_pdf_proposta(proposta) -> BytesIO:
    """Gera PDF da proposta comercial com Dados da Loja, Cliente e Produtos/Serviços."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'PropostaTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0176d3'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
    )

    elements.append(Paragraph('PROPOSTA COMERCIAL', title_style))
    elements.append(Paragraph(f'<b>Título:</b> {proposta.titulo or "—"}', styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # Dados da Loja
    loja_id = getattr(proposta, 'loja_id', None)
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data:
            elements.append(Paragraph('<b>Dados da Loja</b>', section_style))
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
                elements.append(Paragraph(ln, styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))

    # Dados do Cliente
    lead = proposta.oportunidade.lead if proposta.oportunidade and proposta.oportunidade.lead else None
    if lead:
        elements.append(Paragraph('<b>Dados do Cliente</b>', section_style))
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", styles['Normal']))
        if getattr(lead, 'empresa', ''):
            elements.append(Paragraph(f"<b>Empresa:</b> {lead.empresa}", styles['Normal']))
        if getattr(lead, 'cpf_cnpj', ''):
            elements.append(Paragraph(f"<b>CPF/CNPJ:</b> {lead.cpf_cnpj}", styles['Normal']))
        if getattr(lead, 'email', ''):
            elements.append(Paragraph(f"<b>Email:</b> {lead.email}", styles['Normal']))
        if getattr(lead, 'telefone', ''):
            elements.append(Paragraph(f"<b>Telefone:</b> {lead.telefone}", styles['Normal']))
        elements.append(Paragraph(f"<b>Endereço:</b> {_formatar_endereco_lead(lead)}", styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))

    # Produtos e Serviços da Oportunidade (Valor total ao final)
    itens = []
    if proposta.oportunidade:
        itens = list(proposta.oportunidade.itens.all())
    elements.append(Paragraph('<b>Produtos e Serviços da Oportunidade</b>', section_style))
    if itens:
        table_data = [['Item', 'Qtd', 'Preço Unit.', 'Subtotal']]
        for item in itens:
            ps = item.produto_servico
            tipo_ps = ps.get_tipo_display() if hasattr(ps, 'get_tipo_display') else getattr(ps, 'tipo', '')
            nome = f"{tipo_ps}: {ps.nome}" if tipo_ps else ps.nome
            qtd = str(item.quantidade) if item.quantidade is not None else '1'
            preco = _formatar_valor(item.preco_unitario)
            subtotal = _formatar_valor(getattr(item, 'subtotal', None) or (item.quantidade * item.preco_unitario if item.quantidade and item.preco_unitario else None))
            table_data.append([nome, qtd, preco, subtotal])
        t = Table(table_data, colWidths=[None, 40, 70, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f3ff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph('Nenhum item cadastrado.', styles['Normal']))
    # Valor total ao final dos Produtos e Serviços
    valor_str = _formatar_valor(proposta.valor_total)
    elements.append(Paragraph(f'<b>Valor total:</b> {valor_str}', styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # Conteúdo
    conteudo = _strip_html(proposta.conteudo) if proposta.conteudo else 'Conteúdo não informado.'
    elements.append(Paragraph('<b>Conteúdo</b>', section_style))
    elements.append(Paragraph(conteudo[:3000] + ('...' if len(conteudo) > 3000 else ''), styles['Normal']))
    elements.append(Spacer(1, 1*cm))

    # Assinaturas
    nome_vendedor = getattr(proposta, 'nome_vendedor_assinatura', None) or '___________________________'
    nome_cliente = getattr(proposta, 'nome_cliente_assinatura', None) or '___________________________'
    
    elements.append(Paragraph('<b>Assinaturas</b>', section_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Tabela de assinaturas (2 colunas)
    assinatura_data = [
        ['___________________________', '___________________________'],
        [nome_vendedor, nome_cliente],
        ['Vendedor', 'Cliente'],
    ]
    assinatura_table = Table(assinatura_data, colWidths=[8*cm, 8*cm])
    assinatura_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 20),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 5),
    ]))
    elements.append(assinatura_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_contrato(contrato) -> BytesIO:
    """Gera PDF do contrato com Dados da Loja, Cliente e Produtos/Serviços."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ContratoTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0176d3'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
    )

    elements.append(Paragraph('CONTRATO', title_style))
    elements.append(Paragraph(f'<b>Número:</b> {contrato.numero or "—"}', styles['Normal']))
    elements.append(Paragraph(f'<b>Título:</b> {contrato.titulo or "—"}', styles['Normal']))
    valor_str = _formatar_valor(contrato.valor_total)
    elements.append(Paragraph(f'<b>Valor total:</b> {valor_str}', styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # Dados da Loja
    loja_id = getattr(contrato, 'loja_id', None)
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data:
            elements.append(Paragraph('<b>Dados da Loja</b>', section_style))
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
                elements.append(Paragraph(ln, styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))

    # Dados do Cliente
    lead = contrato.oportunidade.lead if contrato.oportunidade and contrato.oportunidade.lead else None
    if lead:
        elements.append(Paragraph('<b>Dados do Cliente</b>', section_style))
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", styles['Normal']))
        if getattr(lead, 'empresa', ''):
            elements.append(Paragraph(f"<b>Empresa:</b> {lead.empresa}", styles['Normal']))
        if getattr(lead, 'cpf_cnpj', ''):
            elements.append(Paragraph(f"<b>CPF/CNPJ:</b> {lead.cpf_cnpj}", styles['Normal']))
        if getattr(lead, 'email', ''):
            elements.append(Paragraph(f"<b>Email:</b> {lead.email}", styles['Normal']))
        if getattr(lead, 'telefone', ''):
            elements.append(Paragraph(f"<b>Telefone:</b> {lead.telefone}", styles['Normal']))
        elements.append(Paragraph(f"<b>Endereço:</b> {_formatar_endereco_lead(lead)}", styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))

    # Produtos e Serviços da Oportunidade
    itens = []
    if contrato.oportunidade:
        itens = list(contrato.oportunidade.itens.all())
    if itens:
        elements.append(Paragraph('<b>Produtos e Serviços da Oportunidade</b>', section_style))
        table_data = [['Item', 'Qtd', 'Preço Unit.', 'Subtotal']]
        for item in itens:
            ps = item.produto_servico
            tipo_ps = ps.get_tipo_display() if hasattr(ps, 'get_tipo_display') else getattr(ps, 'tipo', '')
            nome = f"{tipo_ps}: {ps.nome}" if tipo_ps else ps.nome
            qtd = str(item.quantidade) if item.quantidade is not None else '1'
            preco = _formatar_valor(item.preco_unitario)
            subtotal = _formatar_valor(getattr(item, 'subtotal', None) or (item.quantidade * item.preco_unitario if item.quantidade and item.preco_unitario else None))
            table_data.append([nome, qtd, preco, subtotal])
        t = Table(table_data, colWidths=[None, 40, 70, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f3ff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.5*cm))

    # Conteúdo
    conteudo = _strip_html(contrato.conteudo) if contrato.conteudo else 'Conteúdo não informado.'
    elements.append(Paragraph('<b>Conteúdo</b>', section_style))
    elements.append(Paragraph(conteudo[:3000] + ('...' if len(conteudo) > 3000 else ''), styles['Normal']))
    elements.append(Spacer(1, 1*cm))

    # Assinaturas
    nome_vendedor = getattr(contrato, 'nome_vendedor_assinatura', None) or '___________________________'
    nome_cliente = getattr(contrato, 'nome_cliente_assinatura', None) or '___________________________'
    
    elements.append(Paragraph('<b>Assinaturas</b>', section_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Tabela de assinaturas (2 colunas)
    assinatura_data = [
        ['___________________________', '___________________________'],
        [nome_vendedor, nome_cliente],
        ['Vendedor', 'Cliente'],
    ]
    assinatura_table = Table(assinatura_data, colWidths=[8*cm, 8*cm])
    assinatura_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 20),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 5),
    ]))
    elements.append(assinatura_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
