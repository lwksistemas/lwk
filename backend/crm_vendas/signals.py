"""Signals do CRM Vendas - invalida cache do dashboard ao alterar dados."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Lead, Oportunidade, Atividade


def _invalidate_dashboard_cache(loja_id):
    if not loja_id:
        return
    from django.core.cache import cache
    cache.delete(f'crm_dashboard:{loja_id}:owner')
    try:
        from superadmin.models import VendedorUsuario
        for vid in VendedorUsuario.objects.filter(loja_id=loja_id).values_list('vendedor_id', flat=True).distinct():
            cache.delete(f'crm_dashboard:{loja_id}:{vid}')
    except Exception:
        pass


def _get_loja_id(instance):
    return getattr(instance, 'loja_id', None)


@receiver(post_save, sender=Lead)
@receiver(post_delete, sender=Lead)
@receiver(post_save, sender=Oportunidade)
@receiver(post_delete, sender=Oportunidade)
@receiver(post_save, sender=Atividade)
@receiver(post_delete, sender=Atividade)
def _on_crm_data_change(sender, instance, **kwargs):
    _invalidate_dashboard_cache(_get_loja_id(instance))
