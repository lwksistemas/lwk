"""Views para Relatórios — Clínica da Beleza."""
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
)
from .repasse import RelatorioRepasseConsultaPdfView, RelatorioRepasseConsultaView

__all__ = [
    "RelatorioComissoesPdfView",
    "RelatorioComissoesView",
    "RelatorioDescontosPdfView",
    "RelatorioDescontosView",
    "RelatorioFaturamentoPdfView",
    "RelatorioFaturamentoView",
    "RelatorioInadimplentesPdfView",
    "RelatorioInadimplentesView",
    "RelatorioLancamentosPdfView",
    "RelatorioLancamentosView",
    "RelatorioRepasseConsultaPdfView",
    "RelatorioRepasseConsultaView",
]
