"""
Views de configuração, monitoramento e sincronização do Asaas
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, F
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import logging

from .models import AsaasCustomer, AsaasPayment, LojaAssinatura, AsaasConfig

logger = logging.getLogger(__name__)


# Importações condicionais para evitar erros na inicialização
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Importação condicional do cliente Asaas
if REQUESTS_AVAILABLE:
    try:
        from .client import AsaasClient
    except ImportError:
        AsaasClient = None
else:
    AsaasClient = None


def _asaas_webhook_log_context(payload):
    """Retorna apenas identificadores do webhook, sem registrar dados pessoais/financeiros."""
    payment = payload.get('payment') if isinstance(payload.get('payment'), dict) else {}
    return {
        'event': payload.get('event'),
        'payment_id': payment.get('id'),
        'payment_status': payment.get('status'),
        'external_reference': payment.get('externalReference'),
    }


class IsSuperAdmin(permissions.BasePermission):
    """Permissão apenas para super admins"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


def _asaas_webhook_url(request) -> str:
    return request.build_absolute_uri('/api/asaas/webhook/')


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

        from asaas_integration.api_key_utils import normalize_asaas_api_key, is_valid_asaas_api_key
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
        config = AsaasConfig.get_config()
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


def _diag_item(check_id, label, ok, level, message, details=None, action_path=''):
    return {
        'id': check_id,
        'label': label,
        'ok': ok,
        'level': level,
        'message': message,
        'details': details or [],
        'action_path': action_path,
    }


