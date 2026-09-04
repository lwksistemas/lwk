from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated

from core.permissions import HasLojaAccess
from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .equipe_service import garantir_especialidade_padrao
from .models import Especialidade, Funcionario, Profissional
from .serializers import EspecialidadeSerializer, FuncionarioSerializer, ProfissionalSerializer


class EspecialidadeViewSet(BaseModelViewSet):
    serializer_class = EspecialidadeSerializer
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get_queryset(self):
        ensure_loja_context(self.request)
        garantir_especialidade_padrao()
        ativos = Profissional.objects.filter(is_active=True)
        return Especialidade.objects.filter(is_active=True).prefetch_related(
            Prefetch("profissionais", queryset=ativos)
        )


class ProfissionalViewSet(BaseModelViewSet):
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Profissional.objects.filter(is_active=True).select_related("especialidade")
        especialidade = (self.request.query_params.get("especialidade") or "").strip()
        if especialidade:
            qs = qs.filter(especialidade_id=especialidade)
        return qs


class FuncionarioViewSet(BaseModelViewSet):
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get_queryset(self):
        ensure_loja_context(self.request)
        return Funcionario.objects.filter(is_active=True)
