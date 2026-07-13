"""Facade de templates de e-mail de assinatura digital (CRM).
Mantém imports estáveis para assinatura_digital_emails.py.
"""
from .assinatura_digital_email_cliente import montar_email_cliente_assinatura
from .assinatura_digital_email_finalizado import montar_email_pdf_final
from .assinatura_digital_email_vendedor import montar_email_vendedor_assinatura

__all__ = [
    "montar_email_cliente_assinatura",
    "montar_email_pdf_final",
    "montar_email_vendedor_assinatura",
]
