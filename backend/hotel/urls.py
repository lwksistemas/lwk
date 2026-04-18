from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    HospedeViewSet,
    QuartoViewSet,
    TarifaViewSet,
    ReservaViewSet,
    GovernancaTarefaViewSet,
    HotelDashboardViewSet,
    FuncionarioViewSet,
    ReservaTemplateViewSet,
    ReservaAssinaturaPublicaView,
    ReservaAssinaturaPdfView,
)

router = DefaultRouter()
router.register(r'hospedes', HospedeViewSet, basename='hotel-hospedes')
router.register(r'quartos', QuartoViewSet, basename='hotel-quartos')
router.register(r'tarifas', TarifaViewSet, basename='hotel-tarifas')
router.register(r'reservas', ReservaViewSet, basename='hotel-reservas')
router.register(r'governanca-tarefas', GovernancaTarefaViewSet, basename='hotel-governanca-tarefas')
router.register(r'dashboard', HotelDashboardViewSet, basename='hotel-dashboard')
router.register(r'funcionarios', FuncionarioViewSet, basename='hotel-funcionarios')
router.register(r'reserva-templates', ReservaTemplateViewSet, basename='hotel-reserva-templates')

urlpatterns = [
    path('', include(router.urls)),
    path('assinar-reserva/<path:token>/', ReservaAssinaturaPublicaView.as_view(), name='hotel-assinar-reserva'),
    path('assinar-reserva/<path:token>/pdf/', ReservaAssinaturaPdfView.as_view(), name='hotel-assinar-reserva-pdf'),
]

