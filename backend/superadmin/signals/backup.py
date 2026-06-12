import logging
import os
import shutil
from pathlib import Path

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from core.logging_utils import mask_email

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender='superadmin.HistoricoBackup')
def remover_arquivo_backup_ao_deletar(sender, instance, **kwargs):
    """
    Remove o arquivo de backup do disco quando HistoricoBackup é excluído.
    Evita arquivos órfãos em backups/{slug}/.
    """
    if instance.arquivo_path:
        try:
            if os.path.exists(instance.arquivo_path):
                os.remove(instance.arquivo_path)
                logger.debug(f"🗑️ Arquivo backup removido: {instance.arquivo_nome}")
        except (ValueError, OSError) as e:
            logger.warning(f"⚠️ Erro ao remover arquivo backup: {e}")

