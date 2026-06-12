"""Geração de PDF para Proposta e Contrato do CRM."""
from .generators import gerar_pdf_contrato, gerar_pdf_proposta

__all__ = ['gerar_pdf_proposta', 'gerar_pdf_contrato']
