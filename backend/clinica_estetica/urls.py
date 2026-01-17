from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClienteViewSet, ProfissionalViewSet, ProcedimentoViewSet,
    AgendamentoViewSet, FuncionarioViewSet
)

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='clinica-clientes')
router.register(r'profissionais', ProfissionalViewSet, basename='clinica-profissionais')
router.register(r'procedimentos', ProcedimentoViewSet, basename='clinica-procedimentos')
router.register(r'agendamentos', AgendamentoViewSet, basename='clinica-agendamentos')
router.register(r'funcionarios', FuncionarioViewSet, basename='clinica-funcionarios')

urlpatterns = [
    path('', include(router.urls)),
]
