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
from django.db import models
from .models import Loja, FinanceiroLoja, PagamentoLoja
from .serializers import FinanceiroLojaSerializer, PagamentoLojaSerializer
from .asaas_service import LojaAsaasService
import logging

logger = logging.getLogger(__name__)


def _mercadopago_payment_ids_for_boleto(pagamento):
    """IDs MP únicos para tentar obter URL do boleto (linha do pagamento + financeiro)."""
    ids = []
    pid = (getattr(pagamento, 'mercadopago_payment_id', None) or '').strip()
    if pid:
        ids.append(pid)
    fin = getattr(pagamento, 'financeiro', None)
    if fin:
        fid = (getattr(fin, 'mercadopago_payment_id', None) or '').strip()
        if fid and fid not in ids:
            ids.append(fid)
    return ids


def _resolve_asaas_payment_id(pagamento):
    """
    ID do pagamento Asaas: prioriza PagamentoLoja, depois FinanceiroLoja,
    depois cobrança pendente/vencida na assinatura Asaas com mesma data de vencimento.
    """
    pid = (getattr(pagamento, 'asaas_payment_id', None) or '').strip()
    if pid:
        return pid
    fin = getattr(pagamento, 'financeiro', None)
    if fin:
        pid = (getattr(fin, 'asaas_payment_id', None) or '').strip()
        if pid:
            return pid
    try:
        from asaas_integration.models import LojaAssinatura, AsaasPayment

        ass = (
            LojaAssinatura.objects.filter(loja_slug=pagamento.loja.slug)
            .select_related('asaas_customer')
            .first()
        )
        if not ass:
            return ''
        qs = AsaasPayment.objects.filter(
            customer=ass.asaas_customer,
            status__in=['PENDING', 'OVERDUE'],
        ).order_by('-due_date')
        due = getattr(pagamento, 'data_vencimento', None)
        if due:
            m = qs.filter(due_date=due).first()
            if m and m.asaas_id:
                logger.info(
                    'baixar_boleto: asaas_id resolvido via AsaasPayment (data=%s) id=%s',
                    due,
                    m.asaas_id,
                )
                return m.asaas_id
        m = qs.first()
        if m and m.asaas_id:
            logger.info(
                'baixar_boleto: asaas_id resolvido via último PENDING/OVERDUE id=%s',
                m.asaas_id,
            )
            return m.asaas_id
    except Exception as e:
        logger.warning('baixar_boleto: fallback AsaasPayment: %s', e)
    return ''


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
        
        # Mercado Pago: tentar todos os IDs (PagamentoLoja + FinanceiroLoja); URL salva pode estar truncada
        if getattr(pagamento, 'provedor_boleto', 'asaas') == 'mercadopago':
            from .mercadopago_service import LojaMercadoPagoService

            mp_service = LojaMercadoPagoService()
            for mp_id in _mercadopago_payment_ids_for_boleto(pagamento):
                boleto_url = mp_service.get_boleto_url(mp_id)
                if boleto_url:
                    return Response({'boleto_url': boleto_url, 'provedor': 'mercadopago'})
            return Response(
                {
                    'error': (
                        'Não foi possível obter o link do boleto no Mercado Pago. '
                        'Confirme se a cobrança é por boleto (não só PIX) e se o token MP é de produção. '
                        'Se o problema continuar, use o PIX ou atualize o status da cobrança no painel.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Asaas: ID pode estar só no FinanceiroLoja ou na assinatura Asaas
        asaas_id = _resolve_asaas_payment_id(pagamento)
        if not asaas_id:
            return Response(
                {
                    'error': (
                        'Nenhum ID de cobrança Asaas vinculado a este pagamento. '
                        'Gere uma nova cobrança ou sincronize os dados no suporte.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            asaas_service = LojaAsaasService()
            pdf_content = asaas_service.baixar_pdf_boleto(asaas_id)
            
            if pdf_content:
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="boleto_{pagamento.loja.slug}_{pagamento.referencia_mes.strftime("%m_%Y")}.pdf"'
                return response
            else:
                return Response(
                    {
                        'error': (
                            'O Asaas não retornou o PDF (cobrança pode ser só PIX, cancelada ou expirada). '
                            'Use o PIX na tela ou atualize o status da assinatura.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Erro ao baixar PDF: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='baixar_boleto_mercadopago')
    def baixar_boleto_mercadopago(self, request):
        """Baixar boleto do Mercado Pago usando mercadopago_payment_id"""
        mp_payment_id = request.query_params.get('payment_id')
        
        if not mp_payment_id:
            return Response(
                {'error': 'payment_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .mercadopago_service import LojaMercadoPagoService
            mp_service = LojaMercadoPagoService()
            boleto_url = mp_service.get_boleto_url(mp_payment_id)
            
            if boleto_url:
                return Response({'boleto_url': boleto_url, 'provedor': 'mercadopago'})
            
            return Response(
                {'error': 'Link do boleto Mercado Pago não disponível. Verifique se o pagamento existe na conta (produção/sandbox).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erro ao buscar boleto MP: {e}")
            return Response(
                {'error': f'Erro ao buscar boleto: {str(e)}'},
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
                    'mercadopago_payment_id': '',  # ✅ NOVO v736: Vazio para Asaas
                    'provedor_boleto': 'asaas',  # ✅ NOVO v736: Identificar provedor
                    'valor': float(pag.value),
                    'status': pag.status,
                    'status_display': status_display,
                    'data_vencimento': pag.due_date.strftime('%Y-%m-%d') if pag.due_date else None,
                    'data_pagamento': pag.payment_date.strftime('%Y-%m-%d') if pag.payment_date else None,
                    'boleto_url': pag.bank_slip_url or pag.invoice_url,
                    'pix_copy_paste': pag.pix_copy_paste or '',  # ✅ NOVO v735: Incluir PIX no histórico
                    'pix_qr_code': pag.pix_qr_code or '',  # ✅ NOVO v735: Incluir QR Code no histórico
                    'is_paid': pag.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH'],
                    'is_pending': pag.status == 'PENDING',
                    'is_overdue': pag.status == 'OVERDUE'
                })
            logger.info(f"✅ Histórico preparado: {len(historico_pagamentos)} pagamentos")
    except Exception as e:
        logger.error(f"❌ Erro ao preparar histórico: {e}")

    # Se for loja só Mercado Pago e tiver boleto, incluir cobrança atual no histórico para aparecer no dashboard
    if not historico_pagamentos and boleto_url and getattr(financeiro, 'provedor_boleto', '') == 'mercadopago':
        # Buscar PagamentoLoja correspondente (pendente ou mais recente)
        pagamento_mp = PagamentoLoja.objects.filter(
            loja=loja,
            financeiro=financeiro,
            provedor_boleto='mercadopago'
        ).order_by('-data_vencimento').first()
        
        # Se não existir PagamentoLoja, criar um temporário para o histórico
        if not pagamento_mp:
            logger.warning(f"⚠️ PagamentoLoja não encontrado para loja MP {loja.nome}, criando entrada temporária")
            pagamento_id = 0  # ID temporário, frontend não conseguirá baixar boleto
        else:
            pagamento_id = pagamento_mp.id
        
        historico_pagamentos.append({
            'id': pagamento_id,
            'asaas_id': getattr(financeiro, 'mercadopago_payment_id', '') or '',
            'mercadopago_payment_id': getattr(financeiro, 'mercadopago_payment_id', '') or '',  # ✅ NOVO v736: ID do MP
            'provedor_boleto': 'mercadopago',  # ✅ NOVO v736: Identificar provedor
            'valor': float(financeiro.valor_mensalidade),
            'status': 'PENDING',
            'status_display': 'Aguardando pagamento',
            'data_vencimento': financeiro.data_proxima_cobranca.strftime('%Y-%m-%d') if financeiro.data_proxima_cobranca else None,
            'data_pagamento': None,
            'boleto_url': boleto_url,
            'pix_copy_paste': pix_copy_paste or '',  # ✅ NOVO v736: Incluir PIX
            'pix_qr_code': pix_qr_code or '',  # ✅ NOVO v736: Incluir QR Code
            'is_paid': False,
            'is_pending': True,
            'is_overdue': False,
        })
        logger.info(f"✅ Histórico MP: 1 cobrança atual incluída para {loja.nome} (PagamentoLoja ID: {pagamento_id})")

    # Fallback: se for Mercado Pago e não tiver PIX dinâmico, usar chave PIX estática da config
    if getattr(financeiro, 'provedor_boleto', '') == 'mercadopago' and not (pix_copy_paste or '').strip():
        try:
            from .models import MercadoPagoConfig
            mp_config = MercadoPagoConfig.get_config()
            chave = (getattr(mp_config, 'chave_pix_estatica', '') or '').strip()
            if chave:
                pix_copy_paste = chave
                logger.info(f"Usando chave PIX estática como fallback para loja {loja.nome}")
        except Exception:
            pass

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

    # Asaas (AsaasPayment local)
    total_asaas = LojaAssinatura.objects.count()
    ativas_asaas = LojaAssinatura.objects.filter(ativa=True).count()
    pag_asaas = AsaasPayment.objects
    pagos_asaas_count = pag_asaas.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']).count()
    vencidos_asaas = pag_asaas.filter(status='OVERDUE').count()
    receita_asaas = pag_asaas.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']).aggregate(t=Sum('value'))['t'] or Decimal('0')
    pendente_asaas = pag_asaas.filter(status__in=['PENDING', 'OVERDUE']).aggregate(t=Sum('value'))['t'] or Decimal('0')
    pendentes_asaas_count = pag_asaas.filter(status='PENDING').count()

    # PagamentoLoja pagos que não estão no AsaasPayment (pagamentos antigos)
    asaas_ids_locais = set(pag_asaas.values_list('asaas_id', flat=True))
    pl_pagos = PagamentoLoja.objects.filter(status='pago').exclude(asaas_payment_id__in=asaas_ids_locais)
    receita_pl = pl_pagos.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    pagos_pl_count = pl_pagos.count()

    # Mercado Pago (FinanceiroLoja com boleto MP)
    mp_fin = FinanceiroLoja.objects.filter(provedor_boleto='mercadopago', mercadopago_payment_id__isnull=False).exclude(mercadopago_payment_id='')
    total_mp = mp_fin.count()
    pendente_mp = sum(f.valor_mensalidade for f in mp_fin)

    return {
        'total_assinaturas': total_asaas + total_mp,
        'assinaturas_ativas': ativas_asaas + total_mp,
        'pagamentos_pendentes': pendentes_asaas_count + total_mp,
        'pagamentos_pagos': pagos_asaas_count + pagos_pl_count,
        'pagamentos_vencidos': vencidos_asaas,
        'receita_total': float(receita_asaas + receita_pl),
        'receita_pendente': float(pendente_asaas) + float(pendente_mp),
    }


def _assinaturas_unificado():
    """Lista unificada de assinaturas (Asaas + Mercado Pago) no formato esperado pelo frontend."""
    from asaas_integration.models import LojaAssinatura, AsaasPayment
    from asaas_integration.serializers import LojaAssinaturaSerializer

    out = []
    # Asaas
    for a in LojaAssinatura.objects.all().select_related('asaas_customer', 'current_payment').order_by('-created_at'):
        data = LojaAssinaturaSerializer(a).data

        # Histórico: combinar AsaasPayment + PagamentoLoja para cobrir todos os cenários
        history = []
        seen_asaas_ids = set()

        # 1) AsaasPayment (pagamentos registrados no Asaas local)
        ap_qs = AsaasPayment.objects.filter(
            models.Q(external_reference__contains=f"loja_{a.loja_slug}") |
            models.Q(customer=a.asaas_customer)
        ).order_by('-due_date').distinct()[:20]
        for p in ap_qs:
            seen_asaas_ids.add(p.asaas_id)
            history.append({
                'id': p.id,
                'asaas_id': p.asaas_id,
                'value': str(p.value),
                'status': p.status,
                'status_display': p.get_status_display(),
                'due_date': p.due_date.strftime('%Y-%m-%d') if p.due_date else None,
                'payment_date': p.payment_date.strftime('%Y-%m-%d') if p.payment_date else None,
                'is_paid': p.is_paid,
                'bank_slip_url': p.bank_slip_url or '',
            })

        # 2) PagamentoLoja (histórico local que pode ter pagamentos não presentes no AsaasPayment)
        try:
            from superadmin.models import Loja as LojaModel
            loja_obj = LojaModel.objects.filter(slug=a.loja_slug).first()
            if loja_obj:
                for pl in PagamentoLoja.objects.filter(loja=loja_obj).order_by('-data_vencimento')[:20]:
                    aid = pl.asaas_payment_id or ''
                    if aid and aid in seen_asaas_ids:
                        continue  # já incluído via AsaasPayment
                    status_map = {'pago': 'RECEIVED', 'pendente': 'PENDING', 'atrasado': 'OVERDUE', 'cancelado': 'REFUNDED'}
                    history.append({
                        'id': pl.id,
                        'asaas_id': aid,
                        'value': str(pl.valor),
                        'status': status_map.get(pl.status, 'PENDING'),
                        'status_display': pl.get_status_display(),
                        'due_date': pl.data_vencimento.strftime('%Y-%m-%d') if pl.data_vencimento else None,
                        'payment_date': pl.data_pagamento.strftime('%Y-%m-%d') if pl.data_pagamento else None,
                        'is_paid': pl.status == 'pago',
                        'bank_slip_url': pl.boleto_url or '',
                    })
        except Exception:
            pass

        # Ordenar por data de vencimento (mais recente primeiro)
        history.sort(key=lambda x: x.get('due_date') or '', reverse=True)
        data['payment_history'] = history[:20]
        out.append(data)
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
        
        # ✅ NOVO v730: Status da assinatura (não do próximo pagamento)
        subscription_status = 'active' if f.status_pagamento == 'ativo' else 'inactive'
        subscription_status_display = 'Ativo' if f.status_pagamento == 'ativo' else 'Inativo'
        
        out.append({
            'id': f'mp-{f.id}',
            'loja_slug': loja.slug,
            'loja_nome': loja.nome,
            'plano_nome': loja.plano.nome if loja.plano else 'Plano',
            'plano_valor': str(f.valor_mensalidade),
            'ativa': f.status_pagamento == 'ativo',  # ✅ Baseado no status real
            'subscription_status': subscription_status,  # ✅ NOVO v730
            'subscription_status_display': subscription_status_display,  # ✅ NOVO v730
            'data_vencimento': data_venc,
            'total_payments': 1,
            'financeiro_id': f.id,
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
            'payment_history': [
                {
                    'id': p.id,
                    'asaas_id': p.mercadopago_payment_id or p.asaas_payment_id or '',
                    'value': str(p.valor),
                    'status': 'RECEIVED' if p.status == 'pago' else 'PENDING' if p.status == 'pendente' else 'OVERDUE',
                    'status_display': p.get_status_display(),
                    'due_date': p.data_vencimento.strftime('%Y-%m-%d') if p.data_vencimento else None,
                    'payment_date': p.data_pagamento.strftime('%Y-%m-%d') if p.data_pagamento else None,
                    'is_paid': p.status == 'pago',
                    'bank_slip_url': p.boleto_url or '',
                }
                for p in PagamentoLoja.objects.filter(loja=loja, financeiro=f).order_by('-data_vencimento')[:20]
            ],
        })
    return out


def _pagamentos_unificado():
    """Lista unificada de pagamentos (Asaas + Mercado Pago) no formato esperado pelo frontend."""
    from asaas_integration.models import AsaasPayment
    from asaas_integration.serializers import AsaasPaymentSerializer

    out = []
    seen_asaas_ids = set()

    # 1) AsaasPayment (pagamentos registrados localmente do Asaas)
    for p in AsaasPayment.objects.all().select_related('customer').order_by('-due_date'):
        d = AsaasPaymentSerializer(p).data
        d['provedor'] = 'asaas'
        out.append(d)
        if p.asaas_id:
            seen_asaas_ids.add(p.asaas_id)

    # 2) PagamentoLoja Asaas que não estão no AsaasPayment (pagamentos antigos)
    for pl in PagamentoLoja.objects.filter(
        provedor_boleto='asaas'
    ).exclude(
        asaas_payment_id=''
    ).select_related('loja', 'loja__owner', 'financeiro').order_by('-data_vencimento'):
        if pl.asaas_payment_id in seen_asaas_ids:
            continue
        status_map = {'pago': 'RECEIVED', 'pendente': 'PENDING', 'atrasado': 'OVERDUE', 'cancelado': 'REFUNDED'}
        is_pago = pl.status == 'pago'
        out.append({
            'id': pl.id,
            'asaas_id': pl.asaas_payment_id,
            'customer_name': pl.loja.nome,
            'customer_email': getattr(pl.loja.owner, 'email', '') if pl.loja.owner else '',
            'value': str(pl.valor),
            'status': status_map.get(pl.status, 'PENDING'),
            'status_display': pl.get_status_display(),
            'due_date': pl.data_vencimento.strftime('%Y-%m-%d') if pl.data_vencimento else None,
            'payment_date': pl.data_pagamento.strftime('%Y-%m-%d') if pl.data_pagamento else None,
            'bank_slip_url': pl.boleto_url or '',
            'pix_copy_paste': pl.pix_copy_paste or '',
            'is_paid': is_pago,
            'is_pending': pl.status == 'pendente',
            'is_overdue': pl.status == 'atrasado',
            'provedor': 'asaas',
        })

    # 3) Mercado Pago
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



def _get_asaas_client():
    """Retorna cliente Asaas configurado ou None."""
    from asaas_integration.models import AsaasConfig
    from asaas_integration.client import AsaasClient
    config = AsaasConfig.get_config()
    if not config or not config.api_key:
        return None
    return AsaasClient(api_key=config.api_key, sandbox=config.sandbox)


def _find_invoice_for_payment(client, payment_id):
    """Busca nota fiscal autorizada para um payment_id no Asaas."""
    response = client._make_request('GET', 'invoices', {'payment': payment_id})
    invoices = response.get('data', [])
    if not invoices:
        return None, invoices
    # Priorizar nota autorizada
    for inv in invoices:
        if inv.get('status') == 'AUTHORIZED':
            return inv, invoices
    return invoices[0], invoices


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nf_baixar_por_payment(request, payment_id):
    """Baixar PDF da nota fiscal de um pagamento específico do Asaas."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        client = _get_asaas_client()
        if not client:
            return Response({'success': False, 'error': 'Asaas não configurado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice, invoices = _find_invoice_for_payment(client, payment_id)
        if not invoice:
            return Response({'success': False, 'error': 'Nenhuma nota fiscal encontrada para este pagamento'}, status=status.HTTP_404_NOT_FOUND)

        status_nf = invoice.get('status')
        if status_nf != 'AUTHORIZED':
            return Response({'success': False, 'error': f'Nota fiscal não autorizada. Status: {status_nf}'}, status=status.HTTP_400_BAD_REQUEST)

        pdf_url = invoice.get('pdfUrl') or invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
        if not pdf_url:
            return Response({'success': False, 'error': 'URL do PDF não disponível'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'success': True, 'pdf_url': pdf_url, 'invoice_id': invoice.get('id'), 'status': status_nf})
    except Exception as e:
        logger.exception("nf_baixar_por_payment: %s", e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nf_reenviar_por_payment(request, payment_id):
    """Reenvia nota fiscal por email para o dono da loja do pagamento."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        from asaas_integration.models import AsaasPayment as AP
        from django.core.mail import EmailMessage
        from django.conf import settings

        client = _get_asaas_client()
        if not client:
            return Response({'success': False, 'error': 'Asaas não configurado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice, _ = _find_invoice_for_payment(client, payment_id)
        if not invoice:
            return Response({'success': False, 'error': 'Nenhuma nota fiscal encontrada'}, status=status.HTTP_404_NOT_FOUND)

        if invoice.get('status') != 'AUTHORIZED':
            return Response({'success': False, 'error': f'NF não autorizada. Status: {invoice.get("status")}'}, status=status.HTTP_400_BAD_REQUEST)

        pdf_url = invoice.get('pdfUrl') or invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
        if not pdf_url:
            return Response({'success': False, 'error': 'URL do PDF não disponível'}, status=status.HTTP_404_NOT_FOUND)

        # Buscar loja pelo pagamento
        payment_obj = AP.objects.filter(asaas_id=payment_id).select_related('customer').first()
        email_destino = None
        loja_nome = 'Loja'
        if payment_obj and payment_obj.customer:
            email_destino = payment_obj.customer.email
            loja_nome = payment_obj.customer.name
        if not email_destino:
            # Tentar via FinanceiroLoja
            fin = FinanceiroLoja.objects.filter(asaas_payment_id=payment_id).select_related('loja', 'loja__owner').first()
            if fin:
                email_destino = fin.loja.owner.email
                loja_nome = fin.loja.nome

        if not email_destino:
            return Response({'success': False, 'error': 'Email do destinatário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        invoice_id = invoice.get('id')
        assunto = f'Nota Fiscal – Assinatura LWK Sistemas - {loja_nome}'
        corpo = (
            f'Olá,\n\n'
            f'Segue a nota fiscal referente à assinatura da loja {loja_nome}.\n\n'
            f'Nota Fiscal: {invoice_id}\n'
            f'Acesse a nota fiscal: {pdf_url}\n\n'
            f'Atenciosamente,\nEquipe LWK Sistemas'
        )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
        msg = EmailMessage(subject=assunto, body=corpo, from_email=from_email, to=[email_destino])
        msg.send(fail_silently=False)

        logger.info(f"✅ NF {invoice_id} reenviada para {email_destino}")
        return Response({'success': True, 'message': f'Nota fiscal reenviada para {email_destino}', 'invoice_id': invoice_id})
    except Exception as e:
        logger.exception("nf_reenviar_por_payment: %s", e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nf_cancelar_por_payment(request, payment_id):
    """Cancela a nota fiscal de um pagamento específico no Asaas."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        client = _get_asaas_client()
        if not client:
            return Response({'success': False, 'error': 'Asaas não configurado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice, _ = _find_invoice_for_payment(client, payment_id)
        if not invoice:
            return Response({'success': False, 'error': 'Nenhuma nota fiscal encontrada'}, status=status.HTTP_404_NOT_FOUND)

        invoice_id = invoice.get('id')
        status_nf = invoice.get('status')

        if status_nf == 'CANCELED':
            return Response({'success': False, 'error': 'Nota fiscal já está cancelada'}, status=status.HTTP_400_BAD_REQUEST)

        client.cancel_invoice(invoice_id)
        logger.info(f"✅ NF {invoice_id} cancelada (payment: {payment_id})")
        return Response({'success': True, 'message': f'Nota fiscal {invoice_id} cancelada com sucesso', 'invoice_id': invoice_id})
    except Exception as e:
        logger.exception("nf_cancelar_por_payment: %s", e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
