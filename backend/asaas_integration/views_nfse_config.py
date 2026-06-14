"""
Views para configuração de NFS-e do Superadmin.
GET/PATCH/POST /api/asaas/nfse-config/
POST /api/asaas/nfse-config/test-nacional/
"""
import os
import logging

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from superadmin.views.permissions import IsSuperAdmin

logger = logging.getLogger(__name__)


def _parse_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() in ('true', '1', 'yes', 'on')


def _data_get(data, key, default=''):
    """Extrai valor único de dict ou QueryDict (multipart)."""
    if not hasattr(data, 'get'):
        return default
    if key not in data:
        return default
    val = data.get(key, default)
    if isinstance(val, (list, tuple)):
        val = val[0] if val else default
    if val is None:
        return default
    return val


def _read_issnet_usuario(raw: str) -> str:
    from core.encryption import decrypt_value, is_encrypted

    value = (raw or '').strip()
    if not value:
        return ''
    if is_encrypted(value):
        decrypted = decrypt_value(value)
        return decrypted or value
    return value


def _serialize_nfse_config(config) -> dict:
    issnet_usuario = _read_issnet_usuario(config.issnet_usuario or '')
    issnet_senha_raw = (config.issnet_senha or '').strip()
    issnet_senha_cert_raw = (config.issnet_senha_certificado or '').strip()

    return {
        'provedor_nfse': config.provedor_nfse,
        'emitir_automaticamente': config.emitir_automaticamente,
        'prestador_cnpj': config.prestador_cnpj,
        'prestador_razao_social': config.prestador_razao_social,
        'prestador_inscricao_municipal': config.prestador_inscricao_municipal,
        'prestador_email': config.prestador_email,
        'regime_especial_tributacao': config.regime_especial_tributacao,
        'codigo_servico_municipal': config.codigo_servico_municipal,
        'item_lista_servico': getattr(config, 'item_lista_servico', '') or '14.01',
        'codigo_tributacao_municipio': getattr(config, 'codigo_tributacao_municipio', '') or '',
        'descricao_servico_padrao': config.descricao_servico_padrao,
        'aliquota_iss': str(config.aliquota_iss),
        'codigo_cnae': config.codigo_cnae,
        'optante_simples_nacional': config.optante_simples_nacional,
        'incentivador_cultural': config.incentivador_cultural,
        'issnet_usuario': issnet_usuario,
        'issnet_senha_set': bool(issnet_senha_raw),
        'issnet_certificado_nome': config.issnet_certificado_nome or '',
        'issnet_certificado_set': bool(config.issnet_certificado),
        'issnet_senha_certificado_set': bool(issnet_senha_cert_raw),
        'serie_rps': config.serie_rps or 'E',
        'ultimo_rps': int(config.ultimo_rps or 0),
        'nacional_certificado_nome': config.nacional_certificado_nome,
        'nacional_certificado_set': bool(config.nacional_certificado),
        'nacional_senha_certificado_set': bool(config.nacional_senha_certificado),
        'nacional_ambiente': config.nacional_ambiente,
        'nacional_codigo_municipio': config.nacional_codigo_municipio,
        'nacional_serie_dps': config.nacional_serie_dps,
        'nacional_ultimo_dps': config.nacional_ultimo_dps,
    }


