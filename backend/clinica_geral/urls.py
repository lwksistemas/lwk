from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ConfiguracaoConsultorioViewSet,
    ConsultaViewSet,
    EvolucaoPDFView,
    EvolucaoViewSet,
    FechamentoCaixaViewSet,
    GuiaTissViewSet,
    LoteTissViewSet,
    MeView,
    PacienteAnexoViewSet,
    PacienteViewSet,
    PrescricaoViewSet,
    ProntuarioPacienteView,
    RelatoriosView,
    TarefaViewSet,
    TeleconsultaPublicaView,
)

router = DefaultRouter()
router.register(r"pacientes", PacienteViewSet, basename="clinica-geral-pacientes")
router.register(r"anexos", PacienteAnexoViewSet, basename="clinica-geral-anexos")
router.register(r"consultas", ConsultaViewSet, basename="clinica-geral-consultas")
router.register(r"tarefas", TarefaViewSet, basename="clinica-geral-tarefas")
router.register(r"configuracao", ConfiguracaoConsultorioViewSet, basename="clinica-geral-config")
router.register(r"evolucoes", EvolucaoViewSet, basename="clinica-geral-evolucoes")
router.register(r"prescricoes", PrescricaoViewSet, basename="clinica-geral-prescricoes")
router.register(r"lotes-tiss", LoteTissViewSet, basename="clinica-geral-lotes")
router.register(r"guias-tiss", GuiaTissViewSet, basename="clinica-geral-guias")
router.register(r"caixa", FechamentoCaixaViewSet, basename="clinica-geral-caixa")

urlpatterns = [
    path("relatorios/", RelatoriosView.as_view(), name="clinica-geral-relatorios"),
    path("me/", MeView.as_view(), name="clinica-geral-me"),
    path("pacientes/<int:paciente_id>/prontuario/", ProntuarioPacienteView.as_view(), name="clinica-geral-prontuario"),
    path("evolucoes/<int:pk>/pdf/", EvolucaoPDFView.as_view(), name="clinica-geral-evolucao-pdf"),
    path("teleconsulta/<path:token>/", TeleconsultaPublicaView.as_view(), name="clinica-geral-teleconsulta"),
    path("", include(router.urls)),
]
