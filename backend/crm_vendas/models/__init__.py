"""Modelos do CRM Vendas — multi-tenant (LojaIsolationMixin)."""
from ..models_config import CRMConfig
from ..models_relatorio_comissao import RelatorioComissao
from .vendedores import Vendedor
from .contas import Conta
from .leads import Lead
from .contatos import Contato
from .oportunidades import Oportunidade
from .atividades import Atividade
from .catalogo import CategoriaProdutoServico, ProdutoServico
from .oportunidade_items import OportunidadeItem
from .documentos import Contrato, Proposta
from .templates import ContratoTemplate, PropostaTemplate
from .assinaturas import AssinaturaDigital

__all__ = [
    'Vendedor', 'Conta', 'Lead', 'Contato', 'Oportunidade', 'Atividade',
    'CategoriaProdutoServico', 'ProdutoServico', 'OportunidadeItem',
    'Proposta', 'Contrato', 'PropostaTemplate', 'ContratoTemplate',
    'AssinaturaDigital', 'CRMConfig', 'RelatorioComissao',
]
