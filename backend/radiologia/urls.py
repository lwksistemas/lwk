from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditoriaAcessoViewSet,
    DicomwebProxyView,
    EquipamentoViewSet,
    LaudoViewSet,
    PacienteRadiologiaViewSet,
    PedidoExameViewSet,
    ProcedimentoViewSet,
    RadiologiaHealthView,
)

router = DefaultRouter()
router.register(r"pacientes", PacienteRadiologiaViewSet, basename="radiologia-pacientes")
router.register(r"equipamentos", EquipamentoViewSet, basename="radiologia-equipamentos")
router.register(r"procedimentos", ProcedimentoViewSet, basename="radiologia-procedimentos")
router.register(r"pedidos", PedidoExameViewSet, basename="radiologia-pedidos")
router.register(r"laudos", LaudoViewSet, basename="radiologia-laudos")
router.register(r"auditoria", AuditoriaAcessoViewSet, basename="radiologia-auditoria")

urlpatterns = [
    path("health/", RadiologiaHealthView.as_view(), name="radiologia-health"),
    path("dicomweb/", DicomwebProxyView.as_view(), name="radiologia-dicomweb-root"),
    path("dicomweb/<path:path>", DicomwebProxyView.as_view(), name="radiologia-dicomweb"),
    path("", include(router.urls)),
]