def _apply_nfse_config_update(request, config):
    """Aplica PATCH/POST no singleton de config NFS-e."""
    data = request.data
    update_fields = ['updated_at']
    from core.encryption import encrypt_value

    simple_fields = [
        'provedor_nfse', 'emitir_automaticamente', 'prestador_cnpj',
        'prestador_razao_social', 'prestador_inscricao_municipal',
        'prestador_email', 'regime_especial_tributacao',
        'codigo_servico_municipal', 'descricao_servico_padrao',
        'item_lista_servico', 'codigo_tributacao_municipio',
        'codigo_cnae', 'optante_simples_nacional', 'incentivador_cultural',
        'nacional_ambiente', 'nacional_codigo_municipio',
        'nacional_serie_dps', 'nacional_ultimo_dps',
        'serie_rps', 'ultimo_rps', 'issnet_usuario',
    ]
    for field in simple_fields:
        if field not in data:
            continue
        val = _data_get(data, field)
        if field in ('emitir_automaticamente', 'optante_simples_nacional', 'incentivador_cultural'):
            val = _parse_bool(val)
        elif field in ('nacional_ultimo_dps', 'ultimo_rps'):
            val = int(val) if val not in (None, '') else 0
            if field == 'nacional_ultimo_dps':
                config.nacional_ultimo_dps = val
                update_fields.append('nacional_ultimo_dps')
                config.ultimo_rps = max(int(config.ultimo_rps or 0), val)
                update_fields.append('ultimo_rps')
                continue
            config.ultimo_rps = val
            update_fields.append('ultimo_rps')
            continue
        setattr(config, field, val)
        update_fields.append(field)

    if 'aliquota_iss' in data:
        from decimal import Decimal
        config.aliquota_iss = Decimal(str(_data_get(data, 'aliquota_iss')))
        update_fields.append('aliquota_iss')

    cert_file = request.FILES.get('nacional_certificado')
    if cert_file:
        ext = os.path.splitext(cert_file.name)[1].lower()
        if ext not in ('.pfx', '.p12'):
            return Response({'error': 'Formato inválido. Envie .pfx ou .p12'}, status=status.HTTP_400_BAD_REQUEST)
        if cert_file.size > 5 * 1024 * 1024:
            return Response({'error': 'Certificado muito grande (máx 5MB)'}, status=status.HTTP_400_BAD_REQUEST)
        config.nacional_certificado = cert_file.read()
        config.nacional_certificado_nome = cert_file.name[:255]
        update_fields.extend(['nacional_certificado', 'nacional_certificado_nome'])

    nacional_senha_cert = str(_data_get(data, 'nacional_senha_certificado', '')).strip()
    if nacional_senha_cert:
        config.nacional_senha_certificado = encrypt_value(nacional_senha_cert)
        update_fields.append('nacional_senha_certificado')

    issnet_cert_file = request.FILES.get('issnet_certificado')
    if issnet_cert_file:
        ext = os.path.splitext(issnet_cert_file.name)[1].lower()
        if ext not in ('.pfx', '.p12'):
            return Response({'error': 'Formato inválido. Envie .pfx ou .p12'}, status=status.HTTP_400_BAD_REQUEST)
        if issnet_cert_file.size > 5 * 1024 * 1024:
            return Response({'error': 'Certificado muito grande (máx 5MB)'}, status=status.HTTP_400_BAD_REQUEST)
        config.issnet_certificado = issnet_cert_file.read()
        config.issnet_certificado_nome = issnet_cert_file.name[:255]
        update_fields.extend(['issnet_certificado', 'issnet_certificado_nome'])

    issnet_senha = str(_data_get(data, 'issnet_senha', '')).strip()
    if issnet_senha:
        config.issnet_senha = encrypt_value(issnet_senha)
        update_fields.append('issnet_senha')

    issnet_senha_cert = str(_data_get(data, 'issnet_senha_certificado', '')).strip()
    if issnet_senha_cert:
        config.issnet_senha_certificado = encrypt_value(issnet_senha_cert)
        update_fields.append('issnet_senha_certificado')

    saved_fields = [f for f in update_fields if f != 'updated_at']
    if not saved_fields:
        logger.warning(
            'NFS-e config PATCH sem campos por %s content_type=%s files=%s keys=%s',
            getattr(request.user, 'username', '?'),
            request.content_type,
            list(request.FILES.keys()),
            list(data.keys()) if hasattr(data, 'keys') else [],
        )
        return Response(
            {
                'error': 'Nenhum dado recebido. Recarregue a página e tente salvar novamente.',
                'detail': 'O servidor não interpretou os campos enviados (multipart).',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    needs_full_save = any(
        f in saved_fields
        for f in (
            'issnet_certificado', 'issnet_certificado_nome',
            'nacional_certificado', 'nacional_certificado_nome',
            'issnet_senha', 'issnet_senha_certificado',
            'nacional_senha_certificado',
        )
    )
    if needs_full_save:
        config.save(using='default')
    else:
        config.save(using='default', update_fields=list(dict.fromkeys(update_fields)))
    config.refresh_from_db(using='default')

    logger.info(
        'NFS-e config salva por %s: campos=%s provedor=%s issnet_usuario=%s cert=%s',
        getattr(request.user, 'username', '?'),
        saved_fields,
        config.provedor_nfse,
        bool(config.issnet_usuario),
        bool(config.issnet_certificado),
    )

    return Response({
        'success': True,
        'message': 'Configuração salva',
        **_serialize_nfse_config(config),
    })


@api_view(['GET', 'PATCH', 'POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def nfse_config_view(request):
    """GET: retorna config. PATCH/POST: atualiza config (POST recomendado com multipart)."""
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()

    if request.method == 'GET':
        return Response(_serialize_nfse_config(config))

    return _apply_nfse_config_update(request, config)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def nfse_config_test_nacional(request):
    """Testa conexão com o provedor configurado (ISSNet ou ADN Nacional)."""
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()
    data = request.data

    cert_file = request.FILES.get('issnet_certificado') or request.FILES.get('nacional_certificado')
    if cert_file:
        cert_data = cert_file.read()
    else:
        cert_data = config.issnet_certificado or config.nacional_certificado

    from core.encryption import decrypt_value

    senha_cert_raw = str(_data_get(data, 'issnet_senha_certificado', '')).strip()
    if not senha_cert_raw:
        senha_cert_raw = str(_data_get(data, 'nacional_senha_certificado', '')).strip()
    if senha_cert_raw:
        senha_cert = senha_cert_raw
    else:
        senha_cert = decrypt_value(
            config.issnet_senha_certificado or config.nacional_senha_certificado or ''
        )

    if not cert_data:
        return Response({'success': False, 'detail': 'Certificado não configurado'}, status=400)
    if not senha_cert:
        return Response({'success': False, 'detail': 'Senha do certificado não configurada'}, status=400)

    try:
        if config.provedor_nfse == 'issnet':
            from nfse_integration.issnet_client import testar_conexao_issnet

            usuario = str(_data_get(data, 'issnet_usuario', '')).strip()
            if not usuario:
                usuario = decrypt_value(config.issnet_usuario or '')

            senha_ws = str(_data_get(data, 'issnet_senha', '')).strip()
            if not senha_ws:
                senha_ws = decrypt_value(config.issnet_senha or '')

            ambiente = str(_data_get(data, 'nacional_ambiente', '')).strip() or config.nacional_ambiente or 'producao'

            import tempfile
            import os

            cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx', prefix='issnet_test_')
            cert_tmp.write(bytes(cert_data))
            cert_tmp.close()
            try:
                resultado = testar_conexao_issnet(
                    usuario=usuario,
                    senha=senha_ws,
                    certificado_path=cert_tmp.name,
                    senha_certificado=senha_cert,
                    ambiente=ambiente,
                )
            finally:
                if os.path.isfile(cert_tmp.name):
                    os.unlink(cert_tmp.name)
        else:
            from nfse_integration.nacional import NacionalClient

            client = NacionalClient(
                pfx_bytes=bytes(cert_data),
                senha_pfx=senha_cert,
                ambiente=config.nacional_ambiente or 'homologacao',
            )
            resultado = client.testar_conexao()

        if resultado.get('success'):
            cert_info = {}
            try:
                from nfse_integration.nacional.xml_signer import carregar_certificado_bytes
                _, cert_obj, _ = carregar_certificado_bytes(
                    bytes(config.nacional_certificado),
                    config.nacional_senha_certificado,
                )
                cert_info['subject'] = cert_obj.subject.rfc4514_string()[:300]
                cert_info['valid_to'] = cert_obj.not_valid_after_utc.isoformat()
            except Exception:
                pass

            return Response({
                'success': True,
                'message': resultado.get('message', 'Conexão ADN Nacional OK'),
                'certificado_subject': cert_info.get('subject', ''),
                'certificado_validade': cert_info.get('valid_to', ''),
                'ambiente': config.nacional_ambiente,
            })
        return Response({'success': False, 'detail': resultado.get('detail', 'Falha no teste')}, status=400)

    except Exception as e:
        logger.exception('Erro ao testar Nacional superadmin: %s', e)
        return Response({'success': False, 'detail': str(e)}, status=400)
