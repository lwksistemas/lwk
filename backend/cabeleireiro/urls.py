from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AgendamentoViewSet,
    BloqueioHorarioViewSet,
    CategoriaServicoViewSet,
    ClienteViewSet,
    ProfissionalViewSet,
    SalaoDashboardViewSet,
    ServicoViewSet,
)

router = DefaultRouter()
router.register(r"clientes", ClienteViewSet, basename="salao-clientes")
router.register(r"profissionais", ProfissionalViewSet, basename="salao-profissionais")
router.register(r"servicos", ServicoViewSet, basename="salao-servicos")
router.register(r"categorias-servico", CategoriaServicoViewSet, basename="salao-categorias-servico")
router.register(r"agendamentos", AgendamentoViewSet, basename="salao-agendamentos")
router.register(r"bloqueios", BloqueioHorarioViewSet, basename="salao-bloqueios")
router.register(r"dashboard", SalaoDashboardViewSet, basename="salao-dashboard")

urlpatterns = [
    path("", include(router.urls)),
]
