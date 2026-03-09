"""
Signals do app Restaurante - Remoção de arquivos órfãos

Garante que arquivos de mídia (ex: XML de NF-e) sejam removidos do disco
quando o registro é excluído, evitando arquivos órfãos.
"""
import logging
import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_delete, sender='restaurante.NotaFiscalEntrada')
def remover_arquivo_nfe_ao_deletar(sender, instance, **kwargs):
    """
    Remove o arquivo XML da NF-e do disco quando NotaFiscalEntrada é excluída.
    Evita arquivos órfãos em media/nfe_restaurante/.
    """
    if not instance.xml_file:
        return
    try:
        from django.conf import settings
        file_obj = instance.xml_file
        if hasattr(file_obj, 'path'):
            path = file_obj.path
        else:
            path = str(settings.MEDIA_ROOT / file_obj.name) if file_obj.name else None
        if path and os.path.exists(path):
            os.remove(path)
            logger.debug(f"🗑️ Arquivo NF-e removido: {path}")
    except (ValueError, OSError, AttributeError) as e:
        logger.warning(f"⚠️ Erro ao remover arquivo NF-e: {e}")
