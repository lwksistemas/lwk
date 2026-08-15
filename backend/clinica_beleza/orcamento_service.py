"""Service layer para Orçamentos de consulta."""
import io
import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.utils import timezone

from clinica_beleza.models import OrcamentoConsulta, OrcamentoItem, Consulta, Procedure, Patient
from superadmin.models import Loja

logger = logging.getLogger(__name__)


def criar_orcamento(
    consulta_id: int,
    itens_payload: list[dict],
    observacoes: str = "",
    validade_dias: int = 30,
) -> OrcamentoConsulta:
    """Cria orçamento com itens a partir de uma consulta."""
    consulta = Consulta.objects.select_related("patient", "professional").get(id=consulta_id)

    orcamento = OrcamentoConsulta.objects.create(
        consulta=consulta,
        patient=consulta.patient,
        professional=consulta.professional,
        observacoes=observacoes,
        validade_dias=validade_dias,
        loja_id=consulta.loja_id,
    )

    valor_total = Decimal("0.00")
    for item_data in itens_payload:
        procedure = Procedure.objects.get(id=item_data["procedure_id"])
        valor_custom = Decimal(str(item_data.get("valor_customizado") or procedure.preco))
        quantidade = int(item_data.get("quantidade", 1))

        OrcamentoItem.objects.create(
            orcamento=orcamento,
            procedure=procedure,
            nome_procedimento=procedure.nome,
            descricao_procedimento=procedure.descricao or "",
            valor_original=procedure.preco,
            valor_customizado=valor_custom,
            quantidade=quantidade,
            observacao_item=item_data.get("observacao_item", ""),
        )
        valor_total += valor_custom * quantidade

    orcamento.valor_total = valor_total
    orcamento.save(update_fields=["valor_total"])
    return orcamento


def listar_orcamentos_consulta(consulta_id: int) -> list[dict]:
    """Retorna lista de orçamentos de uma consulta."""
    orcamentos = OrcamentoConsulta.objects.filter(consulta_id=consulta_id).prefetch_related("itens")
    resultado = []
    for orc in orcamentos:
        resultado.append({
            "id": orc.id,
            "consulta_id": orc.consulta_id,
            "patient_name": orc.patient.nome if orc.patient else "",
            "professional_name": orc.professional.nome if orc.professional else "",
            "observacoes": orc.observacoes,
            "valor_total": str(orc.valor_total),
            "validade_dias": orc.validade_dias,
            "status": orc.status,
            "enviado_email": orc.enviado_email,
            "enviado_whatsapp": orc.enviado_whatsapp,
            "data_envio": orc.data_envio.isoformat() if orc.data_envio else None,
            "created_at": orc.created_at.isoformat(),
            "itens": [
                {
                    "id": item.id,
                    "procedure_id": item.procedure_id,
                    "nome_procedimento": item.nome_procedimento,
                    "valor_original": str(item.valor_original),
                    "valor_customizado": str(item.valor_customizado),
                    "quantidade": item.quantidade,
                    "observacao_item": item.observacao_item,
                    "subtotal": str(item.subtotal),
                }
                for item in orc.itens.all()
            ],
        })
    return resultado


def gerar_pdf_orcamento(orcamento_id: int) -> bytes:
    """Gera PDF do orçamento com papel timbrado."""
    orcamento = OrcamentoConsulta.objects.select_related(
        "patient", "professional", "consulta",
    ).prefetch_related("itens").get(id=orcamento_id)

    loja = Loja.objects.using("default").get(id=orcamento.loja_id)
    itens = list(orcamento.itens.all())

    from clinica_beleza.recibo.context import _dados_loja_recibo
    ctx_loja = _dados_loja_recibo(loja)

    pdf_bytes = _build_pdf(ctx_loja, orcamento, itens)

    # Tentar mesclar timbrado se existir
    timbrado_bytes = _obter_timbrado(loja)
    if timbrado_bytes:
        from clinica_beleza.pdf_common.timbrado import merge_timbrado_fundo
        pdf_bytes = merge_timbrado_fundo(pdf_bytes, timbrado_bytes)

    return pdf_bytes


