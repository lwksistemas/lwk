from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasLojaAccess
from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .agenda_service import nome_usuario
from .config_service import get_or_create_config
from .models import ConfiguracaoConsultorio, Tarefa
from .serializers import ConfiguracaoConsultorioSerializer, TarefaSerializer


class TarefaViewSet(BaseModelViewSet):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Tarefa.objects.all()
        data = (self.request.query_params.get("data") or "").strip()
        if data:
            qs = qs.filter(data=data)
        return qs


class ConfiguracaoConsultorioViewSet(BaseModelViewSet):
    serializer_class = ConfiguracaoConsultorioSerializer
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_queryset(self):
        ensure_loja_context(self.request)
        return ConfiguracaoConsultorio.objects.all()

    @action(detail=False, methods=["get", "put", "patch"], url_path="atual")
    def atual(self, request):
        ensure_loja_context(request)
        config = get_or_create_config()
        if request.method == "GET":
            return Response(ConfiguracaoConsultorioSerializer(config).data)
        serializer = ConfiguracaoConsultorioSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MeView(APIView):
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get(self, request):
        ensure_loja_context(request)
        user = request.user
        return Response(
            {
                "username": user.username,
                "nome": nome_usuario(user),
                "email": user.email or "",
            }
        )
