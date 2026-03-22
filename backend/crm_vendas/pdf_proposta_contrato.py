"""
Geração de PDF para Proposta e Contrato do CRM.
Inclui: Dados da Loja, Dados do Cliente, Produtos e Serviços da Oportunidade.
Suporta assinaturas digitais com marca d'água (IP + timestamp).
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER
import re
import pytz
import requests
from PIL import Image as PILImage


def _formatar_timestamp_local(assinado_em):
    """Converte timestamp UTC para timezone local (Brasil)"""
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    timestamp_local = assinado_em.astimezone(tz_brasil)
    return timestamp_local.strftime('%d/%m/%Y %H:%M:%S')


def _adicionar_logo_cabecalho(elements, logo_url, max_width=4*cm, max_height=2*cm):
    """
    Adiciona logo no cabeçalho do PDF.
    
    Args:
        elements: lista de elementos do PDF
        logo_url: URL do logo (Cloudinary)
        max_width: largura máxima do logo
        max_height: altura máxima do logo
    """
    if not logo_url:
        return
    
    try:
        # Baixar imagem do Cloudinary
        response = requests.get(logo_url, timeout=5)
        if response.status_code != 200:
            return
        
        # Criar objeto Image do reportlab
        img_buffer = BytesIO(response.content)
        
        # Obter dimensões originais da imagem
        pil_img = PILImage.open(img_buffer)
        img_width, img_height = pil_img.size
        
        # Calcular proporção para manter aspect ratio
        aspect = img_height / float(img_width)
        
        # Ajustar tamanho mantendo proporção
        if img_width > img_height:
            # Imagem horizontal
            width = min(max_width, img_width)
            height = width * aspect
            if height > max_height:
                height = max_height
                width = height / aspect
        else:
            # Imagem vertical ou quadrada
            height = min(max_height, img_height)
            width = height / aspect
            if width > max_width:
                width = max_width
                height = width * aspect
        
        # Resetar buffer para o início
        img_buffer.seek(0)
        
        # Criar elemento Image do reportlab
        img = Image(img_buffer, width=width, height=height)
        img.hAlign = 'CENTER'
        
        elements.append(img)
        elements.append(Spacer(1, 0.3*cm))
        
    except Exception as e:
        # Se falhar ao carregar logo, continua sem ele
        print(f"⚠️ Erro ao adicionar logo no PDF: {e}")
        pass


def _adicionar_marca_dagua_assinatura(elements, assinatura, styles):
    """
    Adiciona marca d'água com dados da assinatura digital.
    
    Args:
        elements: lista de elementos do PDF
        assinatura: instância de AssinaturaDigital
        styles: estilos do reportlab
    """
    if not assinatura or not assinatura.assinado:
        return
    
    # Formatar timestamp para timezone local (Brasil)
    timestamp_local = assinatura.assinado_em.strftime('%d/%m/%Y às %H:%M:%S')
    ip = assinatura.ip_address
    nome = assinatura.nome_assinante
    tipo = 'Cliente' if assinatura.tipo == 'cliente' else 'Vendedor'
    
    marca_texto = (
        f"<i><font color='#666666'>"
        f"✓ Assinado digitalmente por <b>{nome}</b> ({tipo})<br/>"
        f"Data/Hora: {timestamp_local}<br/>"
        f"IP: {ip}"
        f"</font></i>"
    )
    
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(marca_texto, styles['Normal']))


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
            'logo': getattr(loja, 'logo', '') or None,  # ✅ NOVO: incluir logo
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


def gerar_pdf_proposta(proposta, incluir_assinaturas=True) -> BytesIO:
    """
    Gera PDF da proposta comercial com Dados da Loja, Cliente e Produtos/Serviços.
    
    Args:
        proposta: instância de Proposta
        incluir_assinaturas: Se True, inclui marcas d'água das assinaturas digitais
    
    Returns:
        BytesIO: buffer com o PDF gerado
    """
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
        alignment=0,  # 0 = LEFT (alinhado à esquerda)
    )

    # ✅ NOVO: Adicionar logo no cabeçalho se disponível
    loja_id = getattr(proposta, 'loja_id', None)
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data and loja_data.get('logo'):
            _adicionar_logo_cabecalho(elements, loja_data['logo'])

    elements.append(Paragraph('PROPOSTA COMERCIAL', title_style))
    elements.append(Paragraph(f'<b>Título:</b> {proposta.titulo or "—"}', styles['Normal']))
    elements.append(Spacer(1, 0.2*cm))  # Reduzido de 0.3cm para 0.2cm (subir uma linha antes de Dados da Empresa)

    # Dados da Empresa
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data:
            elements.append(Paragraph('<b>Dados da Empresa</b>', section_style))
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
            elements.append(Spacer(1, 0.15*cm))  # Reduzido de 0.2cm para 0.15cm (subir uma linha antes de Dados do Cliente)

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
        elements.append(Spacer(1, 0.15*cm))  # Reduzido de 0.3cm para 0.15cm (subir uma linha antes de Produtos)

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
        t.hAlign = 'LEFT'  # Alinhar tabela à esquerda
        elements.append(t)
    else:
        elements.append(Paragraph('Nenhum item cadastrado.', styles['Normal']))
    # Valor total ao final dos Produtos e Serviços
    valor_str = _formatar_valor(proposta.valor_total)
    elements.append(Paragraph(f'<b>Valor total:</b> {valor_str}', styles['Normal']))
    elements.append(Spacer(1, 0.3*cm))  # Reduzido de 0.5cm para 0.3cm

    # Conteúdo
    conteudo = _strip_html(proposta.conteudo) if proposta.conteudo else 'Conteúdo não informado.'
    elements.append(Paragraph('<b>Conteúdo</b>', section_style))
    elements.append(Paragraph(conteudo[:3000] + ('...' if len(conteudo) > 3000 else ''), styles['Normal']))
    elements.append(Spacer(1, 0.2*cm))  # Reduzido de 0.3cm para 0.2cm (subir uma linha antes de Assinaturas)

    # Assinaturas (campos tradicionais + digitais integrados)
    nome_vendedor = getattr(proposta, 'nome_vendedor_assinatura', None) or ''
    nome_cliente = getattr(proposta, 'nome_cliente_assinatura', None) or ''
    
    elements.append(Paragraph('<b>Assinaturas</b>', section_style))
    elements.append(Spacer(1, 0.05*cm))  # Reduzido de 0.1cm para 0.05cm (subir mais os nomes)
    
    # Buscar assinaturas digitais se houver
    assinatura_vendedor = None
    assinatura_cliente = None
    if incluir_assinaturas:
        from .models import AssinaturaDigital
        assinaturas = AssinaturaDigital.objects.filter(
            proposta=proposta,
            assinado=True
        ).order_by('assinado_em')
        
        for ass in assinaturas:
            if ass.tipo == 'vendedor':
                assinatura_vendedor = ass
            elif ass.tipo == 'cliente':
                assinatura_cliente = ass
    
    # Montar dados da tabela com informações de assinatura digital
    vendedor_info = [nome_vendedor, 'Vendedor']
    cliente_info = [nome_cliente, 'Cliente']
    
    # Adicionar info de assinatura digital se houver
    if assinatura_vendedor:
        timestamp = _formatar_timestamp_local(assinatura_vendedor.assinado_em)
        vendedor_info.append(f'<font size="8">Assinado em: {timestamp}</font>')
        vendedor_info.append(f'<font size="8">IP: {assinatura_vendedor.ip_address}</font>')
        vendedor_info.append(f'<font size="8">Assinado digitalmente</font>')
    
    if assinatura_cliente:
        timestamp = _formatar_timestamp_local(assinatura_cliente.assinado_em)
        cliente_info.append(f'<font size="8">Assinado em: {timestamp}</font>')
        cliente_info.append(f'<font size="8">IP: {assinatura_cliente.ip_address}</font>')
        cliente_info.append(f'<font size="8">Assinado digitalmente</font>')
    
    # Criar tabela de assinaturas (2 colunas) - SEM linhas de assinatura
    assinatura_data = []
    
    # Adicionar linhas dinamicamente baseado no que tem info
    max_rows = max(len(vendedor_info), len(cliente_info))
    for i in range(max_rows):
        vendedor_text = Paragraph(vendedor_info[i], styles['Normal']) if i < len(vendedor_info) else ''
        cliente_text = Paragraph(cliente_info[i], styles['Normal']) if i < len(cliente_info) else ''
        assinatura_data.append([vendedor_text, cliente_text])
    
    assinatura_table = Table(assinatura_data, colWidths=[8*cm, 8*cm])
    assinatura_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 3),  # Reduzido de 5 para 3
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),  # Reduzido de 3 para 2
    ]))
    elements.append(assinatura_table)
    elements.append(Spacer(1, 0.5*cm))  # Reduzido de 1cm para 0.5cm

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_contrato(contrato, incluir_assinaturas=True) -> BytesIO:
    """
    Gera PDF do contrato com Dados da Loja, Cliente e Produtos/Serviços.
    
    Args:
        contrato: instância de Contrato
        incluir_assinaturas: Se True, inclui marcas d'água das assinaturas digitais
    
    Returns:
        BytesIO: buffer com o PDF gerado
    """
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

    # ✅ NOVO: Adicionar logo no cabeçalho se disponível
    loja_id = getattr(contrato, 'loja_id', None)
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data and loja_data.get('logo'):
            _adicionar_logo_cabecalho(elements, loja_data['logo'])

    elements.append(Paragraph('CONTRATO', title_style))
    elements.append(Paragraph(f'<b>Número:</b> {contrato.numero or "—"}', styles['Normal']))
    elements.append(Paragraph(f'<b>Título:</b> {contrato.titulo or "—"}', styles['Normal']))
    valor_str = _formatar_valor(contrato.valor_total)
    elements.append(Paragraph(f'<b>Valor total:</b> {valor_str}', styles['Normal']))
    elements.append(Spacer(1, 0.2*cm))  # Reduzido de 0.3cm para 0.2cm

    # Dados da Empresa
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data:
            elements.append(Paragraph('<b>Dados da Empresa</b>', section_style))
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
            elements.append(Spacer(1, 0.15*cm))  # Reduzido de 0.2cm para 0.15cm

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
        elements.append(Spacer(1, 0.15*cm))  # Reduzido de 0.5cm para 0.15cm

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
        elements.append(Spacer(1, 0.3*cm))  # Reduzido de 0.5cm para 0.3cm

    # Conteúdo
    conteudo = _strip_html(contrato.conteudo) if contrato.conteudo else 'Conteúdo não informado.'
    elements.append(Paragraph('<b>Conteúdo</b>', section_style))
    elements.append(Paragraph(conteudo[:3000] + ('...' if len(conteudo) > 3000 else ''), styles['Normal']))
    elements.append(Spacer(1, 0.2*cm))  # Reduzido de 1cm para 0.2cm

    # Assinaturas (campos tradicionais + digitais integrados)
    nome_vendedor = getattr(contrato, 'nome_vendedor_assinatura', None) or ''
    nome_cliente = getattr(contrato, 'nome_cliente_assinatura', None) or ''
    
    elements.append(Paragraph('<b>Assinaturas</b>', section_style))
    elements.append(Spacer(1, 0.05*cm))  # Reduzido para 0.05cm
    
    # Buscar assinaturas digitais se houver
    assinatura_vendedor = None
    assinatura_cliente = None
    if incluir_assinaturas:
        from .models import AssinaturaDigital
        assinaturas = AssinaturaDigital.objects.filter(
            contrato=contrato,
            assinado=True
        ).order_by('assinado_em')
        
        for ass in assinaturas:
            if ass.tipo == 'vendedor':
                assinatura_vendedor = ass
            elif ass.tipo == 'cliente':
                assinatura_cliente = ass
    
    # Montar dados da tabela com informações de assinatura digital
    vendedor_info = [nome_vendedor, 'Vendedor']
    cliente_info = [nome_cliente, 'Cliente']
    
    # Adicionar info de assinatura digital se houver
    if assinatura_vendedor:
        timestamp = _formatar_timestamp_local(assinatura_vendedor.assinado_em)
        vendedor_info.append(f'<font size="8">Assinado em: {timestamp}</font>')
        vendedor_info.append(f'<font size="8">IP: {assinatura_vendedor.ip_address}</font>')
        vendedor_info.append(f'<font size="8">Assinado digitalmente</font>')
    
    if assinatura_cliente:
        timestamp = _formatar_timestamp_local(assinatura_cliente.assinado_em)
        cliente_info.append(f'<font size="8">Assinado em: {timestamp}</font>')
        cliente_info.append(f'<font size="8">IP: {assinatura_cliente.ip_address}</font>')
        cliente_info.append(f'<font size="8">Assinado digitalmente</font>')
    
    # Criar tabela de assinaturas (2 colunas) - SEM linhas de assinatura
    assinatura_data = []
    
    # Adicionar linhas dinamicamente baseado no que tem info
    max_rows = max(len(vendedor_info), len(cliente_info))
    for i in range(max_rows):
        vendedor_text = Paragraph(vendedor_info[i], styles['Normal']) if i < len(vendedor_info) else ''
        cliente_text = Paragraph(cliente_info[i], styles['Normal']) if i < len(cliente_info) else ''
        assinatura_data.append([vendedor_text, cliente_text])
    
    assinatura_table = Table(assinatura_data, colWidths=[8*cm, 8*cm])
    assinatura_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 3),  # Reduzido de 5 para 3
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),  # Reduzido de 3 para 2
    ]))
    elements.append(assinatura_table)
    elements.append(Spacer(1, 0.5*cm))  # Reduzido de 1cm para 0.5cm

    doc.build(elements)
    buffer.seek(0)
    return buffer
