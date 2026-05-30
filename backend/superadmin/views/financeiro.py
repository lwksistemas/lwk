from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
from core.logging_utils import mask_email
from ..models import FinanceiroLoja, PagamentoLoja
from ..serializers import FinanceiroLojaSerializer, PagamentoLojaSerializer
from .permissions import IsSuperAdmin


class FinanceiroLojaViewSet(viewsets.ModelViewSet):
    serializer_class = FinanceiroLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        return FinanceiroLoja.objects.select_related('loja', 'loja__plano').all()
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """Lojas com pagamento pendente"""
        pendentes = self.get_queryset().filter(status_pagamento__in=['pendente', 'atrasado'])
        serializer = self.get_serializer(pendentes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def renovar(self, request, pk=None):
        """Cria nova cobrança para renovação de assinatura"""
        from superadmin.cobranca_service import CobrancaService
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            
            dia_vencimento = request.data.get('dia_vencimento')
            antecipado = bool(request.data.get('antecipado', False))
            
            if dia_vencimento and not antecipado:
                try:
                    dia_vencimento = int(dia_vencimento)
                    if dia_vencimento < 1 or dia_vencimento > 28:
                        return Response({
                            'success': False,
                            'error': 'dia_vencimento deve estar entre 1 e 28'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({
                        'success': False,
                        'error': 'dia_vencimento deve ser um número inteiro'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Renovando assinatura para loja {loja.slug} (dia_vencimento={dia_vencimento})")
            
            service = CobrancaService()
            result = service.renovar_cobranca(loja, financeiro, dia_vencimento, antecipado=antecipado)
            
            if result.get('success'):
                logger.info(f"✅ Cobrança renovada para loja {loja.slug}: {result.get('payment_id')}")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"❌ Erro ao renovar cobrança para loja {loja.slug}: {result.get('error')}")
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Erro ao renovar assinatura: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reenviar_senha(self, request, pk=None):
        """Reenvia senha provisória manualmente (apenas se pagamento já confirmado)"""
        from superadmin.email_service import EmailService
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            owner = loja.owner
            
            if financeiro.status_pagamento != 'ativo':
                return Response({
                    'success': False,
                    'error': f'Pagamento ainda não confirmado. Status atual: {financeiro.get_status_pagamento_display()}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            owner_email_log = mask_email(getattr(owner, 'email', ''))
            logger.info("Reenviando senha provisória: loja=%s, owner_email=%s", loja.slug, owner_email_log)
            
            service = EmailService()
            success = service.enviar_senha_provisoria(loja, owner)
            
            if success:
                logger.info("Senha provisória reenviada: loja=%s, owner_email=%s", loja.slug, owner_email_log)
                return Response({
                    'success': True,
                    'message': f'Senha reenviada para {owner.email}'
                }, status=status.HTTP_200_OK)
            else:
                logger.warning("Falha ao reenviar senha provisória: loja=%s, owner_email=%s", loja.slug, owner_email_log)
                return Response({
                    'success': False,
                    'error': 'Falha ao enviar email. Email registrado para retry automático.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Erro ao reenviar senha: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def baixar_nota_fiscal(self, request, pk=None):
        """Baixa a nota fiscal mais recente da loja"""
        from asaas_integration.models import AsaasConfig
        from asaas_integration.client import AsaasClient
        from django.http import HttpResponse
        
        try:
            logger.info(f"🧾 [baixar_nota_fiscal] Iniciando - financeiro_id={pk}")
            
            financeiro = self.get_object()
            loja = financeiro.loja
            
            logger.info(f"🧾 [baixar_nota_fiscal] Loja: {loja.nome} (slug: {loja.slug})")
            logger.info(f"🧾 [baixar_nota_fiscal] Payment ID: {financeiro.asaas_payment_id}")
            
            if not financeiro.asaas_payment_id:
                logger.warning(f"🧾 [baixar_nota_fiscal] Nenhum payment_id encontrado")
                return Response({
                    'success': False,
                    'error': 'Nenhum pagamento Asaas encontrado para esta loja'
                }, status=status.HTTP_404_NOT_FOUND)
            
            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                logger.error(f"🧾 [baixar_nota_fiscal] Asaas não configurado")
                return Response({
                    'success': False,
                    'error': 'Asaas não configurado'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
            
            try:
                response = client._make_request('GET', 'invoices', {'payment': financeiro.asaas_payment_id})
                invoices = response.get('data', [])
                
                if not invoices:
                    return Response({
                        'success': False,
                        'error': 'Nenhuma nota fiscal encontrada para este pagamento. A nota fiscal é emitida automaticamente após a confirmação do pagamento.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                invoice = None
                for inv in invoices:
                    if inv.get('status') == 'AUTHORIZED':
                        invoice = inv
                        break
                
                if not invoice:
                    invoice = invoices[0]
                
                invoice_id = invoice.get('id')
                status_nf = invoice.get('status')
                
                if status_nf != 'AUTHORIZED':
                    return Response({
                        'success': False,
                        'error': f'Nota fiscal ainda não foi autorizada. Status atual: {status_nf}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                pdf_url = invoice.get('pdfUrl')
                if not pdf_url:
                    pdf_url = invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
                
                if not pdf_url:
                    return Response({
                        'success': False,
                        'error': 'URL do PDF da nota fiscal não disponível. Aguarde alguns minutos após a emissão.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                return Response({
                    'success': True,
                    'pdf_url': pdf_url,
                    'invoice_id': invoice_id,
                    'status': status_nf
                })
                
            except Exception as e:
                logger.error(f"❌ [baixar_nota_fiscal] Erro ao buscar nota fiscal: {e}")
                logger.exception(e)
                return Response({
                    'success': False,
                    'error': f'Erro ao buscar nota fiscal: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"❌ [baixar_nota_fiscal] Erro geral: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reenviar_nota_fiscal(self, request, pk=None):
        """Reenvia nota fiscal por email para o proprietário da loja"""
        from asaas_integration.models import AsaasConfig
        from asaas_integration.client import AsaasClient
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            owner = loja.owner
            
            if not financeiro.asaas_payment_id:
                return Response({
                    'success': False,
                    'error': 'Nenhum pagamento Asaas encontrado para esta loja'
                }, status=status.HTTP_404_NOT_FOUND)
            
            owner_email_log = mask_email(getattr(owner, 'email', ''))
            logger.info("Reenviando nota fiscal: loja=%s, owner_email=%s", loja.slug, owner_email_log)
            
            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response({
                    'success': False,
                    'error': 'Asaas não configurado'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
            
            try:
                response = client._make_request('GET', 'invoices', {'payment': financeiro.asaas_payment_id})
                invoices = response.get('data', [])
                
                if not invoices:
                    return Response({
                        'success': False,
                        'error': 'Nenhuma nota fiscal encontrada para este pagamento.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                invoice = None
                for inv in invoices:
                    if inv.get('status') == 'AUTHORIZED':
                        invoice = inv
                        break
                
                if not invoice:
                    invoice = invoices[0]
                
                invoice_id = invoice.get('id')
                status_nf = invoice.get('status')
                
                if status_nf != 'AUTHORIZED':
                    return Response({
                        'success': False,
                        'error': f'Nota fiscal ainda não foi autorizada. Status atual: {status_nf}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                pdf_url = invoice.get('pdfUrl')
                if not pdf_url:
                    pdf_url = invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
                
                if not pdf_url:
                    return Response({
                        'success': False,
                        'error': 'URL do PDF da nota fiscal não disponível.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == 'anual' else loja.plano.preco_mensal
                tipo_assinatura = loja.get_tipo_assinatura_display()
                
                assunto = f'Nota Fiscal – Assinatura LWK Sistemas - {loja.nome}'
                
                corpo = f"""
Olá,

Segue a nota fiscal referente à assinatura da loja {loja.nome}.

Dados da assinatura:
- Loja: {loja.nome}
- Plano: {loja.plano.nome} ({tipo_assinatura})
- Valor: R$ {valor_plano:.2f}
- Nota Fiscal: {invoice_id}

Acesse a nota fiscal: {pdf_url}

Em caso de dúvidas, entre em contato com o suporte.

Atenciosamente,
Equipe LWK Sistemas
"""
                
                from core.email_delivery import create_email_message, send_prepared
                msg = create_email_message(subject=assunto, body=corpo, to=[owner.email])
                send_prepared(msg, fail_silently=False)
                
                logger.info("Nota fiscal reenviada: loja=%s, owner_email=%s", loja.slug, owner_email_log)
                
                return Response({
                    'success': True,
                    'message': f'Nota fiscal reenviada para {owner.email}',
                    'invoice_id': invoice_id
                })
                
            except Exception as e:
                logger.error(f"Erro ao reenviar nota fiscal: {e}")
                return Response({
                    'success': False,
                    'error': f'Erro ao reenviar nota fiscal: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception(f"Erro ao reenviar nota fiscal: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def cancelar_nota_fiscal(self, request, pk=None):
        """Cancela a nota fiscal mais recente da loja no Asaas."""
        from asaas_integration.models import AsaasConfig
        from asaas_integration.client import AsaasClient

        try:
            financeiro = self.get_object()
            loja = financeiro.loja

            if not financeiro.asaas_payment_id:
                return Response({
                    'success': False,
                    'error': 'Nenhum pagamento Asaas encontrado para esta loja'
                }, status=status.HTTP_404_NOT_FOUND)

            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response({
                    'success': False,
                    'error': 'Asaas não configurado'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)

            response = client._make_request('GET', 'invoices', {'payment': financeiro.asaas_payment_id})
            invoices = response.get('data', [])

            if not invoices:
                return Response({
                    'success': False,
                    'error': 'Nenhuma nota fiscal encontrada para este pagamento'
                }, status=status.HTTP_404_NOT_FOUND)

            invoice = None
            for inv in invoices:
                if inv.get('status') in ('AUTHORIZED', 'SCHEDULED'):
                    invoice = inv
                    break

            if not invoice:
                invoice = invoices[0]

            invoice_id = invoice.get('id')
            status_nf = invoice.get('status')

            if status_nf == 'CANCELED':
                return Response({
                    'success': False,
                    'error': 'Nota fiscal já está cancelada'
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Cancelando nota fiscal {invoice_id} (status: {status_nf}) para loja {loja.nome}")

            result = client.cancel_invoice(invoice_id)

            logger.info(f"✅ Nota fiscal {invoice_id} cancelada para loja {loja.nome}")

            return Response({
                'success': True,
                'message': f'Nota fiscal {invoice_id} cancelada com sucesso',
                'invoice_id': invoice_id
            })

        except Exception as e:
            logger.exception(f"Erro ao cancelar nota fiscal: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PagamentoLojaViewSet(viewsets.ModelViewSet):
    serializer_class = PagamentoLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        return PagamentoLoja.objects.select_related('loja', 'financeiro').all()
    
    @action(detail=True, methods=['post'])
    def confirmar_pagamento(self, request, pk=None):
        """Confirmar pagamento de uma loja"""
        pagamento = self.get_object()
        
        pagamento.status = 'pago'
        pagamento.data_pagamento = timezone.now()
        pagamento.save()
        
        financeiro = pagamento.financeiro
        financeiro.status_pagamento = 'ativo'
        financeiro.ultimo_pagamento = timezone.now()
        financeiro.total_pago += pagamento.valor
        financeiro.save()
        
        return Response({'message': 'Pagamento confirmado com sucesso'})
