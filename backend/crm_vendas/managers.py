"""
Custom Managers para CRM Vendas.

Segue o padrão recomendado em Two Scoops of Django:
- Encapsula queries complexas
- Promove reutilização de código
- Mantém Models limpos (Thin Models)
"""
import logging
from django.db import models
from tenants.models import LojaIsolationManager

logger = logging.getLogger(__name__)


class ProdutoServicoManager(LojaIsolationManager):
    """
    Manager customizado para ProdutoServico.
    
    Responsabilidades:
    - Gerar códigos sequenciais
    - Queries otimizadas
    - Filtros comuns
    """
    
    def gerar_proximo_codigo(self, tipo: str, loja_id: int) -> str:
        """
        Gera o próximo código sequencial para produto/serviço.
        
        Formato:
        - Produtos: P001, P002, P003, ...
        - Serviços: S001, S002, S003, ...
        
        Args:
            tipo: 'produto' ou 'servico'
            loja_id: ID da loja
        
        Returns:
            str: Código no formato P001, S001, etc.
        
        Examples:
            >>> manager.gerar_proximo_codigo('produto', 132)
            'P001'
            >>> manager.gerar_proximo_codigo('servico', 132)
            'S001'
        """
        prefixo = 'P' if tipo == 'produto' else 'S'
        
        # Buscar último código com esse prefixo
        ultimo = self.filter(
            loja_id=loja_id,
            codigo__startswith=prefixo
        ).order_by('-codigo').first()
        
        if ultimo and ultimo.codigo:
            try:
                # Extrair número do código (ex: P001 -> 001 -> 1)
                ultimo_num = int(ultimo.codigo[1:])
                proximo_num = ultimo_num + 1
            except (ValueError, IndexError):
                # Se falhar ao extrair número, começar do 1
                logger.warning(
                    f'Erro ao extrair número do código: {ultimo.codigo}. '
                    f'Iniciando do 1.'
                )
                proximo_num = 1
        else:
            # Primeiro código deste tipo
            proximo_num = 1
        
        # Formatar com 3 dígitos (001, 002, etc)
        codigo = f"{prefixo}{proximo_num:03d}"
        
        logger.debug(
            f'Código gerado: {codigo} (tipo={tipo}, loja_id={loja_id})'
        )
        
        return codigo
    
    def ativos(self):
        """
        Retorna apenas produtos/serviços ativos.
        
        Returns:
            QuerySet: Produtos/serviços ativos
        """
        return self.filter(ativo=True)
    
    def por_tipo(self, tipo: str):
        """
        Filtra por tipo (produto ou serviço).
        
        Args:
            tipo: 'produto' ou 'servico'
        
        Returns:
            QuerySet: Produtos/serviços do tipo especificado
        """
        return self.filter(tipo=tipo)
    
    def por_categoria(self, categoria_id: int):
        """
        Filtra por categoria.
        
        Args:
            categoria_id: ID da categoria
        
        Returns:
            QuerySet: Produtos/serviços da categoria
        """
        return self.filter(categoria_id=categoria_id)
    
    def com_categoria(self):
        """
        Retorna queryset otimizado com categoria pré-carregada.
        
        Returns:
            QuerySet: Com select_related('categoria')
        """
        return self.select_related('categoria')


class OportunidadeManager(LojaIsolationManager):
    """
    Manager customizado para Oportunidade.
    
    Responsabilidades:
    - Queries otimizadas com relacionamentos
    - Filtros por etapa e status
    - Estatísticas e agregações
    """
    
    def com_relacionamentos(self):
        """
        Retorna queryset otimizado com relacionamentos pré-carregados.
        
        Otimização: Evita N+1 queries ao acessar lead, vendedor, conta.
        
        Returns:
            QuerySet: Com select_related e prefetch_related
        """
        return self.select_related(
            'lead',
            'vendedor',
            'lead__conta'
        ).prefetch_related(
            'atividades',
            'itens',
            'itens__produto_servico'
        )
    
    def por_etapa(self, etapa: str):
        """
        Filtra oportunidades por etapa do funil.
        
        Args:
            etapa: Nome da etapa (qualificacao, proposta, negociacao, etc)
        
        Returns:
            QuerySet: Oportunidades na etapa especificada
        """
        return self.filter(etapa=etapa)
    
    def abertas(self):
        """
        Retorna apenas oportunidades abertas (não ganhas nem perdidas).
        
        Returns:
            QuerySet: Oportunidades com etapa != 'ganha' e != 'perdida'
        """
        return self.exclude(etapa__in=['ganha', 'perdida'])
    
    def ganhas(self):
        """
        Retorna oportunidades ganhas.
        
        Returns:
            QuerySet: Oportunidades com etapa = 'ganha'
        """
        return self.filter(etapa='ganha')
    
    def perdidas(self):
        """
        Retorna oportunidades perdidas.
        
        Returns:
            QuerySet: Oportunidades com etapa = 'perdida'
        """
        return self.filter(etapa='perdida')
    
    def por_vendedor(self, vendedor_id: int):
        """
        Filtra oportunidades por vendedor.
        
        Args:
            vendedor_id: ID do vendedor
        
        Returns:
            QuerySet: Oportunidades do vendedor
        """
        return self.filter(vendedor_id=vendedor_id)


