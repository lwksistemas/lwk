"""Ações de NFS-e no contexto da loja (CRM / ViewSet)."""
import logging
from decimal import Decimal
from typing import Any

from rest_framework import status

logger = logging.getLogger(__name__)


class ConfigLojaInconsistenteError(ValueError):
    """CRMConfig não pertence à loja informada."""


class ReenvioNFSeLojaError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExclusaoNFSeLojaError(Exception):
    def __init__(self, message: str, http_status: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.http_status = http_status
        super().__init__(message)


def validar_config_crm_loja(loja: Any, config: Any) -> None:
    """Garante que a CRMConfig carregada é da mesma loja do serviço."""
    config_loja_id = getattr(config, 'loja_id', None)
    if config_loja_id is not None and int(config_loja_id) != int(loja.id):
        raise ConfigLojaInconsistenteError(
            f'CRMConfig loja_id={config_loja_id} não corresponde à loja {loja.id}'
        )


def provedor_nf_loja(config: Any) -> str:
    return (getattr(config, 'provedor_nf', None) or 'issnet').strip().lower()


def enviar_email_pos_emissao_loja(
    loja: Any,
    config: Any,
    *,
    numero_nf: str,
    tomador_email: str,
    tomador_nome: str,
    valor: Decimal,
    descricao: str,
    fail_silently: bool = True,
) -> None:
    """E-mail ao tomador após emissão (inclui DANFE ISSNet quando aplicável)."""
    from nfse_integration.danfe import buscar_url_danfe_issnet
    from nfse_integration.email_nfse import enviar_email_nfse_tomador
    from nfse_integration.models import NFSe

    nfse_obj = (
        NFSe.objects.filter(loja_id=loja.id, numero_nf=numero_nf)
        .order_by('-data_emissao')
        .first()
    )
    url_danfe = ''
    if provedor_nf_loja(config) == 'issnet':
        url_danfe = buscar_url_danfe_issnet(
            nfse_obj,
            numero_nf=numero_nf,
            loja_id=loja.id,
            loja=loja,
            config=config,
        )

    enviar_email_nfse_tomador(
        loja=loja,
        tomador_email=tomador_email,
        tomador_nome=tomador_nome,
        numero_nf=numero_nf,
        valor=valor,
        descricao=descricao,
        url_danfe=url_danfe,
        xml_content=nfse_obj.xml_nfse if nfse_obj and nfse_obj.xml_nfse else '',
        fail_silently=fail_silently,
        intro='A nota fiscal de serviço foi emitida.',
        incluir_codigo_verificacao=False,
        xml_filename=f'nfse_{numero_nf[:20]}.xml',
    )


def reenviar_email_nfse_loja(nfse: Any, loja: Any, loja_id: int) -> str:
    """Reenvia e-mail da NFS-e ao tomador (formato loja/CRM). Retorna o e-mail enviado."""
    from nfse_integration.danfe import buscar_url_danfe_issnet
    from nfse_integration.email_nfse import enviar_email_nfse_tomador

    if not nfse.tomador_email:
        raise ReenvioNFSeLojaError('NFS-e não possui email do tomador')

    url_danfe = buscar_url_danfe_issnet(nfse, loja_id=loja_id, loja=loja)
    enviar_email_nfse_tomador(
        loja=loja,
        tomador_email=nfse.tomador_email,
        tomador_nome=nfse.tomador_nome,
        numero_nf=nfse.numero_nf,
        valor=nfse.valor,
        descricao=nfse.servico_descricao,
        url_danfe=url_danfe,
        codigo_verificacao=nfse.codigo_verificacao,
        xml_content=nfse.xml_nfse or nfse.xml_rps or '',
        fail_silently=False,
    )
    return nfse.tomador_email


def validar_exclusao_nfse_loja(nfse: Any) -> None:
    """Levanta ExclusaoNFSeLojaError se a nota não puder ser excluída."""
    if nfse.status == 'emitida':
        raise ExclusaoNFSeLojaError(
            'Nota fiscal emitida não pode ser excluída. Use a opção Cancelar.'
        )
    if nfse.status == 'cancelada':
        raise ExclusaoNFSeLojaError(
            'Nota fiscal cancelada não pode ser excluída (manter para histórico).'
        )


def xml_nfse_conteudo(nfse: Any) -> str:
    return nfse.xml_nfse or nfse.xml_rps or ''


def sincronizar_nfse_asaas_loja(nfse: Any, loja_id: int) -> tuple[dict[str, Any], int]:
    """Consulta invoice no Asaas e atualiza o registro local."""
    from rest_framework import status as http_status

    from crm_vendas.models import CRMConfig
    from nfse_integration.asaas_webhook_sync import sincronizar_nfse_via_api_asaas
    from nfse_integration.serializers import NFSeSerializer

    if nfse.provedor != 'asaas':
        return (
            {'error': 'Sincronização disponível apenas para NFS-e emitidas via Asaas.'},
            http_status.HTTP_400_BAD_REQUEST,
        )

    cfg = CRMConfig.get_or_create_for_loja(loja_id)
    api_key = (getattr(cfg, 'asaas_api_key', None) or '').strip()
    if not api_key:
        return (
            {
                'error': (
                    'Configure a API Key do Asaas em Configurações → Nota Fiscal '
                    '(CRM) para sincronizar.'
                ),
            },
            http_status.HTTP_400_BAD_REQUEST,
        )

    out = sincronizar_nfse_via_api_asaas(
        nfse,
        api_key=api_key,
        sandbox=bool(getattr(cfg, 'asaas_sandbox', False)),
    )
    if out.get('error'):
        return {'error': out['error']}, http_status.HTTP_400_BAD_REQUEST

    nfse.refresh_from_db()
    return (
        {
            'success': True,
            'message': 'Status atualizado conforme o Asaas.',
            'nfse': NFSeSerializer(nfse).data,
        },
        http_status.HTTP_200_OK,
    )


def sincronizar_nfse_issnet_loja(nfse: Any, loja: Any, loja_id: int) -> tuple[dict[str, Any], int]:
    """Consulta o ISSNet e atualiza status local (ex.: cancelada no portal)."""
    from rest_framework import status as http_status

    from crm_vendas.models import CRMConfig
    from nfse_integration.issnet_loja import issnet_client_loja
    from nfse_integration.serializers import NFSeSerializer

    cfg = CRMConfig.get_or_create_for_loja(loja_id)
    cfg_provedor = (getattr(cfg, 'provedor_nf', '') or '').strip().lower()
    nf_provedor = (nfse.provedor or '').strip().lower()
    if nf_provedor != 'issnet' and cfg_provedor != 'issnet':
        return (
            {'error': 'Sincronização disponível apenas para NFS-e emitidas via ISSNet.'},
            http_status.HTTP_400_BAD_REQUEST,
        )

    if not nfse.numero_rps:
        return (
            {'error': 'NFS-e não possui número de RPS para consulta no ISSNet.'},
            http_status.HTTP_400_BAD_REQUEST,
        )
    serie = getattr(cfg, 'issnet_serie_rps', '1') or '1'
    cnpj_prestador = getattr(loja, 'cpf_cnpj', '') or ''
    im_prestador = (
        getattr(cfg, 'inscricao_municipal', '')
        or getattr(loja, 'inscricao_municipal', '')
        or ''
    )

    try:
        with issnet_client_loja(cfg) as client:
            out = client.consultar_nfse_por_rps(
                numero_rps=int(nfse.numero_rps),
                serie_rps=str(serie),
                prestador_cnpj=str(cnpj_prestador),
                inscricao_municipal=str(im_prestador),
            )
    except Exception as exc:
        return ({'error': str(exc)}, http_status.HTTP_400_BAD_REQUEST)

    if out.get('success') is False:
        # Fallback: quando a prefeitura rejeita o ConsultarNfsePorRps por schema (E160/E183),
        # mas a nota existe e o portal já indica "cancelada", tentar via URL oficial.
        err = str(out.get('error') or '')
        if (
            ('E160' in err or 'E183' in err or 'XML Schema' in err)
            and getattr(nfse, 'numero_nf', None)
        ):
            try:
                with issnet_client_loja(cfg) as client2:
                    url_out = client2.consultar_url_nfse(
                        numero_nf=str(nfse.numero_nf),
                        prestador_cnpj=str(cnpj_prestador),
                        inscricao_municipal=str(im_prestador),
                    )
                    if url_out.get('success') and url_out.get('url'):
                        ver = client2.inferir_cancelada_por_url(url=str(url_out['url']))
                        if ver.get('success') and ver.get('cancelada'):
                            from django.utils import timezone

                            if nfse.status != 'cancelada':
                                nfse.status = 'cancelada'
                                nfse.data_cancelamento = nfse.data_cancelamento or timezone.now()
                                nfse.save(update_fields=['status', 'data_cancelamento', 'updated_at'])
                            nfse.refresh_from_db()
                            return (
                                {
                                    'success': True,
                                    'message': 'NFS-e marcada como cancelada conforme o portal ISSNet.',
                                    'nfse': NFSeSerializer(nfse).data,
                                },
                                http_status.HTTP_200_OK,
                            )
            except Exception:
                pass

        return ({'error': out.get('error', 'Erro ao consultar ISSNet')}, http_status.HTTP_400_BAD_REQUEST)

    if out.get('cancelada'):
        if nfse.status != 'cancelada':
            from django.utils import timezone

            nfse.status = 'cancelada'
            nfse.data_cancelamento = nfse.data_cancelamento or timezone.now()
            nfse.save(update_fields=['status', 'data_cancelamento', 'updated_at'])
            message = 'NFS-e marcada como cancelada conforme o ISSNet.'
            # Se a nota foi cancelada fora do fluxo (ex.: no portal), avisar o tomador automaticamente.
            if getattr(nfse, 'tomador_email', None):
                try:
                    from nfse_integration.danfe import buscar_url_danfe_issnet
                    from nfse_integration.email_nfse import enviar_email_nfse_cancelada_tomador

                    url_danfe = buscar_url_danfe_issnet(nfse, loja_id=loja_id, loja=loja, config=cfg)
                    enviar_email_nfse_cancelada_tomador(
                        loja=loja,
                        tomador_email=nfse.tomador_email,
                        tomador_nome=getattr(nfse, 'tomador_nome', '') or 'Cliente',
                        numero_nf=str(nfse.numero_nf or ''),
                        valor=getattr(nfse, 'valor', 0) or 0,
                        descricao=getattr(nfse, 'servico_descricao', '') or '',
                        url_danfe=url_danfe,
                        xml_content=xml_nfse_conteudo(nfse),
                        fail_silently=True,
                    )
                except Exception:
                    pass
        else:
            message = 'NFS-e já constava como cancelada no sistema.'
    else:
        message = 'ISSNet indica nota ainda emitida; nenhuma alteração no CRM.'

    nfse.refresh_from_db()
    return (
        {
            'success': True,
            'message': message,
            'nfse': NFSeSerializer(nfse).data,
        },
        http_status.HTTP_200_OK,
    )


def processar_cancelamento_nfse_loja(
    loja: Any,
    nfse: Any,
    motivo: str,
    codigo_cancelamento: str | int | None = '1',
) -> tuple[dict[str, Any], int]:
    """Cancela NFS-e via NFSeService. Retorna (body, status HTTP)."""
    from rest_framework import status as http_status

    from nfse_integration.service import NFSeService

    if not nfse.pode_cancelar():
        return (
            {'error': 'Esta NFS-e não pode ser cancelada'},
            http_status.HTTP_400_BAD_REQUEST,
        )

    service = NFSeService(loja)
    resultado = service.cancelar_nfse(
        numero_nf=nfse.numero_nf,
        motivo=motivo,
        codigo_cancelamento=codigo_cancelamento,
    )
    if resultado.get('success'):
        nfse.refresh_from_db()
        from nfse_integration.serializers import NFSeSerializer

        return (
            {
                'success': True,
                'message': resultado.get('message', 'NFS-e cancelada com sucesso'),
                'nfse': NFSeSerializer(nfse).data,
            },
            http_status.HTTP_200_OK,
        )
    return (
        {'success': False, 'error': resultado.get('error', 'Erro desconhecido')},
        http_status.HTTP_400_BAD_REQUEST,
    )


def processar_emissao_nfse_loja(
    loja: Any,
    loja_id: int,
    validated_data: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    """
    Emite NFS-e para a loja atual.
    Retorna (corpo da resposta, status HTTP).
    """
    from nfse_integration.emissao import montar_dados_tomador_nfse
    from nfse_integration.models import NFSe
    from nfse_integration.serializers import NFSeSerializer
    from nfse_integration.service import NFSeService

    tomador = montar_dados_tomador_nfse(validated_data, loja_id)
    service = NFSeService(loja)

    codigo_cnae = (validated_data.get('codigo_cnae') or '').strip() or None
    codigo_servico = (validated_data.get('codigo_servico') or '').strip() or None

    resultado = service.emitir_nfse(
        tomador_cpf_cnpj=tomador.cpf_cnpj,
        tomador_nome=tomador.nome,
        tomador_email=tomador.email,
        tomador_endereco=tomador.endereco,
        servico_descricao=validated_data['servico_descricao'],
        valor_servicos=Decimal(str(validated_data['valor_servicos'])),
        enviar_email=validated_data.get('enviar_email', True),
        codigo_cnae=codigo_cnae,
        codigo_servico=codigo_servico,
    )

    if resultado['success']:
        nfse = NFSe.objects.filter(
            loja_id=loja_id,
            numero_nf=resultado['numero_nf'],
        ).first()
        if nfse:
            body = {
                'success': True,
                'message': 'NFS-e emitida com sucesso',
                'nfse': NFSeSerializer(nfse).data,
            }
        else:
            body = {
                'success': True,
                'message': 'NFS-e emitida com sucesso',
                'numero_nf': resultado['numero_nf'],
                'codigo_verificacao': resultado.get('codigo_verificacao', ''),
            }
        return body, status.HTTP_201_CREATED

    erro_msg = resultado.get('error', 'Erro desconhecido')
    nfse_falha = service.registrar_falha_emissao(
        erro_msg=erro_msg,
        tomador_cpf_cnpj=tomador.cpf_cnpj,
        tomador_nome=tomador.nome,
        tomador_email=tomador.email,
        servico_descricao=validated_data['servico_descricao'],
        valor_servicos=Decimal(str(validated_data['valor_servicos'])),
        numero_rps=int(resultado.get('numero_rps') or 0),
    )
    body: dict[str, Any] = {'success': False, 'error': erro_msg}
    if nfse_falha:
        body['nfse'] = NFSeSerializer(nfse_falha).data
    return body, status.HTTP_400_BAD_REQUEST
