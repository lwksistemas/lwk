"""Views para Orçamento de consulta — Clínica da Beleza."""
import logging

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.orcamento_service import (
    criar_orcamento,
    enviar_orcamento,
    excluir_orcamento,
    gerar_pdf_orcamento,
    listar_orcamentos_consulta,
)

logger = logging.getLogger(__name__)


class OrcamentoConsultaView(APIView):
    """CRUD de orçamentos vinculados a uma consulta.

    GET  /api/clinica-beleza/orcamentos/?consulta_id=X
    POST /api/clinica-beleza/orcamentos/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        consulta_id = request.query_params.get("consulta_id")
        if not consulta_id:
            return Response({"error": "consulta_id obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            dados = listar_orcamentos_consulta(int(consulta_id))
            return Response(dados)
        except Exception as e:
            logger.exception("Erro ao listar orçamentos: %s", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        data = request.data
        consulta_id = data.get("consulta_id")
        itens = data.get("itens", [])
        observacoes = data.get("observacoes", "")
        validade_dias = int(data.get("validade_dias", 30))

        if not consulta_id or not itens:
            return Response(
                {"error": "consulta_id e itens são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            orcamento = criar_orcamento(consulta_id, itens, observacoes, validade_dias)
            return Response(
                {"id": orcamento.id, "valor_total": str(orcamento.valor_total)},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.exception("Erro ao criar orçamento: %s", e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrcamentoDetalheView(APIView):
    """Ações em um orçamento específico.

    DELETE /api/clinica-beleza/orcamentos/<id>/
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, orcamento_id):
        try:
            excluir_orcamento(orcamento_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrcamentoPDFView(APIView):
    """Gera PDF do orçamento.

    GET /api/clinica-beleza/orcamentos/<id>/pdf/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, orcamento_id):
        try:
            pdf_bytes = gerar_pdf_orcamento(orcamento_id)
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="orcamento_{orcamento_id}.pdf"'
            return response
        except Exception as e:
            logger.exception("Erro ao gerar PDF do orçamento: %s", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrcamentoEnviarView(APIView):
    """Envia orçamento por email/WhatsApp.

    POST /api/clinica-beleza/orcamentos/<id>/enviar/
    Body: {"canais": ["email", "whatsapp"]}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, orcamento_id):
        canais = request.data.get("canais", [])
        if not canais:
            return Response({"error": "Informe ao menos um canal (email, whatsapp)"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = enviar_orcamento(orcamento_id, canais)
            return Response(resultado)
        except Exception as e:
            logger.exception("Erro ao enviar orçamento: %s", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
