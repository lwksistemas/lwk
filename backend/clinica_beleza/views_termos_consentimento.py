"""API — biblioteca de Termos de Consentimento (simples e TCLE Interativo)."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TermoConsentimentoTemplate
from .pagination import paginate_queryset
from .permissions import CLINICA_RECEPCAO
from .serializers.termos_consentimento import (
    TermoConsentimentoConfigSerializer,
    TermoConsentimentoTemplateSerializer,
)
from .termos_consentimento_service import obter_config_termo
from .views_base import GetObjectMixin, resolve_loja_id_from_request


class TermoConsentimentoTemplateListView(APIView):
    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        qs = TermoConsentimentoTemplate.objects.all().order_by("nome")
        tipo = (request.query_params.get("tipo") or "").strip()
        if tipo:
            qs = qs.filter(tipo=tipo)
        active = (request.query_params.get("active") or "true").strip().lower()
        if active == "true":
            qs = qs.filter(is_active=True)
        elif active == "false":
            qs = qs.filter(is_active=False)
        return paginate_queryset(qs, request, TermoConsentimentoTemplateSerializer)

    def post(self, request):
        serializer = TermoConsentimentoTemplateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        obj = serializer.save()
        return Response(
            TermoConsentimentoTemplateSerializer(obj).data,
            status=status.HTTP_201_CREATED,
        )


class TermoConsentimentoTemplateDetailView(GetObjectMixin, APIView):
    permission_classes = CLINICA_RECEPCAO
    model_class = TermoConsentimentoTemplate

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": "Termo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TermoConsentimentoTemplateSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": "Termo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = TermoConsentimentoTemplateSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(TermoConsentimentoTemplateSerializer(obj).data)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": "Termo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        from .termos_consentimento_service import vincular_procedimento_ao_termo
        vincular_procedimento_ao_termo(obj, None)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TermoConsentimentoConfigView(APIView):
    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        loja_id = resolve_loja_id_from_request(request)
        cfg = obter_config_termo(loja_id)
        return Response(TermoConsentimentoConfigSerializer(cfg).data)

    def put(self, request):
        loja_id = resolve_loja_id_from_request(request)
        cfg = obter_config_termo(loja_id)
        serializer = TermoConsentimentoConfigSerializer(cfg, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(TermoConsentimentoConfigSerializer(cfg).data)
