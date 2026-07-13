"""
Signal handlers para invalidação de cache de admin professional IDs.
Dispara quando ProfissionalUsuario é criado, alterado ou excluído com perfil 'administrador'.
"""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ProfissionalUsuario


@receiver(post_save, sender=ProfissionalUsuario)
def invalidate_admin_cache_on_save(sender, instance, **kwargs):
    """Invalida cache quando ProfissionalUsuario admin é criado ou alterado."""
    if instance.perfil == 'administrador':
        cache.delete(f'admin_professional_ids_{instance.loja_id}')
    elif hasattr(instance, '_original_perfil') and instance._original_perfil == 'administrador':
        # Perfil mudou DE administrador para outro
        cache.delete(f'admin_professional_ids_{instance.loja_id}')


@receiver(post_delete, sender=ProfissionalUsuario)
def invalidate_admin_cache_on_delete(sender, instance, **kwargs):
    """Invalida cache quando ProfissionalUsuario admin é excluído."""
    if instance.perfil == 'administrador':
        cache.delete(f'admin_professional_ids_{instance.loja_id}')
