"""Utilitários compartilhados para relatórios PDF do CRM.
"""
import logging
from io import BytesIO

import requests
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, Table, TableStyle

logger = logging.getLogger(__name__)

def _nome_cliente_venda(venda):
    """Cliente da venda. CNPJ sai pela razão social; CPF pelo nome da pessoa."""
    from .relatorio_comissao_data import nome_da_conta, nome_exibicao_juridica

    lead = getattr(venda, "lead", None)
    if not lead:
        return getattr(venda, "titulo", "") or ""
    conta = None
    if getattr(lead, "conta_id", None):
        try:
            conta = lead.conta
        except Exception:
            conta = None
    if conta is not None:
        return nome_da_conta(conta) or getattr(lead, "nome", "") or getattr(venda, "titulo", "") or ""
    documento = getattr(lead, "cpf_cnpj", "") or ""
    if len("".join(c for c in str(documento) if c.isdigit())) == 14:
        return nome_exibicao_juridica(getattr(lead, "empresa", ""), "", documento) or getattr(lead, "nome", "") or getattr(venda, "titulo", "") or ""
    return getattr(lead, "nome", "") or getattr(venda, "titulo", "") or ""


def _obter_logo_loja(loja_id):
    """Obtém URL do logo da loja."""
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if loja:
            return (getattr(loja, "logo", "") or getattr(loja, "login_logo", "") or "").strip() or None
    except Exception:
        return None
    return None


def carregar_logo_relatorio(logo_url, max_width=5.5 * cm, max_height=2.4 * cm):
    """Baixa a logomarca já no tamanho do PDF. A mídia exige a assinatura do arquivo."""
    if not logo_url:
        return None
    try:
        from core.media_storage import assinar_url_midia

        response = requests.get(assinar_url_midia(logo_url), timeout=8, allow_redirects=False)
        if response.status_code != 200 or not response.content:
            return None
        pil_img = PILImage.open(BytesIO(response.content))
        img_width, img_height = pil_img.size
        if not img_width or not img_height:
            return None
        aspect = img_height / float(img_width)
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
        return response.content, width, height
    except Exception:
        logger.warning("Erro ao carregar logo do relatório")
        return None


def _criar_cabecalho_relatorio(logo_url, titulo, max_width=6*cm, max_height=3*cm, centralizado=False, largura=None):
    """Cria cabeçalho com logo à esquerda e título à direita, ou os dois centralizados.
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0176d3"),
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
        from core.media_storage import assinar_url_midia

        # A mídia recusa o arquivo sem ?e=&s=. A assinatura vale só para este download.
        response = requests.get(assinar_url_midia(logo_url), timeout=8, allow_redirects=False)
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

        if centralizado:
            from reportlab.lib.pagesizes import A4

            title_style.alignment = TA_CENTER
            titulo_paragraph = Paragraph(titulo, title_style)
            img.hAlign = "CENTER"
            coluna = largura or (A4[0] - 2.8 * cm)
            table = Table([[img], [titulo_paragraph]], colWidths=[coluna])
            table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, 0), 0),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
                ("TOPPADDING", (0, 1), (-1, 1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
            ]))
            return table

        # Tabela: [Logo | Título]
        titulo_paragraph = Paragraph(titulo, title_style)
        table_data = [[img, titulo_paragraph]]
        table = Table(table_data, colWidths=[width + 0.5*cm, None])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        return table

    except Exception:
        logger.warning("Erro ao adicionar logo no relatório")
        title_style.alignment = TA_CENTER
        return Paragraph(titulo, title_style)

