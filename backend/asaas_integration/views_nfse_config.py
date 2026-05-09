"""
Views para configuração de NFS-e do Superadmin.
GET/PATCH /api/superadmin/nfse-config/
POST /api/superadmin/nfse-config/test-issnet/
"""
import os
import logging
import tempfile

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
            'issnet_usuario': config.issnet_usuario,
            'issnet_senha_set': bool(config.issnet_senha),
            'issnet_certificado_nome': config.issnet_certificado_nome,
            'issnet_certificado_set': bool(config.issnet_certificado),
            'issnet_senha_certificado_set': bool(config.issnet_senha_certificado),
            'codigo_servico_municipal': config.codigo_servico_municipal,
            'descricao_servico_padrao': config.descricao_servico_padrao,
            'aliquota_iss': str(config.aliquota_iss),
            'codigo_cnae': config.codigo_cnae,
            'optante_simples_nacional': config.optante_simples_nacional,
            'serie_rps': config.serie_rps,
            'ultimo_rps': config.ultimo_rps,
        })

    # PATCH
    data = request.data
    update_fields = ['updated_at']

    # Campos simples
    simple_fields = [
        'provedor_nfse', 'emitir_automaticamente', 'prestador_cnpj',
        'prestador_razao_social', 'prestador_inscricao_municipal',
        'issnet_usuario', 'codigo_servico_municipal', 'descricao_servico_padrao',
        'codigo_cnae', 'optante_simples_nacional', 'serie_rps', 'ultimo_rps',
    ]
    for field in simple_fields:
        if field in data:
            val = data[field]
            if field == 'emitir_automaticamente' or field == 'optante_simples_nacional':
                val = bool(val)
            elif field == 'ultimo_rps':
                val = int(val) if val else 0
            setattr(config, field, val)
            update_fields.append(field)

    # Alíquota ISS
    if 'aliquota_iss' in data:
        from decimal import Decimal
        config.aliquota_iss = Decimal(str(data['aliquota_iss']))
        update_fields.append('aliquota_iss')

    # Senha ISSNet (só atualiza se enviada)
    if data.get('issnet_senha'):
        config.issnet_senha = data['issnet_senha']
        update_fields.append('issnet_senha')

    # Senha certificado
    if data.get('issnet_senha_certificado'):
        config.issnet_senha_certificado = data['issnet_senha_certificado']
        update_fields.append('issnet_senha_certificado')

    # Certificado (upload via multipart)
    cert_file = request.FILES.get('issnet_certificado')
    if cert_file:
        ext = os.path.splitext(cert_file.name)[1].lower()
        if ext not in ('.pfx', '.p12'):
            return Response({'error': 'Formato inválido. Envie .pfx ou .p12'}, status=status.HTTP_400_BAD_REQUEST)
        if cert_file.size > 5 * 1024 * 1024:
            return Response({'error': 'Certificado muito grande (máx 5MB)'}, status=status.HTTP_400_BAD_REQUEST)
        config.issnet_certificado = cert_file.read()
        config.issnet_certificado_nome = cert_file.name[:255]
        update_fields.extend(['issnet_certificado', 'issnet_certificado_nome'])

    config.save(update_fields=update_fields)

    return Response({'success': True, 'message': 'Configuração salva'})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def nfse_config_test_issnet(request):
    """Testa conexão com ISSNet usando certificado configurado."""
    from .models_nfse_config import SuperadminNFSeConfig

    config = SuperadminNFSeConfig.get_config()

    if not config.issnet_usuario:
        return Response({'success': False, 'detail': 'Usuário ISSNet não configurado'}, status=400)
    if not config.issnet_senha:
        return Response({'success': False, 'detail': 'Senha ISSNet não configurada'}, status=400)
    if not config.issnet_certificado:
        return Response({'success': False, 'detail': 'Certificado não configurado'}, status=400)
    if not config.issnet_senha_certificado:
        return Response({'success': False, 'detail': 'Senha do certificado não configurada'}, status=400)

    cert_path = None
    try:
        from nfse_integration.issnet_client import testar_conexao_issnet

        cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
        cert_tmp.write(bytes(config.issnet_certificado))
        cert_tmp.close()
        cert_path = cert_tmp.name

        resultado = testar_conexao_issnet(
            usuario=config.issnet_usuario,
            senha=config.issnet_senha,
            certificado_path=cert_path,
            senha_certificado=config.issnet_senha_certificado,
            ambiente='producao',
        )

        if resultado.get('success'):
            return Response({
                'success': True,
                'message': resultado.get('message', 'Conexão ISSNet OK'),
                'certificado_subject': resultado.get('certificado_subject'),
            })
        return Response({'success': False, 'detail': resultado.get('detail', 'Falha no teste')}, status=400)

    except Exception as e:
        logger.exception('Erro ao testar ISSNet superadmin: %s', e)
        return Response({'success': False, 'detail': str(e)}, status=400)
    finally:
        if cert_path:
            try:
                os.unlink(cert_path)
            except OSError:
                pass
