"""
Serviço de geração de relatórios de vendas em PDF.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
import logging
import requests
from PIL import Image as PILImage

from .models import Oportunidade, Vendedor

logger = logging.getLogger(__name__)


def _obter_logo_loja(loja_id):
    """Obtém URL do logo da loja."""
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja:
            return getattr(loja, 'logo', '') or None
    except Exception:
        return None
    return None


def _criar_cabecalho_relatorio(logo_url, titulo, max_width=6*cm, max_height=3*cm):
    """
    Cria cabeçalho com logo à esquerda e título à direita na mesma linha.
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0176d3'),
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
        leading=22,
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
            width = min(max_width, img_width)
            height = width * aspect
            if height > max_height:
                height = max_height
                width = height / aspect
        else:
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
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        return table
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao adicionar logo no relatório: {e}")
        title_style.alignment = TA_CENTER
        return Paragraph(titulo, title_style)


def calcular_periodo(periodo_tipo: str):
    """
    Calcula data_inicio e data_fim baseado no tipo de período.
    """
    hoje = timezone.now().date()
    
    if periodo_tipo == 'hoje':
        return hoje, hoje
    elif periodo_tipo == 'ontem':
        ontem = hoje - timedelta(days=1)
        return ontem, ontem
    elif periodo_tipo == 'semana_atual':
        inicio = hoje - timedelta(days=hoje.weekday())
        return inicio, hoje
    elif periodo_tipo == 'semana_passada':
        fim = hoje - timedelta(days=hoje.weekday() + 1)
        inicio = fim - timedelta(days=6)
        return inicio, fim
    elif periodo_tipo == 'mes_atual':
        inicio = hoje.replace(day=1)
        return inicio, hoje
    elif periodo_tipo == 'mes_passado':
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)
        primeiro_dia_mes_passado = ultimo_dia_mes_passado.replace(day=1)
        return primeiro_dia_mes_passado, ultimo_dia_mes_passado
    elif periodo_tipo == 'trimestre_atual':
        mes_atual = hoje.month
        mes_inicio_trimestre = ((mes_atual - 1) // 3) * 3 + 1
        inicio = hoje.replace(month=mes_inicio_trimestre, day=1)
        return inicio, hoje
    elif periodo_tipo == 'ano_atual':
        inicio = hoje.replace(month=1, day=1)
        return inicio, hoje
    else:
        # Padrão: mês atual
        inicio = hoje.replace(day=1)
        return inicio, hoje


def gerar_relatorio_vendas_total(loja_id: int, periodo: str) -> BytesIO:
    """
    Gera relatório PDF com total de vendas de todos os vendedores.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    data_inicio, data_fim = calcular_periodo(periodo)
    
    # ✅ NOVO: Adicionar logo no cabeçalho
    logo_url = _obter_logo_loja(loja_id)
    cabecalho = _criar_cabecalho_relatorio(logo_url, 'Relatório de Vendas - Total Geral')
    elements.append(cabecalho)
    elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph(
        f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Buscar oportunidades fechadas ganhas no período
    # Nota: data_fechamento_ganho e data_fechamento são DateField, não DateTimeField - comparar direto
    oportunidades = Oportunidade.objects.filter(
        loja_id=loja_id,
        etapa='closed_won',
    ).filter(
        Q(data_fechamento_ganho__gte=data_inicio, data_fechamento_ganho__lte=data_fim) |
        (Q(data_fechamento_ganho__isnull=True) & Q(data_fechamento__gte=data_inicio, data_fechamento__lte=data_fim))
    ).select_related('vendedor', 'lead')
    
    # Calcular totais
    totais = oportunidades.aggregate(
        total_vendas=Sum('valor'),
        total_comissoes=Sum('valor_comissao'),
        quantidade=Count('id')
    )
    
    total_vendas = float(totais['total_vendas'] or 0)
    total_comissoes = float(totais['total_comissoes'] or 0)
    quantidade = totais['quantidade'] or 0
    
    # Resumo
    data_resumo = [
        ['Métrica', 'Valor'],
        ['Quantidade de Vendas', str(quantidade)],
        ['Total de Vendas', f'R$ {total_vendas:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Total de Comissões', f'R$ {total_comissoes:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
    ]
    
    table_resumo = Table(data_resumo, colWidths=[8*cm, 8*cm])
    table_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0176d3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table_resumo)
    elements.append(Spacer(1, 1*cm))
    
    # Detalhamento por vendedor
    vendedores_stats = oportunidades.values('vendedor__nome').annotate(
        total=Sum('valor'),
        comissao=Sum('valor_comissao'),
        qtd=Count('id')
    ).order_by('-total')
    
    if vendedores_stats:
        elements.append(Paragraph('Detalhamento por Vendedor', styles['Heading2']))
        elements.append(Spacer(1, 0.3*cm))
        
        data_vendedores = [['Vendedor', 'Qtd', 'Total Vendas', 'Comissões']]
        for v in vendedores_stats:
            nome = v['vendedor__nome'] or 'Sem vendedor'
            qtd = v['qtd']
            total = float(v['total'] or 0)
            comissao = float(v['comissao'] or 0)
            data_vendedores.append([
                nome,
                str(qtd),
                f'R$ {total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                f'R$ {comissao:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
            ])
        
        table_vendedores = Table(data_vendedores, colWidths=[6*cm, 2*cm, 4*cm, 4*cm])
        table_vendedores.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0176d3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table_vendedores)
    
    # Rodapé
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f'Relatório gerado em {timezone.now().strftime("%d/%m/%Y às %H:%M")}',
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_relatorio_vendas_vendedor(loja_id: int, periodo: str, vendedor_id: int = None) -> BytesIO:
    """
    Gera relatório PDF com vendas por vendedor específico ou todos.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    data_inicio, data_fim = calcular_periodo(periodo)
    
    # Título
    titulo = 'Relatório de Vendas por Vendedor'
    if vendedor_id and vendedor_id != 'todos':
        try:
            vendedor = Vendedor.objects.get(id=vendedor_id, loja_id=loja_id)
            titulo += f' - {vendedor.nome}'
        except Vendedor.DoesNotExist:
            pass
    
    # ✅ NOVO: Adicionar logo no cabeçalho
    logo_url = _obter_logo_loja(loja_id)
    cabecalho = _criar_cabecalho_relatorio(logo_url, titulo)
    elements.append(cabecalho)
    elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph(
        f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Filtrar oportunidades (DateField - comparar direto, sem __date__)
    oportunidades_qs = Oportunidade.objects.filter(
        loja_id=loja_id,
        etapa='closed_won',
    ).filter(
        Q(data_fechamento_ganho__gte=data_inicio, data_fechamento_ganho__lte=data_fim) |
        (Q(data_fechamento_ganho__isnull=True) & Q(data_fechamento__gte=data_inicio, data_fechamento__lte=data_fim))
    )
    
    if vendedor_id and vendedor_id != 'todos':
        oportunidades_qs = oportunidades_qs.filter(vendedor_id=vendedor_id)
    
    oportunidades_qs = oportunidades_qs.select_related('vendedor', 'lead')
    
    # Agrupar por vendedor
    vendedores_stats = oportunidades_qs.values('vendedor_id', 'vendedor__nome').annotate(
        total=Sum('valor'),
        comissao=Sum('valor_comissao'),
        qtd=Count('id')
    ).order_by('-total')
    
    for v_stat in vendedores_stats:
        vendedor_nome = v_stat['vendedor__nome'] or 'Sem vendedor'
        total = float(v_stat['total'] or 0)
        comissao = float(v_stat['comissao'] or 0)
        qtd = v_stat['qtd']
        
        elements.append(Paragraph(f'<b>{vendedor_nome}</b>', styles['Heading2']))
        elements.append(Spacer(1, 0.2*cm))
        
        # Resumo do vendedor
        data_resumo = [
            ['Métrica', 'Valor'],
            ['Quantidade de Vendas', str(qtd)],
            ['Total de Vendas', f'R$ {total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['Total de Comissões', f'R$ {comissao:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
        ]
        
        table_resumo = Table(data_resumo, colWidths=[8*cm, 8*cm])
        table_resumo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0176d3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table_resumo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Detalhamento de vendas
        vendas = oportunidades_qs.filter(vendedor_id=v_stat['vendedor_id'])
        if vendas.exists():
            data_vendas = [['Data', 'Cliente', 'Valor', 'Comissão']]
            for venda in vendas[:20]:  # Limitar a 20 vendas por vendedor
                data_venda = venda.data_fechamento_ganho or venda.data_fechamento
                data_str = data_venda.strftime('%d/%m/%Y') if data_venda else '-'
                cliente = venda.lead.nome if venda.lead else venda.titulo
                valor = float(venda.valor or 0)
                comissao_venda = float(venda.valor_comissao or 0)
                
                data_vendas.append([
                    data_str,
                    cliente[:30],
                    f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                    f'R$ {comissao_venda:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                ])
            
            table_vendas = Table(data_vendas, colWidths=[3*cm, 6*cm, 3.5*cm, 3.5*cm])
            table_vendas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            elements.append(table_vendas)
        
        elements.append(Spacer(1, 1*cm))
    
    if not vendedores_stats:
        elements.append(Paragraph('Nenhuma venda encontrada no período selecionado.', styles['Normal']))
    
    # Rodapé
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(
        f'Relatório gerado em {timezone.now().strftime("%d/%m/%Y às %H:%M")}',
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
