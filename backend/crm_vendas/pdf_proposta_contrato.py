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


def _criar_cabecalho_com_logo(logo_url, titulo, max_width=6*cm, max_height=3*cm):
    """
    Cria cabeçalho com logo à esquerda e título à direita na mesma linha.
    
    Args:
        logo_url: URL do logo (Cloudinary)
        titulo: Texto do título (ex: 'PROPOSTA COMERCIAL')
        max_width: largura máxima do logo
        max_height: altura máxima do logo
    
    Returns:
        Table ou Paragraph (se não houver logo)
    """
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0176d3'),
        alignment=TA_LEFT,
        spaceBefore=0,  # Sem espaço antes
        spaceAfter=0,   # Sem espaço depois
        leading=22,     # Altura da linha
    )
    
    # Se não houver logo, retorna apenas o título centralizado
    if not logo_url:
        title_style.alignment = TA_CENTER
        return Paragraph(titulo, title_style)
    
    try:
        # Baixar imagem do Cloudinary
        response = requests.get(logo_url, timeout=5)
        if response.status_code != 200:
            title_style.alignment = TA_CENTER
            return Paragraph(titulo, title_style)
        
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
        
        # Criar tabela com logo à esquerda e título à direita
        titulo_paragraph = Paragraph(titulo, title_style)
        
        # Tabela: [Logo | Título]
        table_data = [[img, titulo_paragraph]]
        table = Table(table_data, colWidths=[width + 0.5*cm, None])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical ao meio
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),       # Logo à esquerda
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),       # Título à esquerda
            ('LEFTPADDING', (0, 0), (-1, -1), 0),    # Sem padding esquerdo
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),   # Sem padding direito
            ('TOPPADDING', (0, 0), (-1, -1), 0),     # Sem padding superior
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Sem padding inferior
        ]))
        
        return table
        
    except Exception as e:
        # Se falhar ao carregar logo, retorna apenas título centralizado
        print(f"⚠️ Erro ao adicionar logo no PDF: {e}")
        title_style.alignment = TA_CENTER
        return Paragraph(titulo, title_style)


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


