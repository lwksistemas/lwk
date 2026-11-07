"""PDF das NFS-e emitidas da loja, por empresa prestadora ou no total."""
from __future__ import annotations

import re
from datetime import datetime, time
from decimal import Decimal
from io import BytesIO
from typing import Any

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .periodo import calcular_intervalo_datas
from .relatorio_comissao_data import nome_da_conta
from .relatorios_pdf_common import _criar_cabecalho_relatorio, _obter_logo_loja


def digitos_documento(valor: Any) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def _brl(valor: Any) -> str:
    quant = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    texto = f"{quant:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _nome_empresa(conta: Any) -> str:
    return nome_da_conta(conta) or getattr(conta, "nome", "") or "Empresa"


def agrupar_notas_por_empresa(
    notas: list[Any],
    contas: list[Any],
    empresa_prestadora_id: int | None = None,
) -> list[dict[str, Any]]:
    """Agrupa notas emitidas pelo CNPJ do tomador.

    A empresa do relatório é a prestadora cadastrada com o mesmo documento
    do tomador. Sem empresa escolhida, cada tomador vira um grupo e o PDF
    fecha com o total.
    """
    prestadoras = [
        conta for conta in contas
        if (getattr(conta, "tipo", "") or "") in ("prestadora", "ambos") and digitos_documento(getattr(conta, "cnpj", ""))
    ]
    por_documento = {digitos_documento(conta.cnpj): conta for conta in prestadoras}

    if empresa_prestadora_id:
        escolhida = next((conta for conta in prestadoras if conta.id == int(empresa_prestadora_id)), None)
        if escolhida is None:
            return []
        documento = digitos_documento(escolhida.cnpj)
        da_empresa = [nota for nota in notas if digitos_documento(getattr(nota, "tomador_cpf_cnpj", "")) == documento]
        return [{
            "nome": _nome_empresa(escolhida),
            "notas": da_empresa,
            "total": sum((Decimal(str(getattr(nota, "valor", 0) or 0)) for nota in da_empresa), Decimal("0")),
        }]

    grupos: dict[str, dict[str, Any]] = {}
    for nota in notas:
        conta = por_documento.get(digitos_documento(getattr(nota, "tomador_cpf_cnpj", "")))
        nome = _nome_empresa(conta) if conta is not None else (getattr(nota, "tomador_nome", "") or "Sem empresa")
        grupo = grupos.setdefault(nome, {"nome": nome, "notas": [], "total": Decimal("0")})
        grupo["notas"].append(nota)
        grupo["total"] += Decimal(str(getattr(nota, "valor", 0) or 0))
    return [grupos[nome] for nome in sorted(grupos)]


def _linhas_do_grupo(grupo: dict[str, Any], estilo_celula: ParagraphStyle) -> list[list[Any]]:
    linhas = [["NF", "Data", "Tomador", "Valor"]]
    for nota in grupo["notas"]:
        emissao = getattr(nota, "data_emissao", None)
        if isinstance(emissao, datetime):
            quando = timezone.localtime(emissao).strftime("%d/%m/%Y")
        else:
            quando = ""
        numero = str(getattr(nota, "numero_nf", "") or "—")
        rps = getattr(nota, "numero_rps", None)
        if rps:
            numero = f"{numero} · RPS {rps}"
        tomador = getattr(nota, "tomador_nome", "") or ""
        linhas.append([
            Paragraph(numero, estilo_celula),
            quando,
            Paragraph(tomador, estilo_celula),
            _brl(getattr(nota, "valor", 0)),
        ])
    return linhas


