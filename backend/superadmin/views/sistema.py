from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.db import connection, DatabaseError
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
from ..models import Loja
from .permissions import IsSuperAdmin


# ✅ Endpoint para verificação de storage
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def verificar_storage_todas(request):
    """Recalcula storage de todas as lojas ativas. Apenas superadmin."""
    try:
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('verificar_storage_lojas', stdout=out)

        lojas = Loja.objects.filter(is_active=True)
        return Response({
            'success': True,
            'total': lojas.count(),
            'output': out.getvalue(),
        })
    except Exception as e:
        logger.error(f'Erro ao verificar storage de todas as lojas: {e}', exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def verificar_storage_loja(request, loja_id):
    """Verifica storage de uma loja específica (manual). Apenas superadmin."""
    try:
        loja = Loja.objects.get(id=loja_id)
        
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('verificar_storage_lojas', loja_id=loja_id, stdout=out)
        
        loja.refresh_from_db()
        
        return Response({
            'success': True,
            'loja': {
                'id': loja.id,
                'nome': loja.nome,
                'slug': loja.slug,
            },
            'storage': {
                'usado_mb': float(loja.storage_usado_mb),
                'limite_mb': loja.storage_limite_mb,
                'percentual': loja.get_storage_percentual(),
                'is_critical': loja.is_storage_critical(),
                'is_full': loja.is_storage_full(),
            },
            'alerta_enviado': loja.storage_alerta_enviado,
            'ultima_verificacao': loja.storage_ultima_verificacao.isoformat() if loja.storage_ultima_verificacao else None,
            'output': out.getvalue()
        })
    
    except Loja.DoesNotExist:
        return Response(
            {'error': 'Loja não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Erro ao verificar storage da loja {loja_id}: {e}', exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def listar_storage_lojas(request):
    """Lista uso de storage de todas as lojas. Apenas superadmin."""
    try:
        lojas = Loja.objects.all().select_related('plano', 'owner')
        
        dados = []
        for loja in lojas:
            horas_desde_verificacao = None
            if loja.storage_ultima_verificacao:
                tempo_desde = timezone.now() - loja.storage_ultima_verificacao
                horas_desde_verificacao = int(tempo_desde.total_seconds() / 3600)
            
            percentual = loja.get_storage_percentual()
            if percentual >= 100:
                storage_status = 'critical'
                storage_status_texto = 'Storage cheio'
            elif percentual >= 80:
                storage_status = 'warning'
                storage_status_texto = 'Atingindo o limite'
            else:
                storage_status = 'ok'
                storage_status_texto = 'Normal'
            
            dados.append({
                'id': loja.id,
                'nome': loja.nome,
                'slug': loja.slug,
                'storage_usado_mb': float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0,
                'storage_limite_mb': loja.storage_limite_mb,
                'storage_livre_mb': loja.storage_limite_mb - (float(loja.storage_usado_mb) if loja.storage_usado_mb else 0.0),
                'storage_percentual': percentual,
                'storage_status': storage_status,
                'storage_status_texto': storage_status_texto,
                'storage_alerta_enviado': loja.storage_alerta_enviado,
                'storage_ultima_verificacao': loja.storage_ultima_verificacao.isoformat() if loja.storage_ultima_verificacao else None,
                'storage_horas_desde_verificacao': horas_desde_verificacao,
                'plano_nome': loja.plano.nome if loja.plano else 'Sem plano',
                'is_active': loja.is_active,
                'is_blocked': loja.is_blocked,
            })
        
        dados.sort(key=lambda x: x['storage_percentual'], reverse=True)
        
        return Response({
            'lojas': dados,
            'total': len(dados),
        })
    
    except Exception as e:
        logger.error(f'Erro ao listar storage das lojas: {e}', exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@require_http_methods(['GET'])
def health_check(request):
    """
    Health check endpoint para load balancer e failover automático.
    Endpoint público (sem autenticação). Sempre retorna JSON.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        logger.error(f'Health check: banco falhou: {e}', exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)

    loja_count = None
    try:
        loja_count = Loja.objects.count()
    except Exception as e:
        logger.warning(f'Health check: Loja.objects.count() falhou: {e}')

    import os
    from core.migration_guard import get_pending_critical_migrations
    from core.resend_api import resend_api_key

    pending = []
    try:
        pending = [
            f'{app}.{name}' for app, name in get_pending_critical_migrations()
        ]
    except Exception as e:
        logger.warning('Health check: migrations: %s', e)

    email_provider = 'resend' if resend_api_key() else 'smtp'
    payload = {
        'status': 'healthy',
        'database': 'connected',
        'lojas_count': loja_count,
        'timestamp': timezone.now().isoformat(),
        'version': 'v751',
        'build': os.environ.get('LWK_BUILD', 'unknown'),
        'email_provider': email_provider,
        'email_backend': getattr(settings, 'EMAIL_BACKEND', ''),
        'migrations_pending': pending,
    }

    # Redis
    try:
        from django.core.cache import cache
        cache.set('_health_check', '1', timeout=5)
        redis_ok = cache.get('_health_check') == '1'
        payload['cache'] = 'redis' if getattr(settings, 'USE_REDIS', False) or 'redis' in str(getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', '')) else 'locmem'
        payload['cache_status'] = 'connected' if redis_ok else 'error'
    except Exception as e:
        payload['cache'] = 'error'
        payload['cache_status'] = str(e)[:80]

    try:
        from whatsapp.evolution_client import evolution_configured
        payload['evolution_available'] = evolution_configured()
    except Exception:
        payload['evolution_available'] = False

    try:
        from core.task_queue import queue_health_level, queue_status

        task_queue = queue_status()
        payload['task_queue'] = task_queue
        queue_level = queue_health_level(task_queue)
        if queue_level:
            payload['task_queue']['health'] = queue_level
            if payload['status'] == 'healthy' and queue_level == 'unhealthy':
                payload['status'] = 'degraded'
            elif payload['status'] == 'healthy' and queue_level == 'degraded':
                payload['status'] = 'degraded'
    except Exception:
        payload['task_queue'] = {'enabled': False, 'broker': 'unknown'}

    if pending:
        payload['status'] = 'degraded'
        return JsonResponse(payload, status=503)
    if payload.get('task_queue', {}).get('health') == 'unhealthy':
        return JsonResponse(payload, status=503)
    return JsonResponse(payload, status=200)


class LoginConfigSistemaViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar configurações de login do sistema (superadmin e suporte)."""
    permission_classes = [IsAuthenticated]
    serializer_class = None
    queryset = None
    
    def get_queryset(self):
        from ..models import LoginConfigSistema
        return LoginConfigSistema.objects.all()
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class LoginConfigSistemaSerializer(serializers.ModelSerializer):
            class Meta:
                from ..models import LoginConfigSistema
                model = LoginConfigSistema
                fields = [
                    'id', 'tipo', 'logo', 'login_background',
                    'cor_primaria', 'cor_secundaria', 'titulo', 'subtitulo',
                    'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return LoginConfigSistemaSerializer
    
    def list(self, request, *args, **kwargs):
        """Lista ou retorna configuração específica por tipo"""
        tipo = request.query_params.get('tipo')
        
        if tipo:
            from ..models import LoginConfigSistema
            from ..login_sistema_defaults import LOGIN_SISTEMA_DEFAULTS
            config, created = LoginConfigSistema.objects.get_or_create(
                tipo=tipo,
                defaults=LOGIN_SISTEMA_DEFAULTS.get(tipo, {}),
            )
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        
        return super().list(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Atualiza configuração de login"""
        from django.core.cache import cache
        instance = self.get_object()
        response = super().update(request, *args, **kwargs)
        cache.delete(f'login_config_sistema:{instance.tipo}')
        return response
    
    def partial_update(self, request, *args, **kwargs):
        """Atualiza parcialmente configuração de login"""
        from django.core.cache import cache
        instance = self.get_object()
        response = super().partial_update(request, *args, **kwargs)
        cache.delete(f'login_config_sistema:{instance.tipo}')
        return response


@api_view(['GET'])
@permission_classes([AllowAny])
def login_config_sistema_publico(request, tipo):
    """Endpoint público para obter configurações de login do sistema."""
    from django.core.cache import cache
    from ..models import LoginConfigSistema
    
    if tipo not in ['superadmin', 'suporte']:
        return Response(
            {'error': 'Tipo inválido. Use "superadmin" ou "suporte".'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    cache_key = f'login_config_sistema:{tipo}'
    cached_data = None
    try:
        cached_data = cache.get(cache_key)
    except Exception as e:
        logger.warning(f'Cache não disponível: {e}')
    
    if cached_data:
        return Response(cached_data)

    def _defaults_payload():
        from superadmin.login_sistema_defaults import LOGIN_SISTEMA_DEFAULTS
        base = LOGIN_SISTEMA_DEFAULTS.get(tipo, {})
        return {
            'logo': base.get('logo', ''),
            'login_background': base.get('login_background', ''),
            'cor_primaria': base.get('cor_primaria', '#10B981'),
            'cor_secundaria': base.get('cor_secundaria', '#059669'),
            'titulo': base.get('titulo', tipo),
            'subtitulo': base.get('subtitulo', ''),
        }

    try:
        from ..login_sistema_defaults import LOGIN_SISTEMA_DEFAULTS
        config, created = LoginConfigSistema.objects.get_or_create(
            tipo=tipo,
            defaults=LOGIN_SISTEMA_DEFAULTS.get(tipo, {}),
        )
    except DatabaseError as e:
        logger.warning('login_config_sistema_publico: BD indisponível (tipo=%s): %s', tipo, e)
        return Response(_defaults_payload())

    data = {
        'logo': config.logo or LOGIN_SISTEMA_DEFAULTS.get(tipo, {}).get('logo', ''),
        'login_background': config.login_background or LOGIN_SISTEMA_DEFAULTS.get(tipo, {}).get('login_background', ''),
        'cor_primaria': config.cor_primaria or LOGIN_SISTEMA_DEFAULTS.get(tipo, {}).get('cor_primaria', '#10B981'),
        'cor_secundaria': config.cor_secundaria or LOGIN_SISTEMA_DEFAULTS.get(tipo, {}).get('cor_secundaria', '#059669'),
        'titulo': config.titulo or LOGIN_SISTEMA_DEFAULTS.get(tipo, {}).get('titulo', tipo),
        'subtitulo': config.subtitulo or LOGIN_SISTEMA_DEFAULTS.get(tipo, {}).get('subtitulo', ''),
    }

    try:
        cache.set(cache_key, data, 3600)
    except Exception as e:
        logger.warning(f'Cache não disponível para salvar: {e}')

    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def atalho_redirect(request, atalho):
    """
    Redireciona atalho curto para URL completa da loja.
    Sistema híbrido de acesso às lojas.
    """
    from django.shortcuts import redirect, get_object_or_404
    
    loja = get_object_or_404(Loja, atalho=atalho, is_active=True)
    
    logger.info(f"[atalho_redirect] Atalho '{atalho}' → Loja '{loja.nome}' (slug: {loja.slug})")
    
    if not request.user.is_authenticated:
        login_url = f'/loja/{loja.slug}/login'
        logger.info(f"[atalho_redirect] Usuário não autenticado → Redirecionando para {login_url}")
        return redirect(login_url)
    
    app_url = 'crm-vendas'
    
    if loja.tipo_loja:
        tipo_codigo = loja.tipo_loja.codigo or ''
        if tipo_codigo in ('CLIEST', 'CLIBEL'):
            app_url = 'clinica-beleza/consultas'
        elif tipo_codigo == 'CABEL':
            app_url = 'cabeleireiro'
        elif tipo_codigo == 'ECOMM':
            app_url = 'e-commerce'
    
    dashboard_url = f'/loja/{loja.slug}/{app_url}'
    logger.info(f"[atalho_redirect] Usuário autenticado → Redirecionando para {dashboard_url}")
    
    return redirect(dashboard_url)
