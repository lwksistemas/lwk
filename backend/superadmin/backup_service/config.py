"""Configuração de tabelas para backup de lojas."""
from typing import List

class TabelaConfig:
    """
    Configuração de uma tabela para backup.
    
    Encapsula informações sobre como exportar/importar cada tabela.
    """
    
    def __init__(
        self,
        nome: str,
        ordem_exportacao: int = 100,
        ordem_importacao: int = 100,
        incluir_imagens: bool = False
    ):
        self.nome = nome
        self.ordem_exportacao = ordem_exportacao
        self.ordem_importacao = ordem_importacao
        self.incluir_imagens = incluir_imagens
    
    def __repr__(self):
        return f"TabelaConfig({self.nome})"


class BackupConfig:
    """
    Configuração centralizada de tabelas para backup.
    
    Define quais tabelas devem ser incluídas e em qual ordem.
    Facilita manutenção e extensão do sistema.
    """
    
    # Tabelas principais (ordem de exportação/importação é importante)
    TABELAS = [
        # Cadastros básicos (sem dependências)
        TabelaConfig('categorias', ordem_exportacao=1, ordem_importacao=1),
        TabelaConfig('fornecedores', ordem_exportacao=2, ordem_importacao=2),
        TabelaConfig('clientes', ordem_exportacao=3, ordem_importacao=3),
        TabelaConfig('profissionais', ordem_exportacao=4, ordem_importacao=4),
        
        # Produtos e serviços (dependem de categorias)
        TabelaConfig('produtos', ordem_exportacao=10, ordem_importacao=10),
        TabelaConfig('servicos', ordem_exportacao=11, ordem_importacao=11),
        
        # Estoque (depende de produtos)
        TabelaConfig('estoque', ordem_exportacao=20, ordem_importacao=20),
        TabelaConfig('movimentacoes_estoque', ordem_exportacao=21, ordem_importacao=21),
        
        # Agendamentos (depende de profissionais e serviços)
        TabelaConfig('agendamentos', ordem_exportacao=30, ordem_importacao=30),
        
        # Vendas (depende de clientes e produtos)
        TabelaConfig('vendas', ordem_exportacao=40, ordem_importacao=40),
        TabelaConfig('itens_venda', ordem_exportacao=41, ordem_importacao=41),
        TabelaConfig('pagamentos', ordem_exportacao=42, ordem_importacao=42),
        # CRM Vendas (ordem: vendedor antes de conta/lead; conta antes de lead/contato; lead antes de oportunidade/atividade)
        TabelaConfig('crm_vendas_vendedor', ordem_exportacao=100, ordem_importacao=100),
        TabelaConfig('crm_vendas_conta', ordem_exportacao=101, ordem_importacao=101),
        TabelaConfig('crm_vendas_lead', ordem_exportacao=102, ordem_importacao=102),
        TabelaConfig('crm_vendas_contato', ordem_exportacao=103, ordem_importacao=103),
        TabelaConfig('crm_vendas_oportunidade', ordem_exportacao=104, ordem_importacao=104),
        TabelaConfig('crm_vendas_atividade', ordem_exportacao=105, ordem_importacao=105),
        TabelaConfig('crm_vendas_config', ordem_exportacao=106, ordem_importacao=106),
        TabelaConfig('crm_vendas_produto_servico', ordem_exportacao=107, ordem_importacao=107),
        TabelaConfig('crm_vendas_oportunidade_item', ordem_exportacao=108, ordem_importacao=108),
        TabelaConfig('crm_vendas_proposta', ordem_exportacao=109, ordem_importacao=109),
        TabelaConfig('crm_vendas_contrato', ordem_exportacao=110, ordem_importacao=110),
        TabelaConfig('nfse_integration_nfse', ordem_exportacao=111, ordem_importacao=111),
    ]
    
    @classmethod
    def get_tabelas_ordenadas_exportacao(cls) -> List[TabelaConfig]:
        """Retorna tabelas ordenadas para exportação"""
        return sorted(cls.TABELAS, key=lambda t: t.ordem_exportacao)
    
    @classmethod
    def get_tabelas_ordenadas_importacao(cls) -> List[TabelaConfig]:
        """Retorna tabelas ordenadas para importação"""
        return sorted(cls.TABELAS, key=lambda t: t.ordem_importacao)
    
    @classmethod
    def get_nomes_tabelas(cls) -> List[str]:
        """Retorna lista de nomes de tabelas"""
        return [t.nome for t in cls.TABELAS]
