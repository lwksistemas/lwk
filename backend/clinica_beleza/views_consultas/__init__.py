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
    "ConsultaAplicarProtocoloView",
    "ConsultaDetailView",
    "ConsultaEstornarPagamentoView",
    "ConsultaEvolucaoListView",
    "ConsultaFinalizarView",
    "ConsultaIniciarView",
    "ConsultaListView",
    "ConsultaPrescricaoView",
    "ConsultaProcedimentoDetailView",
    "ConsultaProcedimentoListView",
    "ConsultaProdutoDetailView",
    "ConsultaProdutoListView",
    "ConsultaReceberView",
    "ConsultaSecaoPDFView",
    "PatientAnamneseView",
    "PatientHistoricoConsultasView",
    "PatientPrescricaoView",
    "PrescricaoMemedPdfView",
]
