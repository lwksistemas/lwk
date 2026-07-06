"""Dashboard financeiro por loja."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from ..loja_utils import resolve_loja_by_slug_or_atalho
from ..models import FinanceiroLoja, PagamentoLoja
from ..serializers import PagamentoLojaSerializer
from .helpers import _build_historico_pagamentos_loja, _get_or_create_financeiro_loja
from .renovacao import _executar_renovar_financeiro
from superadmin.services.assinatura_bloqueio_service import (
    situacao_aviso_assinatura,
    situacao_geracao_boleto_assinatura,
)

logger = logging.getLogger(__name__)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def dashboard_financeiro_loja(request, loja_slug):
    """Dashboard financeiro específico de uma loja (GET). POST gera cobrança antecipada."""
    if request.method == 'POST':
        logger.info('POST financeiro/ (gerar cobrança) loja_slug=%s user=%s', loja_slug, request.user.username)
        if not request.user.is_superuser:
            loja = resolve_loja_by_slug_or_atalho(loja_slug, owner=request.user, is_active=True)
            if not loja:
                return Response(
                    {'success': False, 'error': 'Sem permissão. Apenas o responsável pode gerar cobrança.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            loja = resolve_loja_by_slug_or_atalho(loja_slug, is_active=True)
            if not loja:
                return Response(
                    {'success': False, 'error': 'Loja não encontrada'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        try:
            financeiro = _get_or_create_financeiro_loja(loja)
        except Exception as e:
            logger.exception('dashboard_financeiro_loja POST %s: %s', loja_slug, e)
            return Response(
                {'success': False, 'error': 'Não foi possível carregar o financeiro da loja.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return _executar_renovar_financeiro(financeiro, request.data)

    try:
        return _dashboard_financeiro_loja_impl(request, loja_slug)
    except Exception as e:
        logger.exception('dashboard_financeiro_loja %s: %s', loja_slug, e)
        return Response(
            {'error': 'Erro ao carregar dados financeiros. Tente novamente em instantes.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
def _dashboard_financeiro_loja_impl(request, loja_slug):
    # Verificar permissão (slug ou atalho na URL, ex.: /loja/beleza/ ou /loja/34787081845/)
    if not request.user.is_superuser:
        loja = resolve_loja_by_slug_or_atalho(loja_slug, owner=request.user, is_active=True)
        if not loja:
            return Response(
                {'error': 'Sem permissão. Apenas o responsável pode acessar.'},
                status=status.HTTP_403_FORBIDDEN,
            )
    else:
        loja = resolve_loja_by_slug_or_atalho(loja_slug, is_active=True)
        if not loja:
            return Response({'error': 'Loja não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    try:
        financeiro = _get_or_create_financeiro_loja(loja)
    except Exception as e:
        logger.exception('Erro ao obter/criar financeiro loja %s: %s', loja_slug, e)
        return Response(
            {'error': 'Não foi possível carregar o financeiro desta loja. Tente novamente ou contate o suporte.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    proximo_boleto = None
    
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
                try:
                    from .mercadopago_service import LojaMercadoPagoService
                    mp_svc = LojaMercadoPagoService()
                    boleto_url = mp_svc.get_boleto_url(financeiro.mercadopago_payment_id) or ''
                except Exception as mp_err:
                    logger.warning('MP get_boleto_url loja %s: %s', loja.slug, mp_err)
                    boleto_url = ''
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

            logger.debug('Total pagamentos Asaas loja %s: %s', loja.slug, todos_pagamentos.count())

            # Próxima cobrança em aberto (pendente ou vencida no Asaas)
            proximo_boleto = AsaasPayment.objects.filter(
                customer=loja_assinatura.asaas_customer,
                status__in=['PENDING', 'OVERDUE'],
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
                logger.warning('   - Filtro: status in PENDING/OVERDUE')

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
    
    try:
        historico_pagamentos = _build_historico_pagamentos_loja(
            loja,
            financeiro,
            boleto_url or '',
            pix_copy_paste or '',
            proximo_boleto.due_date if proximo_boleto else None,
        )
        logger.info(f"✅ Histórico loja {loja.slug}: {len(historico_pagamentos)} itens")
    except Exception as e:
        logger.exception('Erro ao montar histórico de pagamentos loja %s: %s', loja.slug, e)
        historico_pagamentos = []

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
            'id': financeiro.id,
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
        'historico_pagamentos': historico_pagamentos,
        'assinatura_aviso': situacao_aviso_assinatura(loja),
        'is_blocked': bool(getattr(loja, 'is_blocked', False)),
        'geracao_boleto': situacao_geracao_boleto_assinatura(loja, financeiro),
    })
