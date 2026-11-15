"""Lembrete só das lojas de salão que ligaram a regra."""
import logging

from tenants.middleware import set_current_loja_id, set_current_tenant_db

from .comunicacao_service import lembretes_da_loja
from .permissions import loja_e_salao

logger = logging.getLogger(__name__)


def _banco(loja):
    from core.db_config import ensure_loja_database_config

    nome = getattr(loja, "database_name", None) or f"loja_{getattr(loja, 'slug', loja.id)}".replace("-", "_")
    ensure_loja_database_config(nome, conn_max_age=0)
    return nome


def enviar_lembretes_salao() -> int:
    from superadmin.models import Loja

    total = 0
    lojas = Loja.objects.filter(database_created=True, is_active=True).select_related("tipo_loja")
    for loja in lojas:
        if not loja_e_salao(loja):
            continue
        try:
            set_current_loja_id(loja.id)
            set_current_tenant_db(_banco(loja))
            total += lembretes_da_loja(loja.nome)
        except Exception:
            logger.exception("Lembrete do salão falhou na loja %s", loja.id)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    return total
