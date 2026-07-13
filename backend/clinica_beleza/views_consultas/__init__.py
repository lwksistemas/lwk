"""Views de consultas — re-export do pacote modular."""
from .clinical import (
    ConsultaEvolucaoListView,
    ConsultaSecaoPDFView,
    PatientAnamneseView,
    PatientHistoricoConsultasView,
)
from .crud import (
    ConsultaAplicarProtocoloView,
    ConsultaDetailView,
    ConsultaEstornarPagamentoView,
    ConsultaFinalizarView,
    ConsultaIniciarView,
    ConsultaListView,
    ConsultaReceberView,
)
from .prescricoes import (
    ConsultaPrescricaoView,
    PatientPrescricaoView,
    PrescricaoMemedPdfView,
)
from .procedimentos import ConsultaProcedimentoDetailView, ConsultaProcedimentoListView
from .produtos import ConsultaProdutoDetailView, ConsultaProdutoListView

__all__ = [
    'ConsultaListView',
    'ConsultaDetailView',
    'ConsultaIniciarView',
    'ConsultaReceberView',
    'ConsultaEstornarPagamentoView',
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
