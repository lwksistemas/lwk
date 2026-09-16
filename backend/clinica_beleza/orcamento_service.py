"""Service layer para Orçamentos de consulta."""
import html
import io
import logging
import re
from datetime import timedelta
from decimal import Decimal
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
            loja_id=consulta.loja_id,
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

    timbrado_bytes = _obter_timbrado(loja)
    logo_url = (loja.logo or "").strip() or (getattr(loja, "login_logo", "") or "").strip()
    pdf_bytes = _build_pdf(
        ctx_loja,
        orcamento,
        itens,
        com_timbrado=bool(timbrado_bytes),
        logo_url=logo_url,
    )

    # Tentar mesclar timbrado se existir
    if timbrado_bytes:
        from clinica_beleza.pdf_common.timbrado import merge_timbrado_fundo
        pdf_bytes = merge_timbrado_fundo(pdf_bytes, timbrado_bytes)

    return pdf_bytes


def enviar_orcamento(orcamento_id: int, canais: list[str]) -> dict[str, Any]:
    """Envia orçamento por email e/ou WhatsApp e salva PDF no servidor de mídia."""
    orcamento = OrcamentoConsulta.objects.select_related("patient", "professional").get(id=orcamento_id)
    pdf_bytes = gerar_pdf_orcamento(orcamento_id)
    resultado: dict[str, Any] = {}

    if "email" in canais:
        resultado["email"] = _enviar_email(orcamento, pdf_bytes)

    if "whatsapp" in canais:
        resultado["whatsapp"] = _enviar_whatsapp(orcamento, pdf_bytes)

    # Salvar PDF no servidor de mídia ({paciente}/pdf/)
    try:
        from clinica_beleza.media_docs_service import salvar_orcamento_no_servidor_midia
        salvar_orcamento_no_servidor_midia(orcamento, pdf_bytes)
    except Exception as e:
        logger.warning("Falha ao salvar orçamento no servidor de mídia: %s", e)

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

_OBS_LABELS = (
    r"Dados do Cliente:",
    r"Dados da empresa:",
    r"(?<![Dd]a )Empresa:",
    r"CPF/CNPJ:",
    r"(?<!/)CNPJ",
    r"E-mail:",
    r"Email:",
    r"Telefone:",
    r"Endere[cç]o:",
    r"LGPD",
)
_OBS_SPLIT = re.compile(r"\s+(?=(?:" + "|".join(_OBS_LABELS) + r"))", re.IGNORECASE)


def _format_brl(valor) -> str:
    """R$ 3.580,00"""
    v = Decimal(str(valor))
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def observacoes_para_exibicao(texto: str) -> str:
    """Quebra bloco colado (cadastro/LGPD) em linhas para leitura na tela e no PDF."""
    t = (texto or "").strip()
    if not t or "\n" in t:
        return t
    return _OBS_SPLIT.sub("\n", t).strip()


def montar_mensagem_whatsapp_orcamento(orcamento: OrcamentoConsulta, loja_nome: str = "") -> str:
    """Resumo profissional para WhatsApp — sem observações/cadastro (vão no PDF)."""
    from whatsapp.message_templates import msg_orcamento

    itens = [
        f"• {item.nome_procedimento} ({item.quantidade}x) — {_format_brl(item.subtotal)}"
        for item in orcamento.itens.all()
    ]
    nome = orcamento.patient.nome if orcamento.patient else "Paciente"
    clinica = (loja_nome or "").strip() or (
        orcamento.professional.nome if orcamento.professional else "Clínica"
    )
    return msg_orcamento(
        nome=nome,
        loja_nome=clinica,
        linhas_itens=itens,
        total=_format_brl(orcamento.valor_total),
        validade_dias=orcamento.validade_dias or 30,
    )




_OBS_PDF_LABELS = (
    "Dados do Cliente:",
    "Dados da empresa:",
    "Empresa:",
    "CPF/CNPJ:",
    "CNPJ",
    "E-mail:",
    "Email:",
    "Telefone:",
    "Endereço:",
    "Endereco:",
    "LGPD",
)


_CNPJ_E_RESTO = re.compile(
    r"^([\d./-]{14,18})\s+(.+)$",
)


