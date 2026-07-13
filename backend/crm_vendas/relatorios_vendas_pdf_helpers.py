"""Helpers de agregação e layout para relatórios PDF de vendas (Fase 31)."""
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from .relatorios_pdf_common import _nome_cliente_venda
from .utils import get_vendedor_destino_merge_loja


def merge_detalhamento_vendedores_pdf(loja_id: int, vendedores_stats_raw: list) -> list:
    """Junta linhas sem vendedor ou com vendedor inativo na linha do destino de mesclagem
    (is_admin, ou mesmo e-mail do dono da loja, ou primeiro vendedor ativo) — igual ao dashboard.
    """
    destino = get_vendedor_destino_merge_loja(loja_id)
    if not destino:
        return vendedores_stats_raw

    extras = {"total": 0.0, "comissao": 0.0, "qtd": 0}
    restantes = []
    admin_row = None

    for row in vendedores_stats_raw:
        vid = row.get("vendedor_id")
        inactive = row.get("vendedor__is_active") is False
        if vid is None or inactive:
            extras["total"] += float(row["total"] or 0)
            extras["comissao"] += float(row["comissao"] or 0)
            extras["qtd"] += row["qtd"] or 0
            continue
        if vid == destino.id:
            admin_row = dict(row)
        else:
            restantes.append(row)

    if admin_row is None and (extras["qtd"] > 0 or extras["total"] > 0):
        admin_row = {
            "vendedor_id": destino.id,
            "vendedor__nome": destino.nome,
            "vendedor__is_active": True,
            "total": 0.0,
            "comissao": 0.0,
            "qtd": 0,
        }

    if admin_row is not None:
        admin_row["total"] = float(admin_row.get("total") or 0) + extras["total"]
        admin_row["comissao"] = float(admin_row.get("comissao") or 0) + extras["comissao"]
        admin_row["qtd"] = (admin_row.get("qtd") or 0) + extras["qtd"]
        restantes.append(admin_row)
    elif extras["qtd"] > 0:
        restantes.append(
            {
                "vendedor_id": None,
                "vendedor__nome": "Sem vendedor",
                "vendedor__is_active": None,
                "total": extras["total"],
                "comissao": extras["comissao"],
                "qtd": extras["qtd"],
            },
        )

    restantes.sort(key=lambda x: -float(x.get("total") or 0))
    return restantes


def filtro_detalhe_linha_merged_pdf(row: dict, merge_destino):
    """Oportunidades que compõem a linha do detalhamento (após merge no destino da loja)."""
    vid = row.get("vendedor_id")
    if merge_destino and vid == merge_destino.id:
        return (
            Q(vendedor_id=merge_destino.id)
            | Q(vendedor_id__isnull=True)
            | Q(vendedor__is_active=False)
        )
    if vid is None:
        return Q(vendedor_id__isnull=True) | Q(vendedor__is_active=False)
    return Q(vendedor_id=vid)


def adicionar_secao_vendedor_pdf(elements, styles, vendedor_nome: str, oportunidades_qs):
    """Resumo + tabela ordenada por data (mais recente primeiro)."""
    oportunidades_qs = oportunidades_qs.annotate(
        data_ordem=Coalesce("data_fechamento_ganho", "data_fechamento"),
    ).order_by("-data_ordem", "-id")

    totais = oportunidades_qs.aggregate(
        total=Sum("valor"),
        comissao=Sum("valor_comissao"),
        qtd=Count("id"),
    )
    total = float(totais["total"] or 0)
    comissao = float(totais["comissao"] or 0)
    qtd = totais["qtd"] or 0

    elements.append(Paragraph(f"<b>{vendedor_nome}</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * cm))

    data_resumo = [
        ["Métrica", "Valor"],
        ["Quantidade de Vendas", str(qtd)],
        ["Total de Vendas", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")],
        ["Total de Comissões", f"R$ {comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")],
    ]

    table_resumo = Table(data_resumo, colWidths=[8 * cm, 8 * cm])
    table_resumo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0176d3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ],
        ),
    )

    elements.append(table_resumo)
    elements.append(Spacer(1, 0.5 * cm))

    if not oportunidades_qs.exists():
        elements.append(Spacer(1, 0.3 * cm))
        return

    data_vendas = [["Data", "Cliente", "Valor", "Comissão"]]
    for venda in oportunidades_qs:
        data_venda = venda.data_fechamento_ganho or venda.data_fechamento
        data_str = data_venda.strftime("%d/%m/%Y") if data_venda else "-"
        cliente = _nome_cliente_venda(venda)
        valor = float(venda.valor or 0)
        comissao_venda = float(venda.valor_comissao or 0)

        data_vendas.append(
            [
                data_str,
                (cliente or "")[:30],
                f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                f"R$ {comissao_venda:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            ],
        )

    table_vendas = Table(data_vendas, colWidths=[3 * cm, 6 * cm, 3.5 * cm, 3.5 * cm])
    table_vendas.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ],
        ),
    )

    elements.append(table_vendas)
    elements.append(Spacer(1, 1 * cm))
