from django.urls import path

from .views import (
    AgendaView,
    AgendamentoDetailView,
    BloqueioListCreateView,
    ClienteDetailView,
    ClienteListCreateView,
    ConfigView,
    BloqueioDetailView,
    CaixaView,
    JornadaProfissionalView,
    ProfissionalDetailView,
    ProfissionalListCreateView,
    ReceberAgendamentoView,
    RecebimentoDetailView,
    ResumoView,
    ServicoDetailView,
    ServicoListCreateView,
)

urlpatterns = [
    path("config/", ConfigView.as_view(), name="salao-config"),
    path("resumo/", ResumoView.as_view(), name="salao-resumo"),
    path("agenda/", AgendaView.as_view(), name="salao-agenda"),
    path("agendamentos/<int:pk>/", AgendamentoDetailView.as_view(), name="salao-agendamento"),
    path("agendamentos/<int:pk>/receber/", ReceberAgendamentoView.as_view(), name="salao-receber"),
    path("caixa/", CaixaView.as_view(), name="salao-caixa"),
    path("recebimentos/<int:pk>/", RecebimentoDetailView.as_view(), name="salao-recebimento"),
    path("clientes/", ClienteListCreateView.as_view(), name="salao-clientes"),
    path("clientes/<int:pk>/", ClienteDetailView.as_view(), name="salao-cliente"),
    path("profissionais/", ProfissionalListCreateView.as_view(), name="salao-profissionais"),
    path("profissionais/<int:pk>/", ProfissionalDetailView.as_view(), name="salao-profissional"),
    path("profissionais/<int:pk>/jornada/", JornadaProfissionalView.as_view(), name="salao-jornada"),
    path("servicos/", ServicoListCreateView.as_view(), name="salao-servicos"),
    path("servicos/<int:pk>/", ServicoDetailView.as_view(), name="salao-servico"),
    path("bloqueios/", BloqueioListCreateView.as_view(), name="salao-bloqueios"),
    path("bloqueios/<int:pk>/", BloqueioDetailView.as_view(), name="salao-bloqueio"),
]
