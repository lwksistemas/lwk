"""Service layer para configuração de NFS-e da Clínica da Beleza.
"""
import logging

from nfse_integration.issnet_teste import test_issnet_connection  # noqa: F401

from .models import ClinicaBelezaNFSeConfig

logger = logging.getLogger(__name__)


def get_or_create_nfse_config(loja_id: int) -> ClinicaBelezaNFSeConfig:
    """Busca ou cria a configuração de NFS-e para a loja."""
    config = ClinicaBelezaNFSeConfig.objects.filter(loja_id=loja_id).first()
    if config is None:
        config = ClinicaBelezaNFSeConfig(loja_id=loja_id)
        config.save()
    return config