def _observacoes_html_pdf(texto: str) -> str:
    """Observações com rótulos em negrito e quebra de linha."""
    linhas = observacoes_para_exibicao(texto).split("\n")
    saida = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        marcada = False
        for rotulo in _OBS_PDF_LABELS:
            if linha.lower().startswith(rotulo.lower()):
                resto = linha[len(rotulo):].strip()
                if rotulo.upper() == "CNPJ":
                    extra = _CNPJ_E_RESTO.match(resto)
                    if extra:
                        saida.append(f"<b>CNPJ:</b> {html.escape(extra.group(1))}")
                        saida.append(f"<b>Endereço:</b> {html.escape(extra.group(2))}")
                        marcada = True
                        break
                    saida.append(f"<b>CNPJ:</b> {html.escape(resto)}")
                    marcada = True
                    break
                saida.append(f"<b>{html.escape(rotulo)}</b> {html.escape(resto)}")
                marcada = True
                break
        if not marcada:
            saida.append(html.escape(linha))
    return "<br/>".join(saida)


def _fmt_hora_orcamento(dt) -> str:
    if not dt:
        return "—"
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime("%d/%m/%Y %H:%M")


def _linha_orcamento(story, rotulo: str, valor: str, style) -> None:
    from reportlab.platypus import Paragraph

    valor = (valor or "").strip()
    if not valor:
        return
    story.append(Paragraph(f"<b>{html.escape(rotulo)}:</b> {html.escape(valor)}", style))


