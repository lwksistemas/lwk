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
from .views_financeiro import (
    FinanceiroResumoView,
    LojaInfoView,
    PaymentEnviarReciboView,
    PaymentListView,
    ReciboPdfPublicView,
    RelatorioComissoesPdfView,
    RelatorioComissoesView,
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
    path("loja-info/", LojaInfoView.as_view(), name="salao-loja-info"),
    path("financeiro/resumo/", FinanceiroResumoView.as_view(), name="salao-financeiro-resumo"),
    path("payments/", PaymentListView.as_view(), name="salao-payments"),
    path("payments/<int:pk>/enviar-recibo/", PaymentEnviarReciboView.as_view(), name="salao-enviar-recibo"),
    path("payments/<int:pk>/recibo-pdf/<str:token>/", ReciboPdfPublicView.as_view(), name="salao-recibo-pdf"),
    path("relatorios/comissoes/", RelatorioComissoesView.as_view(), name="salao-relatorio-comissoes"),
    path("relatorios/comissoes/pdf/", RelatorioComissoesPdfView.as_view(), name="salao-relatorio-comissoes-pdf"),
    path("", include(router.urls)),
]