class PropostaManager(LojaIsolationManager):
    """
    Manager customizado para Proposta.
    
    Responsabilidades:
    - Queries otimizadas
    - Filtros por status
    - Estatísticas
    """
    
    def com_relacionamentos(self):
        """
        Retorna queryset otimizado com relacionamentos pré-carregados.
        
        Returns:
            QuerySet: Com select_related
        """
        return self.select_related(
            'oportunidade',
            'oportunidade__lead',
            'oportunidade__vendedor'
        )
    
    def por_status(self, status: str):
        """
        Filtra propostas por status.
        
        Args:
            status: Status da proposta (rascunho, enviada, aprovada, etc)
        
        Returns:
            QuerySet: Propostas com o status especificado
        """
        return self.filter(status=status)
    
    def rascunhos(self):
        """Retorna propostas em rascunho."""
        return self.filter(status='rascunho')
    
    def enviadas(self):
        """Retorna propostas enviadas."""
        return self.filter(status='enviada')
    
    def aprovadas(self):
        """Retorna propostas aprovadas."""
        return self.filter(status='aprovada')
    
    def rejeitadas(self):
        """Retorna propostas rejeitadas."""
        return self.filter(status='rejeitada')


class ContratoManager(LojaIsolationManager):
    """
    Manager customizado para Contrato.
    
    Responsabilidades:
    - Queries otimizadas
    - Filtros por status
    - Controle de assinaturas
    """
    
    def com_relacionamentos(self):
        """
        Retorna queryset otimizado com relacionamentos pré-carregados.
        
        Returns:
            QuerySet: Com select_related
        """
        return self.select_related(
            'oportunidade',
            'oportunidade__lead',
            'oportunidade__vendedor'
        )
    
    def por_status(self, status: str):
        """
        Filtra contratos por status.
        
        Args:
            status: Status do contrato
        
        Returns:
            QuerySet: Contratos com o status especificado
        """
        return self.filter(status=status)
    
    def aguardando_assinatura(self):
        """Retorna contratos aguardando assinatura."""
        return self.filter(status='aguardando_assinatura')
    
    def assinados(self):
        """Retorna contratos assinados."""
        return self.filter(status='assinado')
    
    def ativos(self):
        """Retorna contratos ativos."""
        return self.filter(status='ativo')


class LeadManager(LojaIsolationManager):
    """
    Manager customizado para Lead.
    
    Responsabilidades:
    - Queries otimizadas
    - Filtros por status e origem
    - Conversão para oportunidade
    """
    
    def com_relacionamentos(self):
        """
        Retorna queryset otimizado com relacionamentos pré-carregados.
        
        Returns:
            QuerySet: Com select_related e prefetch_related
        """
        return self.select_related(
            'conta',
            'vendedor'
        ).prefetch_related(
            'oportunidades',
            'contatos'
        )
    
    def por_status(self, status: str):
        """
        Filtra leads por status.
        
        Args:
            status: Status do lead (novo, qualificado, convertido, etc)
        
        Returns:
            QuerySet: Leads com o status especificado
        """
        return self.filter(status=status)
    
    def novos(self):
        """Retorna leads novos."""
        return self.filter(status='novo')
    
    def qualificados(self):
        """Retorna leads qualificados."""
        return self.filter(status='qualificado')
    
    def convertidos(self):
        """Retorna leads convertidos."""
        return self.filter(status='convertido')
    
    def por_origem(self, origem: str):
        """
        Filtra leads por origem.
        
        Args:
            origem: Origem do lead (site, indicacao, evento, etc)
        
        Returns:
            QuerySet: Leads da origem especificada
        """
        return self.filter(origem=origem)