def gerar_pdf_nfse_emitidas(
    loja_id: int,
    grupos: list[dict[str, Any]],
    inicio,
    fim,
    *,
    canceladas: int = 0,
) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm, leftMargin=1.4 * cm, rightMargin=1.4 * cm)
    styles = getSampleStyleSheet()
    celula = ParagraphStyle("NfseCelula", parent=styles["Normal"], fontSize=8, leading=10)
    elements = [
        _criar_cabecalho_relatorio(_obter_logo_loja(loja_id), "Notas fiscais emitidas"),
        Spacer(1, 0.3 * cm),
        Paragraph(
            f'Período: {inicio.strftime("%d/%m/%Y")} a {fim.strftime("%d/%m/%Y")}',
            styles["Normal"],
        ),
        Spacer(1, 0.4 * cm),
    ]

    quantidade = sum(len(grupo["notas"]) for grupo in grupos)
    total = sum((grupo["total"] for grupo in grupos), Decimal("0"))
    if quantidade == 0:
        elements.append(Paragraph("Nenhuma nota emitida neste período.", styles["Normal"]))
    else:
        resumo = [
            ["Notas emitidas", str(quantidade)],
            ["Total", _brl(total)],
        ]
        tabela_resumo = Table(resumo, colWidths=[8 * cm, 8 * cm])
        tabela_resumo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0176d3")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.whitesmoke),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BACKGROUND", (1, 0), (1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(tabela_resumo)
        elements.append(Spacer(1, 0.5 * cm))

        for grupo in grupos:
            if not grupo["notas"]:
                elements.append(Paragraph(grupo["nome"], styles["Heading3"]))
                elements.append(Paragraph("Nenhuma nota emitida para esta empresa no período.", styles["Normal"]))
                elements.append(Spacer(1, 0.4 * cm))
                continue
            elements.append(Paragraph(grupo["nome"], styles["Heading3"]))
            dados = _linhas_do_grupo(grupo, celula)
            tabela = Table(dados, colWidths=[3.4 * cm, 2.4 * cm, 8.2 * cm, 3.2 * cm], repeatRows=1)
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0176d3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (3, 1), (3, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(tabela)
            elements.append(Paragraph(
                f'{len(grupo["notas"])} nota(s) · {_brl(grupo["total"])}',
                ParagraphStyle("Subtotal", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#0f172a")),
            ))
            elements.append(Spacer(1, 0.4 * cm))

    if canceladas:
        elements.append(Paragraph(
            f"{canceladas} nota(s) cancelada(s) no período ficam de fora deste total.",
            ParagraphStyle("Canceladas", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
        ))
    elements.append(Spacer(1, 0.6 * cm))
    elements.append(Paragraph(
        f'Relatório gerado em {timezone.localtime(timezone.now()).strftime("%d/%m/%Y às %H:%M")}',
        ParagraphStyle("Rodape", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
    ))
    doc.build(elements)
    buffer.seek(0)
    return buffer


def _intervalo(inicio, fim):
    tz = timezone.get_current_timezone()
    return (
        timezone.make_aware(datetime.combine(inicio, time.min), tz),
        timezone.make_aware(datetime.combine(fim, time.max), tz),
    )


def gerar_relatorio_nfse_emitidas(
    loja_id: int,
    periodo: str,
    empresa_prestadora_id: int | None = None,
    data_inicio_custom=None,
    data_fim_custom=None,
) -> BytesIO:
    from crm_vendas.models import Conta
    from nfse_integration.models import NFSe

    inicio, fim = calcular_intervalo_datas(periodo, data_inicio_custom, data_fim_custom)
    inicio_dt, fim_dt = _intervalo(inicio, fim)
    notas = list(
        NFSe.objects.filter(
            loja_id=loja_id,
            status="emitida",
            data_emissao__gte=inicio_dt,
            data_emissao__lte=fim_dt,
        ).order_by("data_emissao", "id"),
    )
    canceladas = NFSe.objects.filter(
        loja_id=loja_id,
        status="cancelada",
        data_emissao__gte=inicio_dt,
        data_emissao__lte=fim_dt,
    ).count()
    contas = list(Conta.objects.filter(loja_id=loja_id, tipo__in=["prestadora", "ambos"]))
    empresa_id = int(empresa_prestadora_id) if empresa_prestadora_id else None
    grupos = agrupar_notas_por_empresa(notas, contas, empresa_id)
    return gerar_pdf_nfse_emitidas(loja_id, grupos, inicio, fim, canceladas=canceladas)
