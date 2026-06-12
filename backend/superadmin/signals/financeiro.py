import logging
import os
import shutil
from pathlib import Path

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from core.logging_utils import mask_email

logger = logging.getLogger(__name__)

@receiver(post_save, sender='superadmin.FinanceiroLoja')
def on_payment_confirmed(sender, instance, created, **kwargs):
    """
    Dispara envio de senha provisória quando pagamento é confirmado.
    
    ✅ NOVO v719: Signal para enviar senha após confirmação de pagamento
    
    Trigger: status_pagamento muda para 'ativo' E senha ainda não foi enviada
    
    Fluxo:
    1. Webhook recebe confirmação de pagamento (Asaas ou Mercado Pago)
    2. Webhook atualiza status_pagamento para 'ativo'
    3. Este signal é disparado automaticamente
    4. EmailService envia senha provisória para o administrador
    5. FinanceiroLoja é atualizado (senha_enviada=True, data_envio_senha=now)
    
    Args:
        sender: Modelo FinanceiroLoja
        instance: Instância do FinanceiroLoja atualizado
        created: False (signal só dispara em updates)
        **kwargs: Argumentos adicionais do signal
    """
    # Não processar em criação (apenas em updates)
    if created:
        return
    
    # Verificar se status mudou para 'ativo' e senha ainda não foi enviada
    if instance.status_pagamento == 'ativo' and not instance.senha_enviada:
        from superadmin.email_service import EmailService
        
        try:
            loja = instance.loja
            owner = loja.owner
            
            logger.info(f"💰 Pagamento confirmado para loja {loja.nome}. Enviando senha provisória...")
            
            # Enviar senha provisória
            service = EmailService()
            success = service.enviar_senha_provisoria(loja, owner)
            
            if success:
                logger.info("Senha provisória enviada: loja=%s, owner_email=%s", loja.slug, mask_email(owner.email))
            else:
                logger.warning(
                    "Falha ao enviar senha provisória: loja=%s, owner_email=%s. Email registrado para retry automático.",
                    loja.slug,
                    mask_email(owner.email),
                )
        
        except Exception as e:
            logger.error(
                f"❌ Erro ao processar envio de senha para loja {instance.loja.slug}: {e}",
                exc_info=True
            )
