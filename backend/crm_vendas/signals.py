"""
Signals do CRM Vendas - invalida cache do dashboard ao alterar dados.
Refatorado para usar CRMCacheManager centralizado.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Lead, Oportunidade, Atividade
from .cache import CRMCacheManager


def _get_loja_id(instance):
    """Obtém loja_id da instância."""
    return getattr(instance, 'loja_id', None)


@receiver(post_save, sender=Lead)
@receiver(post_delete, sender=Lead)
@receiver(post_save, sender=Oportunidade)
@receiver(post_delete, sender=Oportunidade)
def _on_crm_data_change(sender, instance, **kwargs):
    """Invalida cache do dashboard quando dados do CRM mudam."""
    CRMCacheManager.invalidate_dashboard(_get_loja_id(instance))


@receiver(post_save, sender=Atividade)
@receiver(post_delete, sender=Atividade)
def _on_atividade_change(sender, instance, **kwargs):
    """Invalida cache do dashboard e atividades quando atividade muda."""
    loja_id = _get_loja_id(instance)
    CRMCacheManager.invalidate_dashboard(loja_id)
    CRMCacheManager.invalidate_atividades(loja_id)
