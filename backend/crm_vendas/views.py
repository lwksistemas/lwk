from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from datetime import date
from core.views import BaseModelViewSet
from .models import Lead, Cliente, Vendedor, Produto, Venda, Pipeline
from .serializers import (
    LeadSerializer, ClienteSerializer, VendedorSerializer,
    ProdutoSerializer, VendaSerializer, PipelineSerializer
)


class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrar por origem
        origem = self.request.query_params.get('origem')
        if origem:
            queryset = queryset.filter(origem=origem)
        
        return queryset

    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Retorna leads mais recentes (respeitando loja do contexto)"""
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class VendedorViewSet(BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer

    def _ensure_owner_vendedor(self):
        """Garante que o administrador da loja exista como vendedor (aparece em Funcionários)."""
        from tenants.middleware import get_current_loja_id
        from superadmin.models import Loja
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        loja_id = get_current_loja_id()
        
        logger.info(f"🔍 [_ensure_owner_vendedor] Chamado - loja_id no contexto: {loja_id}")
        
        if not loja_id:
            logger.warning("⚠️ [_ensure_owner_vendedor] Nenhuma loja_id no contexto")
            return
        
        try:
            loja = Loja.objects.get(id=loja_id)
            owner = loja.owner
            
            logger.info(f"🔍 [_ensure_owner_vendedor] Loja: {loja.slug}, Owner: {owner.email}")
            
            # Verificar se já existe usando all_without_filter para bypass do isolamento
            exists = Vendedor.objects.all_without_filter().filter(
                loja_id=loja_id, 
                email=owner.email
            ).exists()
            
            logger.info(f"🔍 [_ensure_owner_vendedor] Admin já existe? {exists}")
            
            if not exists:
                logger.info(f"✅ [_ensure_owner_vendedor] Criando vendedor admin para loja {loja_id}")
                Vendedor.objects.all_without_filter().create(
                    nome=owner.get_full_name() or owner.username or owner.email.split('@')[0],
                    email=owner.email,
                    telefone=getattr(owner, 'telefone', '') or '',
                    cargo='Administrador',
                    is_admin=True,
                    loja_id=loja_id,
                    meta_mensal=Decimal('10000.00'),
                )
                logger.info(f"✅ [_ensure_owner_vendedor] Vendedor admin criado com sucesso")
            else:
                logger.debug(f"ℹ️ [_ensure_owner_vendedor] Vendedor admin já existe para loja {loja_id}")
                
        except Loja.DoesNotExist:
            logger.error(f"❌ [_ensure_owner_vendedor] Loja {loja_id} não encontrada")
        except Exception as e:
            logger.error(f"❌ [_ensure_owner_vendedor] Erro ao criar vendedor admin: {e}", exc_info=True)

    def list(self, request, *args, **kwargs):
        """
        Lista vendedores garantindo que o admin existe e o queryset é avaliado
        ANTES do contexto ser limpo pelo middleware
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. Garantir que admin existe
        self._ensure_owner_vendedor()
        
        # 2. Obter queryset (ainda lazy)
        queryset = self.filter_queryset(self.get_queryset())
        
        # 3. FORÇAR avaliação do queryset AGORA (antes do middleware limpar contexto)
        # Isso converte o queryset lazy em uma lista concreta
        vendedores_list = list(queryset)
        logger.info(f"✅ [VendedorViewSet.list] Queryset avaliado - {len(vendedores_list)} vendedores encontrados")
        
        # 4. Serializar a lista concreta
        page = self.paginate_queryset(vendedores_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(vendedores_list, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Retorna queryset filtrado por loja
        IMPORTANTE: Este queryset é lazy e só será avaliado no list()
        """
        import logging
        from tenants.middleware import get_current_loja_id
        logger = logging.getLogger(__name__)
        
        loja_id = get_current_loja_id()
        logger.info(f"🔍 [VendedorViewSet.get_queryset] loja_id no contexto: {loja_id}")
        
        # IMPORTANTE: Garantir que admin existe antes de filtrar
        self._ensure_owner_vendedor()
        
        queryset = super().get_queryset()
        logger.info(f"📊 [VendedorViewSet.get_queryset] Queryset base obtido (lazy)")
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            logger.info(f"🔍 [VendedorViewSet.get_queryset] Filtrado por is_active={is_active}")
        
        return queryset


class ProdutoViewSet(BaseModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset


class VendaViewSet(BaseModelViewSet):
    # Otimização: select_related para evitar N+1
    queryset = Venda.objects.select_related('cliente', 'vendedor', 'produto').all()
    serializer_class = VendaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrar por cliente
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtrar por vendedor
        vendedor_id = self.request.query_params.get('vendedor_id')
        if vendedor_id:
            queryset = queryset.filter(vendedor_id=vendedor_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas do dashboard"""
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        
        # Leads ativos (não perdidos)
        leads_ativos = Lead.objects.exclude(status='perdido').count()
        
        # Negociações (vendas em negociação)
        negociacoes = Venda.objects.filter(status='em_negociacao').count()
        
        # Vendas do mês
        vendas_mes = Venda.objects.filter(
            data_fechamento__gte=primeiro_dia_mes,
            data_fechamento__lte=hoje,
            status='fechada'
        ).count()
        
        # Receita do mês
        receita = Venda.objects.filter(
            data_fechamento__gte=primeiro_dia_mes,
            data_fechamento__lte=hoje,
            status='fechada'
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        return Response({
            'leads_ativos': leads_ativos,
            'negociacoes': negociacoes,
            'vendas_mes': vendas_mes,
            'receita': float(receita)
        })


class PipelineViewSet(BaseModelViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset
