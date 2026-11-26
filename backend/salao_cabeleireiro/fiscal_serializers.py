"""Mesma gravação da nota da clínica, na tabela do salão."""
from nfse_integration.serializers_config import BaseNFSeConfigSerializer

from .models_fiscal import SalaoNFSeConfig


class SalaoNFSeConfigSerializer(BaseNFSeConfigSerializer):
    webhook_asaas_prefixo = "salao-cabeleireiro"

    class Meta(BaseNFSeConfigSerializer.Meta):
        model = SalaoNFSeConfig
