"""PDF do Termo de Consentimento Esclarecido — Clínica da Beleza.
Assinaturas no padrão CRM Vendas (lado a lado + logo como marca d'água).
"""
import logging
from io import BytesIO

import pytz
import requests as http_requests
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)

COR_PRIMARIA = colors.HexColor("#8B3D52")


def _ts_local(dt):
    if not dt:
        return "—"
    tz = pytz.timezone("America/Sao_Paulo")
    return dt.astimezone(tz).strftime("%d/%m/%Y %H:%M:%S")


def _logo_url_loja(loja) -> str:
    if not loja:
        return ""
    return (getattr(loja, "login_logo", "") or "") or (getattr(loja, "logo", "") or "")


def _watermark_bytes(logo_url: str) -> bytes | None:
    """Logo da clínica com 25% de opacidade — marca d'água nas assinaturas (padrão CRM)."""
    if not logo_url:
        return None
    try:
        resp = http_requests.get(logo_url, timeout=5)
        if resp.status_code != 200:
            return None
        pil_img = PILImage.open(BytesIO(resp.content)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.25))
        pil_img.putalpha(alpha)
        out_buf = BytesIO()
        pil_img.save(out_buf, format="PNG")
        return out_buf.getvalue()
    except Exception as e:
        logger.warning("Marca dágua termo consentimento: %s", e)
        return None


def _build_secao_assinaturas(elements, termo_proc, compact_style, incluir_assinaturas: bool):
    """Assinaturas Paciente | Profissional — mesmo layout do CRM Vendas."""
    from .models import ConsultaAssinaturaTermo

    consulta = termo_proc.consulta
    elements.append(Spacer(1, 0.3 * cm))
    section = ParagraphStyle(
        "SecAssin", parent=compact_style, fontSize=10, spaceBefore=2, spaceAfter=4,
    )
    elements.append(Paragraph("<b>Assinaturas</b>", section))

    paciente = consulta.patient
    prof = consulta.professional
    paciente_email = (getattr(paciente, "email", "") or "").strip() if paciente else ""
    prof_email = (getattr(prof, "email", "") or "").strip() if prof else ""

    ass_paciente = None
    ass_profissional = None
    if incluir_assinaturas:
        filtro = {"termo_procedimento": termo_proc, "assinado": True}
        for ass in ConsultaAssinaturaTermo.objects.filter(**filtro).order_by("assinado_em"):
            if ass.tipo == "paciente":
                ass_paciente = ass
            elif ass.tipo == "profissional":
                ass_profissional = ass

    paciente_nome = (paciente.nome if paciente else "—").strip().upper() or "—"
    prof_nome = (prof.nome if prof else "—").strip().upper() or "—"

    paciente_info = [f"Paciente: {paciente_nome}"]
    if paciente_email:
        paciente_info.append(f"<font size='8'>Email: {paciente_email}</font>")
    if ass_paciente:
        paciente_info.append(f"<font size='8'>Assinado em: {_ts_local(ass_paciente.assinado_em)}</font>")
        paciente_info.append(f"<font size='8'>IP: {ass_paciente.ip_address}</font>")
        paciente_info.append("<font size='8'>Assinado digitalmente</font>")

    prof_info = [f"Profissional: {prof_nome}"]
    if prof_email:
        prof_info.append(f"<font size='8'>Email: {prof_email}</font>")
    if ass_profissional:
        prof_info.append(f"<font size='8'>Assinado em: {_ts_local(ass_profissional.assinado_em)}</font>")
        prof_info.append(f"<font size='8'>IP: {ass_profissional.ip_address}</font>")
        prof_info.append("<font size='8'>Assinado digitalmente</font>")

    assinatura_data = []
    max_rows = max(len(paciente_info), len(prof_info))
    for i in range(max_rows):
        p_text = Paragraph(paciente_info[i], compact_style) if i < len(paciente_info) else ""
        pr_text = Paragraph(prof_info[i], compact_style) if i < len(prof_info) else ""
        assinatura_data.append([p_text, pr_text])

    t = Table(assinatura_data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("BOX", (1, 0), (1, -1), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.1 * cm))

    validade = ParagraphStyle(
        "Validade", parent=compact_style, fontSize=7,
        textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceBefore=2,
    )
    elements.append(Paragraph(
        "Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, "
        "com registro de data, hora e endereço IP.",
        validade,
    ))

    return ass_paciente, ass_profissional


def _insert_watermark(elements, wm_bytes: bytes):
    """Insere marca d'água (logo) nas duas colunas de assinatura — padrão CRM."""

    class WatermarkFlowable(Flowable):
        def __init__(self, wm_data: bytes):
            Flowable.__init__(self)
            self.wm_bytes = wm_data
            self.width = 16 * cm
            self.height = 0

        def draw(self):
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(BytesIO(self.wm_bytes))
                iw, ih = img.getSize()
                wm_w = 7.5 * cm
                wm_h = wm_w * (ih / float(iw))
                if wm_h > 5 * cm:
                    wm_h = 5 * cm
                    wm_w = wm_h / (ih / float(iw))
                y_offset = -(wm_h * 0.8)
                x_left = (8 * cm - wm_w) / 2
                x_right = 8 * cm + (8 * cm - wm_w) / 2
                self.canv.drawImage(
                    img, x_left, y_offset, width=wm_w, height=wm_h,
                    mask="auto", preserveAspectRatio=True,
                )
                self.canv.drawImage(
                    img, x_right, y_offset, width=wm_w, height=wm_h,
                    mask="auto", preserveAspectRatio=True,
                )
            except Exception:
                pass

    insert_idx = None
    for i in range(len(elements) - 1, -1, -1):
        if isinstance(elements[i], Table):
            insert_idx = i
            break
    if insert_idx is not None:
        elements.insert(insert_idx, WatermarkFlowable(wm_bytes))