def _build_cadastro_diagnostico(request):
    """Monta checklist do fluxo pós-cadastro (PIX → senha + NFS-e)."""
    from django.conf import settings

    checks = []

    # --- API Asaas ---
    asaas_cfg = AsaasConfig.get_config()
    api_key = AsaasConfig.resolve_api_key()
    api_details = []
    api_level = 'ok'
    api_ok = False

    if not api_key:
        api_level = 'error'
        api_details.append('Chave da API não configurada ou inválida (cole o valor completo do Asaas)')
    elif not asaas_cfg.enabled:
        api_level = 'error'
        api_details.append('Integração desabilitada — marque "Habilitar integração Asaas"')
    else:
        sandbox = AsaasConfig.effective_sandbox(api_key)
        if sandbox:
            api_level = 'warn'
            api_details.append('Ambiente Sandbox ($aact_hmlg_) — cadastros reais usam $aact_prod_')
        if not REQUESTS_AVAILABLE or not AsaasClient:
            api_level = 'error'
            api_details.append('Biblioteca/cliente Asaas indisponível')
        else:
            try:
                client = AsaasClient(api_key=api_key, sandbox=sandbox)
                client._make_request('GET', 'customers?limit=1')
                api_ok = True
                api_details.append(f'Conexão OK ({"Sandbox" if sandbox else "Produção"})')
            except Exception as exc:
                api_level = 'error'
                msg = str(exc)
                if '401' in msg:
                    api_details.append('Asaas rejeitou a chave (401) — gere/cole nova chave em Integrações → API')
                else:
                    api_details.append(f'Falha na API: {exc}')

    checks.append(_diag_item(
        'asaas_api', 'API Asaas (criar cobrança no cadastro)',
        api_ok, api_level,
        'Pronta para gerar PIX/boleto no cadastro' if api_ok else 'Configure a API para criar cobranças',
        api_details, '/superadmin/asaas',
    ))

    # --- Webhook ---
    webhook_token = AsaasConfig.resolve_webhook_token()
    webhook_len = len(webhook_token)
    webhook_details = [
        f'URL: {_asaas_webhook_url(request)}',
    ]
    webhook_level = 'ok'
    webhook_ok = False

    if webhook_len < 32:
        webhook_level = 'error'
        webhook_details.append(
            'Token não configurado ou incompleto (mínimo 32 caracteres — copie o valor inteiro no painel Asaas)'
        )
    else:
        webhook_ok = True
        webhook_details.append(f'Token configurado ({webhook_len} caracteres)')
        webhook_details.append(
            'Confirme o mesmo token em Asaas → Integrações → Webhooks → LWK Sistemas'
        )

    strict = bool(getattr(settings, 'WEBHOOK_STRICT_VERIFY', True))
    if strict:
        webhook_details.append('Validação estrita ativa (WEBHOOK_STRICT_VERIFY)')

    checks.append(_diag_item(
        'asaas_webhook', 'Webhook Asaas (confirmar PIX automaticamente)',
        webhook_ok, webhook_level,
        'Webhook autenticado no servidor' if webhook_ok else 'Alinhe o token entre superadmin/Railway e painel Asaas',
        webhook_details, '/superadmin/asaas',
    ))

    # --- E-mail ---
    from_email = (getattr(settings, 'DEFAULT_FROM_EMAIL', None) or '').strip()
    resend_key = (getattr(settings, 'RESEND_API_KEY', None) or '').strip()
    email_backend = getattr(settings, 'EMAIL_BACKEND', '')
    email_details = []
    email_ok = bool(from_email)
    email_level = 'ok' if email_ok else 'error'

    if resend_key:
        email_details.append('Provedor: Resend (API)')
    elif 'smtp' in email_backend.lower():
        email_details.append('Provedor: SMTP')
        if not getattr(settings, 'EMAIL_HOST_PASSWORD', ''):
            email_ok = False
            email_level = 'error'
            email_details.append('Senha SMTP não configurada')
    else:
        email_details.append(f'Backend: {email_backend or "não definido"}')

    if from_email:
        email_details.append(f'Remetente: {from_email}')
    else:
        email_details.append('DEFAULT_FROM_EMAIL não configurado')

    pending_emails = 0
    try:
        from superadmin.models import EmailRetry
        pending_emails = EmailRetry.objects.filter(
            enviado=False,
            tentativas__lt=F('max_tentativas'),
        ).count()
        if pending_emails:
            email_level = 'warn' if email_ok else email_level
            email_details.append(f'{pending_emails} e-mail(s) aguardando reenvio automático')
    except Exception:
        pass

    checks.append(_diag_item(
        'email', 'E-mail (senha provisória após pagamento)',
        email_ok, email_level,
        'E-mail configurado para envio de senha' if email_ok else 'Configure Resend ou SMTP no Railway',
        email_details, '/superadmin/asaas',
    ))

    # --- NFS-e ---
    nfse_details = []
    nfse_ok = False
    nfse_level = 'ok'
    nfse_action = '/superadmin/nfse-config'
    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        nfse_cfg = SuperadminNFSeConfig.get_config()
        provedor = nfse_cfg.provedor_nfse or 'desabilitado'
        nfse_details.append(f'Provedor: {nfse_cfg.get_provedor_nfse_display()}')

        if provedor == 'desabilitado':
            nfse_level = 'warn'
            nfse_ok = True
            nfse_details.append('Emissão desabilitada — senha será enviada, mas NFS-e não')
        elif not nfse_cfg.emitir_automaticamente:
            nfse_level = 'warn'
            nfse_ok = True
            nfse_details.append('"Emitir automaticamente" desativado — NFS-e manual após pagamento')
        else:
            missing = []
            if not (nfse_cfg.prestador_cnpj or '').strip():
                missing.append('CNPJ do prestador')
            if not (nfse_cfg.prestador_razao_social or '').strip():
                missing.append('Razão social')
            if not (nfse_cfg.prestador_inscricao_municipal or '').strip():
                missing.append('Inscrição municipal')

            if provedor == 'nacional':
                if not nfse_cfg.nacional_certificado:
                    missing.append('Certificado digital (.pfx)')
                if not nfse_cfg.nacional_senha_certificado_decrypted:
                    missing.append('Senha do certificado')
                if not (nfse_cfg.nacional_codigo_municipio or '').strip():
                    missing.append('Código IBGE do município')
            elif provedor == 'issnet':
                cert = nfse_cfg.issnet_certificado or nfse_cfg.nacional_certificado
                senha = nfse_cfg.issnet_senha_certificado or nfse_cfg.nacional_senha_certificado
                if not cert:
                    missing.append('Certificado digital')
                if not senha:
                    missing.append('Senha do certificado')

            if missing:
                nfse_level = 'error'
                nfse_details.append('Pendências: ' + ', '.join(missing))
            else:
                nfse_ok = True
                nfse_details.append('Emissão automática configurada')
                if provedor == 'nacional' and nfse_cfg.nacional_ambiente != 'producao':
                    nfse_level = 'warn'
                    nfse_details.append('Ambiente Nacional em homologação — notas de teste')
    except Exception as exc:
        nfse_level = 'error'
        nfse_details.append(f'Erro ao ler config NFS-e: {exc}')

    checks.append(_diag_item(
        'nfse', 'NFS-e (nota fiscal após pagamento)',
        nfse_ok, nfse_level,
        'NFS-e pronta para emissão automática' if nfse_ok and nfse_level == 'ok'
        else ('NFS-e opcional/desativada' if nfse_level == 'warn' else 'Complete a configuração NFS-e'),
        nfse_details, nfse_action,
    ))

    core_ids = ('asaas_api', 'asaas_webhook', 'email')
    core_ok = all(c['ok'] for c in checks if c['id'] in core_ids)
    nfse_check = next(c for c in checks if c['id'] == 'nfse')
    cadastro_ready = core_ok and nfse_check['level'] != 'error'

    ok_count = sum(1 for c in checks if c['ok'] and c['level'] == 'ok')
    warn_count = sum(1 for c in checks if c['level'] == 'warn')
    err_count = sum(1 for c in checks if c['level'] == 'error')

    return {
        'ready': cadastro_ready,
        'summary': f'{ok_count} OK · {warn_count} aviso(s) · {err_count} pendência(s)',
        'cadastro_fluxo': {
            'ok': cadastro_ready,
            'message': (
                'Fluxo automático pós-PIX pronto (cobrança → webhook → senha + NFS-e)'
                if cadastro_ready
                else 'Corrija os itens em vermelho antes de um novo cadastro com PIX'
            ),
        },
        'checks': checks,
        'checked_at': timezone.now().isoformat(),
    }


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def asaas_diagnostico(request):
    """Diagnóstico do fluxo de cadastro: API, webhook, e-mail e NFS-e."""
    try:
        return Response(_build_cadastro_diagnostico(request))
    except Exception as e:
        logger.exception('Erro no diagnóstico Asaas: %s', e)
        return Response(
            {'detail': f'Erro ao gerar diagnóstico: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def asaas_stats(request):
    """Estatísticas da integração Asaas"""
    
    try:
        # Estatísticas dos clientes
        total_customers = AsaasCustomer.objects.count()
        
        # Estatísticas dos pagamentos
        total_payments = AsaasPayment.objects.count()
        pending_payments = AsaasPayment.objects.filter(status='PENDING').count()
        confirmed_payments = AsaasPayment.objects.filter(
            status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
        ).count()
        
        # Receita total (apenas pagamentos confirmados)
        total_revenue = AsaasPayment.objects.filter(
            status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
        ).aggregate(total=Sum('value'))['total'] or 0
        
        # Último pagamento
        last_payment = AsaasPayment.objects.order_by('-created_at').first()
        last_payment_date = last_payment.created_at.isoformat() if last_payment else None
        
        # Estatísticas por período (últimos 30 dias)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_payments = AsaasPayment.objects.filter(created_at__gte=thirty_days_ago)
        recent_revenue = recent_payments.filter(
            status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
        ).aggregate(total=Sum('value'))['total'] or 0
        
        return Response({
            'total_customers': total_customers,
            'total_payments': total_payments,
            'pending_payments': pending_payments,
            'confirmed_payments': confirmed_payments,
            'total_revenue': float(total_revenue),
            'last_payment_date': last_payment_date,
            'recent_revenue_30d': float(recent_revenue),
            'recent_payments_30d': recent_payments.count()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas Asaas: {e}")
        return Response(
            {'detail': f'Erro ao obter estatísticas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_sync(request):
    """Sincronização manual de pagamentos"""
    try:
        from superadmin.sync_service import AsaasSyncService
        
        sync_service = AsaasSyncService()
        loja_slug = request.data.get('loja')
        
        if loja_slug:
            # Sincronizar loja específica
            try:
                from superadmin.models import Loja
                loja = Loja.objects.get(slug=loja_slug, is_active=True)
                resultado = sync_service.sync_loja_payments(loja)
            except Loja.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Loja "{loja_slug}" não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Sincronizar todas as lojas
            resultado = sync_service.sync_all_payments()
        
        return Response(resultado)
        
    except ImportError:
        return Response({
            'success': False,
            'error': 'Serviço de sincronização não disponível'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Erro na sincronização manual: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def asaas_sync_stats(request):
    """Estatísticas de sincronização"""
    try:
        from superadmin.sync_service import AsaasSyncService
        
        sync_service = AsaasSyncService()
        stats = sync_service.get_sync_stats()
        
        return Response(stats)
        
    except ImportError:
        return Response({
            'error': 'Serviço de sincronização não disponível'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([])  # Webhook público, sem autenticação
def asaas_webhook(request):
    """Webhook para receber notificações do Asaas"""
    from core.webhook_security import verify_asaas_access_token, webhook_auth_failed_response

    if not verify_asaas_access_token(request):
        return webhook_auth_failed_response()

    try:
        payload = request.data if isinstance(request.data, dict) else {}
        logger.info("Webhook Asaas recebido: %s", _asaas_webhook_log_context(payload))
        
        # Verificar se é uma notificação de pagamento
        event_type = payload.get('event')
        payment_data = payload.get('payment', {})
        
        if not event_type or not payment_data:
            return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        
        # Processar apenas eventos de pagamento relevantes
        if event_type in ['PAYMENT_CREATED', 'PAYMENT_UPDATED', 'PAYMENT_CONFIRMED', 'PAYMENT_RECEIVED']:
            
            # Usar o novo serviço de sincronização
            try:
                from superadmin.sync_service import AsaasSyncService
                
                sync_service = AsaasSyncService()
                resultado = sync_service.process_webhook_payment(payment_data)
                
                if resultado['success']:
                    logger.info(f"Webhook processado com sucesso: {resultado}")
                    
                    response_data = {
                        'status': resultado.get('status', 'processed'),
                        'payment_id': resultado.get('payment_id'),
                        'status_updated': resultado.get('status_updated', False)
                    }
                    
                    # Se foi ignorado, adicionar razão
                    if resultado.get('status') == 'ignored':
                        response_data['reason'] = resultado.get('reason')
                        logger.info(f"Webhook ignorado: {resultado.get('reason')}")
                    
                    # Adicionar informações sobre bloqueio/desbloqueio
                    if resultado.get('blocked'):
                        response_data['loja_blocked'] = True
                        logger.warning(f"Loja bloqueada via webhook: {resultado.get('payment_id')}")
                    
                    if resultado.get('unblocked'):
                        response_data['loja_unblocked'] = True
                        logger.info(f"Loja desbloqueada via webhook: {resultado.get('payment_id')}")
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Erro ao processar webhook: {resultado.get('error')}")
                    return Response({
                        'status': 'error',
                        'error': resultado.get('error')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except ImportError:
                logger.error("Serviço de sincronização não disponível")
                return Response({
                    'status': 'error',
                    'error': 'Serviço de sincronização não disponível'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Evento não processado
        return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erro no webhook Asaas: {e}")
        # Retornar 200 para não reenviar o webhook
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_test_public(request):
    """Testar conexão com a API do Asaas informando uma chave temporária."""
    
    if not REQUESTS_AVAILABLE or not AsaasClient:
        return Response(
            {'detail': 'Biblioteca requests não disponível. Instale com: pip install requests'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Pegar chave da requisição
        api_key = request.data.get('api_key')
        if not api_key:
            return Response(
                {'detail': 'Chave da API é obrigatória no body da requisição'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Auto-detectar sandbox baseado na chave
        is_sandbox = 'hmlg' in api_key
        client = AsaasClient(api_key=api_key, sandbox=is_sandbox)
        
        # Testar com uma requisição simples
        result = client._make_request('GET', 'customers?limit=1')
        
        return Response({
            'message': 'Conexão testada com sucesso',
            'environment': 'Sandbox' if is_sandbox else 'Produção',
            'api_status': 'Conectado',
            'test_time': timezone.now().isoformat(),
            'customers_count': result.get('totalCount', 0),
            'api_key_masked': f"{api_key[:10]}...{api_key[-4:]}"
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar API Asaas: {e}")
        return Response(
            {'detail': f'Erro na conexão: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_sync_realtime(request):
    """Sincronização em tempo real de pagamentos específicos"""
    try:
        from superadmin.sync_service import AsaasSyncService
        
        sync_service = AsaasSyncService()
        
        # Pegar parâmetros da requisição
        payment_id = request.data.get('payment_id')
        loja_slug = request.data.get('loja_slug')
        
        if payment_id:
            # Sincronizar pagamento específico
            try:
                from asaas_integration.models import AsaasPayment
                from superadmin.models import PagamentoLoja
                
                # Buscar pagamento
                pagamento = None
                try:
                    pagamento = AsaasPayment.objects.get(asaas_id=payment_id)
                except AsaasPayment.DoesNotExist:
                    try:
                        pagamento = PagamentoLoja.objects.get(asaas_payment_id=payment_id)
                    except PagamentoLoja.DoesNotExist:
                        return Response({
                            'success': False,
                            'error': f'Pagamento {payment_id} não encontrado'
                        }, status=status.HTTP_404_NOT_FOUND)
                
                # Consultar status atual no Asaas
                resultado = sync_service.sync_payment_status(pagamento)
                
                return Response({
                    'success': True,
                    'payment_id': payment_id,
                    'sync_result': resultado
                })
                
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif loja_slug:
            # Sincronizar loja específica
            try:
                from superadmin.models import Loja
                loja = Loja.objects.get(slug=loja_slug, is_active=True)
                resultado = sync_service.sync_loja_payments(loja)
                return Response(resultado)
            except Loja.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Loja "{loja_slug}" não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        
        else:
            return Response({
                'success': False,
                'error': 'payment_id ou loja_slug é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Erro na sincronização em tempo real: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_cleanup_orphans(request):
    """Limpar dados Asaas órfãos"""
    try:
        from .deletion_service import AsaasDeletionService
        
        deletion_service = AsaasDeletionService()
        
        if not deletion_service.available:
            return Response({
                'success': False,
                'error': 'Serviço Asaas não disponível ou não configurado'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Verificar se é dry-run
        dry_run = request.data.get('dry_run', False)
        
        if dry_run:
            # Simular limpeza
            from .models import LojaAssinatura
            from superadmin.models import Loja
            
            orphaned_subscriptions = []
            for subscription in LojaAssinatura.objects.all():
                try:
                    Loja.objects.get(slug=subscription.loja_slug, is_active=True)
                except Loja.DoesNotExist:
                    orphaned_subscriptions.append({
                        'loja_slug': subscription.loja_slug,
                        'customer_id': subscription.asaas_customer.asaas_id,
                        'created_at': subscription.created_at.isoformat()
                    })
            
            return Response({
                'success': True,
                'dry_run': True,
                'orphaned_subscriptions': orphaned_subscriptions,
                'count': len(orphaned_subscriptions)
            })
        else:
            # Executar limpeza
            result = deletion_service.cleanup_orphaned_asaas_data()
            return Response(result)
            
    except Exception as e:
        logger.error(f"Erro na limpeza de órfãos Asaas: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsSuperAdmin])
def asaas_delete_loja(request):
    """Excluir dados de uma loja específica do Asaas"""
    try:
        loja_slug = request.data.get('loja_slug')
        
        if not loja_slug:
            return Response({
                'success': False,
                'error': 'loja_slug é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from .deletion_service import AsaasDeletionService
        
        deletion_service = AsaasDeletionService()
        
        if not deletion_service.available:
            return Response({
                'success': False,
                'error': 'Serviço Asaas não disponível ou não configurado'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        result = deletion_service.delete_loja_from_asaas(loja_slug)
        
        if result.get('success'):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Erro ao excluir loja do Asaas: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def set_last_sync_time():
    """Definir timestamp da última sincronização"""
    try:
        config = AsaasConfig.get_config()
        config.last_sync = timezone.now()
        config.save()
    except Exception as e:
        logger.error(f"Erro ao salvar timestamp de sincronização: {e}")
    """Obter timestamp da última sincronização"""
    try:
        config = AsaasConfig.get_config()
        return config.last_sync.isoformat() if config.last_sync else None
    except Exception as e:
        logger.error(f"Erro ao obter timestamp de sincronização: {e}")
        return None
