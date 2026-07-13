"""
Funções de envio de e-mail para Assinatura Digital de Propostas e Contratos.
"""
import logging

from .assinatura_digital_email_common import (
    construir_link_assinatura,
    enviar_email_multipart,
    obter_loja_nome,
    tipo_documento,
)
from .assinatura_digital_email_templates import (
    montar_email_cliente_assinatura,
    montar_email_pdf_final,
    montar_email_vendedor_assinatura,
)

logger = logging.getLogger(__name__)


def enviar_email_assinatura_cliente(documento, assinatura, request):
    """
    Envia email para cliente com link de assinatura.

    Returns:
        tuple: (sucesso: bool, erro: str ou None)
    """
    del request  # mantido na assinatura pública da API
    lead = documento.oportunidade.lead

    if not lead.email:
        return False, 'Lead não possui email cadastrado.'

    link_assinatura = construir_link_assinatura(assinatura.token)
    loja_nome = obter_loja_nome(assinatura.loja_id)
    tipo_doc = tipo_documento(documento)

    html_content, texto_plano = montar_email_cliente_assinatura(
        lead=lead,
        documento=documento,
        loja_nome=loja_nome,
        link_assinatura=link_assinatura,
        tipo_doc=tipo_doc,
    )

    try:
        enviar_email_multipart(
            subject=f'📄 Assinatura Digital - {tipo_doc}: {documento.titulo}',
            texto_plano=texto_plano,
            html_content=html_content,
            to=[lead.email],
        )

        logger.info(
            f'Email de assinatura enviado para cliente: {lead.email}, '
            f'documento={documento.__class__.__name__}#{documento.id}'
        )

        return True, None
    except Exception as e:
        logger.exception(f'Erro ao enviar email de assinatura para cliente: {e}')
        return False, str(e)


def enviar_email_assinatura_vendedor(documento, assinatura, request):
    """
    Envia email para vendedor com link de assinatura.

    Returns:
        tuple: (sucesso: bool, erro: str ou None)
    """
    del request
    if not (assinatura.email_assinante or '').strip():
        documento = assinatura.documento
        if documento:
            oportunidade = getattr(documento, 'oportunidade', None)
            vendedor = getattr(oportunidade, 'vendedor', None) if oportunidade else None
            email_doc = (getattr(vendedor, 'email', None) or '').strip()
            if email_doc:
                assinatura.email_assinante = email_doc
    if not (assinatura.email_assinante or '').strip():
        return False, 'Vendedor não possui email cadastrado.'

    link_assinatura = construir_link_assinatura(assinatura.token)
    loja_nome = obter_loja_nome(assinatura.loja_id)
    tipo_doc = tipo_documento(documento)
    lead = documento.oportunidade.lead

    html_content, texto_plano = montar_email_vendedor_assinatura(
        assinatura=assinatura,
        lead=lead,
        documento=documento,
        loja_nome=loja_nome,
        link_assinatura=link_assinatura,
        tipo_doc=tipo_doc,
    )

    try:
        enviar_email_multipart(
            subject=f'✅ Cliente Assinou - {tipo_doc}: {documento.titulo}',
            texto_plano=texto_plano,
            html_content=html_content,
            to=[assinatura.email_assinante],
        )

        logger.info(
            f'Email de assinatura enviado para vendedor: {assinatura.email_assinante}, '
            f'documento={documento.__class__.__name__}#{documento.id}'
        )

        return True, None
    except Exception as e:
        logger.exception(f'Erro ao enviar email de assinatura para vendedor: {e}')
        return False, str(e)


def enviar_pdf_final(documento, loja_id):
    """
    Envia PDF final com ambas assinaturas para cliente e vendedor.

    Returns:
        tuple: (sucesso: bool, erro: str ou None)
    """
    from superadmin.models import Loja

    from .pdf_proposta_contrato import gerar_pdf_contrato, gerar_pdf_proposta

    if documento.__class__.__name__ == 'Proposta':
        pdf_buffer = gerar_pdf_proposta(documento, incluir_assinaturas=True)
        tipo_doc = 'Proposta'
    else:
        pdf_buffer = gerar_pdf_contrato(documento, incluir_assinaturas=True)
        tipo_doc = 'Contrato'

    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.read()

    lead = documento.oportunidade.lead
    vendedor = documento.oportunidade.vendedor
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    loja_nome = loja.nome if loja else 'Sistema'

    destinatarios = []
    if lead.email:
        destinatarios.append(lead.email)
    if vendedor and vendedor.email:
        destinatarios.append(vendedor.email)
    elif loja and loja.owner and loja.owner.email:
        destinatarios.append(loja.owner.email)

    if not destinatarios:
        return False, 'Nenhum destinatário com email cadastrado.'

    filename = f'{tipo_doc.lower()}_{documento.titulo or documento.id}_assinado.pdf'

    html_content, texto_plano = montar_email_pdf_final(
        documento=documento,
        lead=lead,
        loja_nome=loja_nome,
        tipo_doc=tipo_doc,
    )

    try:
        enviar_email_multipart(
            subject=f'🎉 {tipo_doc} Assinado: {documento.titulo}',
            texto_plano=texto_plano,
            html_content=html_content,
            to=destinatarios,
            attachment=(filename, pdf_bytes, 'application/pdf'),
        )

        logger.info(
            f'PDF final enviado: documento={documento.__class__.__name__}#{documento.id}, '
            f'destinatarios={destinatarios}'
        )

        return True, None
    except Exception as e:
        logger.exception(f'Erro ao enviar PDF final: {e}')
        return False, str(e)