def gerar_pdf_termo_consentimento(termo_proc, incluir_assinaturas: bool = False) -> BytesIO:
    """PDF de um único procedimento — conteúdo e assinaturas isolados."""
    consulta = termo_proc.consulta
    procedure = termo_proc.procedure
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )
    elements = []
    styles = getSampleStyleSheet()
    col1, col2 = 5.5 * cm, 11 * cm

    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"], fontSize=18,
        textColor=COR_PRIMARIA, alignment=TA_CENTER, spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"], fontSize=12,
        textColor=COR_PRIMARIA, spaceBefore=10, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=4,
    )
    compact = ParagraphStyle(
        "Compact", parent=styles["Normal"], fontSize=9, spaceBefore=0, spaceAfter=1, leading=11,
    )

    from superadmin.models import Loja
    loja = Loja.objects.using("default").filter(id=consulta.loja_id).first()
    nome_clinica = loja.nome if loja else "Clínica"
    logo_url = _logo_url_loja(loja)

    if logo_url:
        try:
            resp = http_requests.get(logo_url, timeout=5)
            if resp.status_code == 200:
                img_buf = BytesIO(resp.content)
                pil = PILImage.open(img_buf)
                iw, ih = pil.size
                w = min(5 * cm, iw)
                h = w * (ih / float(iw))
                if h > 2.5 * cm:
                    h = 2.5 * cm
                    w = h * (iw / float(ih))
                img_buf.seek(0)
                logo = Image(img_buf, width=w, height=h)
                logo.hAlign = "CENTER"
                elements.append(logo)
                elements.append(Spacer(1, 0.3 * cm))
        except Exception as e:
            logger.warning("Logo termo consentimento: %s", e)

    elements.append(Paragraph(nome_clinica, ParagraphStyle(
        "Clinica", parent=styles["Normal"], fontSize=11,
        textColor=colors.grey, alignment=TA_CENTER,
    )))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph("Termo de Consentimento Esclarecido", title_style))

    from django.utils import timezone as dj_tz

    paciente = consulta.patient
    prof = consulta.professional
    data_str = dj_tz.localtime().strftime("%d/%m/%Y")
    if consulta.data_inicio:
        data_str = dj_tz.localtime(consulta.data_inicio).strftime("%d/%m/%Y")
    dados = [
        ["Paciente", paciente.nome if paciente else "—"],
        ["CPF", getattr(paciente, "cpf", "") or "—"],
        ["Procedimento", procedure.nome if procedure else "—"],
        ["Profissional", prof.nome if prof else "—"],
        ["Conselho", (prof.formatar_conselho() if prof else "") or "—"],
        ["Data", data_str],
    ]
    if loja and loja.cpf_cnpj:
        dados.append(["CNPJ Clínica", loja.cpf_cnpj])
    if loja:
        endereco = ", ".join(
            p for p in [
                getattr(loja, "endereco", "") or "",
                getattr(loja, "cidade", "") or "",
                getattr(loja, "estado", "") or "",
            ] if p
        )
        if endereco:
            dados.append(["Endereço", endereco])
    t = Table(dados, colWidths=[col1, col2])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(t)

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Conteúdo do Termo", section_style))
    from .consentimento_service import limpar_conteudo_termo_exibicao, montar_conteudo_termo_procedimento
    if termo_proc.status_assinatura_termo == "concluido":
        conteudo = limpar_conteudo_termo_exibicao(termo_proc.conteudo_termo or "")
    else:
        conteudo = limpar_conteudo_termo_exibicao(
            montar_conteudo_termo_procedimento(consulta, procedure)
            or termo_proc.conteudo_termo
            or "",
        )
    for line in conteudo.split("\n"):
        stripped = line.strip()
        if not stripped:
            elements.append(Spacer(1, 0.12 * cm))
        else:
            elements.append(Paragraph(stripped.replace("&", "&amp;"), body_style))

    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(
        "Ao assinar digitalmente, declaro ter lido e compreendido o termo acima, "
        "estando ciente dos riscos, benefícios e alternativas deste procedimento.",
        ParagraphStyle("Aceite", parent=body_style, fontSize=9, textColor=colors.HexColor("#555")),
    ))

    ass_p, ass_pr = _build_secao_assinaturas(elements, termo_proc, compact, incluir_assinaturas)

    if (ass_p or ass_pr) and logo_url:
        wm_bytes = _watermark_bytes(logo_url)
        if wm_bytes:
            _insert_watermark(elements, wm_bytes)

    doc.build(elements)
    buf.seek(0)
    return buf
