"""
Views para dashboard financeiro das lojas
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
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
    
    @action(detail=True, methods=['post'])
    def gerar_pix(self, request, pk=None):
        """Gera PIX para um pagamento Mercado Pago que ainda não tem PIX (copia e cola + QR)."""
        pagamento = self.get_object()
        if getattr(pagamento, 'provedor_boleto', 'asaas') != 'mercadopago':
            return Response(
                {'error': 'Apenas pagamentos Mercado Pago podem gerar PIX aqui.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .mercadopago_service import LojaMercadoPagoService
        svc = LojaMercadoPagoService()
        result = svc.gerar_pix_para_pagamento(pagamento)
        if not result.get('success'):
            return Response(
                {'error': result.get('error', 'Não foi possível gerar o PIX.')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({
            'pix_copy_paste': result.get('pix_copy_paste', ''),
            'pix_qr_code': result.get('pix_qr_code'),
        })

    @action(detail=True, methods=['get'])
    def baixar_boleto_pdf(self, request, pk=None):
        """Baixar PDF do boleto (Asaas) ou redirecionar para o boleto (Mercado Pago)"""
        pagamento = self.get_object()
        
        # Boleto via Mercado Pago: sempre buscar URL completa na API (a salva é truncada a 200 chars e perde o hash)
        if getattr(pagamento, 'provedor_boleto', 'asaas') == 'mercadopago' and pagamento.mercadopago_payment_id:
            from .mercadopago_service import LojaMercadoPagoService
            mp_service = LojaMercadoPagoService()
            boleto_url = mp_service.get_boleto_url(pagamento.mercadopago_payment_id)
            if boleto_url:
                return Response({'boleto_url': boleto_url, 'provedor': 'mercadopago'})
            return Response(
                {'error': 'Link do boleto Mercado Pago não disponível. Verifique se o pagamento existe na conta (produção x sandbox).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Boleto via Asaas
        if not pagamento.asaas_payment_id:
            return Response(
                {'error': 'Pagamento não possui boleto (Asaas/Mercado Pago)'},
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
    
    # Estatísticas baseadas em PagamentoLoja
    total_pagamentos_loja = pagamentos.count()
    pagamentos_pagos_loja = pagamentos.filter(status='pago').count()
    pagamentos_pendentes_loja = pagamentos.filter(status='pendente').count()
    pagamentos_atrasados_loja = pagamentos.filter(status='atrasado').count()
    
    valor_total_pago_loja = sum(p.valor for p in pagamentos.filter(status='pago'))
    valor_total_pendente_loja = sum(p.valor for p in pagamentos.filter(status__in=['pendente', 'atrasado']))
    
    # Próximo pagamento
    proximo_pagamento = pagamentos.filter(status='pendente').first()
    
    # Buscar próximo boleto pendente no Asaas (mais recente)
    boleto_url = None
    pix_qr_code = None
    pix_copy_paste = None
    
    # Estatísticas do Asaas (mais precisas)
    total_pagamentos_asaas = 0
    pagamentos_pagos_asaas = 0
    pagamentos_pendentes_asaas = 0
    pagamentos_atrasados_asaas = 0
    valor_total_pago_asaas = 0
    valor_total_pendente_asaas = 0
    
    logger.info(f"🔍 Buscando boleto para loja: {loja.nome} (slug: {loja.slug})")
    
    try:
        from asaas_integration.models import LojaAssinatura, AsaasPayment
        from decimal import Decimal
        
        # Buscar assinatura da loja (Asaas); se não existir, loja pode ser Mercado Pago e usamos FinanceiroLoja
        try:
            loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
            logger.info(f"✅ LojaAssinatura encontrada: customer_id={loja_assinatura.asaas_customer.asaas_id}")
        except LojaAssinatura.DoesNotExist:
            # Loja com boleto Mercado Pago (ou sem assinatura Asaas): usar dados do FinanceiroLoja
            pix_qr_code = financeiro.pix_qr_code or ''
            pix_copy_paste = financeiro.pix_copy_paste or ''
            # URL do boleto MP: só da API (a salva é truncada a 200 chars e gera "Pagamento não encontrado")
            if getattr(financeiro, 'provedor_boleto', '') == 'mercadopago' and getattr(financeiro, 'mercadopago_payment_id', ''):
                from .mercadopago_service import LojaMercadoPagoService
                mp_svc = LojaMercadoPagoService()
                boleto_url = mp_svc.get_boleto_url(financeiro.mercadopago_payment_id) or ''
                # Não usar financeiro.boleto_url (truncada); se API falhar, front deve chamar baixar_boleto_pdf
            else:
                boleto_url = financeiro.boleto_url or ''
            logger.info(f"Loja {loja.slug} sem LojaAssinatura (provedor={getattr(financeiro, 'provedor_boleto', 'asaas')}), usando FinanceiroLoja")
            loja_assinatura = None

        if loja_assinatura is not None:
            # Buscar todos os pagamentos do customer para debug
            todos_pagamentos = AsaasPayment.objects.filter(
                customer=loja_assinatura.asaas_customer
            ).order_by('-due_date')

            logger.info(f"📊 Total de pagamentos no Asaas: {todos_pagamentos.count()}")
            for pag in todos_pagamentos[:5]:
                logger.info(f"   - ID: {pag.asaas_id}, Status: {pag.status}, Vencimento: {pag.due_date}, Valor: R$ {pag.value}")

            # Buscar próximo pagamento pendente (mais recente)
            proximo_boleto = AsaasPayment.objects.filter(
                customer=loja_assinatura.asaas_customer,
                status='PENDING',
                due_date__gte=timezone.now().date()
            ).order_by('due_date').first()

            if proximo_boleto:
                boleto_url = proximo_boleto.bank_slip_url or proximo_boleto.invoice_url
                pix_qr_code = proximo_boleto.pix_qr_code
                pix_copy_paste = proximo_boleto.pix_copy_paste

                logger.info(f"✅ Próximo boleto encontrado para {loja.nome}:")
                logger.info(f"   - ID: {proximo_boleto.asaas_id}")
                logger.info(f"   - Vencimento: {proximo_boleto.due_date}")
                logger.info(f"   - Status: {proximo_boleto.status}")
                logger.info(f"   - Boleto URL: {boleto_url[:50] if boleto_url else 'None'}...")
                logger.info(f"   - PIX: {'Sim' if pix_copy_paste else 'Não'}")
            else:
                logger.warning(f"⚠️ Nenhum boleto pendente encontrado para {loja.nome}")
                logger.warning(f"   - Data atual: {timezone.now().date()}")
                logger.warning(f"   - Filtro: status=PENDING, due_date >= {timezone.now().date()}")

            # Calcular estatísticas do Asaas
            total_pagamentos_asaas = todos_pagamentos.count()
            pagamentos_pagos_asaas = todos_pagamentos.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']).count()
            pagamentos_pendentes_asaas = todos_pagamentos.filter(status='PENDING').count()
            pagamentos_atrasados_asaas = todos_pagamentos.filter(status='OVERDUE').count()

            # Calcular valores
            for pag in todos_pagamentos.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']):
                valor_total_pago_asaas += Decimal(str(pag.value))

            for pag in todos_pagamentos.filter(status__in=['PENDING', 'OVERDUE']):
                valor_total_pendente_asaas += Decimal(str(pag.value))

            logger.info(f"📊 Estatísticas do Asaas para {loja.nome}:")
            logger.info(f"   - Total: {total_pagamentos_asaas}")
            logger.info(f"   - Pagos: {pagamentos_pagos_asaas}")
            logger.info(f"   - Pendentes: {pagamentos_pendentes_asaas}")
            logger.info(f"   - Atrasados: {pagamentos_atrasados_asaas}")
            logger.info(f"   - Valor pago: R$ {valor_total_pago_asaas}")
            logger.info(f"   - Valor pendente: R$ {valor_total_pendente_asaas}")

    except Exception as e:
        logger.error(f"❌ Erro ao buscar boleto do Asaas para {loja.nome}: {e}")
        import traceback
        logger.error(f"Traceback completo:")
        logger.error(traceback.format_exc())
        import traceback
        traceback.print_exc()
        # Fallback para dados do FinanceiroLoja
        boleto_url = financeiro.boleto_url
        pix_qr_code = financeiro.pix_qr_code
        pix_copy_paste = financeiro.pix_copy_paste
        logger.info(f"   - Usando fallback: boleto_url={boleto_url[:50] if boleto_url else 'None'}")
    
    # Usar estatísticas do Asaas se disponíveis, senão usar do PagamentoLoja
    total_pagamentos = total_pagamentos_asaas if total_pagamentos_asaas > 0 else total_pagamentos_loja
    pagamentos_pagos = pagamentos_pagos_asaas if total_pagamentos_asaas > 0 else pagamentos_pagos_loja
    pagamentos_pendentes = pagamentos_pendentes_asaas if total_pagamentos_asaas > 0 else pagamentos_pendentes_loja
    pagamentos_atrasados = pagamentos_atrasados_asaas if total_pagamentos_asaas > 0 else pagamentos_atrasados_loja
    valor_total_pago = float(valor_total_pago_asaas) if total_pagamentos_asaas > 0 else valor_total_pago_loja
    valor_total_pendente = float(valor_total_pendente_asaas) if total_pagamentos_asaas > 0 else valor_total_pendente_loja
    
    logger.info(f"📊 Estatísticas finais para {loja.nome}:")
    logger.info(f"   - Total Pagamentos: {total_pagamentos} (Asaas: {total_pagamentos_asaas}, Loja: {total_pagamentos_loja})")
    logger.info(f"   - Pagos: {pagamentos_pagos} (Asaas: {pagamentos_pagos_asaas}, Loja: {pagamentos_pagos_loja})")
    logger.info(f"   - Pendentes: {pagamentos_pendentes} (Asaas: {pagamentos_pendentes_asaas}, Loja: {pagamentos_pendentes_loja})")
    logger.info(f"   - Atrasados: {pagamentos_atrasados} (Asaas: {pagamentos_atrasados_asaas}, Loja: {pagamentos_atrasados_loja})")
    logger.info(f"   - Valor Pago: R$ {valor_total_pago} (Asaas: {valor_total_pago_asaas}, Loja: {valor_total_pago_loja})")
    logger.info(f"   - Valor Pendente: R$ {valor_total_pendente} (Asaas: {valor_total_pendente_asaas}, Loja: {valor_total_pendente_loja})")
    
    # Preparar histórico: Asaas e/ou cobrança atual Mercado Pago
    historico_pagamentos = []
    try:
        if 'todos_pagamentos' in locals() and todos_pagamentos:
            for pag in todos_pagamentos:
                # Determinar status display de forma limpa
                if pag.status in ['RECEIVED', 'CONFIRMED']:
                    status_display = 'Recebida'
                elif pag.status == 'PENDING':
                    status_display = 'Aguardando pagamento'
                else:
                    status_display = 'Vencida'
                
                historico_pagamentos.append({
                    'id': pag.id,
                    'asaas_id': pag.asaas_id,
                    'valor': float(pag.value),
                    'status': pag.status,
                    'status_display': status_display,
                    'data_vencimento': pag.due_date.strftime('%Y-%m-%d') if pag.due_date else None,
                    'data_pagamento': pag.payment_date.strftime('%Y-%m-%d') if pag.payment_date else None,
                    'boleto_url': pag.bank_slip_url or pag.invoice_url,
                    'is_paid': pag.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH'],
                    'is_pending': pag.status == 'PENDING',
                    'is_overdue': pag.status == 'OVERDUE'
                })
            logger.info(f"✅ Histórico preparado: {len(historico_pagamentos)} pagamentos")
    except Exception as e:
        logger.error(f"❌ Erro ao preparar histórico: {e}")

    # Se for loja só Mercado Pago e tiver boleto, incluir cobrança atual no histórico para aparecer no dashboard
    if not historico_pagamentos and boleto_url and getattr(financeiro, 'provedor_boleto', '') == 'mercadopago':
        historico_pagamentos.append({
            'id': getattr(financeiro, 'id', 0),
            'asaas_id': getattr(financeiro, 'mercadopago_payment_id', '') or '',
            'valor': float(financeiro.valor_mensalidade),
            'status': 'PENDING',
            'status_display': 'Aguardando pagamento',
            'data_vencimento': financeiro.data_proxima_cobranca.strftime('%Y-%m-%d') if financeiro.data_proxima_cobranca else None,
            'data_pagamento': None,
            'boleto_url': boleto_url,
            'is_paid': False,
            'is_pending': True,
            'is_overdue': False,
        })
        logger.info(f"✅ Histórico MP: 1 cobrança atual incluída para {loja.nome}")
    
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
            'data_proxima_cobranca': financeiro.data_proxima_cobranca.strftime('%Y-%m-%d') if financeiro.data_proxima_cobranca else None,
            'ultimo_pagamento': financeiro.ultimo_pagamento.strftime('%Y-%m-%d') if financeiro.ultimo_pagamento else None,
            'dia_vencimento': financeiro.dia_vencimento,
            'total_pago': float(financeiro.total_pago),
            'total_pendente': float(financeiro.total_pendente),
            'tem_asaas': bool(financeiro.asaas_payment_id) or bool(boleto_url),
            'tem_mercadopago': bool(getattr(financeiro, 'mercadopago_payment_id', None)) or getattr(financeiro, 'provedor_boleto', 'asaas') == 'mercadopago',
            'provedor_boleto': getattr(financeiro, 'provedor_boleto', 'asaas'),
            'asaas_customer_id': financeiro.asaas_customer_id,
            'asaas_payment_id': financeiro.asaas_payment_id,
            'boleto_url': boleto_url,
            'pix_qr_code': pix_qr_code,
            'pix_copy_paste': pix_copy_paste
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
        'pagamentos_recentes': PagamentoLojaSerializer(pagamentos[:5], many=True).data,
        'historico_pagamentos': historico_pagamentos
    })


def _financeiro_unificado_stats():
    """Estatísticas unificadas (Asaas + Mercado Pago) para superadmin."""
    from asaas_integration.models import LojaAssinatura, AsaasPayment
    from django.db.models import Sum
    from decimal import Decimal

    # Asaas
    total_asaas = LojaAssinatura.objects.count()
    ativas_asaas = LojaAssinatura.objects.filter(ativa=True).count()
    pag_asaas = AsaasPayment.objects
    pendentes_asaas = pag_asaas.filter(status='PENDING').count()
    pagos_asaas = pag_asaas.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']).count()
    vencidos_asaas = pag_asaas.filter(status='OVERDUE').count()
    receita_asaas = pag_asaas.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']).aggregate(t=Sum('value'))['t'] or Decimal('0')
    pendente_asaas = pag_asaas.filter(status__in=['PENDING', 'OVERDUE']).aggregate(t=Sum('value'))['t'] or Decimal('0')

    # Mercado Pago (FinanceiroLoja com boleto MP)
    mp_fin = FinanceiroLoja.objects.filter(provedor_boleto='mercadopago', mercadopago_payment_id__isnull=False).exclude(mercadopago_payment_id='')
    total_mp = mp_fin.count()
    pendente_mp = sum(f.valor_mensalidade for f in mp_fin)

    return {
        'total_assinaturas': total_asaas + total_mp,
        'assinaturas_ativas': ativas_asaas + total_mp,
        'pagamentos_pendentes': pendentes_asaas + total_mp,
        'pagamentos_pagos': pagos_asaas,
        'pagamentos_vencidos': vencidos_asaas,
        'receita_total': float(receita_asaas),
        'receita_pendente': float(pendente_asaas) + float(pendente_mp),
    }


def _assinaturas_unificado():
    """Lista unificada de assinaturas (Asaas + Mercado Pago) no formato esperado pelo frontend."""
    from asaas_integration.models import LojaAssinatura
    from asaas_integration.serializers import LojaAssinaturaSerializer

    out = []
    # Asaas
    for a in LojaAssinatura.objects.all().select_related('asaas_customer', 'current_payment').order_by('-created_at'):
        out.append(LojaAssinaturaSerializer(a).data)
    # Mercado Pago (FinanceiroLoja com boleto)
    for f in FinanceiroLoja.objects.filter(
        provedor_boleto='mercadopago'
    ).exclude(mercadopago_payment_id='').select_related('loja', 'loja__plano'):
        loja = f.loja
        data_venc = f.data_proxima_cobranca.strftime('%Y-%m-%d') if f.data_proxima_cobranca else ''
        # ID do PagamentoLoja (pendente ou último) para o endpoint baixar_boleto_pdf
        pagamento_atual = (
            PagamentoLoja.objects.filter(loja=loja, financeiro=f, status='pendente')
            .order_by('-data_vencimento')
            .first()
        )
        if not pagamento_atual:
            pagamento_atual = (
                PagamentoLoja.objects.filter(loja=loja, financeiro=f)
                .order_by('-data_vencimento')
                .first()
            )
        payment_pk = pagamento_atual.id if pagamento_atual else None
        # PIX: preferir do PagamentoLoja (pagamento atual), senão do FinanceiroLoja
        pix_cp = ''
        pix_qr = ''
        if pagamento_atual and (pagamento_atual.pix_copy_paste or pagamento_atual.pix_qr_code):
            pix_cp = pagamento_atual.pix_copy_paste or ''
            pix_qr = pagamento_atual.pix_qr_code or ''
        else:
            pix_cp = f.pix_copy_paste or ''
            pix_qr = f.pix_qr_code or ''
        # Status real: pagamento_atual.status (pago/pendente/atrasado)
        is_pago = pagamento_atual and getattr(pagamento_atual, 'status', '') == 'pago'
        status_mp = 'RECEIVED' if is_pago else 'PENDING'
        status_display_mp = 'Pago' if is_pago else 'Pendente'
        out.append({
            'id': f'mp-{f.id}',
            'loja_slug': loja.slug,
            'loja_nome': loja.nome,
            'plano_nome': loja.plano.nome if loja.plano else 'Plano',
            'plano_valor': str(f.valor_mensalidade),
            'ativa': True,
            'data_vencimento': data_venc,
            'total_payments': 1,
            'current_payment_data': {
                'id': payment_pk,
                'asaas_id': f.mercadopago_payment_id,
                'provedor': 'mercadopago',
                'customer_name': loja.nome,
                'value': str(f.valor_mensalidade),
                'status': status_mp,
                'status_display': status_display_mp,
                'due_date': data_venc,
                'bank_slip_url': f.boleto_url or '',
                'pix_copy_paste': pix_cp,
                'pix_qr_code': pix_qr or None,
                'is_paid': is_pago,
                'is_pending': not is_pago,
                'is_overdue': False,
            },
        })
    return out


def _pagamentos_unificado():
    """Lista unificada de pagamentos (Asaas + Mercado Pago) no formato esperado pelo frontend."""
    from asaas_integration.models import AsaasPayment
    from asaas_integration.serializers import AsaasPaymentSerializer

    out = []
    for p in AsaasPayment.objects.all().select_related('customer').order_by('-due_date'):
        d = AsaasPaymentSerializer(p).data
        d['provedor'] = 'asaas'
        out.append(d)
    for f in FinanceiroLoja.objects.filter(
        provedor_boleto='mercadopago'
    ).exclude(mercadopago_payment_id='').select_related('loja'):
        data_venc = f.data_proxima_cobranca.strftime('%Y-%m-%d') if f.data_proxima_cobranca else ''
        pag = (
            PagamentoLoja.objects.filter(loja=f.loja, financeiro=f)
            .order_by('-data_vencimento')
            .first()
        )
        payment_pk = pag.id if pag else f.id
        pix_cp = (pag.pix_copy_paste if pag else '') or f.pix_copy_paste or ''
        is_pago = pag and getattr(pag, 'status', '') == 'pago'
        payment_date_str = pag.data_pagamento.strftime('%Y-%m-%d') if pag and getattr(pag, 'data_pagamento', None) else None
        out.append({
            'id': payment_pk,
            'asaas_id': f.mercadopago_payment_id,
            'customer_name': f.loja.nome,
            'customer_email': getattr(f.loja.owner, 'email', ''),
            'value': str(f.valor_mensalidade),
            'status': 'RECEIVED' if is_pago else 'PENDING',
            'status_display': 'Pago' if is_pago else 'Pendente',
            'due_date': data_venc,
            'payment_date': payment_date_str,
            'bank_slip_url': f.boleto_url or '',
            'pix_copy_paste': pix_cp,
            'is_paid': is_pago,
            'is_pending': not is_pago,
            'is_overdue': False,
            'provedor': 'mercadopago',
        })
    return out


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financeiro_unificado(request):
    """
    Resumo financeiro unificado para superadmin: Asaas + Mercado Pago.
    Retorna stats, assinaturas e pagamentos no mesmo formato dos endpoints Asaas
    para compatibilidade com a página /superadmin/financeiro.
    """
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        stats = _financeiro_unificado_stats()
        assinaturas = _assinaturas_unificado()
        pagamentos = _pagamentos_unificado()
        # Mesmo formato dos 3 endpoints Asaas: stats no top level + results para listas
        data = {**stats, 'assinaturas': assinaturas, 'pagamentos': pagamentos}
        return Response(data)
    except Exception as e:
        logger.exception("financeiro_unificado: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)