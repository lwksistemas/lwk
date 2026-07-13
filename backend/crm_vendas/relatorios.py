"""Relatórios de vendas em PDF — re-exporta módulos especializados e aliases de período.
"""
from .periodo import calcular_intervalo_datas as calcular_periodo
from .periodo import filtro_fechamento_no_periodo as _filtro_datas_fechamento_ganho
from .relatorios_pdf_common import (
    _criar_cabecalho_relatorio,
    _nome_cliente_venda,
    _obter_logo_loja,
)
from .relatorios_vendas_pdf import (
    gerar_relatorio_vendas_total,
    gerar_relatorio_vendas_vendedor,
)

__all__ = [
    "_criar_cabecalho_relatorio",
    "_filtro_datas_fechamento_ganho",
    "_nome_cliente_venda",
    "_obter_logo_loja",
    "calcular_periodo",
    "gerar_relatorio_vendas_total",
    "gerar_relatorio_vendas_vendedor",
]
