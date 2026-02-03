from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClienteViewSet, ProfissionalViewSet, ServicoViewSet, AgendamentoViewSet,
    ProdutoViewSet, VendaViewSet, FuncionarioViewSet, HorarioFuncionamentoViewSet,
    BloqueioAgendaViewSet
)

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cabeleireiro-cliente')
router.register(r'profissionais', ProfissionalViewSet, basename='cabeleireiro-profissional')
router.register(r'servicos', ServicoViewSet, basename='cabeleireiro-servico')
router.register(r'agendamentos', AgendamentoViewSet, basename='cabeleireiro-agendamento')
router.register(r'produtos', ProdutoViewSet, basename='cabeleireiro-produto')
router.register(r'vendas', VendaViewSet, basename='cabeleireiro-venda')
router.register(r'funcionarios', FuncionarioViewSet, basename='cabeleireiro-funcionario')
router.register(r'horarios', HorarioFuncionamentoViewSet, basename='cabeleireiro-horario')
router.register(r'bloqueios', BloqueioAgendaViewSet, basename='cabeleireiro-bloqueio')

urlpatterns = [
    path('', include(router.urls)),
]