def enviar_orcamento(orcamento_id: int, canais: list[str]) -> dict[str, Any]:
    """Envia orçamento por email e/ou WhatsApp."""
    orcamento = OrcamentoConsulta.objects.select_related("patient", "professional").get(id=orcamento_id)
    pdf_bytes = gerar_pdf_orcamento(orcamento_id)
    resultado: dict[str, Any] = {}

    if "email" in canais:
        resultado["email"] = _enviar_email(orcamento, pdf_bytes)

    if "whatsapp" in canais:
        resultado["whatsapp"] = _enviar_whatsapp(orcamento, pdf_bytes)

    # Atualizar status
    algum_sucesso = any(r.get("sucesso") for r in resultado.values())
    if algum_sucesso:
        orcamento.status = "ENVIADO"
        orcamento.data_envio = timezone.now()
    if resultado.get("email", {}).get("sucesso"):
        orcamento.enviado_email = True
    if resultado.get("whatsapp", {}).get("sucesso"):
        orcamento.enviado_whatsapp = True
    orcamento.save()

    return resultado


def excluir_orcamento(orcamento_id: int) -> None:
    """Exclui orçamento."""
    OrcamentoConsulta.objects.filter(id=orcamento_id).delete()


# ---------------------------------------------------------------------------
# Internos
# ---------------------------------------------------------------------------

