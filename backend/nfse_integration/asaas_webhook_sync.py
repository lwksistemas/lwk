"""
Sincroniza registros NFSe (CRM) com o objeto invoice do Asaas (webhook ou GET /invoices/:id).

Situação típica: a API retorna sucesso ao agendar/autorizar, mas a prefeitura processa depois;
o painel Asaas mostra «Erro na emissão» enquanto o CRM ainda está «Emitida».
Ver: https://docs.asaas.com/docs/invoices-events
"""
import json
import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from .models import NFSe

logger = logging.getLogger(__name__)


def _mensagem_erro_invoice_asaas(invoice: Dict[str, Any]) -> str:
    if not invoice:
        return 'Erro na emissão (Asaas).'
    partes = []
    for key in ('message', 'note', 'validationDetails', 'errorDescription', 'denialReason'):
        v = invoice.get(key)
        if v:
            partes.append(str(v))
    errs = invoice.get('errors')
    if errs and not partes:
        try:
            partes.append(json.dumps(errs, ensure_ascii=False)[:1500])
        except Exception:
            partes.append(str(errs)[:1500])
    out = '; '.join(partes)[:2000]
    return out or 'Erro na emissão (Asaas).'


def aplicar_objeto_invoice_asaas_em_nfse(
    nfse: 'NFSe',
    invoice: Dict[str, Any],
    event: str = '',
) -> bool:
    """
    Atualiza campos de `nfse` conforme `status` / evento do Asaas.
    Retorna True se houve alteração persistida.
    """
    if not isinstance(invoice, dict) or not invoice:
        return False

    status_raw = (invoice.get('status') or '').strip().upper()
    event_u = (event or '').strip().upper()

    if event_u == 'INVOICE_ERROR' or status_raw == 'ERROR':
        nfse.status = 'erro'
        nfse.erro = _mensagem_erro_invoice_asaas(invoice)
        nfse.save()
        logger.info('NFSe id=%s → erro (Asaas)', nfse.id)
        return True

    if event_u == 'INVOICE_AUTHORIZED' or status_raw == 'AUTHORIZED':
        nfse.status = 'emitida'
        if nfse.erro:
            nfse.erro = ''
        pdf = (
            invoice.get('pdfUrl')
            or invoice.get('invoiceUrl')
            or invoice.get('url')
            or nfse.pdf_url
        )
        if pdf and str(pdf) != (nfse.pdf_url or ''):
            nfse.pdf_url = str(pdf)[:500]
        nfse.save()
        logger.info('NFSe id=%s → emitida/autorizada (Asaas)', nfse.id)
        return True

    if event_u == 'INVOICE_CANCELED' or status_raw == 'CANCELED':
        nfse.status = 'cancelada'
        if not nfse.data_cancelamento:
            nfse.data_cancelamento = timezone.now()
        nfse.save()
        logger.info('NFSe id=%s → cancelada (Asaas)', nfse.id)
        return True

    return False


def sincronizar_nfse_com_webhook_invoice(event: str, invoice: Dict[str, Any]) -> None:
    """Localiza NFSe por `asaas_invoice_id` e aplica o objeto do webhook."""
    from .models import NFSe

    if not isinstance(invoice, dict):
        return

    invoice_id = invoice.get('id')
    if not invoice_id:
        return

    invoice_id = str(invoice_id).strip()
    nf = NFSe.objects.filter(asaas_invoice_id=invoice_id).first()
    if not nf:
        logger.debug(
            'Webhook Asaas NF: nenhuma NFSe com asaas_invoice_id=%s (event=%s)',
            invoice_id,
            event,
        )
        return

    aplicar_objeto_invoice_asaas_em_nfse(nf, invoice, event)


def sincronizar_nfse_via_api_asaas(nfse: 'NFSe', api_key: str, sandbox: bool) -> Optional[Dict[str, Any]]:
    """
    Busca GET /v3/invoices/:id no Asaas e atualiza o registro local.
    Retorna dict com erro em caso de falha, ou {'ok': True} se sucesso.
    """
    if not (nfse.asaas_invoice_id or '').strip():
        return {'error': 'Esta NFS-e não possui vínculo com o Asaas (emitida antes da sincronização).'}

    from asaas_integration.client import AsaasClient

    try:
        client = AsaasClient(api_key=api_key, sandbox=sandbox)
        inv = client.get_invoice(nfse.asaas_invoice_id.strip())
    except Exception as e:
        logger.warning('sincronizar_nfse_via_api_asaas: %s', e, exc_info=True)
        return {'error': str(e)}

    aplicar_objeto_invoice_asaas_em_nfse(nfse, inv, '')
    nfse.refresh_from_db()
    return {'ok': True}