def _build_pdf(
    ctx_loja: dict,
    orcamento: OrcamentoConsulta,
    itens: list,
    com_timbrado: bool = False,
    logo_url: str = "",
) -> bytes:
    """PDF do orçamento no visual do pedido de compra (vinho + marca d'água)."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    from clinica_beleza.pdf_common import QuadroComMarcaDagua, logo_image, watermark_logo_bytes
    from core.phone_utils import telefone_exibicao_brasileiro

    vinho = colors.HexColor("#8B3D52")
    fundo = colors.HexColor("#f8eef1")
    borda = colors.HexColor("#e5e7eb")

    buffer = io.BytesIO()
    top_margin = 3.2 * cm if com_timbrado else 1.2 * cm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=top_margin,
        bottomMargin=1.6 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    story = []
    base = getSampleStyleSheet()
    s_title = ParagraphStyle(
        "OrcTitle", parent=base["Heading1"], fontSize=16, textColor=vinho,
        alignment=TA_LEFT, spaceBefore=0, spaceAfter=0, leading=18,
    )
    s_section = ParagraphStyle(
        "OrcSection", parent=base["Normal"], fontSize=10, fontName="Helvetica-Bold",
        textColor=vinho, spaceBefore=2, spaceAfter=2, leading=13,
    )
    s_line = ParagraphStyle(
        "OrcLine", parent=base["Normal"], fontSize=9, spaceBefore=0, spaceAfter=1, leading=12,
    )
    s_cell = ParagraphStyle(
        "OrcCell", parent=base["Normal"], fontSize=8, leading=10,
        spaceBefore=0, spaceAfter=0, splitLongWords=True,
    )
    s_cell_r = ParagraphStyle(
        "OrcCellR", parent=base["Normal"], fontSize=8, leading=10,
        alignment=TA_RIGHT, spaceBefore=0, spaceAfter=0,
    )
    s_head = ParagraphStyle(
        "OrcHead", parent=base["Normal"], fontSize=8, leading=10,
        textColor=vinho, fontName="Helvetica-Bold", spaceBefore=0, spaceAfter=0,
    )
    s_head_r = ParagraphStyle(
        "OrcHeadR", parent=base["Normal"], fontSize=8, leading=10,
        textColor=vinho, fontName="Helvetica-Bold", alignment=TA_RIGHT,
        spaceBefore=0, spaceAfter=0,
    )
    s_obs = ParagraphStyle(
        "OrcObs", parent=base["Normal"], fontSize=8, leading=11, spaceBefore=1, spaceAfter=1,
    )
    s_box = ParagraphStyle(
        "OrcBox", parent=base["Normal"], fontSize=8, leading=11, spaceBefore=0, spaceAfter=1,
    )
    s_disc = ParagraphStyle(
        "OrcDisc", parent=base["Normal"], fontSize=7, leading=9,
        textColor=colors.HexColor("#666666"), spaceBefore=2, spaceAfter=0,
    )

    titulo_txt = f"ORÇAMENTO Nº {orcamento.id:02d}"
    if com_timbrado:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(html.escape(titulo_txt), s_title))
    else:
        logo = logo_image(logo_url, max_w=6 * cm, max_h=3 * cm) if logo_url else None
        titulo = Paragraph(html.escape(titulo_txt), s_title)
        if logo:
            cab = Table([[logo, titulo]], colWidths=[6.5 * cm, 10.5 * cm])
            cab.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(cab)
        else:
            s_title.alignment = TA_CENTER
            story.append(titulo)
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("<b>Dados da Clínica</b>", s_section))
        if ctx_loja.get("loja_nome"):
            _linha_orcamento(story, "Nome", ctx_loja["loja_nome"], s_line)
        if ctx_loja.get("loja_documento"):
            _linha_orcamento(
                story,
                ctx_loja.get("loja_documento_label", "CNPJ"),
                ctx_loja["loja_documento"],
                s_line,
            )
        if ctx_loja.get("loja_endereco"):
            _linha_orcamento(story, "Endereço", ctx_loja["loja_endereco"], s_line)
        if ctx_loja.get("loja_telefone"):
            _linha_orcamento(story, "Telefone", ctx_loja["loja_telefone"], s_line)
        if ctx_loja.get("loja_email"):
            _linha_orcamento(story, "E-mail", ctx_loja["loja_email"], s_line)

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("<b>Dados do Paciente</b>", s_section))
    paciente = orcamento.patient
    _linha_orcamento(story, "Nome", getattr(paciente, "nome", "") or "", s_line)
    _linha_orcamento(
        story, "Telefone",
        telefone_exibicao_brasileiro(getattr(paciente, "telefone", "") or ""),
        s_line,
    )
    _linha_orcamento(story, "E-mail", getattr(paciente, "email", "") or "", s_line)
    cpf = getattr(paciente, "cpf", "") or ""
    if cpf:
        _linha_orcamento(story, "CPF", cpf, s_line)

    if orcamento.professional:
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("<b>Profissional</b>", s_section))
        _linha_orcamento(story, "Nome", orcamento.professional.nome or "", s_line)

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("<b>Procedimentos</b>", s_section))
    rows = [[
        Paragraph("Procedimento", s_head),
        Paragraph("Qtd", s_head_r),
        Paragraph("Valor unit.", s_head_r),
        Paragraph("Subtotal", s_head_r),
    ]]
    for item in itens:
        rows.append([
            Paragraph(html.escape(item.nome_procedimento or ""), s_cell),
            Paragraph(str(item.quantidade), s_cell_r),
            Paragraph(_format_brl(item.valor_customizado), s_cell_r),
            Paragraph(_format_brl(item.subtotal), s_cell_r),
        ])
    tabela = Table(rows, colWidths=[8.2 * cm, 1.6 * cm, 3.6 * cm, 3.6 * cm])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), fundo),
        ("TEXTCOLOR", (0, 0), (-1, 0), vinho),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    tabela.hAlign = "LEFT"
    story.append(tabela)

    resumo = Table([["Valor total", _format_brl(orcamento.valor_total)]], colWidths=[5 * cm, 5 * cm])
    resumo.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), fundo),
        ("BOX", (0, 0), (-1, -1), 0.5, vinho),
        ("TEXTCOLOR", (1, 0), (1, 0), vinho),
    ]))
    resumo.hAlign = "LEFT"
    story.append(Spacer(1, 3 * mm))
    story.append(resumo)

    if orcamento.observacoes:
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("<b>Observações</b>", s_section))
        story.append(Paragraph(_observacoes_html_pdf(orcamento.observacoes), s_obs))

    data_validade = orcamento.created_at + timedelta(days=orcamento.validade_dias or 30)
    box_linhas = [
        Paragraph("<b>Validade e emissão</b>", s_box),
        Paragraph(f"<b>Válido até:</b> {data_validade:%d/%m/%Y}", s_box),
        Paragraph(f"<b>Emitido em:</b> {_fmt_hora_orcamento(orcamento.created_at)}", s_box),
    ]
    if orcamento.professional and orcamento.professional.nome:
        box_linhas.append(Paragraph(
            f"<b>Profissional:</b> {html.escape(orcamento.professional.nome)}",
            s_box,
        ))
    box_linhas.append(Paragraph(
        "Este orçamento é meramente informativo e não constitui contrato de prestação de serviço.",
        s_disc,
    ))
    quadro = Table([[linha] for linha in box_linhas], colWidths=[17 * cm])
    quadro.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
        ("TOPPADDING", (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
        ("BOX", (0, 0), (-1, -1), 0.5, borda),
    ]))
    wm = watermark_logo_bytes(logo_url) if logo_url else None
    story.append(Spacer(1, 6 * mm))
    story.append(QuadroComMarcaDagua(quadro, wm))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _obter_timbrado(loja) -> bytes | None:
    """Busca PDF de timbrado da loja (MemedTimbrado)."""
    try:
        from clinica_beleza.models import MemedTimbrado
        timbrado = MemedTimbrado.objects.filter(loja_id=loja.id).first()
        if timbrado and timbrado.pdf:
            return bytes(timbrado.pdf)
    except Exception as e:
        logger.debug("Timbrado não encontrado para loja %s: %s", getattr(loja, "id", "?"), e)
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
            f"Valor total: {_format_brl(orcamento.valor_total)}\n\n"
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
    """Envia orçamento por WhatsApp: mensagem de texto + PDF anexo.
    Mesmo padrão usado no recibo (send_whatsapp + _send_whatsapp_document_evolution).
    """
    telefone = (getattr(orcamento.patient, "telefone", "") or "").strip()
    if not telefone:
        return {"sucesso": False, "erro": "Paciente sem telefone cadastrado."}

    try:
        import hashlib
        import time
        from django.conf import settings
        from django.core.cache import cache as django_cache
        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp, _send_whatsapp_document_evolution

        config = WhatsAppConfig.objects.filter(loja_id=orcamento.loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return {"sucesso": False, "erro": "WhatsApp não está ativo. Configure em Configurações → WhatsApp."}

        loja_nome = "Clínica"
        try:
            loja = Loja.objects.using("default").filter(id=orcamento.loja_id).first()
            if loja and getattr(loja, "nome", ""):
                loja_nome = loja.nome
        except Exception:
            if orcamento.professional:
                loja_nome = orcamento.professional.nome

        mensagem = montar_mensagem_whatsapp_orcamento(orcamento, loja_nome)

        # Enviar mensagem de texto
        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if not ok:
            return {"sucesso": False, "erro": err or "Erro ao enviar WhatsApp."}

        # Enviar PDF via URL temporária (mesmo padrão do recibo)
        try:
            ts = str(int(time.time()))
            token_raw = f"orcamento-{orcamento.id}-{ts}-{settings.SECRET_KEY[:16]}"
            token = hashlib.sha256(token_raw.encode()).hexdigest()[:32]

            django_cache.set(
                f"orcamento_pdf_{token}",
                {"orcamento_id": orcamento.id, "pdf": pdf_bytes},
                300,
            )

            api_base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
            pdf_url = f"{api_base}/api/clinica-beleza/orcamentos/{orcamento.id}/pdf-public/{token}/"

            _send_whatsapp_document_evolution(
                telefone, pdf_url, f"orcamento_{orcamento.id}.pdf",
                caption="Orçamento", config=config,
            )
        except Exception as pdf_err:
            logger.warning("PDF via WhatsApp falhou (texto já enviado): %s", pdf_err)

        logger.info("Orçamento %d enviado por WhatsApp para %s", orcamento.id, telefone)
        return {"sucesso": True, "erro": ""}
    except ImportError as e:
        return {"sucesso": False, "erro": f"WhatsApp não configurado: {e}"}
    except Exception as e:
        logger.warning("Erro ao enviar orçamento por WhatsApp: %s", e)
        return {"sucesso": False, "erro": str(e)}
