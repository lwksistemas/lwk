"""ISSNet no contexto superadmin (NFSeEmitida). Cliente em issnet_client_factory."""
import logging
from typing import Any

from django.utils import timezone

from nfse_integration.issnet_client_factory import issnet_client_superadmin
from nfse_integration.issnet_shared import CODIGOS_CANCELAMENTO, normalizar_codigo_cancelamento
from nfse_integration.issnet_status_sync import consultar_nfse_cancelada_issnet

logger = logging.getLogger(__name__)

__all__ = [
    'certificado_configurado',
    'senha_certificado_configurada',
    'issnet_client_superadmin',
    'cancelar_nfse_emitida_superadmin',
    'consultar_url_nfse_superadmin',
]


def certificado_configurado(config: Any) -> bool:
    return bool(config.issnet_certificado or config.nacional_certificado)


def senha_certificado_configurada(config: Any) -> bool:
    return bool(config.issnet_senha_certificado or config.nacional_senha_certificado)


def _marcar_cancelada(nf: Any) -> None:
    nf.status = 'cancelada'
    nf.data_cancelamento = nf.data_cancelamento or timezone.now()
    nf.save(update_fields=['status', 'data_cancelamento'])


def cancelar_nfse_emitida_superadmin(
    nf: Any,
    config: Any,
    codigo_cancelamento: str | int | None,
    motivo_texto: str,
) -> dict[str, Any]:
    """Cancela NFSeEmitida no ISSNet (quando aplicável) e atualiza status local."""
    codigo = normalizar_codigo_cancelamento(codigo_cancelamento)
    motivo_issnet = motivo_texto or CODIGOS_CANCELAMENTO[codigo]

    if nf.provedor == 'issnet' and nf.numero_nf:
        if not certificado_configurado(config):
            _marcar_cancelada(nf)
            return {
                'success': True,
                'message': (
                    f'NFS-e {nf.numero_nf} cancelada no sistema '
                    '(certificado não configurado para cancelar no portal).'
                ),
            }

        cnpj = config.prestador_cnpj or ''
        im = config.prestador_inscricao_municipal or ''
        serie = (getattr(nf, 'serie_rps', '') or '1').strip() or '1'
        numero_rps = int(nf.numero_rps) if getattr(nf, 'numero_rps', 0) else None

        try:
            with issnet_client_superadmin(config) as client:
                resultado = client.cancelar_nfse(
                    numero_nf=nf.numero_nf,
                    motivo=motivo_issnet,
                    prestador_cnpj=cnpj,
                    inscricao_municipal=im,
                    codigo_cancelamento=codigo,
                )
                if resultado.get('success'):
                    _marcar_cancelada(nf)
                    return {
                        'success': True,
                        'message': f'NFS-e {nf.numero_nf} cancelada no ISSNet e no sistema.',
                    }

                if consultar_nfse_cancelada_issnet(
                    client,
                    numero_nf=str(nf.numero_nf),
                    numero_rps=numero_rps,
                    serie_rps=serie,
                    prestador_cnpj=cnpj,
                    inscricao_municipal=im,
                ):
                    _marcar_cancelada(nf)
                    return {
                        'success': True,
                        'message': (
                            f'NFS-e {nf.numero_nf} cancelada no ISSNet. '
                            'Status sincronizado com o portal.'
                        ),
                    }

                return {
                    'success': False,
                    'error': (
                        f'Erro ao cancelar no ISSNet: '
                        f'{resultado.get("error", "Erro desconhecido")}'
                    ),
                }
        except Exception as exc:
            logger.exception('Erro ao cancelar NFS-e superadmin via ISSNet: %s', exc)
            return {'success': False, 'error': str(exc)}

    _marcar_cancelada(nf)
    return {'success': True, 'message': 'NFS-e marcada como cancelada'}


def consultar_url_nfse_superadmin(nf: Any, config: Any) -> dict[str, Any]:
    """Chama ConsultarUrlNfse no ISSNet (diagnóstico superadmin)."""
    with issnet_client_superadmin(config, prefix='issnet_dbg_') as client:
        return client.consultar_url_nfse(
            numero_nf=nf.numero_nf,
            prestador_cnpj=config.prestador_cnpj or '',
            inscricao_municipal=config.prestador_inscricao_municipal or '',
        )
