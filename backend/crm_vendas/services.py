"""
Service Layer para CRM Vendas.

Segue o padrão recomendado em Two Scoops of Django:
- Isola lógica de negócio das Views
- Facilita testes unitários
- Promove reutilização de código
- Segue Single Responsibility Principle
"""
import logging
from typing import Dict, Any, Optional
from django.db import transaction
from .models import Oportunidade, Proposta, Contrato, Lead, ProdutoServico
from .utils import get_current_vendedor_id, get_vendedor_padrao_admin_loja

logger = logging.getLogger(__name__)


def _oportunidade_tem_vendedor(validated_data: Dict[str, Any]) -> bool:
    if validated_data.get('vendedor'):
        return True
    if validated_data.get('vendedor_id') is not None:
        return True
    return False


class OportunidadeService:
    """
    Service Layer para lógica de negócio de Oportunidades.
    
    Responsabilidades:
    - Criar oportunidades com regras de negócio
    - Atualizar oportunidades mantendo integridade
    - Aplicar regras de atribuição de vendedor
    """
    
    def __init__(self, request):
        """
        Inicializa o service com contexto da requisição.
        
        Args:
            request: Request object do Django
        """
        self.request = request
        self.vendedor_id = get_current_vendedor_id(request)
        self.user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
    
    def criar_oportunidade(self, validated_data: Dict[str, Any]) -> Oportunidade:
        """
        Cria uma oportunidade aplicando regras de negócio.
        
        Regras de atribuição de vendedor (em ordem de prioridade):
        1. Usar vendedor logado (VendedorUsuario) — se existir no tenant
        2. Herdar vendedor do lead
        3. Usar vendedor admin padrão da loja
        4. Criar sem vendedor (com warning)
        
        Args:
            validated_data: Dados validados do serializer
        
        Returns:
            Oportunidade: Instância criada
        """
        from .models import Vendedor
        
        # Regra 1: Vendedor logado (VendedorUsuario) tem prioridade — validar que existe no tenant
        if self.vendedor_id and not _oportunidade_tem_vendedor(validated_data):
            if Vendedor.objects.filter(id=self.vendedor_id).exists():
                validated_data['vendedor_id'] = self.vendedor_id
                validated_data.pop('vendedor', None)
                logger.info(
                    f'Oportunidade criada com vendedor logado: '
                    f'vendedor_id={self.vendedor_id}, user_id={self.user_id}'
                )
                return Oportunidade.objects.create(**validated_data)
            else:
                logger.warning(
                    f'Vendedor logado vendedor_id={self.vendedor_id} não existe no tenant, ignorando'
                )

        # Regra 2: Herdar vendedor do lead — validar que existe no tenant
        lead = validated_data.get('lead')
        if lead and not _oportunidade_tem_vendedor(validated_data) and getattr(lead, 'vendedor_id', None):
            if Vendedor.objects.filter(id=lead.vendedor_id).exists():
                validated_data['vendedor_id'] = lead.vendedor_id
                validated_data.pop('vendedor', None)
                logger.info(
                    f'Oportunidade herdou vendedor do lead: '
                    f'lead_id={lead.id}, vendedor_id={lead.vendedor_id}'
                )
                return Oportunidade.objects.create(**validated_data)

        # Regra 3: Vendedor administrador da loja — validar que existe no tenant
        if not _oportunidade_tem_vendedor(validated_data):
            padrao = get_vendedor_padrao_admin_loja(self.request)
            if padrao and Vendedor.objects.filter(id=padrao).exists():
                validated_data['vendedor_id'] = padrao
                validated_data.pop('vendedor', None)
                logger.info(
                    'Oportunidade atribuída ao vendedor administrador da loja: vendedor_id=%s, user_id=%s',
                    padrao,
                    self.user_id,
                )
                return Oportunidade.objects.create(**validated_data)
            elif padrao:
                logger.warning(f'Vendedor admin vendedor_id={padrao} não existe no tenant, ignorando')

        # Regra 4: Criar sem vendedor (warning)
        if not _oportunidade_tem_vendedor(validated_data):
            logger.warning(
                f'Oportunidade criada SEM vendedor: '
                f'user_id={self.user_id}, lead_id={lead.id if lead else None}. '
                f'Vendedores não verão esta oportunidade na lista.'
            )

        return Oportunidade.objects.create(**validated_data)
    
    def atualizar_oportunidade(
        self, 
        instance: Oportunidade, 
        validated_data: Dict[str, Any]
    ) -> Oportunidade:
        """
        Atualiza oportunidade aplicando regras de negócio.
        
        Regra: Se é vendedor logado e a oportunidade não tem vendedor,
        vincular automaticamente.
        
        Args:
            instance: Instância da oportunidade
            validated_data: Dados validados do serializer
        
        Returns:
            Oportunidade: Instância atualizada
        """
        # Vincular vendedor se necessário (vendedor comum ou administrador da loja)
        if instance.vendedor_id is None and not _oportunidade_tem_vendedor(validated_data):
            if self.vendedor_id:
                validated_data['vendedor_id'] = self.vendedor_id
                validated_data.pop('vendedor', None)
                logger.info(
                    f'Oportunidade vinculada ao vendedor logado: '
                    f'oportunidade_id={instance.id}, vendedor_id={self.vendedor_id}'
                )
            else:
                padrao = get_vendedor_padrao_admin_loja(self.request)
                if padrao:
                    validated_data['vendedor_id'] = padrao
                    validated_data.pop('vendedor', None)
                    logger.info(
                        'Oportunidade vinculada ao vendedor administrador da loja: '
                        'oportunidade_id=%s, vendedor_id=%s',
                        instance.id,
                        padrao,
                    )
        
        # Atualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Sincronizar valor_total das propostas em rascunho quando valor da oportunidade muda
        if 'valor' in validated_data:
            from .models import Proposta, Contrato
            novo_valor = validated_data['valor']
            propostas_atualizadas = Proposta.objects.filter(
                oportunidade_id=instance.id,
                status='rascunho',
            ).update(valor_total=novo_valor)
            contratos_atualizados = Contrato.objects.filter(
                oportunidade_id=instance.id,
                status='rascunho',
            ).update(valor_total=novo_valor)
            if propostas_atualizadas or contratos_atualizados:
                logger.info(
                    'Valor atualizado: %d proposta(s) e %d contrato(s) em rascunho (oportunidade_id=%s, valor=%s)',
                    propostas_atualizadas, contratos_atualizados, instance.id, novo_valor,
                )
        
        return instance


