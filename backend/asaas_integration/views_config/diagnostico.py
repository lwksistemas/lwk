"""Diagnóstico de cadastro Asaas."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ._common import IsSuperAdmin, _build_cadastro_diagnostico

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsSuperAdmin])
def asaas_diagnostico(request):
    """Diagnóstico do fluxo de cadastro: API, webhook, e-mail e NFS-e."""
    try:
        return Response(_build_cadastro_diagnostico(request))
    except Exception as e:
        logger.exception("Erro no diagnóstico Asaas: %s", e)
        return Response(
            {"detail": f"Erro ao gerar diagnóstico: {e!s}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

