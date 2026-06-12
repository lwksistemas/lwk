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
from .leads import LeadListSerializer, LeadSerializer
from .oportunidade_items import OportunidadeItemSerializer
from .oportunidades import OportunidadeSerializer
from .vendedores import VendedorSerializer

__all__ = [
    'VendedorSerializer',
    'ContaSerializer',
    'LeadSerializer',
    'LeadListSerializer',
    'ContatoSerializer',
    'OportunidadeSerializer',
    'AtividadeSerializer',
    'AtividadeListSerializer',
    'CategoriaProdutoServicoSerializer',
    'ProdutoServicoSerializer',
    'OportunidadeItemSerializer',
    'PropostaSerializer',
    'PropostaTemplateSerializer',
    'ContratoTemplateSerializer',
    'ContratoSerializer',
    'CRMConfigSerializer',
]