class PropostaService:
    """
    Service Layer para lógica de negócio de Propostas.
    
    Responsabilidades:
    - Gerar propostas a partir de templates
    - Enviar propostas para clientes
    - Gerenciar workflow de aprovação
    """
    
    def __init__(self, request):
        self.request = request
        self.vendedor_id = get_current_vendedor_id(request)
    
    @transaction.atomic
    def gerar_proposta_de_template(
        self, 
        oportunidade: Oportunidade, 
        template_id: int,
        customizacoes: Optional[Dict[str, Any]] = None
    ) -> Proposta:
        """
        Gera uma proposta a partir de um template.
        
        Args:
            oportunidade: Oportunidade relacionada
            template_id: ID do template
            customizacoes: Customizações opcionais (título, conteúdo, etc)
        
        Returns:
            Proposta: Instância criada
        """
        from .models import PropostaTemplate
        
        template = PropostaTemplate.objects.get(id=template_id)
        
        # Dados base do template
        proposta_data = {
            'oportunidade': oportunidade,
            'titulo': template.titulo,
            'conteudo': template.conteudo,
            'status': 'rascunho',
        }
        
        # Aplicar customizações
        if customizacoes:
            proposta_data.update(customizacoes)
        
        proposta = Proposta.objects.create(**proposta_data)
        
        logger.info(
            f'Proposta gerada de template: '
            f'proposta_id={proposta.id}, template_id={template_id}, '
            f'oportunidade_id={oportunidade.id}'
        )
        
        return proposta
    
    def enviar_para_cliente(self, proposta: Proposta) -> bool:
        """
        Envia proposta para o cliente.
        
        Args:
            proposta: Instância da proposta
        
        Returns:
            bool: True se enviado com sucesso
        """
        from django.utils import timezone
        
        # Validar se pode enviar
        if proposta.status not in ['rascunho', 'revisao']:
            logger.warning(
                f'Tentativa de enviar proposta com status inválido: '
                f'proposta_id={proposta.id}, status={proposta.status}'
            )
            return False
        
        # Atualizar status
        proposta.status = 'enviada'
        proposta.data_envio = timezone.now()
        proposta.save()
        
        # TODO: Integrar com sistema de email/notificação
        
        logger.info(
            f'Proposta enviada para cliente: '
            f'proposta_id={proposta.id}, oportunidade_id={proposta.oportunidade_id}'
        )
        
        return True


