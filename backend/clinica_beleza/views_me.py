"""GET /clinica-beleza/me/ — nome de quem fez login, para o topo da clínica."""

from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.middleware import ensure_loja_context, get_current_loja_id

from .me_service import build_me_payload
from .permissions import CLINICA_MEMBER


class MeView(APIView):
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        ensure_loja_context(request)
        return Response(build_me_payload(request.user, get_current_loja_id()))
