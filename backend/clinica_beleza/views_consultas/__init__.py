"""Views de consultas — re-export do pacote modular."""
from .crud import (
    ConsultaAplicarProtocoloView,
    ConsultaDetailView,
    ConsultaFinalizarView,
    ConsultaIniciarView,
    ConsultaListView,
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

__all__ = [
    'ConsultaListView',
    'ConsultaDetailView',
    'ConsultaIniciarView',
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
]
