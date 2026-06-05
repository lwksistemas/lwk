"""Constantes compartilhadas para geração de PDF do prontuário."""
import logging

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

logger = logging.getLogger(__name__)

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2 * cm
