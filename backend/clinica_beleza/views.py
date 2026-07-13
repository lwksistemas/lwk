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
# Agenda & Bloqueios
from .views_agenda import (  # noqa: F401
    AgendaCreateView,
    AgendaDeleteView,
    AgendaReenviarMensagemView,
    AgendaUpdateView,
    AgendaView,
    BloqueioHorarioDetailView,
    BloqueioHorarioListView,
)
from .views_dashboard import DashboardView, LojaInfoView  # noqa: F401

# Financeiro
from .views_financeiro import (  # noqa: F401
    CategoriaDespesaListView,
    DespesaDetailView,
    DespesaListView,
    FinanceiroResumoView,
    PaymentDetailView,
    PaymentEnviarReciboView,
    PaymentListView,
    PaymentParcelaView,
    ReciboPdfPublicView,
)

# Pacientes
from .views_pacientes import PatientDetailView, PatientListView  # noqa: F401

# Procedimentos
from .views_procedimentos import (  # noqa: F401
    ProcedimentoConvenioPrecosMatrixView,
    ProcedureDetailView,
    ProcedureListView,
    ProcedurePrecosConvenioView,
)

# Profissionais
from .views_profissionais import (  # noqa: F401
    HorarioTrabalhoProfissionalView,
    ProfessionalCommissionView,
    ProfessionalDetailView,
    ProfessionalListView,
)

# Campanhas WhatsApp
from .views_whatsapp import (  # noqa: F401
    CampanhaPromocaoDetailView,
    CampanhaPromocaoEnviarView,
    CampanhaPromocaoListView,
)
