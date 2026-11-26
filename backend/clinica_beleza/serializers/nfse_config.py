"""Serializer de configuração NFS-e da Clínica da Beleza."""
from nfse_integration.serializers_config import BaseNFSeConfigSerializer

from ..models import ClinicaBelezaNFSeConfig


class ClinicaBelezaNFSeConfigSerializer(BaseNFSeConfigSerializer):
    webhook_asaas_prefixo = "clinica-beleza"

    class Meta(BaseNFSeConfigSerializer.Meta):
        model = ClinicaBelezaNFSeConfig
