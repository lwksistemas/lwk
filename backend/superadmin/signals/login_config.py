import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender="superadmin.LoginConfigSistema")
def delete_old_media_images(sender, instance, **kwargs):
    """Exclui imagens antigas do servidor de mídia quando uma nova imagem é enviada.

    Trigger: Antes de salvar LoginConfigSistema

    Verifica se logo ou login_background foram alterados e exclui a imagem antiga
    do servidor de mídia para evitar acúmulo de imagens não utilizadas.
    """
    if not instance.pk:
        return

    try:
        from superadmin.models import LoginConfigSistema

        try:
            old_instance = LoginConfigSistema.objects.get(pk=instance.pk)
        except LoginConfigSistema.DoesNotExist:
            return

        from core.media_storage import is_media_url, media_delete_by_url

        if old_instance.logo and old_instance.logo != instance.logo and is_media_url(old_instance.logo):
            logger.info(
                "Logo alterado para %s, excluindo imagem antiga...",
                instance.get_tipo_display(),
            )
            media_delete_by_url(old_instance.logo)

        if (
            old_instance.login_background
            and old_instance.login_background != instance.login_background
            and is_media_url(old_instance.login_background)
        ):
            logger.info(
                "Background alterado para %s, excluindo imagem antiga...",
                instance.get_tipo_display(),
            )
            media_delete_by_url(old_instance.login_background)

    except Exception as e:
        logger.error("Erro ao processar exclusão de imagens antigas: %s", e)
        import traceback
        logger.error(traceback.format_exc())
