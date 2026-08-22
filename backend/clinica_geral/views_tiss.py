from django.db.models import Count
from rest_framework.decorators import action

from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .config_service import get_or_create_config
from .models import GuiaTiss, LoteTiss
from .pdf_service import pdf_guia_tiss, pdf_response
from .serializers import GuiaTissSerializer, LoteTissSerializer
from .tiss_service import numerar_guia, numerar_lote


class LoteTissViewSet(BaseModelViewSet):
    serializer_class = LoteTissSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        return LoteTiss.objects.annotate(guias_count=Count("guias"))

    def perform_create(self, serializer):
        ensure_loja_context(self.request)
        numerar_lote(serializer.save())


class GuiaTissViewSet(BaseModelViewSet):
    serializer_class = GuiaTissSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = GuiaTiss.objects.select_related("consulta__paciente", "lote")
        lote = (self.request.query_params.get("lote") or "").strip()
        if lote:
            qs = qs.filter(lote_id=lote)
        return qs

    def perform_create(self, serializer):
        ensure_loja_context(self.request)
        consulta = serializer.validated_data["consulta"]
        guia = serializer.save(valor=serializer.validated_data.get("valor") or consulta.valor)
        numerar_guia(guia)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        ensure_loja_context(request)
        guia = self.get_object()
        return pdf_response(
            pdf_guia_tiss(guia, guia.consulta, guia.consulta.paciente, get_or_create_config()),
            f"guia-tiss-{guia.numero_guia or guia.id}.pdf",
        )
