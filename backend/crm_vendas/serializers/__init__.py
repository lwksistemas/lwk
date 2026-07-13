"""Serializers do CRM Vendas."""
from .atividades import AtividadeListSerializer, AtividadeSerializer
from .catalogo import CategoriaProdutoServicoSerializer, ProdutoServicoSerializer
from .config import CRMConfigSerializer
from .contas import ContaSerializer
from .contatos import ContatoSerializer
from .documentos import (
    ContratoSerializer,
    ContratoTemplateSerializer,
    PropostaSerializer,
    PropostaTemplateSerializer,
)
from .financeiro import (
    GrupoFinanceiroCRMSerializer,
    LancamentoFinanceiroCRMSerializer,
)
from .leads import LeadListSerializer, LeadSerializer
from .oportunidade_items import OportunidadeItemSerializer
from .oportunidade_notas import OportunidadeNotaSerializer
from .oportunidades import OportunidadeSerializer
from .vendedores import VendedorSerializer

__all__ = [
    "AtividadeListSerializer",
    "AtividadeSerializer",
    "CRMConfigSerializer",
    "CategoriaProdutoServicoSerializer",
    "ContaSerializer",
    "ContatoSerializer",
    "ContratoSerializer",
    "ContratoTemplateSerializer",
    "GrupoFinanceiroCRMSerializer",
    "LancamentoFinanceiroCRMSerializer",
    "LeadListSerializer",
    "LeadSerializer",
    "OportunidadeItemSerializer",
    "OportunidadeNotaSerializer",
    "OportunidadeSerializer",
    "ProdutoServicoSerializer",
    "PropostaSerializer",
    "PropostaTemplateSerializer",
    "VendedorSerializer",
]
