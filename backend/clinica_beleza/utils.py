"""Utilitários compartilhados para Clínica da Beleza
"""
from django.core.cache import cache

from core.loja_context import LojaContextHelper, registrar_invalidador_cache_loja  # noqa: F401

DASHBOARD_CACHE_VERSION = "v13"


def invalidate_dashboard_cache(loja_id, *, mes=None, ano=None, professional_id=None):
    """Limpa cache do dashboard para o mês informado (ou mês atual).
    Chamado após pagamentos, consultas e agendamentos.
    """
    from clinica_beleza.dashboard_service import data_hoje_clinica

    today = data_hoje_clinica()
    mes = mes or today.month
    ano = ano or today.year
    prof_key = str(professional_id) if professional_id else "all"
    for period in ("hoje", "semana", "proximos"):
        cache.delete(
            f"clinica_beleza_dashboard_{DASHBOARD_CACHE_VERSION}_{loja_id}_{ano}_{mes:02d}_{period}_{prof_key}",
        )
        if prof_key != "all":
            cache.delete(
                f"clinica_beleza_dashboard_{DASHBOARD_CACHE_VERSION}_{loja_id}_{ano}_{mes:02d}_{period}_all",
            )


registrar_invalidador_cache_loja(lambda loja_id: invalidate_dashboard_cache(loja_id))
