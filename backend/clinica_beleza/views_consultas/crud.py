"""Compat: re-exporta lista, detalhe e fluxo da consulta."""
from .consulta_detail import ConsultaDetailView
from .consulta_fluxo import (
    ConsultaAplicarProtocoloView,
    ConsultaEmitirNfseView,
    ConsultaEstornarPagamentoView,
    ConsultaFinalizarView,
    ConsultaIniciarView,
    ConsultaReabrirView,
    ConsultaReceberView,
)
from .consulta_list import ConsultaListView

__all__ = [
    "ConsultaAplicarProtocoloView",
    "ConsultaDetailView",
    "ConsultaEmitirNfseView",
    "ConsultaEstornarPagamentoView",
    "ConsultaFinalizarView",
    "ConsultaIniciarView",
    "ConsultaListView",
    "ConsultaReabrirView",
    "ConsultaReceberView",
]
