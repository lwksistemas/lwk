"""
Views para dashboard financeiro das lojas
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Loja, FinanceiroLoja, PagamentoLoja
from .serializers import FinanceiroLojaSerializer, PagamentoLojaSerializer
from .asaas_service import LojaAsaasService
import logging

logger = logging.getLogger(__name__)

class IsLojaOwner(permissions.BasePermission):
    """Permissão para proprietário da loja"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin tem acesso total
        if request.user.is_superuser:
            return True
        
        # Verificar se é proprietário de alguma loja
        return Loja.objects.filter(owner=request.user, is_active=True).exists()
    
    def has_object_permission(self, request, view, obj):
        # Super admin tem acesso total
        if request.user.is_superuser:
            return True
        
        # Verificar se é proprietário da loja específica
        if hasattr(obj, 'loja'):
            return obj.loja.owner == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class FinanceiroLojaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para financeiro das lojas (somente leitura para proprietários)"""
    serializer_class = FinanceiroLojaSerializer
    permission_classes = [IsLojaOwner]
    
    def get_queryset(self):
        user = self.request.user
        
        # Super admin vê tudo
        if user.is_superuser:
            return FinanceiroLoja.objects.select_related('loja').all()
        
        # Proprietário vê apenas suas lojas
        return FinanceiroLoja.objects.select_related('loja').filter(
            loja__owner=user,
            loja__is_active=True
        )
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Dashboard financeiro completo da loja"""
        financeiro = self.get_object()
        
        # Buscar pagamentos recentes
        pagamentos_recentes = PagamentoLoja.objects.filter(
            financeiro=financeiro
        ).order_by('-data_vencimento')[:5]
        
        # Estatísticas
        total_pagamentos = PagamentoLoja.objects.filter(financeiro=financeiro).count()
        pagamentos_pagos = PagamentoLoja.objects.filter(
            financeiro=financeiro, 
            status='pago'
        ).count()
        pagamentos_pendentes = PagamentoLoja.objects.filter(
            financeiro=financeiro, 
            status='pendente'
        ).count()
        
        return Response({
            'financeiro': self.get_serializer(financeiro).data,
            'pagamentos_recentes': PagamentoLojaSerializer(pagamentos_recentes, many=True).data,
            'estatisticas': {
                'total_pagamentos': total_pagamentos,
                'pagamentos_pagos': pagamentos_pagos,
                'pagamentos_pendentes': pagamentos_pendentes,
                'taxa_pagamento': (pagamentos_pagos / total_pagamentos * 100) if total_pagamentos > 0 else 0
            }
        })
    
    @action(detail=True, methods=['post'])
    def atualizar_status_asaas(self, request, pk=None):
        """Atualizar status do pagamento consultando Asaas"""
        financeiro = self.get_object()
        
        if not financeiro.asaas_payment_id:
            return Response(
                {'error': 'Pagamento não possui ID do Asaas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            asaas_service = LojaAsaasService()
            resultado = asaas_service.consultar_status_pagamento(financeiro.asaas_payment_id)
            
            if resultado.get('success'):
                # Atualizar status local baseado no Asaas
                asaas_status = resultado.get('status', '')
                
                if asaas_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                    financeiro.status_pagamento = 'ativo'
                    financeiro.ultimo_pagamento = resultado.get('payment_date')
                elif asaas_status == 'OVERDUE':
                    financeiro.status_pagamento = 'atrasado'
                else:
                    financeiro.status_pagamento = 'pendente'
                
                financeiro.save()
                
                return Response({
                    'message': 'Status atualizado com sucesso',
                    'status_asaas': asaas_status,
                    'status_local': financeiro.status_pagamento
                })
            else:
                return Response(
                    {'error': resultado.get('error', 'Erro ao consultar Asaas')},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status Asaas: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PagamentoLojaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para pagamentos das lojas (somente leitura para proprietários)"""
    serializer_class = PagamentoLojaSerializer
    permission_classes = [IsLojaOwner]
    
    def get_queryset(self):
        user = self.request.user
        
        # Super admin vê tudo
        if user.is_superuser:
            return PagamentoLoja.objects.select_related('loja', 'financeiro').all()
        
        # Proprietário vê apenas suas lojas
        return PagamentoLoja.objects.select_related('loja', 'financeiro').filter(
            loja__owner=user,
            loja__is_active=True
        )
    
    @action(detail=True, methods=['get'])
    def baixar_boleto_pdf(self, request, pk=None):
        """Baixar PDF do boleto via Asaas"""
        pagamento = self.get_object()
        
        if not pagamento.asaas_payment_id:
            return Response(
                {'error': 'Pagamento não possui ID do Asaas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            asaas_service = LojaAsaasService()
            pdf_content = asaas_service.baixar_pdf_boleto(pagamento.asaas_payment_id)
            
            if pdf_content:
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="boleto_{pagamento.loja.slug}_{pagamento.referencia_mes.strftime("%m_%Y")}.pdf"'
                return response
            else:
                return Response(
                    {'error': 'Não foi possível baixar o PDF do boleto'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Erro ao baixar PDF: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def meus_pagamentos(self, request):
        """Listar pagamentos do usuário logado"""
        user = request.user
        
        if user.is_superuser:
            pagamentos = self.get_queryset()
        else:
            # Buscar loja do usuário
            try:
                loja = Loja.objects.get(owner=user, is_active=True)
                pagamentos = PagamentoLoja.objects.filter(loja=loja).order_by('-data_vencimento')
            except Loja.DoesNotExist:
                return Response(
                    {'error': 'Usuário não possui loja associada'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Filtros opcionais
        status_filter = request.query_params.get('status')
        if status_filter:
            pagamentos = pagamentos.filter(status=status_filter)
        
        # Paginação
        page = self.paginate_queryset(pagamentos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(pagamentos, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_financeiro_loja(request, loja_slug):
    """Dashboard financeiro específico de uma loja"""
    
    # Verificar permissão
    if not request.user.is_superuser:
        loja = get_object_or_404(Loja, slug=loja_slug, owner=request.user, is_active=True)
    else:
        loja = get_object_or_404(Loja, slug=loja_slug, is_active=True)
    
    try:
        financeiro = loja.financeiro
    except FinanceiroLoja.DoesNotExist:
        return Response(
            {'error': 'Financeiro não encontrado para esta loja'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Buscar dados financeiros
    pagamentos = PagamentoLoja.objects.filter(loja=loja).order_by('-data_vencimento')
    
    # Estatísticas
    total_pagamentos = pagamentos.count()
    pagamentos_pagos = pagamentos.filter(status='pago').count()
    pagamentos_pendentes = pagamentos.filter(status='pendente').count()
    pagamentos_atrasados = pagamentos.filter(status='atrasado').count()
    
    valor_total_pago = sum(p.valor for p in pagamentos.filter(status='pago'))
    valor_total_pendente = sum(p.valor for p in pagamentos.filter(status__in=['pendente', 'atrasado']))
    
    # Próximo pagamento
    proximo_pagamento = pagamentos.filter(status='pendente').first()
    
    return Response({
        'loja': {
            'id': loja.id,
            'nome': loja.nome,
            'slug': loja.slug,
            'plano': loja.plano.nome,
            'tipo_assinatura': loja.get_tipo_assinatura_display()
        },
        'financeiro': {
            'status_pagamento': financeiro.get_status_pagamento_display(),
            'valor_mensalidade': float(financeiro.valor_mensalidade),
            'data_proxima_cobranca': financeiro.data_proxima_cobranca,
            'dia_vencimento': financeiro.dia_vencimento,
            'total_pago': float(financeiro.total_pago),
            'total_pendente': float(financeiro.total_pendente),
            'tem_asaas': bool(financeiro.asaas_payment_id),
            'boleto_url': financeiro.boleto_url,
            'pix_qr_code': financeiro.pix_qr_code,
            'pix_copy_paste': financeiro.pix_copy_paste
        },
        'estatisticas': {
            'total_pagamentos': total_pagamentos,
            'pagamentos_pagos': pagamentos_pagos,
            'pagamentos_pendentes': pagamentos_pendentes,
            'pagamentos_atrasados': pagamentos_atrasados,
            'valor_total_pago': float(valor_total_pago),
            'valor_total_pendente': float(valor_total_pendente),
            'taxa_pagamento': (pagamentos_pagos / total_pagamentos * 100) if total_pagamentos > 0 else 0
        },
        'proximo_pagamento': PagamentoLojaSerializer(proximo_pagamento).data if proximo_pagamento else None,
        'pagamentos_recentes': PagamentoLojaSerializer(pagamentos[:5], many=True).data
    })