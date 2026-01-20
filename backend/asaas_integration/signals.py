"""
Signals para integração automática com Asaas
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='superadmin.Loja')
def create_asaas_subscription_on_loja_creation(sender, instance, created, **kwargs):
    """
    Cria automaticamente uma assinatura no Asaas quando uma nova loja é criada
    """
    if not created:
        return
    
    # Verificar se a integração com Asaas está habilitada
    if not getattr(settings, 'ASAAS_INTEGRATION_ENABLED', False):
        logger.info(f"Integração Asaas desabilitada. Loja {instance.nome} criada sem cobrança.")
        return
    
    try:
        from .client import AsaasPaymentService
        from .models import AsaasCustomer, AsaasPayment, LojaAssinatura
        from django.db import transaction
        
        logger.info(f"Criando assinatura Asaas para loja: {instance.nome}")
        
        # Preparar dados da loja
        loja_data = {
            'nome': instance.nome,
            'slug': instance.slug,
            'email': instance.owner.email,
            'cpf_cnpj': instance.cpf_cnpj or '000.000.000-00',  # CPF padrão se não informado
            'telefone': getattr(instance.owner, 'telefone', ''),
        }
        
        # Preparar dados do plano
        valor_plano = instance.plano.preco_anual if instance.tipo_assinatura == 'anual' else instance.plano.preco_mensal
        plano_data = {
            'nome': f"{instance.plano.nome} ({instance.get_tipo_assinatura_display()})",
            'preco': valor_plano
        }
        
        with transaction.atomic():
            # Criar cobrança no Asaas
            service = AsaasPaymentService()
            result = service.create_loja_subscription_payment(loja_data, plano_data)
            
            if not result['success']:
                logger.error(f"Erro ao criar cobrança Asaas para loja {instance.nome}: {result['error']}")
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
            
            logger.info(f"✅ Assinatura Asaas criada com sucesso para loja {instance.nome}")
            logger.info(f"   Payment ID: {payment.asaas_id}")
            logger.info(f"   Valor: R$ {payment.value}")
            logger.info(f"   Vencimento: {payment.due_date}")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar assinatura Asaas para loja {instance.nome}: {e}")
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