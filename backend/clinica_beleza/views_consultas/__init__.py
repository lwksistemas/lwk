"""Views de consultas — re-export do pacote modular."""
from .crud import (
    ConsultaAplicarProtocoloView,
    ConsultaDetailView,
    ConsultaFinalizarView,
    ConsultaIniciarView,
    ConsultaListView,
    ConsultaReceberView,
)
from .clinical import (
    ConsultaEvolucaoListView,
    ConsultaSecaoPDFView,
    PatientAnamneseView,
    PatientHistoricoConsultasView,
)
from .prescricoes import (
    ConsultaPrescricaoView,
    PatientPrescricaoView,
    PrescricaoMemedPdfView,
)
from .produtos import ConsultaProdutoDetailView, ConsultaProdutoListView
from .procedimentos import ConsultaProcedimentoDetailView, ConsultaProcedimentoListView

__all__ = [
    'ConsultaListView',
    'ConsultaDetailView',
    'ConsultaIniciarView',
    'ConsultaReceberView',
    'ConsultaFinalizarView',
    'ConsultaAplicarProtocoloView',
    'PatientAnamneseView',
    'ConsultaEvolucaoListView',
    'ConsultaSecaoPDFView',
    'PatientHistoricoConsultasView',
    'ConsultaPrescricaoView',
    'PatientPrescricaoView',
    'PrescricaoMemedPdfView',
    'ConsultaProdutoListView',
    'ConsultaProdutoDetailView',
    'ConsultaProcedimentoListView',
    'ConsultaProcedimentoDetailView',
]