def _build_pdf(ctx_loja: dict, orcamento: OrcamentoConsulta, itens: list) -> bytes:
    """Constrói PDF do orçamento com ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm, cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    story = []

    s_center = ParagraphStyle("c", fontSize=9, alignment=TA_CENTER, leading=12)
    s_bold_center = ParagraphStyle("bc", fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=15)
    s_title = ParagraphStyle("ti", fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=18)
    s_left = ParagraphStyle("l", fontSize=9, leading=12)
    s_bold = ParagraphStyle("b", fontSize=9, fontName="Helvetica-Bold", leading=12)
    s_total = ParagraphStyle("t", fontSize=13, fontName="Helvetica-Bold", alignment=TA_RIGHT, leading=16)
    s_obs = ParagraphStyle("obs", fontSize=9, leading=12, leftIndent=10)
    s_footer = ParagraphStyle("f", fontSize=7, alignment=TA_CENTER, textColor=colors.HexColor("#666"), leading=10)
    hr = HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#ccc"), spaceAfter=6, spaceBefore=6)

    # Cabeçalho da clínica
    if ctx_loja.get("loja_nome"):
        story.append(Paragraph(ctx_loja["loja_nome"].upper(), s_bold_center))
    if ctx_loja.get("loja_documento"):
        story.append(Paragraph(f'{ctx_loja.get("loja_documento_label", "CNPJ")}: {ctx_loja["loja_documento"]}', s_center))
    if ctx_loja.get("loja_endereco"):
        story.append(Paragraph(ctx_loja["loja_endereco"], s_center))
    if ctx_loja.get("loja_telefone"):
        story.append(Paragraph(f'Tel: {ctx_loja["loja_telefone"]}', s_center))
    story.append(Spacer(1, 6*mm))
    story.append(hr)

    # Título
    story.append(Paragraph("ORÇAMENTO", s_title))
    story.append(Spacer(1, 4*mm))

    # Dados paciente
    story.append(Paragraph(f'<b>Paciente:</b> {orcamento.patient.nome}', s_left))
    paciente_tel = getattr(orcamento.patient, "telefone", "") or ""
    paciente_email = getattr(orcamento.patient, "email", "") or ""
    if paciente_tel:
        story.append(Paragraph(f'<b>Telefone:</b> {paciente_tel}', s_left))
    if paciente_email:
        story.append(Paragraph(f'<b>Email:</b> {paciente_email}', s_left))
    story.append(Spacer(1, 3*mm))

    # Dados profissional
    if orcamento.professional:
        story.append(Paragraph(f'<b>Profissional:</b> {orcamento.professional.nome}', s_left))
        story.append(Spacer(1, 3*mm))

    story.append(hr)

    # Tabela de itens
    table_data = [["Procedimento", "Qtd", "Valor Unit.", "Subtotal"]]
    for item in itens:
        table_data.append([
            item.nome_procedimento,
            str(item.quantidade),
            f"R$ {item.valor_customizado:,.2f}",
            f"R$ {item.subtotal:,.2f}",
        ])

    t = Table(table_data, colWidths=[220, 40, 90, 90])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    # Total
    story.append(Paragraph(f"TOTAL: R$ {orcamento.valor_total:,.2f}", s_total))
    story.append(Spacer(1, 4*mm))

    # Observações
    if orcamento.observacoes:
        story.append(hr)
        story.append(Paragraph("<b>Observações:</b>", s_bold))
        story.append(Paragraph(orcamento.observacoes, s_obs))
        story.append(Spacer(1, 3*mm))

    # Validade
    story.append(hr)
    data_validade = orcamento.created_at + timedelta(days=orcamento.validade_dias)
    story.append(Paragraph(f"Válido até: {data_validade:%d/%m/%Y}", s_left))
    story.append(Paragraph(f"Emitido em: {orcamento.created_at:%d/%m/%Y %H:%M}", s_left))

    # Rodapé
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        "Este orçamento é meramente informativo e não constitui contrato de prestação de serviço.",
        s_footer,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _obter_timbrado(loja) -> bytes | None:
    """Busca PDF de timbrado da loja (se configurado)."""
    timbrado = getattr(loja, "timbrado_pdf", None)
    if timbrado and hasattr(timbrado, "read"):
        return timbrado.read()
    return None


def _enviar_email(orcamento: OrcamentoConsulta, pdf_bytes: bytes) -> dict:
    """Envia orçamento por email."""
    email = (getattr(orcamento.patient, "email", "") or "").strip()
    if not email:
        return {"sucesso": False, "erro": "Paciente sem e-mail cadastrado."}

    try:
        from core.email_delivery import create_email_message, send_prepared

        profissional = orcamento.professional.nome if orcamento.professional else "Clínica"
        assunto = f"Orçamento — {profissional}"
        corpo = (
            f"Olá {orcamento.patient.nome},\n\n"
            f"Segue em anexo o orçamento dos procedimentos conversados.\n"
            f"Valor total: R$ {orcamento.valor_total:,.2f}\n\n"
            f"Qualquer dúvida, estamos à disposição.\n\n"
            f"Atenciosamente,\n{profissional}"
        )

        msg = create_email_message(subject=assunto, body=corpo, to=[email])
        msg.attach(f"orcamento_{orcamento.id}.pdf", pdf_bytes, "application/pdf")
        send_prepared(msg, fail_silently=False)

        logger.info("Orçamento %d enviado por email para %s", orcamento.id, email)
        return {"sucesso": True}
    except Exception as e:
        logger.warning("Erro ao enviar orçamento por email: %s", e)
        return {"sucesso": False, "erro": str(e)}


def _enviar_whatsapp(orcamento: OrcamentoConsulta, pdf_bytes: bytes) -> dict:
    """Envia orçamento por WhatsApp (como documento PDF via Evolution API)."""
    telefone = (getattr(orcamento.patient, "telefone", "") or "").strip()
    if not telefone:
        return {"sucesso": False, "erro": "Paciente sem telefone cadastrado."}

    try:
        import base64
        from whatsapp.evolution_client import send_document
        from whatsapp.config_helpers import get_instance_name_for_loja

        instance_name = get_instance_name_for_loja(orcamento.loja_id)
        if not instance_name:
            return {"sucesso": False, "erro": "WhatsApp não configurado nesta loja."}

        # Evolution API aceita base64 como document_url com prefixo data:
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        document_url = f"data:application/pdf;base64,{pdf_b64}"
        filename = f"orcamento_{orcamento.id}.pdf"
        caption = f"Orçamento — {orcamento.patient.nome} — R$ {orcamento.valor_total:,.2f}"

        send_document(instance_name, telefone, document_url, filename, caption=caption)
        logger.info("Orçamento %d enviado por WhatsApp para %s", orcamento.id, telefone)
        return {"sucesso": True, "erro": ""}
    except ImportError:
        return {"sucesso": False, "erro": "WhatsApp não configurado nesta loja."}
    except Exception as e:
        logger.warning("Erro ao enviar orçamento por WhatsApp: %s", e)
        return {"sucesso": False, "erro": str(e)}
