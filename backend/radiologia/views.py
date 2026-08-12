"""API do RIS Radiologia."""
from __future__ import annotations

import logging

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id

from .models import (
    AuditoriaAcessoEstudo,
    Equipamento,
    Laudo,
    PacienteRadiologia,
    PedidoExame,
    Procedimento,
)
from .dicom_storage_service import sincronizar_imagens_pedido
from .orthanc_service import proxy_dicomweb
from .pedido_service import (
    cancelar_pedido,
    finalizar_laudo,
    gerar_pdf_laudo_bytes,
    obter_ou_criar_laudo,
    preparar_pedido_uids,
    publicar_pedido_na_worklist,
)
from .serializers import (
    AuditoriaAcessoEstudoSerializer,
    EquipamentoSerializer,
    LaudoSerializer,
    PacienteRadiologiaSerializer,
    PedidoExameSerializer,
    ProcedimentoSerializer,
)

logger = logging.getLogger(__name__)


class PacienteRadiologiaViewSet(BaseModelViewSet):
    serializer_class = PacienteRadiologiaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PacienteRadiologia.objects.all()
        if self.request.query_params.get("ativos", "1") != "0":
            qs = qs.filter(is_active=True)
        busca = (self.request.query_params.get("busca") or "").strip()
        if busca:
            qs = qs.filter(nome__icontains=busca)
        return qs


class EquipamentoViewSet(BaseModelViewSet):
    serializer_class = EquipamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Equipamento.objects.all()
        if self.request.query_params.get("ativos", "1") != "0":
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=True, methods=["post"], url_path="regenerar-codigo")
    def regenerar_codigo(self, request, pk=None):
        from .equipamento_vinculo_service import gerar_codigo_vinculo

        eq = self.get_object()
        eq.codigo_vinculo = gerar_codigo_vinculo()
        eq.save(update_fields=["codigo_vinculo", "updated_at"])
        return Response(EquipamentoSerializer(eq).data)


