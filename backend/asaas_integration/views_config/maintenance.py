"""Manutenção: limpeza e exclusão de lojas Asaas."""
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ..models import AsaasConfig
from ._common import IsSuperAdmin

logger = logging.getLogger(__name__)

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
