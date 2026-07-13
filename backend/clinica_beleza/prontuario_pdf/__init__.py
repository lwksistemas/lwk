"""Geração de PDF para prontuário clínico com timbrado da clínica.
"""
from .generators import (
    gerar_pdf_consulta_secao,
    gerar_pdf_documento,
    gerar_pdf_prescricao_memed,
    gerar_pdf_prontuario_completo,
    gerar_pdf_secao,
)
from .header import _resolver_cabecalho, _resolver_cabecalho_relatorio

__all__ = [
    "_resolver_cabecalho",
    "_resolver_cabecalho_relatorio",
    "gerar_pdf_consulta_secao",
    "gerar_pdf_documento",
    "gerar_pdf_prescricao_memed",
    "gerar_pdf_prontuario_completo",
    "gerar_pdf_secao",
]
