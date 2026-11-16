"""Mesma gravação da nota da clínica, na tabela do salão."""
from clinica_beleza.serializers.nfse_config import ClinicaBelezaNFSeConfigSerializer

from .models_fiscal import SalaoNFSeConfig


class SalaoNFSeConfigSerializer(ClinicaBelezaNFSeConfigSerializer):
    def get_asaas_webhook_url(self, obj):
        loja_id = self.context.get("loja_id")
        if not loja_id:
            return ""
        from superadmin.models import Loja

        loja = Loja.objects.filter(id=loja_id).first()
        if not loja:
            return ""
        slug = (getattr(loja, "atalho", None) or getattr(loja, "slug", "") or "").strip()
        if not slug:
            return ""
        request = self.context.get("request")
        base = request.build_absolute_uri("/").rstrip("/") if request else ""
        if not base:
            from django.conf import settings

            base = (getattr(settings, "API_BASE_URL", None) or "https://api.lwksistemas.com.br").rstrip("/")
        return f"{base}/api/salao-cabeleireiro/webhooks/asaas/{slug}/"

    class Meta(ClinicaBelezaNFSeConfigSerializer.Meta):
        model = SalaoNFSeConfig
