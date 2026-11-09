"""Configuração da simulação estética da clínica."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.middleware import get_current_loja_id

from .permissions import CLINICA_ADMIN
from .simulacao_estetica_service import SimulacaoEsteticaError, resposta_config, salvar_config


class SimulacaoEsteticaConfigView(APIView):
    """GET/PATCH /clinica-beleza/simulacao-estetica/config/ — chave da própria clínica."""

    permission_classes = CLINICA_ADMIN

    def get(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"error": "Contexto de loja não encontrado"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resposta_config(loja_id))

    def patch(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"error": "Contexto de loja não encontrado"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(salvar_config(loja_id, request.data or {}))
        except SimulacaoEsteticaError as exc:
            return Response({"error": exc.message}, status=exc.status)
