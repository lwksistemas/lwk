"""Views para Orçamento de consulta — Clínica da Beleza."""
import logging

from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.models.orcamento import OrcamentoConsulta
from clinica_beleza.orcamento_service import (
    atualizar_status_orcamento,
    buscar_clientes_orcamento,
    criar_orcamento,
    enviar_orcamento,
    excluir_orcamento,
    gerar_pdf_orcamento,
    listar_orcamentos_consulta,
    listar_orcamentos_paciente,
)
from clinica_beleza.permissions import CLINICA_CLINICAL, _loja_and_profissional
from clinica_beleza.permissions import CLINICA_CLINICAL
from clinica_beleza.serializers import OrcamentoCreateSerializer, OrcamentoStatusSerializer
from clinica_beleza.throttles import PublicPdfThrottle
from clinica_beleza.views_base import GetObjectMixin, MSG_ERRO_PDF, resposta_erro_interno

logger = logging.getLogger(__name__)


class _OrcamentoObjectMixin(GetObjectMixin):
    model_class = OrcamentoConsulta
    not_found_message = "Orçamento não encontrado"
    select_related_fields = ("patient", "professional", "consulta")


class OrcamentoConsultaView(APIView):
    """CRUD de orçamentos vinculados a uma consulta.

    GET  /api/clinica-beleza/orcamentos/?consulta_id=X
    POST /api/clinica-beleza/orcamentos/
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request):
        busca = (request.query_params.get("search") or "").strip()
        patient_id = request.query_params.get("patient_id")
        consulta_id = request.query_params.get("consulta_id")
        if busca and not patient_id and not consulta_id:
            return Response(buscar_clientes_orcamento(busca))
        try:
            if patient_id:
                dados = listar_orcamentos_paciente(int(patient_id))
            elif consulta_id:
                dados = listar_orcamentos_consulta(int(consulta_id))
            else:
                return Response(
                    {"error": "Informe o cliente ou o atendimento."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(dados)
        except (TypeError, ValueError):
            return Response({"error": "Identificador inválido"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return resposta_erro_interno(logger, "Erro ao listar orçamentos", e)

    def post(self, request):
        serializer = OrcamentoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        professional_id = None
        if not data.get("consulta_id"):
            _loja, prof = _loja_and_profissional(request)
            if prof and prof != "superuser":
                professional_id = getattr(prof, "professional_id", None)
        try:
            orcamento = criar_orcamento(
                data.get("consulta_id"),
                data["itens"],
                data.get("observacoes", ""),
                data.get("validade_dias", 30),
                patient_id=data.get("patient_id"),
                professional_id=professional_id,
            )
            return Response(
                {"id": orcamento.id, "valor_total": str(orcamento.valor_total)},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return resposta_erro_interno(logger, "Erro ao criar orçamento", e)


class OrcamentoDetalheView(_OrcamentoObjectMixin, APIView):
    """Ações em um orçamento específico.

    PATCH  /api/clinica-beleza/orcamentos/<id>/  {"status": "ACEITO"|"RECUSADO"}
    DELETE /api/clinica-beleza/orcamentos/<id>/
    """

    permission_classes = CLINICA_CLINICAL

    def patch(self, request, orcamento_id):
        orcamento, err = self.object_or_404(orcamento_id)
        if err:
            return err
        serializer = OrcamentoStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            atualizar_status_orcamento(orcamento, serializer.validated_data["status"])
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"id": orcamento.id, "status": orcamento.status})

    def delete(self, request, orcamento_id):
        orcamento, err = self.object_or_404(orcamento_id)
        if err:
            return err
        try:
            excluir_orcamento(orcamento)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrcamentoPDFView(_OrcamentoObjectMixin, APIView):
    """Gera PDF do orçamento.

    GET /api/clinica-beleza/orcamentos/<id>/pdf/
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request, orcamento_id):
        _, err = self.object_or_404(orcamento_id)
        if err:
            return err
        try:
            pdf_bytes = gerar_pdf_orcamento(orcamento_id)
            try:
                from clinica_beleza.media_docs_service import salvar_orcamento_no_servidor_midia
                orcamento = OrcamentoConsulta.objects.select_related("patient").filter(pk=orcamento_id).first()
                if orcamento:
                    salvar_orcamento_no_servidor_midia(orcamento, pdf_bytes)
            except Exception:
                logger.warning("Falha ao arquivar PDF do orçamento %s", orcamento_id, exc_info=True)
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="orcamento_{orcamento_id}.pdf"'
            return response
        except OrcamentoConsulta.DoesNotExist:
            return Response({"error": "Orçamento não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return resposta_erro_interno(
                logger, "Erro ao gerar PDF do orçamento", e, error=MSG_ERRO_PDF,
            )


class OrcamentoPDFPublicView(APIView):
    """GET /clinica-beleza/orcamentos/<id>/pdf-public/<token>/ — PDF público (para WhatsApp)."""

    permission_classes = []
    authentication_classes = []
    throttle_classes = [PublicPdfThrottle]

    def get(self, request, orcamento_id, token):
        from clinica_beleza.public_pdf import PREFIX_ORCAMENTO, ler_pdf_publico

        cached = ler_pdf_publico(PREFIX_ORCAMENTO, token)
        if not cached or cached.get("orcamento_id") != orcamento_id:
            return Response({"error": "Orçamento expirado ou inválido."}, status=status.HTTP_404_NOT_FOUND)

        pdf_bytes = cached.get("pdf")
        if not pdf_bytes:
            return Response({"error": "PDF não disponível."}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="orcamento_{orcamento_id}.pdf"'
        return response


class OrcamentoImagemPublicView(APIView):
    """GET /clinica-beleza/orcamentos/<id>/img-public/<token>/ — JPEG para WhatsApp."""

    permission_classes = []
    authentication_classes = []
    throttle_classes = [PublicPdfThrottle]

    def get(self, request, orcamento_id, token):
        from clinica_beleza.public_pdf import PREFIX_ORCAMENTO, ler_pdf_publico

        cached = ler_pdf_publico(PREFIX_ORCAMENTO, token)
        if not cached or cached.get("orcamento_id") != orcamento_id:
            return Response({"error": "Orçamento expirado ou inválido."}, status=status.HTTP_404_NOT_FOUND)
        imagem = cached.get("imagem")
        if not imagem:
            return Response({"error": "Imagem não disponível."}, status=status.HTTP_404_NOT_FOUND)
        response = HttpResponse(imagem, content_type="image/jpeg")
        response["Content-Disposition"] = f'inline; filename="orcamento_{orcamento_id}.jpg"'
        return response


class OrcamentoEnviarView(_OrcamentoObjectMixin, APIView):
    """Envia orçamento por email/WhatsApp.

    POST /api/clinica-beleza/orcamentos/<id>/enviar/
    Body: {"canais": ["email", "whatsapp"]}
    """

    permission_classes = CLINICA_CLINICAL

    def post(self, request, orcamento_id):
        _, err = self.object_or_404(orcamento_id)
        if err:
            return err
        canais = request.data.get("canais", [])
        if not canais:
            return Response({"error": "Informe ao menos um canal (email, whatsapp)"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = enviar_orcamento(orcamento_id, canais)
            return Response(resultado)
        except OrcamentoConsulta.DoesNotExist:
            return Response({"error": "Orçamento não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return resposta_erro_interno(logger, "Erro ao enviar orçamento", e)
