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
    """Retorna o nome do cliente para exibição em relatórios.
    Prioridade: nome da empresa (Conta) > nome do lead > título da oportunidade.
    """
    if venda.lead:
        # Se tem Conta (empresa) vinculada, usar nome da empresa
        if venda.lead.conta_id:
            try:
                return venda.lead.conta.nome
            except Exception:
                pass
        return venda.lead.nome
    return venda.titulo


def _obter_logo_loja(loja_id):
    """Obtém URL do logo da loja."""
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if loja:
            return getattr(loja, "logo", "") or None
    except Exception:
        return None
    return None


def _criar_cabecalho_relatorio(logo_url, titulo, max_width=6*cm, max_height=3*cm):
    """Cria cabeçalho com logo à esquerda e título à direita na mesma linha.
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
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        return table

    except Exception as e:
        logger.warning(f"⚠️ Erro ao adicionar logo no relatório: {e}")
        title_style.alignment = TA_CENTER
        return Paragraph(titulo, title_style)

