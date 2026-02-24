"""
Signals para integração automática com Asaas
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='superadmin.FinanceiroLoja')
def create_asaas_subscription_on_financeiro_creation(sender, instance, created, **kwargs):
    """
    Cria automaticamente a primeira cobrança (boleto) quando o FinanceiroLoja é criado.
    Respeita a preferência da loja: Mercado Pago ou Asaas.
    """
    if not created:
        return
    
    # Ler loja direto do banco pelo FK para garantir valor persistido (evita cache)
    from superadmin.models import Loja
    loja = Loja.objects.get(pk=instance.loja_id)
    provedor = (getattr(loja, 'provedor_boleto_preferido', None) or '').strip() or 'asaas'
    logger.info(f"Primeira cobrança para loja {loja.nome} (provedor_boleto_preferido={provedor!r})")

    # Se a loja escolheu Mercado Pago, usar LojaAsaasService (que delega para MP)
    if provedor == 'mercadopago':
        try:
            from superadmin.asaas_service import LojaAsaasService
            from superadmin.models import MercadoPagoConfig
            mp_config = MercadoPagoConfig.get_config()
            if not mp_config.enabled or not (getattr(mp_config, 'access_token', '') or '').strip():
                logger.warning(
                    f"Loja {loja.nome} escolheu Mercado Pago mas a API não está configurada. "
                    "Configure em Superadmin → Mercado Pago (habilitar e preencher Access Token). Tentando Asaas."
                )
            elif mp_config.enabled and mp_config.access_token:
                logger.info(f"Criando cobrança Mercado Pago para loja: {loja.nome}")
                service = LojaAsaasService()
                result = service.criar_cobranca_loja(loja, instance)
                if result.get('success') and result.get('provedor') == 'mercadopago':
                    # Cobrança foi criada pelo Mercado Pago no asaas_service; só atualizar campos no signal
                    # (asaas_service já atualizou financeiro e criou PagamentoLoja; truncar URL para limite do banco)
                    instance.provedor_boleto = 'mercadopago'
                    instance.mercadopago_payment_id = (result.get('payment_id') or '')[:100]
                    instance.boleto_url = (result.get('boleto_url') or '')[:200]
                    instance.save(update_fields=['provedor_boleto', 'mercadopago_payment_id', 'boleto_url'])
                    logger.info(f"✅ Cobrança Mercado Pago criada para loja {loja.nome}")
                    logger.info(f"   Payment ID: {instance.mercadopago_payment_id}, Boleto URL: {(instance.boleto_url or '')[:50]}...")
                    return
                if result.get('success') and result.get('provedor') == 'asaas':
                    # Fallback Asaas já foi feito em criar_cobranca_loja (financeiro + PagamentoLoja atualizados)
                    logger.info(f"✅ Cobrança Asaas criada para loja {loja.nome} (fallback após falha MP)")
                    return
                logger.warning(f"Mercado Pago falhou para {loja.nome}: {result.get('error')}, tentando Asaas")
        except Exception as e:
            logger.warning(f"Mercado Pago não usado para {loja.nome}: {e}, tentando Asaas")

    # Verificar se a integração com Asaas está habilitada
    if not getattr(settings, 'ASAAS_INTEGRATION_ENABLED', False):
        logger.info(f"Integração Asaas desabilitada. Loja {loja.nome} criada sem cobrança.")
        return
    
    try:
        from .client import AsaasPaymentService
        from .models import AsaasCustomer, AsaasPayment, LojaAssinatura
        from django.db import transaction
        
        logger.info(f"Criando assinatura Asaas para loja: {loja.nome}")
        
        # Usar data_proxima_cobranca do FinanceiroLoja
        due_date_str = instance.data_proxima_cobranca.strftime('%Y-%m-%d')
        logger.info(f"Usando data_proxima_cobranca do FinanceiroLoja: {due_date_str}")
        
        # Preparar dados da loja
        loja_data = {
            'nome': loja.nome,
            'slug': loja.slug,
            'email': loja.owner.email,
            'cpf_cnpj': loja.cpf_cnpj or '000.000.000-00',  # CPF padrão se não informado
            'telefone': getattr(loja.owner, 'telefone', ''),
        }
        
        # Preparar dados do plano
        valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == 'anual' else loja.plano.preco_mensal
        plano_data = {
            'nome': f"{loja.plano.nome} ({loja.get_tipo_assinatura_display()})",
            'preco': valor_plano
        }
        
        with transaction.atomic():
            # Criar cobrança no Asaas com data correta
            service = AsaasPaymentService()
            result = service.create_loja_subscription_payment(loja_data, plano_data, due_date=due_date_str)
            
            if not result['success']:
                logger.error(f"Erro ao criar cobrança Asaas para loja {loja.nome}: {result['error']}")
                return
            
            # Criar cliente no banco local
            customer = AsaasCustomer.objects.create(
                asaas_id=result['customer_id'],
                name=loja_data['nome'],
                email=loja_data['email'],
                cpf_cnpj=loja_data['cpf_cnpj'],
                phone=loja_data.get('telefone', ''),
                external_reference=f"loja_{loja_data['slug']}",
                raw_data=result['raw_customer']
            )
            
            # Criar pagamento no banco local
            from datetime import datetime
            payment = AsaasPayment.objects.create(
                asaas_id=result['payment_id'],
                customer=customer,
                external_reference=f"loja_{loja_data['slug']}_assinatura",
                billing_type='BOLETO',
                status=result['status'],
                value=result['value'],
                due_date=datetime.strptime(result['due_date'], '%Y-%m-%d').date(),
                invoice_url=result['payment_url'],
                bank_slip_url=result['boleto_url'],
                pix_qr_code=result['pix_qr_code'],
                pix_copy_paste=result['pix_copy_paste'],
                description=f"Assinatura {plano_data['nome']} - Loja {loja_data['nome']}",
                raw_data=result['raw_payment']
            )
            
            # Criar assinatura
            assinatura = LojaAssinatura.objects.create(
                loja_slug=loja_data['slug'],
                loja_nome=loja_data['nome'],
                asaas_customer=customer,
                current_payment=payment,
                plano_nome=plano_data['nome'],
                plano_valor=plano_data['preco'],
                data_vencimento=payment.due_date
            )
            
            # Atualizar FinanceiroLoja com boleto para exibir no dashboard
            instance.asaas_customer_id = result['customer_id']
            instance.asaas_payment_id = result['payment_id']
            instance.boleto_url = result.get('boleto_url', '')
            instance.pix_qr_code = result.get('pix_qr_code', '')
            instance.data_proxima_cobranca = datetime.strptime(result['due_date'], '%Y-%m-%d').date()
            instance.save(update_fields=['asaas_customer_id', 'asaas_payment_id', 'boleto_url', 'pix_qr_code', 'data_proxima_cobranca'])
            
            logger.info(f"✅ Assinatura Asaas criada com sucesso para loja {loja.nome}")
            logger.info(f"   Payment ID: {payment.asaas_id}")
            logger.info(f"   Valor: R$ {payment.value}")
            logger.info(f"   Vencimento: {payment.due_date}")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar assinatura Asaas para loja {loja.nome}: {e}")
        import traceback
        traceback.print_exc()
        # Não interrompe a criação da loja, apenas loga o erro

@receiver(post_save, sender='superadmin.Loja')
def update_asaas_subscription_on_loja_update(sender, instance, created, **kwargs):
    """
    Atualiza dados da assinatura no Asaas quando a loja é atualizada
    """
    if created:
        return
    
    # Verificar se a integração com Asaas está habilitada
    if not getattr(settings, 'ASAAS_INTEGRATION_ENABLED', False):
        return
    
    try:
        from .models import LojaAssinatura
        
        # Buscar assinatura existente
        try:
            assinatura = LojaAssinatura.objects.get(loja_slug=instance.slug)
        except LojaAssinatura.DoesNotExist:
            logger.warning(f"Assinatura Asaas não encontrada para loja {instance.nome}")
            return
        
        # Atualizar dados básicos
        if assinatura.loja_nome != instance.nome:
            assinatura.loja_nome = instance.nome
            assinatura.save()
            logger.info(f"Nome da loja atualizado na assinatura Asaas: {instance.nome}")
        
        # Se o plano mudou, criar nova cobrança
        valor_atual = instance.plano.preco_anual if instance.tipo_assinatura == 'anual' else instance.plano.preco_mensal
        if assinatura.plano_valor != valor_atual:
            logger.info(f"Plano alterado para loja {instance.nome}. Valor: R$ {assinatura.plano_valor} → R$ {valor_atual}")
            # Aqui poderia criar uma nova cobrança ou ajustar a existente
            # Por simplicidade, apenas atualizamos o valor na assinatura
            assinatura.plano_valor = valor_atual
            assinatura.plano_nome = f"{instance.plano.nome} ({instance.get_tipo_assinatura_display()})"
            assinatura.save()
            
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar assinatura Asaas para loja {instance.nome}: {e}")