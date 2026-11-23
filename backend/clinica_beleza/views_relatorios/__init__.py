"""Views para Relatórios — Clínica da Beleza."""
from .agenda import RelatorioFolgasBloqueiosPdfView, RelatorioFolgasBloqueiosView
from .comissoes import RelatorioComissoesPdfView, RelatorioComissoesView
from .financeiro import (
    RelatorioDescontosPdfView,
    RelatorioDescontosView,
    RelatorioFaturamentoPdfView,
    RelatorioFaturamentoView,
    RelatorioInadimplentesPdfView,
    RelatorioInadimplentesView,
    RelatorioLancamentosPdfView,
    RelatorioLancamentosView,
    RelatorioVendaPrazoPdfView,
    RelatorioVendaPrazoView,
)
from .repasse import RelatorioRepasseConsultaPdfView, RelatorioRepasseConsultaView

__all__ = [
    "RelatorioComissoesPdfView",
    "RelatorioComissoesView",
    "RelatorioDescontosPdfView",
    "RelatorioDescontosView",
    "RelatorioFaturamentoPdfView",
    "RelatorioFaturamentoView",
    "RelatorioFolgasBloqueiosPdfView",
    "RelatorioFolgasBloqueiosView",
    "RelatorioInadimplentesPdfView",
    "RelatorioInadimplentesView",
    "RelatorioLancamentosPdfView",
    "RelatorioLancamentosView",
    "RelatorioVendaPrazoPdfView",
    "RelatorioVendaPrazoView",
    "RelatorioRepasseConsultaPdfView",
    "RelatorioRepasseConsultaView",
]
