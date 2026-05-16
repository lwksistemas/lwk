"""
Views para configuração de NFS-e do Superadmin.
GET/PATCH /api/superadmin/nfse-config/
POST /api/superadmin/nfse-config/test-nacional/
"""
import os
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def nfse_config_view(request):
    """GET: retorna config. PATCH: atualiza config."""
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()

    if request.method == 'GET':
        return Response({
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
            # Nacional
            'nacional_certificado_nome': config.nacional_certificado_nome,
            'nacional_certificado_set': bool(config.nacional_certificado),
            'nacional_senha_certificado_set': bool(config.nacional_senha_certificado),
            'nacional_ambiente': config.nacional_ambiente,
            'nacional_codigo_municipio': config.nacional_codigo_municipio,
            'nacional_serie_dps': config.nacional_serie_dps,
            'nacional_ultimo_dps': config.nacional_ultimo_dps,
        })

    # PATCH
    data = request.data
    update_fields = ['updated_at']

    # Campos simples
    simple_fields = [
        'provedor_nfse', 'emitir_automaticamente', 'prestador_cnpj',
        'prestador_razao_social', 'prestador_inscricao_municipal',
        'prestador_email', 'regime_especial_tributacao',
        'codigo_servico_municipal', 'descricao_servico_padrao',
        'codigo_cnae', 'optante_simples_nacional', 'incentivador_cultural',
        'nacional_ambiente', 'nacional_codigo_municipio',
        'nacional_serie_dps', 'nacional_ultimo_dps',
    ]
    for field in simple_fields:
        if field in data:
            val = data[field]
            if field in ('emitir_automaticamente', 'optante_simples_nacional', 'incentivador_cultural'):
                val = bool(val)
            elif field == 'nacional_ultimo_dps':
                val = int(val) if val else 0
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
        config.nacional_senha_certificado = data['nacional_senha_certificado']
        update_fields.append('nacional_senha_certificado')

    config.save(update_fields=update_fields)

    return Response({'success': True, 'message': 'Configuração salva'})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def nfse_config_test_nacional(request):
    """Testa conexão com ADN Nacional usando certificado configurado."""
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()

    if not config.nacional_certificado:
        return Response({'success': False, 'detail': 'Certificado Nacional não configurado'}, status=400)
    if not config.nacional_senha_certificado:
        return Response({'success': False, 'detail': 'Senha do certificado Nacional não configurada'}, status=400)

    try:
        from nfse_integration.nacional import NacionalClient

        client = NacionalClient(
            pfx_bytes=bytes(config.nacional_certificado),
            senha_pfx=config.nacional_senha_certificado,
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
