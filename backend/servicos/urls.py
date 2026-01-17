from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet, ServicoViewSet, ClienteViewSet,
    ProfissionalViewSet, AgendamentoViewSet, OrdemServicoViewSet,
    OrcamentoViewSet, FuncionarioViewSet
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='servicos-categorias')
router.register(r'servicos', ServicoViewSet, basename='servicos-servicos')
router.register(r'clientes', ClienteViewSet, basename='servicos-clientes')
router.register(r'profissionais', ProfissionalViewSet, basename='servicos-profissionais')
router.register(r'agendamentos', AgendamentoViewSet, basename='servicos-agendamentos')
router.register(r'ordens-servico', OrdemServicoViewSet, basename='servicos-ordens-servico')
router.register(r'orcamentos', OrcamentoViewSet, basename='servicos-orcamentos')
router.register(r'funcionarios', FuncionarioViewSet, basename='servicos-funcionarios')

urlpatterns = [
    path('', include(router.urls)),
]
