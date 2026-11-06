"""Seções reutilizáveis do PDF de proposta/contrato."""
import logging
from io import BytesIO
from xml.sax.saxutils import escape

from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily, stringWidth
from reportlab.platypus import HRFlowable, Image, Paragraph, Spacer, Table, TableStyle

from core.cpf_utils import normalizar_cpf_cnpj
from core.phone_utils import telefone_exibicao_brasileiro

from .formatters import (
    _formatar_endereco_lead,
    _formatar_nome_usuario,
    _formatar_timestamp_local,
    _formatar_valor,
    _html_to_paragraphs,
    _title_case_endereco,
    baixar_logo_pdf,
    blocos_formatados,
    descricoes_da_oportunidade,
    linguagem_investimento,
    titulo_de_bloco,
)

logger = logging.getLogger(__name__)

FONTE = "DejaVu"
FONTE_NEGRITO = "DejaVu-Bold"
_pasta_fontes = Path(__file__).resolve().parent / "fonts"
if FONTE not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont(FONTE, str(_pasta_fontes / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONTE_NEGRITO, str(_pasta_fontes / "DejaVuSans-Bold.ttf")))
    registerFontFamily(FONTE, normal=FONTE, bold=FONTE_NEGRITO, italic=FONTE, boldItalic=FONTE_NEGRITO)

__all__ = [nome for nome in globals() if not nome.startswith("__")]


