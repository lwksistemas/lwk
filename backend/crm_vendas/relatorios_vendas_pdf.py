"""Geração de relatórios PDF de vendas (total e por vendedor).
"""
from io import BytesIO

from django.db.models import Count, Q, Sum
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Oportunidade, Vendedor
from .periodo import calcular_intervalo_datas as calcular_periodo
from .periodo import filtro_fechamento_no_periodo as _filtro_datas_fechamento_ganho
from .relatorios_pdf_common import (
    _criar_cabecalho_relatorio,
    _obter_logo_loja,
)
from .relatorios_vendas_pdf_helpers import (
    adicionar_secao_vendedor_pdf as _adicionar_secao_vendedor_pdf,
)
from .relatorios_vendas_pdf_helpers import (
    filtro_detalhe_linha_merged_pdf as _filtro_detalhe_linha_merged_pdf,
)
from .relatorios_vendas_pdf_helpers import (
    merge_detalhamento_vendedores_pdf as _merge_detalhamento_vendedores_pdf,
)
from .utils import get_vendedor_destino_merge_loja


def gerar_relatorio_vendas_total(loja_id: int, periodo: str, empresa_prestadora_id: int = None, data_inicio_custom=None, data_fim_custom=None) -> BytesIO:
    """Gera relatório PDF com total de vendas de todos os vendedores.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    data_inicio, data_fim = calcular_periodo(periodo)
    if data_inicio_custom and data_fim_custom:
        from datetime import date as date_type
        try:
            data_inicio = date_type.fromisoformat(str(data_inicio_custom))
            data_fim = date_type.fromisoformat(str(data_fim_custom))
        except Exception:
            pass

    # ✅ NOVO: Adicionar logo no cabeçalho
    logo_url = _obter_logo_loja(loja_id)
    cabecalho = _criar_cabecalho_relatorio(logo_url, "Relatório de Vendas - Total Geral")
    elements.append(cabecalho)
    elements.append(Spacer(1, 0.3*cm))

    elements.append(Paragraph(
        f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
        styles["Normal"],
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Buscar oportunidades fechadas ganhas no período
    oportunidades = Oportunidade.objects.filter(
        loja_id=loja_id,
        etapa="closed_won",
    ).filter(_filtro_datas_fechamento_ganho(data_inicio, data_fim)).select_related("vendedor", "lead", "lead__conta", "empresa_prestadora")

    # Filtro por empresa prestadora (inclui vendas sem empresa prestadora definida)
    if empresa_prestadora_id:
        from .models import Conta
        oportunidades = oportunidades.filter(
            Q(empresa_prestadora_id=empresa_prestadora_id)
            | Q(empresa_prestadora_id__isnull=True),
        )
        try:
            from .models import Conta
            ep = Conta.objects.filter(id=empresa_prestadora_id, loja_id=loja_id).first()
            if ep:
                elements.append(Paragraph(f"Empresa Prestadora: {ep.nome}", styles["Normal"]))
                elements.append(Spacer(1, 0.3*cm))
        except Exception:
            pass

    # Calcular totais
    totais = oportunidades.aggregate(
        total_vendas=Sum("valor"),
        total_comissoes=Sum("valor_comissao"),
        quantidade=Count("id"),
    )

    total_vendas = float(totais["total_vendas"] or 0)
    total_comissoes = float(totais["total_comissoes"] or 0)
    quantidade = totais["quantidade"] or 0

    # Resumo
    data_resumo = [
        ["Métrica", "Valor"],
        ["Quantidade de Vendas", str(quantidade)],
        ["Total de Vendas", f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")],
        ["Total de Comissões", f"R$ {total_comissoes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")],
    ]

    table_resumo = Table(data_resumo, colWidths=[8*cm, 8*cm])
    table_resumo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0176d3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table_resumo)
    elements.append(Spacer(1, 1*cm))

    # Detalhamento por vendedor (sem vendedor / inativo somados no administrador — igual ao dashboard)
    vendedores_stats_raw = list(
        oportunidades.values("vendedor_id", "vendedor__nome", "vendedor__is_active").annotate(
            total=Sum("valor"),
            comissao=Sum("valor_comissao"),
            qtd=Count("id"),
        ),
    )
    vendedores_stats = _merge_detalhamento_vendedores_pdf(loja_id, vendedores_stats_raw)

    if vendedores_stats:
        elements.append(Paragraph("Detalhamento por Vendedor", styles["Heading2"]))
        elements.append(Spacer(1, 0.3*cm))

        data_vendedores = [["Vendedor", "Qtd", "Total Vendas", "Comissões"]]
        for v in vendedores_stats:
            nome = v["vendedor__nome"] or "Sem vendedor"
            qtd = v["qtd"]
            total = float(v["total"] or 0)
            comissao = float(v["comissao"] or 0)
            data_vendedores.append([
                nome,
                str(qtd),
                f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                f"R$ {comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            ])

        table_vendedores = Table(data_vendedores, colWidths=[6*cm, 2*cm, 4*cm, 4*cm])
        table_vendedores.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0176d3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table_vendedores)

    # Rodapé
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f'Relatório gerado em {timezone.now().strftime("%d/%m/%Y às %H:%M")}',
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_relatorio_vendas_vendedor(loja_id: int, periodo: str, vendedor_id: int = None, empresa_prestadora_id: int = None, data_inicio_custom=None, data_fim_custom=None) -> BytesIO:
    """Gera relatório PDF com vendas por vendedor específico ou todos.
    Para o vendedor destino da mesclagem (admin / e-mail do dono / primeiro ativo), inclui também
    vendas sem vendedor ou com vendedor inativo — igual ao dashboard CRM.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()

    data_inicio, data_fim = calcular_periodo(periodo)
    if data_inicio_custom and data_fim_custom:
        from datetime import date as date_type
        try:
            data_inicio = date_type.fromisoformat(str(data_inicio_custom))
            data_fim = date_type.fromisoformat(str(data_fim_custom))
        except Exception:
            pass
    merge_destino = get_vendedor_destino_merge_loja(loja_id)

    base = (
        Oportunidade.objects.filter(loja_id=loja_id, etapa="closed_won")
        .filter(_filtro_datas_fechamento_ganho(data_inicio, data_fim))
        .select_related("vendedor", "lead", "lead__conta", "empresa_prestadora")
    )

    # Filtro por empresa prestadora (inclui vendas sem empresa prestadora definida)
    if empresa_prestadora_id:
        from .models import Conta
        base = base.filter(
            Q(empresa_prestadora_id=empresa_prestadora_id)
            | Q(empresa_prestadora_id__isnull=True),
        )

    titulo = "Relatório de Vendas por Vendedor"
    is_todos = vendedor_id is None or str(vendedor_id).lower() == "todos"

    # Info da empresa prestadora para o título
    _ep_nome = None
    if empresa_prestadora_id:
        try:
            from .models import Conta
            ep = Conta.objects.filter(id=empresa_prestadora_id, loja_id=loja_id).first()
            if ep:
                _ep_nome = ep.nome
        except Exception:
            pass

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
                titulo += f" - {v_sel.nome}"
            except Vendedor.DoesNotExist:
                v_sel = None

        cabecalho = _criar_cabecalho_relatorio(logo_url, titulo)
        elements.append(cabecalho)
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(
            Paragraph(
                f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
                styles["Normal"],
            ),
        )
        elements.append(Spacer(1, 0.5 * cm))

        if not v_sel:
            elements.append(Paragraph("Vendedor não encontrado.", styles["Normal"]))
        elif merge_destino and v_sel.id == merge_destino.id:
            qs = base.filter(
                Q(vendedor_id=v_sel.id)
                | Q(vendedor_id__isnull=True)
                | Q(vendedor__is_active=False),
            )
            _adicionar_secao_vendedor_pdf(elements, styles, v_sel.nome, qs)
        else:
            _adicionar_secao_vendedor_pdf(
                elements, styles, v_sel.nome, base.filter(vendedor_id=v_sel.id),
            )
    else:
        titulo += " - Todos os vendedores"
        cabecalho = _criar_cabecalho_relatorio(logo_url, titulo)
        elements.append(cabecalho)
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(
            Paragraph(
                f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
                styles["Normal"],
            ),
        )
        elements.append(Spacer(1, 0.5 * cm))

        vendedores_stats_raw = list(
            base.values("vendedor_id", "vendedor__nome", "vendedor__is_active").annotate(
                total=Sum("valor"),
                comissao=Sum("valor_comissao"),
                qtd=Count("id"),
            ),
        )
        vendedores_stats = _merge_detalhamento_vendedores_pdf(loja_id, vendedores_stats_raw)

        if not vendedores_stats:
            elements.append(Paragraph("Nenhuma venda encontrada no período selecionado.", styles["Normal"]))
        else:
            for row in vendedores_stats:
                nome = row.get("vendedor__nome") or "Sem vendedor"
                secao_qs = base.filter(_filtro_detalhe_linha_merged_pdf(row, merge_destino))
                _adicionar_secao_vendedor_pdf(elements, styles, nome, secao_qs)

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(
        Paragraph(
            f'Relatório gerado em {timezone.now().strftime("%d/%m/%Y às %H:%M")}',
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
        ),
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer
