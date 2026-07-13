"""Modelos do CRM Vendas — multi-tenant (LojaIsolationMixin)."""
from ..models_config import CRMConfig
from ..models_relatorio_comissao import RelatorioComissao
from .assinaturas import AssinaturaDigital
from .atividades import Atividade
from .catalogo import CategoriaProdutoServico, ProdutoServico
from .contas import Conta
from .contatos import Contato
from .documentos import Contrato, Proposta
from .financeiro import GrupoFinanceiroCRM, LancamentoFinanceiroCRM, RecorrenciaFinanceiroCRM
from .leads import Lead
from .oportunidade_items import OportunidadeItem
from .oportunidade_notas import OportunidadeNota
from .oportunidades import Oportunidade
from .templates import ContratoTemplate, PropostaTemplate
from .vendedores import Vendedor

__all__ = [
    "AssinaturaDigital",
    "Atividade",
    "CRMConfig",
    "CategoriaProdutoServico",
    "Conta",
    "Contato",
    "Contrato",
    "ContratoTemplate",
    "GrupoFinanceiroCRM",
    "LancamentoFinanceiroCRM",
    "Lead",
    "Oportunidade",
    "OportunidadeItem",
    "OportunidadeNota",
    "ProdutoServico",
    "Proposta",
    "PropostaTemplate",
    "RecorrenciaFinanceiroCRM",
    "RelatorioComissao",
    "Vendedor",
]
