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
    
    ✅ MODIFICAÇÃO v719: Usa CobrancaService unificado (Strategy Pattern)
    - Respeita a preferência da loja: Mercado Pago ou Asaas
    - NÃO envia mais senha provisória aqui
    - Senha será enviada pelo signal on_payment_confirmed após confirmação do pagamento
    
    ✅ MODIFICAÇÃO v720: Proteção contra duplicação
    - Verifica se cobrança já foi criada antes de criar novamente
    - Adiciona logs detalhados para debug
    """
    if not created:
        return
    
    # Log detalhado para debug
    import threading
    logger.info(f"{'='*80}")
    logger.info(f"🔔 SIGNAL DISPARADO: create_asaas_subscription_on_financeiro_creation")
    logger.info(f"   Loja ID: {instance.loja_id}")
    logger.info(f"   Financeiro ID: {instance.id}")
    logger.info(f"   Thread: {threading.current_thread().name}")
    logger.info(f"{'='*80}")
    
    # Ler loja direto do banco pelo FK para garantir valor persistido (evita cache)
    from superadmin.models import Loja, FinanceiroLoja
    from superadmin.cobranca_service import CobrancaService
    
    # 🔒 PROTEÇÃO CONTRA DUPLICAÇÃO: Verificar se já tem payment_id
    # Se já tem payment_id (Asaas ou Mercado Pago), significa que a cobrança já foi criada
    if instance.asaas_payment_id or instance.mercadopago_payment_id:
        logger.warning(
            f"⚠️ Cobrança já existe para loja ID {instance.loja_id} "
            f"(asaas_payment_id={instance.asaas_payment_id}, "
            f"mercadopago_payment_id={instance.mercadopago_payment_id}). "
            f"Pulando criação para evitar duplicação."
        )
        return
    
    loja = Loja.objects.get(pk=instance.loja_id)
    provedor = (getattr(loja, 'provedor_boleto_preferido', None) or '').strip() or 'asaas'
    
    logger.info(f"Criando primeira cobrança para loja {loja.nome} (provedor={provedor})")
    
    # Usar serviço unificado para criar cobrança
    service = CobrancaService()
    result = service.criar_cobranca(loja, instance)
    
    if result.get('success'):
        logger.info(f"✅ Cobrança criada para loja {loja.nome}")
        logger.info(f"   Provedor: {result.get('provedor')}")
        logger.info(f"   Payment ID: {result.get('payment_id')}")
        logger.info(f"   Boleto URL: {(result.get('boleto_url') or '')[:50]}...")
        logger.info(f"   Valor: R$ {result.get('value')}")
        logger.info(f"   Vencimento: {result.get('due_date')}")
    else:
        logger.error(f"❌ Erro ao criar cobrança para loja {loja.nome}: {result.get('error')}")
        logger.error(f"   Provedor: {provedor}")
        logger.error(f"   Loja pode ser criada manualmente em Superadmin → Financeiro")

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