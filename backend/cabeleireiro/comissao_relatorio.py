"""Relatório de comissões do salão (por profissional)."""
from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from .models import Payment


def calcular_comissoes_salao(
    data_inicio: date,
    data_fim: date,
    *,
    profissional_id: int | None = None,
) -> dict:
    qs = (
        Payment.objects.filter(
            status=Payment.STATUS_PAID,
            payment_date__date__gte=data_inicio,
            payment_date__date__lte=data_fim,
        )
        .select_related(
            "agendamento",
            "agendamento__cliente",
            "agendamento__profissional",
            "agendamento__servico",
        )
        .order_by("agendamento__profissional__nome", "payment_date")
    )
    if profissional_id:
        qs = qs.filter(agendamento__profissional_id=profissional_id)

    por_prof: dict[int, dict] = {}
    for p in qs:
        ag = p.agendamento
        pid = ag.profissional_id or 0
        nome = ag.profissional.nome if ag.profissional_id else "Sem profissional"
        entry = por_prof.setdefault(
            pid,
            {
                "profissional_id": pid or None,
                "nome": nome,
                "qtd": 0,
                "valor_total": Decimal("0"),
                "comissao_total": Decimal("0"),
                "itens": [],
            },
        )
        entry["qtd"] += 1
        entry["valor_total"] += Decimal(str(p.amount or 0))
        entry["comissao_total"] += Decimal(str(p.comissao_valor or 0))
        entry["itens"].append(
            {
                "payment_id": p.id,
                "data": p.payment_date.date().isoformat() if p.payment_date else ag.data.isoformat(),
                "cliente": ag.cliente.nome if ag.cliente_id else "",
                "servico": ag.servico.nome if ag.servico_id else "",
                "valor": float(p.amount or 0),
                "comissao": float(p.comissao_valor or 0),
                "comissao_percentual": float(p.comissao_percentual or 0),
                "modo": "percentual" if float(p.comissao_percentual or 0) > 0 else "fixo",
            },
        )

    profissionais = sorted(por_prof.values(), key=lambda x: x["nome"].lower())
    for e in profissionais:
        e["valor_total"] = float(e["valor_total"])
        e["comissao_total"] = float(e["comissao_total"])

    tot_valor = sum(p["valor_total"] for p in profissionais)
    tot_comissao = sum(p["comissao_total"] for p in profissionais)
    return {
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "profissionais": profissionais,
        "totais": {
            "qtd": sum(p["qtd"] for p in profissionais),
            "valor_total": tot_valor,
            "comissao_total": tot_comissao,
        },
    }


def gerar_pdf_comissoes_salao(resultado: dict, data_inicio: date, data_fim: date) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    s_title = ParagraphStyle("t", fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=8)
    s_sub = ParagraphStyle("s", fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#555555"))
    s_prof = ParagraphStyle("p", fontSize=11, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)
    s_cell = ParagraphStyle("c", fontSize=8, alignment=TA_LEFT)
    s_right = ParagraphStyle("r", fontSize=8, alignment=TA_RIGHT)

    story = [
        Paragraph("Relatório de Comissões — Salão", s_title),
        Paragraph(
            f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
            s_sub,
        ),
        Spacer(1, 12),
    ]

    for prof in resultado.get("profissionais") or []:
        story.append(
            Paragraph(
                f'{prof["nome"]} — {prof["qtd"]} atend. | '
                f'Faturado R$ {prof["valor_total"]:.2f} | '
                f'Comissão R$ {prof["comissao_total"]:.2f}',
                s_prof,
            ),
        )
        rows = [[
            Paragraph("<b>Data</b>", s_cell),
            Paragraph("<b>Cliente</b>", s_cell),
            Paragraph("<b>Serviço</b>", s_cell),
            Paragraph("<b>Valor</b>", s_right),
            Paragraph("<b>Comissão</b>", s_right),
        ]]
        for it in prof.get("itens") or []:
            rows.append([
                Paragraph(it.get("data", ""), s_cell),
                Paragraph(it.get("cliente", ""), s_cell),
                Paragraph(it.get("servico", ""), s_cell),
                Paragraph(f'R$ {it.get("valor", 0):.2f}', s_right),
                Paragraph(f'R$ {it.get("comissao", 0):.2f}', s_right),
            ])
        table = Table(rows, colWidths=[70, 130, 140, 70, 70])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7F0F3")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(table)

    totais = resultado.get("totais") or {}
    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            f'<b>TOTAL</b> — {totais.get("qtd", 0)} atend. | '
            f'Faturado R$ {float(totais.get("valor_total") or 0):.2f} | '
            f'Comissões R$ {float(totais.get("comissao_total") or 0):.2f}',
            s_prof,
        ),
    )
    doc.build(story)
    return buf.getvalue()
