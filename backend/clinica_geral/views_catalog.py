from rest_framework.permissions import IsAuthenticated

from core.permissions import HasLojaAccess
from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .catalog_service import garantir_convenios_padrao, garantir_tipos_padrao
from .models import ConvenioConsultorio, TipoConsulta
from .serializers import ConvenioConsultorioSerializer, TipoConsultaSerializer


class TipoConsultaViewSet(BaseModelViewSet):
    serializer_class = TipoConsultaSerializer
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get_queryset(self):
        ensure_loja_context(self.request)
        garantir_tipos_padrao()
        return TipoConsulta.objects.filter(is_active=True)


class ConvenioConsultorioViewSet(BaseModelViewSet):
    serializer_class = ConvenioConsultorioSerializer
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get_queryset(self):
        ensure_loja_context(self.request)
        garantir_convenios_padrao()
        return ConvenioConsultorio.objects.filter(is_active=True)
