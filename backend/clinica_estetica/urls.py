from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClienteViewSet, ProfissionalViewSet, ProcedimentoViewSet,
    AgendamentoViewSet, FuncionarioViewSet, ProtocoloProcedimentoViewSet,
    EvolucaoPacienteViewSet, AnamnesesTemplateViewSet, AnamneseViewSet,
    HorarioFuncionamentoViewSet, BloqueioAgendaViewSet, ConsultaViewSet,
    HistoricoLoginViewSet, CategoriaFinanceiraViewSet, TransacaoViewSet
)

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='clinica-clientes')
router.register(r'profissionais', ProfissionalViewSet, basename='clinica-profissionais')
router.register(r'procedimentos', ProcedimentoViewSet, basename='clinica-procedimentos')
router.register(r'protocolos', ProtocoloProcedimentoViewSet, basename='clinica-protocolos')
router.register(r'agendamentos', AgendamentoViewSet, basename='clinica-agendamentos')
router.register(r'consultas', ConsultaViewSet, basename='clinica-consultas')
router.register(r'evolucoes', EvolucaoPacienteViewSet, basename='clinica-evolucoes')
router.register(r'anamneses-templates', AnamnesesTemplateViewSet, basename='clinica-anamneses-templates')
router.register(r'anamneses', AnamneseViewSet, basename='clinica-anamneses')
router.register(r'horarios', HorarioFuncionamentoViewSet, basename='clinica-horarios')
router.register(r'bloqueios', BloqueioAgendaViewSet, basename='clinica-bloqueios')
router.register(r'funcionarios', FuncionarioViewSet, basename='clinica-funcionarios')
router.register(r'historico-login', HistoricoLoginViewSet, basename='clinica-historico-login')
router.register(r'categorias-financeiras', CategoriaFinanceiraViewSet, basename='clinica-categorias-financeiras')
router.register(r'transacoes', TransacaoViewSet, basename='clinica-transacoes')

urlpatterns = [
    path('', include(router.urls)),
]