class DicomReceberView(APIView):
    """Recebe exame: serial (+ CPF/CNPJ) → clínica; Accession → pedido do paciente."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .equipamento_vinculo_service import receber_exame_por_accession_e_serial

        accession = (request.data.get("accession_number") or "").strip()
        serial = (request.data.get("numero_serie") or "").strip()
        cpf_cnpj = (request.data.get("cpf_cnpj") or "").strip() or None

        # Se autenticado na loja, usa CPF/CNPJ da loja como confirmação
        if not cpf_cnpj:
            loja_id = get_current_loja_id()
            if loja_id:
                from superadmin.models import Loja

                loja = Loja.objects.using("default").filter(id=loja_id).first()
                if loja:
                    cpf_cnpj = loja.cpf_cnpj

        try:
            result = receber_exame_por_accession_e_serial(
                accession_number=accession,
                numero_serie=serial,
                cpf_cnpj_loja=cpf_cnpj,
            )
        except LookupError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("dicom receber: %s", exc)
            return Response(
                {"error": "Falha ao vincular/arquivar exame DICOM."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(result)


class ProcedimentoViewSet(BaseModelViewSet):
    serializer_class = ProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Procedimento.objects.all()
        if self.request.query_params.get("ativos", "1") != "0":
            qs = qs.filter(is_active=True)
        return qs


class PedidoExameViewSet(BaseModelViewSet):
    serializer_class = PedidoExameSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PedidoExame.objects.select_related("paciente", "procedimento", "equipamento")
        st = (self.request.query_params.get("status") or "").strip()
        if st:
            qs = qs.filter(status=st)
        return qs

    def perform_create(self, serializer):
        pedido = serializer.save()
        preparar_pedido_uids(pedido)
        publicar_pedido_na_worklist(pedido)

    @action(detail=True, methods=["post"], url_path="publicar-mwl")
    def publicar_mwl(self, request, pk=None):
        pedido = self.get_object()
        publicar_pedido_na_worklist(pedido)
        return Response(PedidoExameSerializer(pedido).data)

    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        pedido = cancelar_pedido(self.get_object())
        return Response(PedidoExameSerializer(pedido).data)

    @action(detail=True, methods=["post"], url_path="sincronizar-imagens")
    def sincronizar_imagens(self, request, pk=None):
        pedido = self.get_object()
        try:
            pedido = sincronizar_imagens_pedido(pedido)
        except LookupError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("sincronizar_imagens pedido=%s: %s", pedido.id, exc)
            return Response(
                {"error": "Falha ao arquivar imagens DICOM."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(PedidoExameSerializer(pedido).data)

    @action(detail=True, methods=["post"], url_path="abrir-laudo")
    def abrir_laudo(self, request, pk=None):
        pedido = self.get_object()
        laudo = obter_ou_criar_laudo(pedido)
        return Response(LaudoSerializer(laudo).data, status=status.HTTP_200_OK)


class LaudoViewSet(BaseModelViewSet):
    serializer_class = LaudoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "put", "patch", "head", "options", "post"]

    def get_queryset(self):
        return Laudo.objects.select_related("pedido", "pedido__paciente", "pedido__procedimento")

    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request, pk=None):
        laudo = self.get_object()
        serializer = self.get_serializer(laudo, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        laudo = serializer.save()
        assinar = bool(request.data.get("assinar"))
        laudo = finalizar_laudo(laudo, assinar=assinar)
        return Response(LaudoSerializer(laudo).data)

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        laudo = self.get_object()
        if laudo.pdf_url:
            return Response({"url": laudo.pdf_url})
        pdf_bytes = gerar_pdf_laudo_bytes(laudo)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="laudo_{laudo.id}.pdf"'
        return response


class AuditoriaAcessoViewSet(BaseModelViewSet):
    serializer_class = AuditoriaAcessoEstudoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return AuditoriaAcessoEstudo.objects.all()[:500]


class DicomwebProxyView(APIView):
    """Proxy DICOMweb: frontend nunca fala direto com Orthanc."""

    permission_classes = [IsAuthenticated]

    def get(self, request, path=""):
        return self._proxy(request, path, "GET")

    def post(self, request, path=""):
        return self._proxy(request, path, "POST")

    def _proxy(self, request, path: str, method: str):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"error": "Loja não identificada"}, status=status.HTTP_400_BAD_REQUEST)

        path_clean = path.strip("/")
        first_seg = path_clean.split("/")[0] if path_clean else ""

        study_uid = request.query_params.get("StudyInstanceUID") or ""
        # Extrai StudyInstanceUID de paths /studies/{uid}/...
        if not study_uid and path:
            parts = path_clean.split("/")
            if len(parts) >= 2 and parts[0] == "studies":
                study_uid = parts[1]

        # Bloqueia buscas globais por paciente/série sem estudo autorizado (anti-vazamento PACS)
        if first_seg in ("patients", "series", "instances") and not study_uid:
            return Response(
                {"error": "Acesso negado: informe StudyInstanceUID de um pedido desta loja"},
                status=status.HTTP_403_FORBIDDEN,
            )

        pedido = None
        allowed_uids = set(
            PedidoExame.objects.exclude(study_instance_uid="")
            .values_list("study_instance_uid", flat=True)[:5000]
        )
        if study_uid:
            if study_uid not in allowed_uids:
                return Response(
                    {"error": "Estudo não pertence a esta loja / pedido não encontrado"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            pedido = PedidoExame.objects.filter(study_instance_uid=study_uid).first()
        elif path_clean in ("", "studies") and method.upper() == "GET":
            # Listagem sem filtro: restringe a UIDs desta loja
            if not allowed_uids:
                return HttpResponse("[]", content_type="application/dicom+json")
        elif not study_uid and first_seg == "studies" and method.upper() == "GET":
            # /studies sem UID na URL exige filtro via query ou retorna vazio
            if not request.query_params.get("StudyInstanceUID"):
                return HttpResponse("[]", content_type="application/dicom+json")

        try:
            params = request.query_params.dict()
            if not study_uid and allowed_uids and path.strip("/").startswith("studies"):
                # Orthanc QIDO: filtrar pelo primeiro UID conhecido se o cliente não passou
                # (OHIF tipicamente passa StudyInstanceUID; listagem ampla fica no RIS)
                pass
            upstream = proxy_dicomweb(path, method=method, params=params)
        except Exception as exc:
            logger.warning("Orthanc proxy falhou: %s", exc)
            return Response(
                {"error": "PACS indisponível. Verifique Orthanc na VM de imagens."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        AuditoriaAcessoEstudo.objects.create(
            loja_id=loja_id,
            pedido=pedido,
            study_instance_uid=study_uid or (pedido.study_instance_uid if pedido else ""),
            usuario_id=getattr(request.user, "id", None),
            usuario_nome=getattr(request.user, "get_full_name", lambda: "")()
            or getattr(request.user, "username", ""),
            acao=f"dicomweb_{method.lower()}",
            ip=request.META.get("REMOTE_ADDR"),
            detalhe=path[:500],
        )

        content_type = upstream.headers.get("Content-Type", "application/octet-stream")
        body = upstream.content
        # Filtra QIDO studies JSON pelos UIDs da loja quando listagem ampla
        if (
            method.upper() == "GET"
            and path.strip("/").startswith("studies")
            and "json" in (content_type or "").lower()
            and allowed_uids
        ):
            try:
                import json

                data = json.loads(body.decode("utf-8"))
                if isinstance(data, list):
                    filtered = []
                    for item in data:
                        uid = ""
                        if isinstance(item, dict):
                            tag = item.get("0020000D") or item.get("0020,000D")
                            if isinstance(tag, dict):
                                uid = (tag.get("Value") or [""])[0]
                            elif isinstance(tag, str):
                                uid = tag
                        if uid in allowed_uids:
                            filtered.append(item)
                    body = json.dumps(filtered).encode("utf-8")
            except Exception:
                pass

        return HttpResponse(
            body,
            status=upstream.status_code,
            content_type=content_type,
        )


class RadiologiaHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .orthanc_service import orthanc_base_url, orthanc_request

        orthanc_ok = False
        try:
            r = orthanc_request("GET", "/system", timeout=5)
            orthanc_ok = r.ok
        except Exception:
            orthanc_ok = False
        return Response(
            {
                "app": "radiologia",
                "orthanc_url": orthanc_base_url(),
                "orthanc_ok": orthanc_ok,
            }
        )
