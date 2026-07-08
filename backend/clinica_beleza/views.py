"""
Views/API para Clínica da Beleza — módulo de re-exportação.

Cada domínio está em seu próprio arquivo:
- views_dashboard.py   → LojaInfoView, DashboardView
- views_pacientes.py   → PatientListView, PatientDetailView
- views_profissionais.py → ProfessionalListView, ProfessionalDetailView, HorarioTrabalhoProfissionalView
- views_procedimentos.py → ProcedureListView, ProcedureDetailView
- views_financeiro.py  → PaymentListView, PaymentDetailView, FinanceiroResumoView
- views_agenda.py      → AgendaView, AgendaUpdateView, AgendaCreateView,
                          AgendaDeleteView, AgendaReenviarMensagemView,
                          BloqueioHorarioListView, BloqueioHorarioDetailView
- views_whatsapp.py    → CampanhaPromocaoListView,
                          CampanhaPromocaoDetailView, CampanhaPromocaoEnviarView
"""

# Dashboard & Info
from .views_dashboard import LojaInfoView, DashboardView  # noqa: F401

# Pacientes
from .views_pacientes import PatientListView, PatientDetailView  # noqa: F401

# Profissionais
from .views_profissionais import (  # noqa: F401
    ProfessionalListView, ProfessionalDetailView,
    HorarioTrabalhoProfissionalView, ProfessionalCommissionView,
)

# Procedimentos
from .views_procedimentos import (  # noqa: F401
    ProcedureListView,
    ProcedureDetailView,
    ProcedimentoConvenioPrecosMatrixView,
    ProcedurePrecosConvenioView,
)
from .views_protocolos import ProtocolListView, ProtocolDetailView
from .views_consultas import (
    ConsultaListView, ConsultaDetailView, ConsultaAplicarProtocoloView, ConsultaFinalizarView,
    PatientAnamneseView, ConsultaEvolucaoListView, PatientHistoricoConsultasView,
)  # noqa: F401

# Financeiro
from .views_financeiro import (  # noqa: F401
    PaymentListView, PaymentDetailView, PaymentParcelaView, FinanceiroResumoView,
    CategoriaDespesaListView, DespesaListView, DespesaDetailView,
)

# Agenda & Bloqueios
from .views_agenda import (  # noqa: F401
    AgendaView, AgendaUpdateView, AgendaCreateView,
    AgendaDeleteView, AgendaPagamentoView, AgendaReenviarMensagemView,
    BloqueioHorarioListView, BloqueioHorarioDetailView,
)

# Campanhas WhatsApp
from .views_whatsapp import (  # noqa: F401
    CampanhaPromocaoListView, CampanhaPromocaoDetailView, CampanhaPromocaoEnviarView,
)
