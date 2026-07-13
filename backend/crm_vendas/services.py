"""
Service Layer para CRM Vendas.

Segue o padrão recomendado em Two Scoops of Django:
- Isola lógica de negócio das Views
- Facilita testes unitários
- Promove reutilização de código
- Segue Single Responsibility Principle
"""
import logging
from typing import Any

from .models import Contrato, Oportunidade, Proposta, Vendedor
from .utils import get_current_vendedor_id, get_vendedor_padrao_admin_loja

logger = logging.getLogger(__name__)


def _oportunidade_tem_vendedor(validated_data: dict[str, Any]) -> bool:
    if validated_data.get('vendedor'):
        return True
    return validated_data.get('vendedor_id') is not None


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
    
    def criar_oportunidade(self, validated_data: dict[str, Any]) -> Oportunidade:
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
        from django.utils import timezone
        
        # Garantir datas de fechamento ao criar com etapa fechada
        etapa = validated_data.get('etapa', 'prospecting')
        if etapa == 'closed_won' and not validated_data.get('data_fechamento_ganho'):
            from django.utils import timezone
            validated_data['data_fechamento_ganho'] = timezone.now().date()
        elif etapa == 'closed_lost' and not validated_data.get('data_fechamento_perdido'):
            from django.utils import timezone
            validated_data['data_fechamento_perdido'] = timezone.now().date()
        
        # Regra 1: Vendedor logado (VendedorUsuario) tem prioridade — validar que existe no tenant
        if self.vendedor_id and not _oportunidade_tem_vendedor(validated_data):
            if Vendedor.objects.filter(id=self.vendedor_id).exists():
                validated_data['vendedor_id'] = self.vendedor_id
                validated_data.pop('vendedor', None)
                logger.info(
                    'Oportunidade criada com vendedor logado: vendedor_id=%s, user_id=%s',
                    self.vendedor_id, self.user_id,
                )
                return Oportunidade.objects.create(**validated_data)
            else:
                logger.warning(
                    'Vendedor logado vendedor_id=%s não existe no tenant, ignorando',
                    self.vendedor_id,
                )

        # Regra 2: Herdar vendedor do lead — validar que existe no tenant
        lead = validated_data.get('lead')
        if lead and not _oportunidade_tem_vendedor(validated_data) and getattr(lead, 'vendedor_id', None) and Vendedor.objects.filter(id=lead.vendedor_id).exists():
            validated_data['vendedor_id'] = lead.vendedor_id
            validated_data.pop('vendedor', None)
            logger.info(
                'Oportunidade herdou vendedor do lead: lead_id=%s, vendedor_id=%s',
                lead.id, lead.vendedor_id,
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
                logger.warning('Vendedor admin vendedor_id=%s não existe no tenant, ignorando', padrao)

        # Regra 4: Criar sem vendedor (warning)
        if not _oportunidade_tem_vendedor(validated_data):
            logger.warning(
                'Oportunidade criada SEM vendedor: user_id=%s, lead_id=%s. '
                'Vendedores não verão esta oportunidade na lista.',
                self.user_id, lead.id if lead else None,
            )

        return Oportunidade.objects.create(**validated_data)
    
    def atualizar_oportunidade(
        self, 
        instance: Oportunidade, 
        validated_data: dict[str, Any]
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
        
        # Garantir data_fechamento_ganho ao fechar como ganho
        nova_etapa = validated_data.get('etapa')
        if nova_etapa == 'closed_won' and not validated_data.get('data_fechamento_ganho') and not instance.data_fechamento_ganho:
            from django.utils import timezone
            validated_data['data_fechamento_ganho'] = timezone.now().date()
            logger.info(
                'data_fechamento_ganho definida automaticamente para oportunidade_id=%s',
                instance.id,
            )
        
        # Garantir data_fechamento_perdido ao fechar como perdido
        if nova_etapa == 'closed_lost' and not validated_data.get('data_fechamento_perdido') and not instance.data_fechamento_perdido:
            from django.utils import timezone
            validated_data['data_fechamento_perdido'] = timezone.now().date()

        # Atualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Receita automática de comissão ao fechar venda
        try:
            from .services_financeiro import sincronizar_receita_comissao_oportunidade
            sincronizar_receita_comissao_oportunidade(instance)
        except Exception as exc:
            logger.warning('Falha ao sincronizar receita comissão opp=%s: %s', instance.id, exc)

        # Sincronizar valor_total das propostas em rascunho quando valor da oportunidade muda
        if 'valor' in validated_data:
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
