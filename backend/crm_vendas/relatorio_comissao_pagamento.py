"""
Pagamento, boleto e NFS-e do Relatório de Comissão (CRM).
"""
import logging
import re
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)


def gerar_boleto_comissao(relatorio):
    """
    Gera boleto no Asaas para pagamento da comissão.
    Usa a API Key da loja (CRMConfig.asaas_api_key).
    """
    from asaas_integration.client import AsaasClient

    from .models_config import CRMConfig
    from .models_relatorio_comissao import RelatorioComissao

    try:
        config = CRMConfig.get_or_create_for_loja(relatorio.loja_id)
        api_key = config.asaas_api_key
        if not api_key:
            return False, 'API Key Asaas não configurada na loja.'

        client = AsaasClient(api_key=api_key, sandbox=config.asaas_sandbox)
        ep = relatorio.empresa_prestadora

        cnpj_digits = re.sub(r'\D', '', ep.cnpj or '')
        if not cnpj_digits:
            return False, 'Empresa prestadora não possui CNPJ cadastrado.'

        customer_data = {
            'name': ep.nome,
            'cpfCnpj': cnpj_digits,
            'email': ep.email or '',
            'externalReference': f'ep_{ep.id}_comissao',
        }

        customer_id = (relatorio.asaas_customer_id or '').strip()
        if not customer_id:
            prev = (
                RelatorioComissao.objects.filter(
                    empresa_prestadora_id=ep.id,
                    loja_id=relatorio.loja_id,
                )
                .exclude(asaas_customer_id='')
                .order_by('-id')
                .first()
            )
            if prev:
                customer_id = prev.asaas_customer_id.strip()

        if customer_id:
            try:
                customer = client.get_customer(customer_id)
            except Exception:
                customer = client.get_or_create_customer(customer_data)
        else:
            customer = client.get_or_create_customer(customer_data)

        customer_id = customer.get('id')
        if not customer_id:
            return False, 'Falha ao criar cliente no Asaas.'

        vencimento = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        payment_data = {
            'customer': customer_id,
            'billingType': 'BOLETO',
            'value': float(relatorio.valor_total_comissao),
            'dueDate': vencimento,
            'description': f'Comissão {relatorio.numero} — {relatorio.periodo_descricao}',
            'externalReference': f'rc_{relatorio.id}',
        }
        payment = client.create_payment(payment_data)
        payment_id = payment.get('id')
        if not payment_id:
            return False, 'Falha ao criar cobrança no Asaas.'

        relatorio.asaas_payment_id = payment_id
        relatorio.asaas_customer_id = customer_id
        relatorio.boleto_url = payment.get('bankSlipUrl', '') or payment.get('invoiceUrl', '')
        relatorio.boleto_vencimento = timezone.now().date() + timedelta(days=7)
        relatorio.save(update_fields=[
            'asaas_payment_id', 'asaas_customer_id',
            'boleto_url', 'boleto_vencimento', 'updated_at',
        ])

        logger.info(
            'Boleto gerado para relatório %s: payment_id=%s',
            relatorio.numero, payment_id,
        )
        return True, None

    except Exception as e:
        logger.exception('Erro ao gerar boleto: %s', e)
        return False, str(e)


def emitir_nfse_comissao_sync(relatorio_id: int, loja_id: int) -> None:
    """Emite NFS-e do relatório de comissão (síncrono)."""
    from nfse_integration.service import NFSeService
    from superadmin.models import Loja

    from .models_relatorio_comissao import RelatorioComissao

    relatorio = RelatorioComissao.objects.filter(id=relatorio_id, loja_id=loja_id).first()
    if not relatorio:
        logger.warning('Relatório comissão id=%s loja=%s não encontrado', relatorio_id, loja_id)
        return

    try:
        loja = Loja.objects.using('default').filter(id=relatorio.loja_id).first()
        if not loja:
            logger.warning('Loja não encontrada para emissão de NFS-e: loja_id=%s', relatorio.loja_id)
            return

        from core.db_config import ensure_loja_database_config
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        set_current_loja_id(loja.id)
        db_name = getattr(loja, 'database_name', None) or f'loja_{loja.slug}'
        ensure_loja_database_config(db_name, conn_max_age=0)
        set_current_tenant_db(db_name)

        ep = relatorio.empresa_prestadora
        cnpj_digits = re.sub(r'\D', '', ep.cnpj or '')

        service = NFSeService(loja)
        resultado = service.emitir_nfse(
            tomador_cpf_cnpj=cnpj_digits,
            tomador_nome=ep.nome,
            tomador_email=ep.email or '',
            tomador_endereco={
                'logradouro': ep.logradouro or '',
                'numero': ep.numero or 'S/N',
                'complemento': ep.complemento or '',
                'bairro': ep.bairro or '',
                'cidade': ep.cidade or '',
                'uf': ep.uf or '',
                'cep': ep.cep or '',
            },
            servico_descricao=(
                f'Comissão de vendas ref. {relatorio.periodo_descricao} '
                f'— Relatório {relatorio.numero}'
            ),
            valor_servicos=relatorio.valor_total_comissao,
            enviar_email=True,
        )

        if resultado.get('success'):
            relatorio.status = 'nfse_emitida'
            relatorio.nfse_numero = resultado.get('numero_nf', '')
            relatorio.nfse_emitida_em = timezone.now()
            relatorio.save(update_fields=[
                'status', 'nfse_numero', 'nfse_emitida_em', 'updated_at',
            ])
            logger.info(
                'NFS-e emitida para relatório %s: %s',
                relatorio.numero,
                relatorio.nfse_numero,
            )
        else:
            logger.warning(
                'Falha ao emitir NFS-e para relatório %s: %s',
                relatorio.numero,
                resultado.get('error'),
            )
    except Exception as e:
        logger.exception(
            'Erro ao emitir NFS-e para relatório id=%s loja=%s: %s',
            relatorio_id,
            loja_id,
            e,
        )


def processar_pagamento_comissao(relatorio):
    """
    Chamado quando o pagamento do boleto é confirmado (via webhook Asaas).
    Emite NFS-e automaticamente.
    """
    relatorio.status = 'pago'
    relatorio.pago_em = timezone.now()
    relatorio.save(update_fields=['status', 'pago_em', 'updated_at'])
    logger.info('Relatório %s marcado como pago.', relatorio.numero)

    from nfse_integration.queue_dispatch import enqueue_emitir_nfse_comissao, should_enqueue_nfse

    if should_enqueue_nfse():
        enqueue_emitir_nfse_comissao(relatorio.id, relatorio.loja_id)
        logger.info('NFS-e comissão enfileirada: relatório %s', relatorio.numero)
        return

    emitir_nfse_comissao_sync(relatorio.id, relatorio.loja_id)
