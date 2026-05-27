"""Cancelamento de NFS-e no contexto da loja (CRM)."""
import logging
import re
from typing import Any

from django.utils import timezone

from nfse_integration.email_nfse import notificar_cancelamento_nfse
from nfse_integration.issnet_loja import certificado_configurado_loja, issnet_client_loja
from nfse_integration.issnet_shared import CODIGOS_CANCELAMENTO, normalizar_codigo_cancelamento
from nfse_integration.issnet_status_sync import consultar_nfse_cancelada_issnet

logger = logging.getLogger(__name__)


def _marcar_cancelada_loja(nfse: Any) -> None:
    nfse.status = 'cancelada'
    nfse.data_cancelamento = timezone.now()
    nfse.save(update_fields=['status', 'data_cancelamento', 'updated_at'])


def cancelar_nfse_loja(
    loja: Any,
    config: Any,
    nfse: Any,
    numero_nf: str,
    motivo: str,
    codigo_cancelamento: str | int | None = '1',
) -> dict[str, Any]:
    """Cancela NFS-e no ISSNet (quando aplicável) e atualiza status local."""
    if not nfse.pode_cancelar():
        return {'success': False, 'error': 'Esta NFS-e não pode ser cancelada'}

    provedor = (nfse.provedor or getattr(config, 'provedor_nf', '') or '').lower()
    if provedor == 'asaas':
        return {
            'success': False,
            'error': 'NFS-e emitida via Asaas: cancele no painel Asaas e use «Sincronizar».',
        }

    codigo = normalizar_codigo_cancelamento(codigo_cancelamento)
    motivo_final = motivo or CODIGOS_CANCELAMENTO[codigo]

    if provedor == 'issnet' and numero_nf and not str(numero_nf).startswith('FALHA-'):
        if not certificado_configurado_loja(config):
            _marcar_cancelada_loja(nfse)
            return {
                'success': True,
                'message': (
                    'NFS-e cancelada no sistema '
                    '(certificado não configurado para cancelar no portal).'
                ),
            }

        cnpj_prestador = re.sub(r'\D', '', loja.cpf_cnpj or '')
        im_prestador = (
            getattr(config, 'inscricao_municipal', '')
            or getattr(loja, 'inscricao_municipal', '')
            or ''
        )
        serie = getattr(config, 'issnet_serie_rps', '1') or '1'
        numero_rps = int(nfse.numero_rps) if nfse.numero_rps else None

        try:
            with issnet_client_loja(config) as client:
                resultado = client.cancelar_nfse(
                    numero_nf=numero_nf,
                    motivo=motivo_final,
                    prestador_cnpj=cnpj_prestador,
                    inscricao_municipal=im_prestador,
                    codigo_cancelamento=codigo,
                )
                if resultado.get('success'):
                    _marcar_cancelada_loja(nfse)
                    try:
                        notificar_cancelamento_nfse(
                            nfse=nfse,
                            loja=loja,
                            loja_id=getattr(loja, 'id', None),
                            config=config,
                        )
                    except Exception as exc:
                        logger.warning('Falha ao enviar email de cancelamento: %s', exc)
                    return {'success': True, 'message': 'NFS-e cancelada com sucesso'}

                if consultar_nfse_cancelada_issnet(
                    client,
                    numero_nf=str(numero_nf),
                    numero_rps=numero_rps,
                    serie_rps=str(serie),
                    prestador_cnpj=cnpj_prestador,
                    inscricao_municipal=im_prestador,
                ):
                    _marcar_cancelada_loja(nfse)
                    try:
                        notificar_cancelamento_nfse(
                            nfse=nfse,
                            loja=loja,
                            loja_id=getattr(loja, 'id', None),
                            config=config,
                        )
                    except Exception as exc:
                        logger.warning('Falha ao enviar email de cancelamento: %s', exc)
                    return {
                        'success': True,
                        'message': (
                            'NFS-e cancelada no ISSNet. O status foi sincronizado '
                            '(a prefeitura confirmou o cancelamento).'
                        ),
                    }

            return {
                'success': False,
                'error': resultado.get('error', 'Erro ao cancelar no ISSNet'),
            }
        except Exception as exc:
            logger.exception('Erro ao cancelar NFS-e via ISSNet: %s', exc)
            return {'success': False, 'error': str(exc)}

    _marcar_cancelada_loja(nfse)
    return {'success': True, 'message': 'NFS-e marcada como cancelada'}
