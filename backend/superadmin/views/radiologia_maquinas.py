"""API Super Admin: contrato PACS + cadastro/liberação de máquinas."""
from __future__ import annotations

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from superadmin.models import ContratoPacsLoja, Loja, MaquinaRadiologia
from superadmin.serializers.radiologia_maquinas import (
    ContratoPacsLojaSerializer,
    MaquinaRadiologiaSerializer,
)
from superadmin.services.maquina_radiologia_service import (
    liberar_maquina_no_cliente,
    processar_vinculo_maquina,
    suspender_maquina_no_cliente,
    sincronizar_valor_mensalidade,
)
from superadmin.views.permissions import IsSuperAdmin

logger = logging.getLogger(__name__)


class ContratoPacsLojaViewSet(viewsets.ModelViewSet):
    serializer_class = ContratoPacsLojaSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = None
    queryset = ContratoPacsLoja.objects.select_related("loja").all()

    def perform_create(self, serializer):
        obj = serializer.save()
        sincronizar_valor_mensalidade(obj.loja)

    def perform_update(self, serializer):
        obj = serializer.save()
        sincronizar_valor_mensalidade(obj.loja)


class MaquinaRadiologiaViewSet(viewsets.ModelViewSet):
    serializer_class = MaquinaRadiologiaSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = None
    queryset = MaquinaRadiologia.objects.select_related("loja", "loja__tipo_loja").all()

    def get_queryset(self):
        qs = super().get_queryset()
        loja_id = self.request.query_params.get("loja")
        if loja_id:
            qs = qs.filter(loja_id=loja_id)
        status_f = (self.request.query_params.get("status") or "").strip()
        if status_f:
            qs = qs.filter(status=status_f)
        if self.request.query_params.get("ativos", "1") != "0":
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=False, methods=["get"], url_path="lojas-radiologia")
    def lojas_radiologia(self, request):
        from django.db.models import Q

        lojas = Loja.objects.filter(is_active=True).filter(
            Q(tipo_loja__slug__icontains="radiolog")
            | Q(tipo_loja__dashboard_template="radiologia")
            | Q(tipo_loja__nome__icontains="radiolog")
        ).select_related("tipo_loja", "plano")
        data = []
        for l in lojas:
            contrato = ContratoPacsLoja.objects.filter(loja=l).first()
            data.append(
                {
                    "id": l.id,
                    "nome": l.nome,
                    "slug": l.slug,
                    "cpf_cnpj": l.cpf_cnpj,
                    "plano": l.plano.nome if l.plano_id else "",
                    "dicom_contratado": bool(contrato and contrato.dicom_contratado and contrato.is_active),
                    "worklist_contratado": bool(contrato and contrato.worklist_contratado and contrato.is_active),
                }
            )
        return Response(data)

    @action(detail=True, methods=["post"], url_path="liberar")
    def liberar(self, request, pk=None):
        maquina = self.get_object()
        try:
            result = liberar_maquina_no_cliente(maquina)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("liberar maquina %s: %s", maquina.id, exc)
            return Response({"error": "Falha ao liberar máquina no cliente."}, status=status.HTTP_502_BAD_GATEWAY)
        maquina.refresh_from_db()
        return Response({"maquina": MaquinaRadiologiaSerializer(maquina).data, **result})

    @action(detail=True, methods=["post"], url_path="vincular")
    def vincular(self, request, pk=None):
        maquina = self.get_object()
        try:
            result = processar_vinculo_maquina(maquina)
        except LookupError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("vincular maquina %s: %s", maquina.id, exc)
            return Response({"error": "Falha ao vincular DICOM no PACS."}, status=status.HTTP_502_BAD_GATEWAY)
        maquina.refresh_from_db()
        return Response({"maquina": MaquinaRadiologiaSerializer(maquina).data, **result})

    @action(detail=True, methods=["post"], url_path="suspender")
    def suspender(self, request, pk=None):
        maquina = self.get_object()
        try:
            result = suspender_maquina_no_cliente(maquina)
        except Exception as exc:
            logger.exception("suspender maquina %s: %s", maquina.id, exc)
            return Response({"error": "Falha ao suspender máquina."}, status=status.HTTP_502_BAD_GATEWAY)
        maquina.refresh_from_db()
        return Response({"maquina": MaquinaRadiologiaSerializer(maquina).data, **result})
