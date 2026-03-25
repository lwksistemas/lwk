"""
Serviço de emissão de Nota Fiscal via API Asaas.
Emitir NF vinculada à cobrança (payment) e enviar por e-mail ao admin da loja.
"""
import logging
from datetime import date
from typing import Optional, Dict, Any

from django.conf import settings

logger = logging.getLogger(__name__)


def get_invoice_client():
    """Retorna o cliente Asaas configurado para chamadas de NF."""
    from .models import AsaasConfig
    from .client import AsaasClient
    config = AsaasConfig.get_config()
    if not config.api_key or not config.enabled:
        return None
    return AsaasClient(api_key=config.api_key, sandbox=config.sandbox)


def _get_municipal_config() -> Dict[str, Optional[str]]:
    """Serviço municipal para NF (conta LWK na prefeitura)."""
    code = getattr(settings, 'ASAAS_INVOICE_SERVICE_CODE', None)
    name = getattr(settings, 'ASAAS_INVOICE_SERVICE_NAME', 'Software sob demanda / Assinatura de sistema')
    service_id = getattr(settings, 'ASAAS_INVOICE_SERVICE_ID', None)
    
    # Log para debug
    logger.info(f"Configuração municipal NF: code={code}, name={name}, service_id={service_id}")
    
    return {
        'municipal_service_code': code if code else None,
        'municipal_service_name': name,
        'municipal_service_id': service_id if service_id else None,
    }


def emitir_nf_para_pagamento(
    asaas_payment_id: str,
    loja,
    value: float,
    description: str,
    send_email: bool = True,
) -> Dict[str, Any]:
    """
    Agenda e emite a nota fiscal no Asaas para a cobrança e envia por e-mail ao admin da loja.

    Args:
        asaas_payment_id: ID da cobrança no Asaas (payment.id).
        loja: instância de superadmin.models.Loja (com owner.email).
        value: valor da cobrança.
        description: descrição do serviço (ex.: "Assinatura Plano X - Loja Y").
        send_email: se True, envia e-mail ao loja.owner.email com a confirmação/link da NF.

    Returns:
        Dict com success, invoice_id, error (se houver), email_sent.
    """
    result = {'success': False, 'invoice_id': None, 'error': None, 'email_sent': False}
    client = get_invoice_client()
    if not client:
        result['error'] = 'Asaas não configurado ou desabilitado'
        logger.warning("Emissão NF: Asaas não configurado")
        return result

    municipal = _get_municipal_config()
    effective_date = date.today().isoformat()
    service_description = description or 'Assinatura LWK Sistemas'

    try:
        # 1. Agendar NF
        created = client.create_invoice(
            payment_id=asaas_payment_id,
            service_description=service_description,
            value=float(value),
            effective_date=effective_date,
            municipal_service_code=municipal.get('municipal_service_code'),
            municipal_service_name=municipal.get('municipal_service_name'),
            municipal_service_id=municipal.get('municipal_service_id'),
        )
        invoice_id = created.get('id')
        if not invoice_id:
            result['error'] = 'Resposta da API sem id da nota fiscal'
            logger.error("Emissão NF: resposta sem id: %s", created)
            return result

        logger.info("NF agendada no Asaas: invoice_id=%s, payment=%s", invoice_id, asaas_payment_id)

        # 2. Emitir (autorizar) NF
        client.authorize_invoice(invoice_id)
        result['success'] = True
        result['invoice_id'] = invoice_id
        logger.info("NF emitida no Asaas: invoice_id=%s", invoice_id)

        # 3. Opcional: link do PDF (se a API retornar)
        pdf_url = None
        try:
            inv = client.get_invoice(invoice_id)
            pdf_url = inv.get('invoiceUrl') or inv.get('pdfUrl') or inv.get('invoicePdfUrl')
        except Exception as e:
            logger.debug("Não foi possível obter link da NF: %s", e)

        # 4. Enviar e-mail ao admin da loja
        if send_email and loja and getattr(loja, 'owner', None):
            email_to = getattr(loja.owner, 'email', None)
            if email_to:
                try:
                    _send_nf_email_to_loja(
                        to_email=email_to,
                        loja_nome=loja.nome,
                        invoice_id=invoice_id,
                        value=value,
                        description=service_description,
                        pdf_url=pdf_url,
                    )
                    result['email_sent'] = True
                except Exception as e:
                    logger.exception("Falha ao enviar e-mail da NF para %s: %s", email_to, e)
                    result['error'] = result.get('error') or f'Emitida, mas e-mail falhou: {e}'
            else:
                logger.warning("Loja %s sem e-mail do owner para envio da NF", getattr(loja, 'nome', loja))

    except Exception as e:
        logger.exception("Erro ao emitir NF para payment %s: %s", asaas_payment_id, e)
        result['error'] = str(e)
    return result


def _send_nf_email_to_loja(
    to_email: str,
    loja_nome: str,
    invoice_id: str,
    value: float,
    description: str,
    pdf_url: Optional[str] = None,
) -> None:
    """Envia e-mail ao admin da loja com a confirmação da nota fiscal."""
    from django.core.mail import EmailMessage

    subject = 'Nota Fiscal – Assinatura LWK Sistemas'
    body_lines = [
        f'Olá,',
        f'',
        f'A nota fiscal referente à assinatura da loja **{loja_nome}** foi emitida.',
        f'',
        f'Identificador da NF: {invoice_id}',
        f'Descrição: {description}',
        f'Valor: R$ {value:.2f}',
        f'',
    ]
    if pdf_url:
        body_lines.append(f'Acesse a nota fiscal em: {pdf_url}')
        body_lines.append('')
    body_lines.append('Em caso de dúvidas, entre em contato com o suporte.')
    body = '\n'.join(body_lines)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
    msg = EmailMessage(subject=subject, body=body, from_email=from_email, to=[to_email])
    msg.send(fail_silently=False)
