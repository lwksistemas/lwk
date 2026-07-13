"""Helpers compartilhados de CRMConfig (patch de schema tenant)."""
import logging

from tenants.middleware import get_current_tenant_db

logger = logging.getLogger(__name__)


def get_crm_config_for_loja(loja_id: int):
    """Obtém CRMConfig. Se faltar coluna (ex.: Asaas), aplica patch SQL no tenant.
    """
    from django.db.utils import ProgrammingError

    from .models import CRMConfig

    try:
        return CRMConfig.get_or_create_for_loja(loja_id)
    except ProgrammingError as exc:
        err = str(exc).lower()
        if "column" not in err or "does not exist" not in err:
            raise
        db_name = get_current_tenant_db()
        if not db_name or db_name == "default":
            raise
        logger.warning("CRMConfig: colunas ausentes no tenant, aplicando patch em %s", db_name)
        from .schema_service import patch_crm_vendas_asaas_columns_if_missing

        patch_crm_vendas_asaas_columns_if_missing(db_name)
        return CRMConfig.get_or_create_for_loja(loja_id)
