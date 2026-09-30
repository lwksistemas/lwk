"""Views de consultas — re-export do pacote modular."""
from .clinical import (
    ConsultaEvolucaoListView,
    ConsultaReciboPdfView,
    ConsultaSecaoPDFView,
    PatientAnamneseView,
    PatientHistoricoConsultasView,
)
from .crud import (
    ConsultaAplicarProtocoloView,
    ConsultaDetailView,
    ConsultaEmitirNfseView,
    ConsultaEstornarPagamentoView,
    ConsultaFinalizarView,
    ConsultaIniciarView,
    ConsultaListView,
    ConsultaTrocarProfissionalView,
    ConsultaResumoFinanceiroView,
    ConsultaReabrirView,
    ConsultaReceberView,
)
from .prescricoes import (
    ConsultaPrescricaoDeleteView,
    ConsultaPrescricaoView,
    PatientPrescricaoView,
    PrescricaoMemedPdfView,
)
from .procedimentos import ConsultaProcedimentoDetailView, ConsultaProcedimentoListView
from .produtos import ConsultaProdutoDetailView, ConsultaProdutoListView

__all__ = [
    "ConsultaAplicarProtocoloView",
    "ConsultaDetailView",
    "ConsultaEmitirNfseView",
    "ConsultaEstornarPagamentoView",
    "ConsultaEvolucaoListView",
    "ConsultaFinalizarView",
    "ConsultaIniciarView",
    "ConsultaListView",
    "ConsultaTrocarProfissionalView",
    "ConsultaResumoFinanceiroView",
    "ConsultaPrescricaoDeleteView",
    "ConsultaPrescricaoView",
    "ConsultaProcedimentoDetailView",
    "ConsultaProcedimentoListView",
    "ConsultaProdutoDetailView",
    "ConsultaProdutoListView",
    "ConsultaReabrirView",
    "ConsultaReceberView",
    "ConsultaReciboPdfView",
    "ConsultaSecaoPDFView",
    "PatientAnamneseView",
    "PatientHistoricoConsultasView",
    "PatientPrescricaoView",
    "PrescricaoMemedPdfView",
]
