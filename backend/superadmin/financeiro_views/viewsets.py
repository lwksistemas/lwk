"""ViewSets financeiro e pagamentos das lojas."""
import logging

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..asaas_service import LojaAsaasService
from ..models import FinanceiroLoja, Loja, PagamentoLoja
from ..serializers import FinanceiroLojaSerializer, PagamentoLojaSerializer
from .helpers import (
    _mercadopago_payment_ids_for_boleto,
    _nfse_para_pagamento,
    _resolve_asaas_payment_id,
)
from .nf_asaas import _find_invoice_for_payment, _get_asaas_client
from .permissions import IsLojaOwner
from .renovacao import _executar_renovar_financeiro

logger = logging.getLogger(__name__)

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
        """Atualizar status consultando Asaas (todos PagamentoLoja pendentes + financeiro)."""
        financeiro = self.get_object()
        loja = financeiro.loja

        try:
            from superadmin.sync_service import AsaasSyncService

            sync = AsaasSyncService()
            if not sync.asaas_service.available:
                return Response(
                    {'error': 'Serviço Asaas não disponível'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            resultado_sync = sync.sync_loja_payments(loja)
            financeiro.refresh_from_db()

            pagamentos_pendentes = PagamentoLoja.objects.filter(
                loja=loja,
                status__in=['pendente', 'atrasado'],
            ).exclude(asaas_payment_id='').count()

            # Fallback: financeiro.asaas_payment_id quando não há PagamentoLoja vinculado
            payment_id = (financeiro.asaas_payment_id or '').strip()
            if payment_id and pagamentos_pendentes == 0:
                resultado = sync.asaas_service.consultar_status_pagamento(payment_id)
                if resultado.get('success'):
                    asaas_status = resultado.get('status', '')
                    if asaas_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                        sync._process_payment_confirmed(
                            loja,
                            financeiro,
                            payment_id,
                            resultado.get('raw_payment') or {},
                        )
                        financeiro.refresh_from_db()
                    elif asaas_status == 'OVERDUE':
                        financeiro.status_pagamento = 'atrasado'
                        financeiro.save(update_fields=['status_pagamento'])
                    else:
                        financeiro.status_pagamento = 'pendente'
                        financeiro.save(update_fields=['status_pagamento'])

            return Response({
                'message': 'Status atualizado com sucesso',
                'status_local': financeiro.status_pagamento,
                'senha_enviada': financeiro.senha_enviada,
                'pagamentos_atualizados': resultado_sync.get('pagamentos_atualizados', 0),
                'pagamentos_pendentes': pagamentos_pendentes,
            })
        except Exception as e:
            logger.exception('Erro ao atualizar status Asaas loja %s: %s', loja.slug, e)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'])
    def renovar(self, request, pk=None):
        return _executar_renovar_financeiro(self.get_object(), request.data)

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

    @action(detail=True, methods=['get'], url_path='nota-fiscal')
    def nota_fiscal(self, request, pk=None):
        """PDF/link da NFS-e da assinatura (proprietário da loja)."""
        pagamento = self.get_object()
        asaas_id = _resolve_asaas_payment_id(pagamento)

        nf = _nfse_para_pagamento(pagamento, asaas_id)
        if nf:
            if (nf.pdf_url or '').strip():
                return Response({
                    'success': True,
                    'pdf_url': nf.pdf_url.strip(),
                    'numero_nf': nf.numero_nf or '',
                    'provedor': nf.provedor,
                })
            try:
                from nfse_integration.pdf_download import resolver_download_pdf_superadmin
                resultado = resolver_download_pdf_superadmin(nf)
                if resultado.tipo == 'url' and resultado.url:
                    return Response({
                        'success': True,
                        'pdf_url': resultado.url,
                        'numero_nf': nf.numero_nf or '',
                        'provedor': nf.provedor,
                    })
            except Exception as e:
                logger.warning('nota_fiscal resolver pagamento %s: %s', pk, e)

        if asaas_id:
            try:
                client = _get_asaas_client()
                if client:
                    invoice, _ = _find_invoice_for_payment(client, asaas_id)
                    if invoice and invoice.get('status') == 'AUTHORIZED':
                        pdf_url = invoice.get('pdfUrl') or invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
                        if pdf_url:
                            return Response({
                                'success': True,
                                'pdf_url': pdf_url,
                                'numero_nf': str(invoice.get('number') or invoice.get('id') or ''),
                                'provedor': 'asaas',
                            })
            except Exception as e:
                logger.warning('nota_fiscal asaas pagamento %s: %s', pk, e)

        return Response(
            {
                'success': False,
                'error': (
                    'Nota fiscal não disponível para este pagamento. '
                    'Ela é gerada após a confirmação do pagamento.'
                ),
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    @action(detail=True, methods=['get'], url_path='nota-fiscal-arquivo')
    def nota_fiscal_arquivo(self, request, pk=None):
        """Baixa PDF da NFS-e (gerado internamente ou URL resolvida)."""
        pagamento = self.get_object()
        asaas_id = _resolve_asaas_payment_id(pagamento)
        nf = _nfse_para_pagamento(pagamento, asaas_id)
        if not nf:
            return Response({'error': 'Nota fiscal não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            from nfse_integration.pdf_download import resolver_download_pdf_superadmin
            resultado = resolver_download_pdf_superadmin(nf)
            if resultado.tipo == 'url' and resultado.url:
                return Response({'success': True, 'pdf_url': resultado.url, 'numero_nf': nf.numero_nf or ''})
            if resultado.tipo == 'pdf' and resultado.conteudo_pdf:
                response = HttpResponse(resultado.conteudo_pdf, content_type='application/pdf')
                response['Content-Disposition'] = (
                    f'{resultado.content_disposition}; filename="{resultado.nome_arquivo}"'
                )
                return response
        except Exception as e:
            logger.exception('nota_fiscal_arquivo pagamento %s: %s', pk, e)
        return Response({'error': 'Não foi possível gerar o PDF da nota fiscal.'}, status=status.HTTP_404_NOT_FOUND)
    
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
