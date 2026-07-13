"""Helpers compartilhados para e-mails de assinatura digital (CRM).
"""
from urllib.parse import quote

from django.conf import settings


def tipo_documento(documento) -> str:
    return "Proposta" if documento.__class__.__name__ == "Proposta" else "Contrato"


def obter_loja_nome(loja_id) -> str:
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    return loja.nome if loja else "Sistema"


def construir_link_assinatura(token: str) -> str:
    frontend_url = getattr(settings, "FRONTEND_URL", "https://lwksistemas.com.br")
    return f'{frontend_url}/assinar/{quote(token, safe="")}'


def enviar_email_multipart(*, subject: str, texto_plano: str, html_content: str, to: list, attachment=None):
    """attachment: tuple (filename, bytes, mimetype) ou None."""
    from core.email_delivery import create_email_multipart

    email = create_email_multipart(
        subject=subject,
        body=texto_plano,
        to=to,
        html=html_content,
    )
    if attachment:
        filename, content, mimetype = attachment
        email.attach(filename, content, mimetype)
    email.send(fail_silently=False)
