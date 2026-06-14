"""
Views para configuração de NFS-e do Superadmin.
GET/PATCH /api/asaas/nfse-config/
POST /api/asaas/nfse-config/test-nacional/
"""
import os
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from superadmin.views.permissions import IsSuperAdmin

logger = logging.getLogger(__name__)


def _parse_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() in ('true', '1', 'yes', 'on')


def _serialize_nfse_config(config) -> dict:
    return {
        'provedor_nfse': config.provedor_nfse,
        'emitir_automaticamente': config.emitir_automaticamente,
        'prestador_cnpj': config.prestador_cnpj,
        'prestador_razao_social': config.prestador_razao_social,
        'prestador_inscricao_municipal': config.prestador_inscricao_municipal,
        'prestador_email': config.prestador_email,
        'regime_especial_tributacao': config.regime_especial_tributacao,
        'codigo_servico_municipal': config.codigo_servico_municipal,
        'descricao_servico_padrao': config.descricao_servico_padrao,
        'aliquota_iss': str(config.aliquota_iss),
        'codigo_cnae': config.codigo_cnae,
        'optante_simples_nacional': config.optante_simples_nacional,
        'incentivador_cultural': config.incentivador_cultural,
        'issnet_usuario': config.issnet_usuario or '',
        'issnet_senha_set': bool((config.issnet_senha or '').strip()),
        'issnet_certificado_nome': config.issnet_certificado_nome or '',
        'issnet_certificado_set': bool(config.issnet_certificado),
        'issnet_senha_certificado_set': bool((config.issnet_senha_certificado or '').strip()),
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


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def nfse_config_view(request):
    """GET: retorna config. PATCH: atualiza config."""
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()

    if request.method == 'GET':
        return Response(_serialize_nfse_config(config))

    # PATCH
    data = request.data
    update_fields = ['updated_at']
    from core.encryption import encrypt_value

    # Campos simples
    simple_fields = [
        'provedor_nfse', 'emitir_automaticamente', 'prestador_cnpj',
        'prestador_razao_social', 'prestador_inscricao_municipal',
        'prestador_email', 'regime_especial_tributacao',
        'codigo_servico_municipal', 'descricao_servico_padrao',
        'codigo_cnae', 'optante_simples_nacional', 'incentivador_cultural',
        'nacional_ambiente', 'nacional_codigo_municipio',
        'nacional_serie_dps', 'nacional_ultimo_dps',
        'issnet_usuario', 'serie_rps', 'ultimo_rps',
    ]
    for field in simple_fields:
        if field not in data:
            continue
        val = data[field]
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

    # Alíquota ISS
    if 'aliquota_iss' in data:
        from decimal import Decimal
        config.aliquota_iss = Decimal(str(data['aliquota_iss']))
        update_fields.append('aliquota_iss')

    # Certificado Nacional (upload via multipart)
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

    # Senha certificado Nacional
    if data.get('nacional_senha_certificado'):
        config.nacional_senha_certificado = encrypt_value(str(data['nacional_senha_certificado']))
        update_fields.append('nacional_senha_certificado')

    # Certificado ISSNet (upload via multipart)
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

    if data.get('issnet_senha'):
        config.issnet_senha = encrypt_value(str(data['issnet_senha']))
        update_fields.append('issnet_senha')

    if data.get('issnet_senha_certificado'):
        config.issnet_senha_certificado = encrypt_value(str(data['issnet_senha_certificado']))
        update_fields.append('issnet_senha_certificado')

    config.save(using='default', update_fields=list(dict.fromkeys(update_fields)))
    config.refresh_from_db(using='default')

    logger.info(
        'NFS-e config salva por %s: campos=%s provedor=%s',
        getattr(request.user, 'username', '?'),
        [f for f in update_fields if f != 'updated_at'],
        config.provedor_nfse,
    )

    return Response({
        'success': True,
        'message': 'Configuração salva',
        **_serialize_nfse_config(config),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def nfse_config_test_nacional(request):
    """Testa conexão com o provedor configurado (ISSNet ou ADN Nacional)."""
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()

    cert_data = config.issnet_certificado or config.nacional_certificado
    from core.encryption import decrypt_value
    senha_cert = decrypt_value(
        config.issnet_senha_certificado or config.nacional_senha_certificado or ''
    )

    if not cert_data:
        return Response({'success': False, 'detail': 'Certificado não configurado'}, status=400)
    if not senha_cert:
        return Response({'success': False, 'detail': 'Senha do certificado não configurada'}, status=400)

    try:
        # Rotear teste conforme provedor
        if config.provedor_nfse == 'issnet':
            from nfse_integration.issnet_client import testar_conexao_issnet

            resultado = testar_conexao_issnet(
                usuario=config.issnet_usuario or '',
                senha=decrypt_value(config.issnet_senha or ''),
                certificado_path='',  # Não usado diretamente — vamos testar via bytes
                senha_certificado=senha_cert,
                ambiente=config.nacional_ambiente or 'producao',
            )
            # Se não tem path de certificado, testar manualmente
            if not resultado.get('success') and 'nao encontrado' in (resultado.get('detail') or '').lower():
                # Salvar cert temporário e testar
                import tempfile, os
                cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx', prefix='issnet_test_')
                cert_tmp.write(bytes(cert_data))
                cert_tmp.close()
                try:
                    resultado = testar_conexao_issnet(
                        usuario=config.issnet_usuario or '',
                        senha=decrypt_value(config.issnet_senha or ''),
                        certificado_path=cert_tmp.name,
                        senha_certificado=senha_cert,
                        ambiente=config.nacional_ambiente or 'producao',
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
