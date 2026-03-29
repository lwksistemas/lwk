"""
Serviço de geração de relatórios de vendas em PDF.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
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
from .utils import get_vendedor_destino_merge_loja

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


def _filtro_datas_fechamento_ganho(data_inicio, data_fim):
    """Mesmo critério do dashboard e de gerar_relatorio_vendas_* (DateField)."""
    return (
        Q(data_fechamento_ganho__gte=data_inicio, data_fechamento_ganho__lte=data_fim)
        | (
            Q(data_fechamento_ganho__isnull=True)
            & Q(data_fechamento__gte=data_inicio, data_fechamento__lte=data_fim)
        )
    )


def _merge_detalhamento_vendedores_pdf(loja_id: int, vendedores_stats_raw: list) -> list:
    """
    Junta linhas sem vendedor ou com vendedor inativo na linha do destino de mesclagem
    (is_admin, ou mesmo e-mail do dono da loja, ou primeiro vendedor ativo) — igual ao dashboard.
    """
    destino = get_vendedor_destino_merge_loja(loja_id)
    if not destino:
        return vendedores_stats_raw

    extras = {'total': 0.0, 'comissao': 0.0, 'qtd': 0}
    restantes = []
    admin_row = None

    for row in vendedores_stats_raw:
        vid = row.get('vendedor_id')
        inactive = row.get('vendedor__is_active') is False
        if vid is None or inactive:
            extras['total'] += float(row['total'] or 0)
            extras['comissao'] += float(row['comissao'] or 0)
            extras['qtd'] += row['qtd'] or 0
            continue
        if vid == destino.id:
            admin_row = dict(row)
        else:
            restantes.append(row)

    if admin_row is None and (extras['qtd'] > 0 or extras['total'] > 0):
        admin_row = {
            'vendedor_id': destino.id,
            'vendedor__nome': destino.nome,
            'vendedor__is_active': True,
            'total': 0.0,
            'comissao': 0.0,
            'qtd': 0,
        }

    if admin_row is not None:
        admin_row['total'] = float(admin_row.get('total') or 0) + extras['total']
        admin_row['comissao'] = float(admin_row.get('comissao') or 0) + extras['comissao']
        admin_row['qtd'] = (admin_row.get('qtd') or 0) + extras['qtd']
        restantes.append(admin_row)
    elif extras['qtd'] > 0:
        restantes.append(
            {
                'vendedor_id': None,
                'vendedor__nome': 'Sem vendedor',
                'vendedor__is_active': None,
                'total': extras['total'],
                'comissao': extras['comissao'],
                'qtd': extras['qtd'],
            }
        )

    restantes.sort(key=lambda x: -float(x.get('total') or 0))
    return restantes


def _filtro_detalhe_linha_merged_pdf(row: dict, merge_destino):
    """Oportunidades que compõem a linha do detalhamento (após merge no destino da loja)."""
    vid = row.get('vendedor_id')
    if merge_destino and vid == merge_destino.id:
        return (
            Q(vendedor_id=merge_destino.id)
            | Q(vendedor_id__isnull=True)
            | Q(vendedor__is_active=False)
        )
    if vid is None:
        return Q(vendedor_id__isnull=True) | Q(vendedor__is_active=False)
    return Q(vendedor_id=vid)


def _adicionar_secao_vendedor_pdf(elements, styles, vendedor_nome: str, oportunidades_qs):
    """Resumo + tabela ordenada por data (mais recente primeiro)."""
    oportunidades_qs = oportunidades_qs.annotate(
        data_ordem=Coalesce('data_fechamento_ganho', 'data_fechamento')
    ).order_by('-data_ordem', '-id')

    totais = oportunidades_qs.aggregate(
        total=Sum('valor'),
        comissao=Sum('valor_comissao'),
        qtd=Count('id'),
    )
    total = float(totais['total'] or 0)
    comissao = float(totais['comissao'] or 0)
    qtd = totais['qtd'] or 0

    elements.append(Paragraph(f'<b>{vendedor_nome}</b>', styles['Heading2']))
    elements.append(Spacer(1, 0.2 * cm))

    data_resumo = [
        ['Métrica', 'Valor'],
        ['Quantidade de Vendas', str(qtd)],
        ['Total de Vendas', f'R$ {total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Total de Comissões', f'R$ {comissao:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
    ]

    table_resumo = Table(data_resumo, colWidths=[8 * cm, 8 * cm])
    table_resumo.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0176d3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table_resumo)
    elements.append(Spacer(1, 0.5 * cm))

    if not oportunidades_qs.exists():
        elements.append(Spacer(1, 0.3 * cm))
        return

    data_vendas = [['Data', 'Cliente', 'Valor', 'Comissão']]
    for venda in oportunidades_qs:
        data_venda = venda.data_fechamento_ganho or venda.data_fechamento
        data_str = data_venda.strftime('%d/%m/%Y') if data_venda else '-'
        cliente = venda.lead.nome if venda.lead else venda.titulo
        valor = float(venda.valor or 0)
        comissao_venda = float(venda.valor_comissao or 0)

        data_vendas.append(
            [
                data_str,
                (cliente or '')[:30],
                f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                f'R$ {comissao_venda:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
            ]
        )

    table_vendas = Table(data_vendas, colWidths=[3 * cm, 6 * cm, 3.5 * cm, 3.5 * cm])
    table_vendas.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )

    elements.append(table_vendas)
    elements.append(Spacer(1, 1 * cm))


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
    ).filter(_filtro_datas_fechamento_ganho(data_inicio, data_fim)).select_related('vendedor', 'lead')
    
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
    
    # Detalhamento por vendedor (sem vendedor / inativo somados no administrador — igual ao dashboard)
    vendedores_stats_raw = list(
        oportunidades.values('vendedor_id', 'vendedor__nome', 'vendedor__is_active').annotate(
            total=Sum('valor'),
            comissao=Sum('valor_comissao'),
            qtd=Count('id'),
        )
    )
    vendedores_stats = _merge_detalhamento_vendedores_pdf(loja_id, vendedores_stats_raw)

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
    Para o vendedor destino da mesclagem (admin / e-mail do dono / primeiro ativo), inclui também
    vendas sem vendedor ou com vendedor inativo — igual ao dashboard CRM.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()

    data_inicio, data_fim = calcular_periodo(periodo)
    merge_destino = get_vendedor_destino_merge_loja(loja_id)

    base = (
        Oportunidade.objects.filter(loja_id=loja_id, etapa='closed_won')
        .filter(_filtro_datas_fechamento_ganho(data_inicio, data_fim))
        .select_related('vendedor', 'lead')
    )

    titulo = 'Relatório de Vendas por Vendedor'
    is_todos = vendedor_id is None or str(vendedor_id).lower() == 'todos'

    logo_url = _obter_logo_loja(loja_id)

    if not is_todos:
        try:
            vid = int(vendedor_id)
        except (TypeError, ValueError):
            vid = None
        v_sel = None
        if vid is not None:
            try:
                v_sel = Vendedor.objects.get(id=vid, loja_id=loja_id)
                titulo += f' - {v_sel.nome}'
            except Vendedor.DoesNotExist:
                v_sel = None

        cabecalho = _criar_cabecalho_relatorio(logo_url, titulo)
        elements.append(cabecalho)
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(
            Paragraph(
                f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
                styles['Normal'],
            )
        )
        elements.append(Spacer(1, 0.5 * cm))

        if not v_sel:
            elements.append(Paragraph('Vendedor não encontrado.', styles['Normal']))
        elif merge_destino and v_sel.id == merge_destino.id:
            qs = base.filter(
                Q(vendedor_id=v_sel.id)
                | Q(vendedor_id__isnull=True)
                | Q(vendedor__is_active=False)
            )
            _adicionar_secao_vendedor_pdf(elements, styles, v_sel.nome, qs)
        else:
            _adicionar_secao_vendedor_pdf(
                elements, styles, v_sel.nome, base.filter(vendedor_id=v_sel.id)
            )
    else:
        titulo += ' - Todos os vendedores'
        cabecalho = _criar_cabecalho_relatorio(logo_url, titulo)
        elements.append(cabecalho)
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(
            Paragraph(
                f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
                styles['Normal'],
            )
        )
        elements.append(Spacer(1, 0.5 * cm))

        vendedores_stats_raw = list(
            base.values('vendedor_id', 'vendedor__nome', 'vendedor__is_active').annotate(
                total=Sum('valor'),
                comissao=Sum('valor_comissao'),
                qtd=Count('id'),
            )
        )
        vendedores_stats = _merge_detalhamento_vendedores_pdf(loja_id, vendedores_stats_raw)

        if not vendedores_stats:
            elements.append(Paragraph('Nenhuma venda encontrada no período selecionado.', styles['Normal']))
        else:
            for row in vendedores_stats:
                nome = row.get('vendedor__nome') or 'Sem vendedor'
                secao_qs = base.filter(_filtro_detalhe_linha_merged_pdf(row, merge_destino))
                _adicionar_secao_vendedor_pdf(elements, styles, nome, secao_qs)

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(
        Paragraph(
            f'Relatório gerado em {timezone.now().strftime("%d/%m/%Y às %H:%M")}',
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey),
        )
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer
