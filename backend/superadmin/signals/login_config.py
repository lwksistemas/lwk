import logging
import os
import shutil
from pathlib import Path

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from core.logging_utils import mask_email

logger = logging.getLogger(__name__)

@receiver(pre_save, sender='superadmin.LoginConfigSistema')
def delete_old_cloudinary_images(sender, instance, **kwargs):
    """
    Exclui imagens antigas do Cloudinary quando uma nova imagem é enviada.
    
    Trigger: Antes de salvar LoginConfigSistema
    
    Verifica se logo ou login_background foram alterados e exclui a imagem antiga
    do Cloudinary para evitar acúmulo de imagens não utilizadas.
    
    Args:
        sender: Modelo LoginConfigSistema
        instance: Instância sendo salva
        **kwargs: Argumentos adicionais do signal
    """
    if not instance.pk:
        # Nova instância, não há imagem antiga para excluir
        return
    
    try:
        from superadmin.models import LoginConfigSistema
        
        # Buscar instância antiga do banco
        try:
            old_instance = LoginConfigSistema.objects.get(pk=instance.pk)
        except LoginConfigSistema.DoesNotExist:
            return
        
        from superadmin.cloudinary_utils import delete_cloudinary_image as _delete_img
        
        # Verificar se logo foi alterado
        if old_instance.logo and old_instance.logo != instance.logo:
            logger.info(f"🗑️  Logo alterado para {instance.get_tipo_display()}, excluindo imagem antiga...")
            _delete_img(old_instance.logo)
        
        # Verificar se login_background foi alterado
        if old_instance.login_background and old_instance.login_background != instance.login_background:
            logger.info(f"🗑️  Background alterado para {instance.get_tipo_display()}, excluindo imagem antiga...")
            _delete_img(old_instance.login_background)
    
    except Exception as e:
        logger.error(f"❌ Erro ao processar exclusão de imagens antigas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Não interrompe o salvamento, apenas loga o erro
