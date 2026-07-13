"""Configuração e teste de conexão Asaas."""
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ..models import AsaasConfig
from ._common import REQUESTS_AVAILABLE, AsaasClient, IsSuperAdmin, _asaas_webhook_url

logger = logging.getLogger(__name__)

@api_view(['GET', 'POST'])
@permission_classes([IsSuperAdmin])
def asaas_config(request):
    """Gerenciar configurações do Asaas"""
    
    if not REQUESTS_AVAILABLE:
        return Response(
            {'detail': 'Biblioteca requests não disponível. Instale com: pip install requests'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    if request.method == 'GET':
        # Retornar configurações atuais do banco de dados
        config = AsaasConfig.get_config()
        resolved_key = AsaasConfig.resolve_api_key()
        webhook_token = config.webhook_token_decrypted or AsaasConfig.resolve_webhook_token()
        
        return Response({
            'api_key': '',
            'api_key_masked': config.api_key_masked if config.api_key_decrypted else (
                f"{resolved_key[:10]}...{resolved_key[-4:]}" if len(resolved_key) > 14 else ''
            ),
            'api_key_configured': bool(resolved_key),
            'api_key_length': len(resolved_key),
            'sandbox': AsaasConfig.effective_sandbox(resolved_key),
            'enabled': config.enabled,
            'last_sync': config.last_sync.isoformat() if config.last_sync else None,
            'webhook_url': _asaas_webhook_url(request),
            'webhook_token': config.webhook_token_masked,
            'webhook_token_configured': bool(webhook_token),
            'webhook_token_length': len(webhook_token) if webhook_token else 0,
        })
    
    elif request.method == 'POST':
        # Salvar novas configurações no banco de dados
        api_key = request.data.get('api_key', '').strip()
        enabled = request.data.get('enabled', False)
        webhook_token = request.data.get('webhook_token')

        if api_key and '...' in api_key:
            api_key = ''

        from asaas_integration.api_key_utils import is_valid_asaas_api_key, normalize_asaas_api_key
        if api_key:
            api_key = normalize_asaas_api_key(api_key)

        config = AsaasConfig.get_config()
        webhook_incoming = webhook_token.strip() if isinstance(webhook_token, str) else ''
        resolved_key = AsaasConfig.resolve_api_key()

        if not api_key and not resolved_key and not webhook_incoming:
            return Response(
                {'detail': 'Chave da API é obrigatória na primeira configuração'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if api_key and not is_valid_asaas_api_key(api_key):
            return Response(
                {'detail': 'Chave API inválida. Use $aact_prod_... (Produção) ou $aact_hmlg_... (Sandbox)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if api_key and (len(api_key) < 40 or '...' in api_key):
            return Response(
                {'detail': 'Cole a chave API completa do painel Asaas (não use o valor mascarado da tela)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if webhook_incoming and len(webhook_incoming) < 32:
            return Response(
                {'detail': 'Token do webhook deve ter pelo menos 32 caracteres (requisito Asaas)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Salvar configuração no banco
        try:
            if api_key:
                config.api_key = api_key
            config.enabled = enabled
            if webhook_incoming:
                config.webhook_token = webhook_incoming
            config.save()  # O sandbox será detectado automaticamente no save()
            
            effective_webhook = config.webhook_token_decrypted or AsaasConfig.resolve_webhook_token()
            return Response({
                'message': 'Configuração salva com sucesso no banco de dados.',
                'api_key': '',
                'api_key_masked': config.api_key_masked,
                'api_key_configured': bool(AsaasConfig.resolve_api_key()),
                'api_key_length': len(AsaasConfig.resolve_api_key()),
                'sandbox': config.sandbox,
                'enabled': config.enabled,
                'webhook_url': _asaas_webhook_url(request),
                'webhook_token': config.webhook_token_masked,
                'webhook_token_configured': bool(effective_webhook),
                'webhook_token_length': len(effective_webhook) if effective_webhook else 0,
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Erro ao salvar configuração: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_test(request):
    """Testar conexão com a API do Asaas"""
    
    if not REQUESTS_AVAILABLE or not AsaasClient:
        return Response(
            {'detail': 'Biblioteca requests não disponível. Instale com: pip install requests'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        AsaasConfig.get_config()
        api_key = AsaasConfig.resolve_api_key()
        if not api_key:
            return Response(
                {'detail': 'Chave da API não configurada. Cole a chave completa do Asaas e salve.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sandbox = AsaasConfig.effective_sandbox(api_key)
        client = AsaasClient(api_key=api_key, sandbox=sandbox)

        # Testar com uma requisição simples
        client._make_request('GET', 'customers?limit=1')

        return Response({
            'message': 'Conexão testada com sucesso',
            'environment': 'Sandbox' if sandbox else 'Produção',
            'api_status': 'Conectado',
            'test_time': timezone.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Erro ao testar API Asaas: {e}")
        err_text = str(e)
        detail = f'Erro na conexão: {err_text}'
        if '401' in err_text:
            detail = (
                'Chave API rejeitada pelo Asaas (401). '
                'Gere uma nova chave em Asaas → Integrações → API e cole o valor completo. '
                'Chave Sandbox contém "hmlg"; Produção não.'
            )
        return Response(
            {'detail': detail},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def asaas_status(request):
    """Status atual da integração Asaas"""
    
    try:
        config = AsaasConfig.get_config()
        
        api_connected = False
        error_message = None
        
        if not REQUESTS_AVAILABLE:
            error_message = 'Biblioteca requests não disponível'
        elif config.enabled and AsaasClient:
            try:
                api_key = AsaasConfig.resolve_api_key()
                if not api_key:
                    error_message = 'Chave da API inválida ou incompleta no banco'
                else:
                    sandbox = AsaasConfig.effective_sandbox(api_key)
                    client = AsaasClient(api_key=api_key, sandbox=sandbox)
                    client._make_request('GET', 'customers?limit=1')
                    api_connected = True
            except Exception as e:
                error_message = str(e)
                if '401' in str(e):
                    error_message = (
                        'Chave API rejeitada pelo Asaas. Cole a chave completa de '
                        'Integrações → API (Sandbox com "hmlg", Produção sem).'
                    )
        elif not config.enabled:
            error_message = 'Integração desabilitada'
        
        return Response({
            'api_connected': api_connected,
            'last_check': timezone.now().isoformat(),
            'error_message': error_message,
            'environment': 'Sandbox' if AsaasConfig.effective_sandbox() else 'Produção',
            'enabled': config.enabled,
            'requests_available': REQUESTS_AVAILABLE
        })
        
    except Exception as e:
        return Response(
            {'detail': f'Erro ao verificar status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