class ContratoService:
    """
    Service Layer para lógica de negócio de Contratos.
    
    Responsabilidades:
    - Gerar contratos a partir de propostas aprovadas
    - Gerenciar assinaturas digitais
    - Controlar workflow de aprovação
    """
    
    def __init__(self, request):
        self.request = request
        self.vendedor_id = get_current_vendedor_id(request)
    
    @transaction.atomic
    def gerar_contrato_de_proposta(
        self, 
        proposta: Proposta,
        customizacoes: Optional[Dict[str, Any]] = None
    ) -> Contrato:
        """
        Gera um contrato a partir de uma proposta aprovada.
        
        Args:
            proposta: Proposta aprovada
            customizacoes: Customizações opcionais
        
        Returns:
            Contrato: Instância criada
        
        Raises:
            ValueError: Se proposta não está aprovada
        """
        if proposta.status != 'aprovada':
            raise ValueError(
                f'Proposta deve estar aprovada para gerar contrato. '
                f'Status atual: {proposta.status}'
            )
        
        # Verificar se já existe contrato
        if Contrato.objects.filter(oportunidade=proposta.oportunidade).exists():
            raise ValueError(
                f'Já existe contrato para esta oportunidade: '
                f'oportunidade_id={proposta.oportunidade_id}'
            )
        
        # Dados base da proposta
        contrato_data = {
            'oportunidade': proposta.oportunidade,
            'titulo': proposta.titulo,
            'conteudo': proposta.conteudo,
            'valor_total': proposta.valor_total,
            'status': 'rascunho',
        }
        
        # Aplicar customizações
        if customizacoes:
            contrato_data.update(customizacoes)
        
        contrato = Contrato.objects.create(**contrato_data)
        
        logger.info(
            f'Contrato gerado de proposta: '
            f'contrato_id={contrato.id}, proposta_id={proposta.id}, '
            f'oportunidade_id={proposta.oportunidade_id}'
        )
        
        return contrato
    
    def enviar_para_assinatura(self, contrato: Contrato) -> bool:
        """
        Envia contrato para assinatura digital.
        
        Args:
            contrato: Instância do contrato
        
        Returns:
            bool: True se enviado com sucesso
        """
        from django.utils import timezone
        
        # Validar se pode enviar
        if contrato.status not in ['rascunho', 'revisao']:
            logger.warning(
                f'Tentativa de enviar contrato com status inválido: '
                f'contrato_id={contrato.id}, status={contrato.status}'
            )
            return False
        
        # Atualizar status
        contrato.status = 'aguardando_assinatura'
        contrato.data_envio = timezone.now()
        contrato.save()
        
        # TODO: Integrar com sistema de assinatura digital
        
        logger.info(
            f'Contrato enviado para assinatura: '
            f'contrato_id={contrato.id}, oportunidade_id={contrato.oportunidade_id}'
        )
        
        return True


class ProdutoServicoService:
    """
    Service Layer para lógica de negócio de Produtos/Serviços.
    
    Responsabilidades:
    - Gerenciar catálogo de produtos/serviços
    - Calcular preços e descontos
    - Validar disponibilidade
    """
    
    @staticmethod
    def calcular_valor_total_itens(itens: list) -> float:
        """
        Calcula o valor total de uma lista de itens.
        
        Args:
            itens: Lista de OportunidadeItem
        
        Returns:
            float: Valor total
        """
        total = sum(
            float(item.quantidade) * float(item.preco_unitario)
            for item in itens
        )
        return round(total, 2)
    
    @staticmethod
    def validar_disponibilidade(produto_servico: ProdutoServico) -> bool:
        """
        Valida se produto/serviço está disponível para venda.
        
        Args:
            produto_servico: Instância do produto/serviço
        
        Returns:
            bool: True se disponível
        """
        if not produto_servico.ativo:
            logger.warning(
                f'Produto/serviço inativo: id={produto_servico.id}, '
                f'nome={produto_servico.nome}'
            )
            return False
        
        return True