def _formatar_nome_usuario(user):
    """Tenta montar um nome legível para o usuário (vendedor)."""
    if not user:
        return '—'
    first_name = getattr(user, 'first_name', '') or ''
    last_name = getattr(user, 'last_name', '') or ''
    full = f'{first_name} {last_name}'.strip()
    return full or getattr(user, 'nome', '') or getattr(user, 'username', '') or '—'


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
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*cm, bottomMargin=1*cm, leftMargin=2*cm, rightMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
        alignment=0,  # 0 = LEFT (alinhado à esquerda)
    )

    # ✅ NOVO: Criar cabeçalho com logo à esquerda e título à direita
    loja_id = getattr(proposta, 'loja_id', None)
    logo_url = None
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data:
            logo_url = loja_data.get('logo')
    
    cabecalho = _criar_cabecalho_com_logo(logo_url, 'PROPOSTA COMERCIAL')
    elements.append(cabecalho)
    elements.append(Spacer(1, 0.01*cm))  # ✅ MÍNIMO (subir Título)
    
    elements.append(Paragraph(f'<b>Título:</b> {proposta.titulo or "—"}', styles['Normal']))
    # Sem Spacer - colar direto

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
            # Sem Spacer - colar direto

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
        # Sem Spacer - colar direto

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
    
    # Desconto (se houver)
    desconto_valor = getattr(proposta, 'desconto_valor', None) or 0
    if desconto_valor and float(desconto_valor) > 0:
        desconto_tipo = getattr(proposta, 'desconto_tipo', 'percentual')
        if desconto_tipo == 'percentual':
            elements.append(Paragraph(f'<b>Desconto:</b> {desconto_valor}%', styles['Normal']))
        else:
            elements.append(Paragraph(f'<b>Desconto:</b> {_formatar_valor(desconto_valor)}', styles['Normal']))
        valor_final = getattr(proposta, 'valor_com_desconto', proposta.valor_total)
        elements.append(Paragraph(f'<b>Valor com desconto:</b> {_formatar_valor(valor_final)}', styles['Normal']))
    
    elements.append(Spacer(1, 0.05*cm))  # ✅ SUPER REDUZIDO

    # Conteúdo
    conteudo = _strip_html(proposta.conteudo) if proposta.conteudo else 'Conteúdo não informado.'
    elements.append(Paragraph('<b>Conteúdo</b>', section_style))
    elements.append(Paragraph(conteudo[:3000] + ('...' if len(conteudo) > 3000 else ''), styles['Normal']))
    # Sem Spacer - colar direto

    # Assinaturas (campos tradicionais + digitais integrados)
    nome_vendedor = getattr(proposta, 'nome_vendedor_assinatura', None) or ''
    nome_cliente = getattr(proposta, 'nome_cliente_assinatura', None) or ''
    lead_email = getattr(lead, 'email', '') or '' if lead else ''
    vendedor = proposta.oportunidade.vendedor if proposta.oportunidade and getattr(proposta.oportunidade, 'vendedor', None) else None
    vendedor_email = getattr(vendedor, 'email', '') or '' if vendedor else ''
    
    elements.append(Paragraph('<b>Assinaturas</b>', section_style))
    # Sem Spacer - colar direto
    
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
    # Formato desejado: "Vendedor: NOME" e "Cliente: NOME" na mesma linha.
    vendedor_nome_fmt = (nome_vendedor or _formatar_nome_usuario(vendedor)).strip() or '—'
    cliente_nome_fmt = (nome_cliente or getattr(lead, 'nome', '') or '—').strip() or '—'

    vendedor_info = [f"Vendedor: {vendedor_nome_fmt}"]
    if vendedor_email:
        vendedor_info.append(f"<font size='8'>Email: {vendedor_email}</font>")

    cliente_info = [f"Cliente: {cliente_nome_fmt}"]
    if lead_email:
        cliente_info.append(f"<font size='8'>Email: {lead_email}</font>")
    
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
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 3),  # Reduzido de 5 para 3
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),  # Reduzido de 3 para 2
    ]))
    elements.append(assinatura_table)
    elements.append(Spacer(1, 0.5*cm))

    # Mensagem de validade jurídica
    validade_style = ParagraphStyle(
        'ValidadeJuridica',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceBefore=6,
        spaceAfter=0,
    )
    elements.append(Paragraph(
        'Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, '
        'com registro de data, hora e endereço IP.',
        validade_style,
    ))

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
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*cm, bottomMargin=1*cm, leftMargin=2*cm, rightMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
    )

    # ✅ NOVO: Criar cabeçalho com logo à esquerda e título à direita
    loja_id = getattr(contrato, 'loja_id', None)
    logo_url = None
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data:
            logo_url = loja_data.get('logo')
    
    cabecalho = _criar_cabecalho_com_logo(logo_url, 'CONTRATO')
    elements.append(cabecalho)
    elements.append(Spacer(1, 0.01*cm))  # ✅ MÍNIMO (subir Título)

    elements.append(Paragraph(f'<b>Número:</b> {contrato.numero or "—"}', styles['Normal']))
    elements.append(Paragraph(f'<b>Título:</b> {contrato.titulo or "—"}', styles['Normal']))
    valor_str = _formatar_valor(contrato.valor_total)
    elements.append(Paragraph(f'<b>Valor total:</b> {valor_str}', styles['Normal']))
    
    # Desconto (se houver)
    desconto_valor = getattr(contrato, 'desconto_valor', None) or 0
    if desconto_valor and float(desconto_valor) > 0:
        desconto_tipo = getattr(contrato, 'desconto_tipo', 'percentual')
        if desconto_tipo == 'percentual':
            elements.append(Paragraph(f'<b>Desconto:</b> {desconto_valor}%', styles['Normal']))
        else:
            elements.append(Paragraph(f'<b>Desconto:</b> {_formatar_valor(desconto_valor)}', styles['Normal']))
        valor_final = getattr(contrato, 'valor_com_desconto', contrato.valor_total)
        elements.append(Paragraph(f'<b>Valor com desconto:</b> {_formatar_valor(valor_final)}', styles['Normal']))
    
    elements.append(Spacer(1, 0.03*cm))  # ✅ SUPER REDUZIDO

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
            # Sem Spacer - colar direto

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
        # Sem Spacer - colar direto

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
        elements.append(Spacer(1, 0.05*cm))  # ✅ SUPER REDUZIDO

    # Conteúdo
    conteudo = _strip_html(contrato.conteudo) if contrato.conteudo else 'Conteúdo não informado.'
    elements.append(Paragraph('<b>Conteúdo</b>', section_style))
    elements.append(Paragraph(conteudo[:3000] + ('...' if len(conteudo) > 3000 else ''), styles['Normal']))
    # Sem Spacer - colar direto

    # Assinaturas (campos tradicionais + digitais integrados)
    nome_vendedor = getattr(contrato, 'nome_vendedor_assinatura', None) or ''
    nome_cliente = getattr(contrato, 'nome_cliente_assinatura', None) or ''
    lead_email = getattr(lead, 'email', '') or '' if lead else ''
    vendedor = contrato.oportunidade.vendedor if contrato.oportunidade and getattr(contrato.oportunidade, 'vendedor', None) else None
    vendedor_email = getattr(vendedor, 'email', '') or '' if vendedor else ''
    
    elements.append(Paragraph('<b>Assinaturas</b>', section_style))
    # Sem Spacer - colar direto
    
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
    # Formato desejado: "Vendedor: NOME" e "Cliente: NOME" na mesma linha.
    vendedor_nome_fmt = (nome_vendedor or _formatar_nome_usuario(vendedor)).strip() or '—'
    cliente_nome_fmt = (nome_cliente or getattr(lead, 'nome', '') or '—').strip() or '—'

    vendedor_info = [f"Vendedor: {vendedor_nome_fmt}"]
    if vendedor_email:
        vendedor_info.append(f"<font size='8'>Email: {vendedor_email}</font>")

    cliente_info = [f"Cliente: {cliente_nome_fmt}"]
    if lead_email:
        cliente_info.append(f"<font size='8'>Email: {lead_email}</font>")
    
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
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 3),  # Reduzido de 5 para 3
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),  # Reduzido de 3 para 2
    ]))
    elements.append(assinatura_table)
    elements.append(Spacer(1, 0.5*cm))

    # Mensagem de validade jurídica
    validade_style = ParagraphStyle(
        'ValidadeJuridicaContrato',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceBefore=6,
        spaceAfter=0,
    )
    elements.append(Paragraph(
        'Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, '
        'com registro de data, hora e endereço IP.',
        validade_style,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
