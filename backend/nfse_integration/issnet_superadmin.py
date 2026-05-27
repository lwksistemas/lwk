"""Cliente ISSNet a partir da SuperadminNFSeConfig (certificado em arquivo temporario)."""
import logging
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Generator

from django.utils import timezone

from nfse_integration.issnet_shared import CODIGOS_CANCELAMENTO, normalizar_codigo_cancelamento

logger = logging.getLogger(__name__)


def certificado_configurado(config: Any) -> bool:
    return bool(config.issnet_certificado or config.nacional_certificado)


def senha_certificado_configurada(config: Any) -> bool:
    return bool(
        config.issnet_senha_certificado or config.nacional_senha_certificado
    )


@contextmanager
def issnet_client_superadmin(
    config: Any, *, prefix: str = 'issnet_'
) -> Generator[Any, None, None]:
    """Abre ISSNetClient com certificado PFX temporario; remove o arquivo ao sair."""
    from nfse_integration.issnet_client import ISSNetClient

    cert_data = config.issnet_certificado or config.nacional_certificado
    if not cert_data:
        raise ValueError('Certificado não configurado')

    senha_cert = (
        config.issnet_senha_certificado or config.nacional_senha_certificado or ''
    )
    cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx', prefix=prefix)
    try:
        cert_tmp.write(bytes(cert_data))
        cert_tmp.close()
        client = ISSNetClient(
            usuario=config.issnet_usuario or '',
            senha=config.issnet_senha or '',
            certificado_path=cert_tmp.name,
            senha_certificado=senha_cert,
            ambiente=config.nacional_ambiente or 'producao',
        )
        yield client
    finally:
        if os.path.isfile(cert_tmp.name):
            try:
                os.unlink(cert_tmp.name)
            except OSError:
                pass


def cancelar_nfse_emitida_superadmin(
    nf: Any,
    config: Any,
    codigo_cancelamento: str | int | None,
    motivo_texto: str,
) -> dict[str, Any]:
    """
    Cancela NFSeEmitida no ISSNet (quando aplicavel) e atualiza status local.
    Retorna dict com success, message ou error.
    """
    codigo = normalizar_codigo_cancelamento(codigo_cancelamento)
    motivo_issnet = motivo_texto or CODIGOS_CANCELAMENTO[codigo]

    if nf.provedor == 'issnet' and nf.numero_nf:
        if not certificado_configurado(config):
            nf.status = 'cancelada'
            nf.data_cancelamento = timezone.now()
            nf.save()
            return {
                'success': True,
                'message': (
                    f'NFS-e {nf.numero_nf} cancelada no sistema '
                    '(certificado não configurado para cancelar no portal).'
                ),
            }

        with issnet_client_superadmin(config) as client:
            resultado = client.cancelar_nfse(
                numero_nf=nf.numero_nf,
                motivo=motivo_issnet,
                prestador_cnpj=config.prestador_cnpj or '',
                inscricao_municipal=config.prestador_inscricao_municipal or '',
                codigo_cancelamento=codigo,
            )

        if resultado.get('success'):
            nf.status = 'cancelada'
            nf.data_cancelamento = timezone.now()
            nf.save()
            return {
                'success': True,
                'message': f'NFS-e {nf.numero_nf} cancelada no ISSNet e no sistema.',
            }

        # Se o ISSNet cancelou mas o retorno veio ambíguo/erro, tentar confirmar e sincronizar.
        # (Mesma ideia aplicada no fluxo da loja.)
        try:
            with issnet_client_superadmin(config) as client:
                # 1) Tentar confirmar via RPS quando disponível
                if getattr(nf, 'numero_rps', 0):
                    serie = (getattr(nf, 'serie_rps', '') or '1').strip() or '1'
                    ver = client.consultar_nfse_por_rps(
                        numero_rps=int(nf.numero_rps),
                        serie_rps=str(serie),
                        prestador_cnpj=config.prestador_cnpj or '',
                        inscricao_municipal=config.prestador_inscricao_municipal or '',
                    )
                    if ver.get('cancelada'):
                        nf.status = 'cancelada'
                        nf.data_cancelamento = nf.data_cancelamento or timezone.now()
                        nf.save(update_fields=['status', 'data_cancelamento'])
                        return {
                            'success': True,
                            'message': (
                                f'NFS-e {nf.numero_nf} cancelada no ISSNet. '
                                'Status sincronizado após confirmação por RPS.'
                            ),
                        }

                # 2) Fallback via URL do portal (útil quando ConsultarNfsePorRps falha com E160/E183)
                url_out = client.consultar_url_nfse(
                    numero_nf=str(nf.numero_nf),
                    prestador_cnpj=config.prestador_cnpj or '',
                    inscricao_municipal=config.prestador_inscricao_municipal or '',
                )
                if url_out.get('success') and url_out.get('url'):
                    inf = client.inferir_cancelada_por_url(url=str(url_out['url']))
                    if inf.get('success') and inf.get('cancelada'):
                        nf.status = 'cancelada'
                        nf.data_cancelamento = nf.data_cancelamento or timezone.now()
                        nf.save(update_fields=['status', 'data_cancelamento'])
                        return {
                            'success': True,
                            'message': (
                                f'NFS-e {nf.numero_nf} marcada como cancelada '
                                'conforme o portal ISSNet.'
                            ),
                        }
        except Exception:
            # Não quebrar o cancelamento por falha de verificação.
            pass

        return {
            'success': False,
            'error': (
                f'Erro ao cancelar no ISSNet: '
                f'{resultado.get("error", "Erro desconhecido")}'
            ),
        }

    nf.status = 'cancelada'
    nf.data_cancelamento = timezone.now()
    nf.save()
    return {'success': True, 'message': 'NFS-e marcada como cancelada'}


def consultar_url_nfse_superadmin(nf: Any, config: Any) -> dict[str, Any]:
    """Chama ConsultarUrlNfse no ISSNet (diagnostico superadmin)."""
    with issnet_client_superadmin(config, prefix='issnet_dbg_') as client:
        return client.consultar_url_nfse(
            numero_nf=nf.numero_nf,
            prestador_cnpj=config.prestador_cnpj or '',
            inscricao_municipal=config.prestador_inscricao_municipal or '',
        )
