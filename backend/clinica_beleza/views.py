"""
Views/API para Clínica da Beleza — módulo de re-exportação.

Cada domínio está em seu próprio arquivo:
- views_dashboard.py   → LojaInfoView, DashboardView
- views_pacientes.py   → PatientListView, PatientDetailView
- views_profissionais.py → ProfessionalListView, ProfessionalDetailView, HorarioTrabalhoProfissionalView
- views_procedimentos.py → ProcedureListView, ProcedureDetailView
- views_financeiro.py  → PaymentListView, PaymentDetailView, FinanceiroResumoView
- views_agenda.py      → AgendaView, AgendaHojeView, AgendaUpdateView, AgendaCreateView,
                          AgendaDeleteView, AgendaReenviarMensagemView,
                          AppointmentListView, AppointmentDetailView,
                          BloqueioHorarioListView, BloqueioHorarioDetailView
- views_whatsapp.py    → WhatsAppConfigView, CampanhaPromocaoListView,
                          CampanhaPromocaoDetailView, CampanhaPromocaoEnviarView
"""

# Dashboard & Info
from .views_dashboard import LojaInfoView, DashboardView  # noqa: F401

# Pacientes
from .views_pacientes import PatientListView, PatientDetailView  # noqa: F401

# Profissionais
from .views_profissionais import (  # noqa: F401
    ProfessionalListView, ProfessionalDetailView, HorarioTrabalhoProfissionalView,
)

# Procedimentos
from .views_procedimentos import ProcedureListView, ProcedureDetailView  # noqa: F401
from .views_protocolos import ProtocolListView, ProtocolDetailView
from .views_consultas import (
    ConsultaListView, ConsultaDetailView, ConsultaAplicarProtocoloView, ConsultaFinalizarView,
    PatientAnamneseView, ConsultaEvolucaoListView, PatientHistoricoConsultasView,
)  # noqa: F401

# Financeiro
from .views_financeiro import PaymentListView, PaymentDetailView, FinanceiroResumoView  # noqa: F401

# Agenda & Bloqueios
from .views_agenda import (  # noqa: F401
    AppointmentListView, AppointmentDetailView,
    AgendaView, AgendaHojeView, AgendaUpdateView, AgendaCreateView,
    AgendaDeleteView, AgendaReenviarMensagemView,
    BloqueioHorarioListView, BloqueioHorarioDetailView,
)

# WhatsApp & Campanhas
from .views_whatsapp import (  # noqa: F401
    WhatsAppConfigView,
    CampanhaPromocaoListView, CampanhaPromocaoDetailView, CampanhaPromocaoEnviarView,
)
