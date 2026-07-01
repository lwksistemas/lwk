"""
CRM: configuração da loja e testes de integração (Asaas, ISSNet).
"""
import logging
import os
import tempfile

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenants.middleware import get_current_loja_id
from .cache import CRMCacheManager
from .crm_config_helpers import get_crm_config_for_loja as _get_crm_config_for_loja

logger = logging.getLogger(__name__)

@api_view(['GET', 'PATCH'])
def crm_config(request):
    """
    GET: Retorna configurações do CRM da loja
    PATCH: Atualiza configurações do CRM (personalizar: origens, etapas, colunas, módulos)
    Admin e vendedores podem acessar e personalizar.
    """
    from .models import CRMConfig
    from .serializers import CRMConfigSerializer
    
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)
    
    # Buscar ou criar configuração (com auto-recovery se schema não configurado)
    try:
        config = _get_crm_config_for_loja(loja_id)
    except Exception as e:
        from django.db.utils import ProgrammingError, OperationalError
        if isinstance(e, (ProgrammingError, OperationalError)):
            # Auto-recovery: tentar configurar schema e retry
            from superadmin.models import Loja
            from .schema_service import configurar_schema_crm_loja
            loja = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
            if loja and configurar_schema_crm_loja(loja):
                try:
                    config = _get_crm_config_for_loja(loja_id)
                except Exception as retry_err:
                    logger.exception('Erro ao buscar config CRM após recovery: %s', retry_err)
                    return Response(
                        {
                            'detail': 'O banco de dados da loja precisa ser configurado. Entre em contato com o suporte.',
                            'code': 'SCHEMA_NOT_CONFIGURED',
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                logger.exception('Erro ao buscar config CRM (recovery falhou): %s', e)
                return Response(
                    {
                        'detail': 'O banco de dados da loja precisa ser configurado. Entre em contato com o suporte.',
                        'code': 'SCHEMA_NOT_CONFIGURED',
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            logger.exception('Erro ao buscar config CRM: %s', e)
            raise
    
    from superadmin.models import Loja
    loja = Loja.objects.filter(id=loja_id).first()
    serializer_context = {'request': request, 'loja': loja}

    if request.method == 'GET':
        serializer = CRMConfigSerializer(config, context=serializer_context)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = CRMConfigSerializer(
            config, data=request.data, partial=True, context=serializer_context,
        )
        if serializer.is_valid():
            serializer.save()
            # Invalidar cache do dashboard quando configurações mudarem
            CRMCacheManager.invalidate_dashboard(loja_id)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crm_config_asaas_test(request):
    """
    Testa a comunicação com a API Asaas usando a chave da loja (NFS-e).

    Body JSON (opcional):
      - api_key: se omitido ou vazio, usa a chave já salva em CRMConfig
      - asaas_sandbox: se omitido, usa o valor salvo na config
    """
    from .models import CRMConfig

    try:
        from asaas_integration.client import AsaasClient
    except ImportError:
        return Response(
            {'success': False, 'detail': 'Cliente Asaas indisponível no servidor.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'success': False, 'detail': 'Loja não identificada.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cfg = _get_crm_config_for_loja(loja_id)
    except Exception as e:
        logger.exception('crm_config_asaas_test: config')
        return Response(
            {'success': False, 'detail': f'Erro ao carregar configuração: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    from asaas_integration.api_key_utils import normalize_asaas_api_key, asaas_key_is_sandbox

    body = request.data if isinstance(request.data, dict) else {}
    api_key = (body.get('api_key') or '').strip()
    if not api_key:
        api_key = (getattr(cfg, 'asaas_api_key', None) or '').strip()
    api_key = normalize_asaas_api_key(api_key)

    if body.get('asaas_sandbox') is None:
        sandbox = asaas_key_is_sandbox(api_key) if api_key else bool(getattr(cfg, 'asaas_sandbox', False))
    else:
        sb = body.get('asaas_sandbox')
        sandbox = bool(sb) if isinstance(sb, bool) else str(sb).lower() in ('true', '1', 'yes', 'on')

    if not api_key:
        return Response(
            {
                'success': False,
                'detail': 'Informe a API Key acima ou salve uma chave antes de testar.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = AsaasClient(api_key=api_key, sandbox=sandbox)
        client._make_request('GET', 'customers?limit=1')
        environment = 'sandbox (homologação)' if sandbox else 'produção'
        return Response(
            {
                'success': True,
                'message': f'Conexão com o Asaas OK ({environment}).',
                'environment': environment,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.warning('crm_config_asaas_test falhou: %s', e)
        err = str(e)
        if len(err) > 500:
            err = err[:500] + '…'
        return Response(
            {'success': False, 'detail': err or 'Falha ao contactar a API do Asaas.'},
            status=status.HTTP_400_BAD_REQUEST,
        )




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crm_config_issnet_test(request):
    """
    Testa conexão com o WebService ISSNet usando certificado da loja.
    Valida PFX/senha e tenta acessar o WSDL.
    """
    from .models import CRMConfig

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'success': False, 'detail': 'Loja não identificada.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cfg = _get_crm_config_for_loja(loja_id)
    except Exception as e:
        return Response({'success': False, 'detail': str(e)}, status=500)

    # Certificado: do upload ou do banco
    cert_file = request.FILES.get('issnet_certificado')
    if cert_file:
        cert_data = cert_file.read()
    else:
        cert_data = getattr(cfg, 'issnet_certificado', None)
        if cert_data:
            cert_data = bytes(cert_data)

    senha = (request.data.get('issnet_senha_certificado') or '').strip()
    if not senha:
        senha = getattr(cfg, 'issnet_senha_certificado', '') or ''

    if not cert_data:
        return Response({'success': False, 'detail': 'Certificado .pfx não configurado.'}, status=400)
    if not senha:
        return Response({'success': False, 'detail': 'Senha do certificado não informada.'}, status=400)

    try:
        from nfse_integration.issnet_client import testar_conexao_issnet
        import tempfile, os

        usuario = (request.data.get('issnet_usuario') or '').strip() or getattr(cfg, 'issnet_usuario', '') or ''
        senha_ws = (request.data.get('issnet_senha') or '').strip() or getattr(cfg, 'issnet_senha', '') or ''
        ambiente = 'homologacao' if getattr(cfg, 'issnet_ambiente_homologacao', False) else 'producao'

        # Salvar cert em arquivo temporário para a função
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
        tmp.write(cert_data)
        tmp.close()

        try:
            resultado = testar_conexao_issnet(
                usuario=usuario,
                senha=senha_ws,
                certificado_path=tmp.name,
                senha_certificado=senha,
                ambiente=ambiente,
            )
        finally:
            os.unlink(tmp.name)

        if resultado.get('success'):
            return Response({
                'success': True,
                'message': resultado.get('message', 'Conexão ISSNet OK.'),
                'ambiente': ambiente,
            })
        else:
            return Response({
                'success': False,
                'detail': resultado.get('detail', 'Falha ao conectar ao ISSNet.'),
            }, status=400)

    except Exception as e:
        logger.warning('crm_config_issnet_test: %s', e)
        return Response({'success': False, 'detail': str(e)}, status=400)
