from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.views import BaseModelViewSet
from .models import Categoria, Servico, Cliente, Profissional, Agendamento, OrdemServico, Orcamento, Funcionario
from .serializers import (
    CategoriaSerializer, ServicoSerializer, ClienteSerializer,
    ProfissionalSerializer, AgendamentoSerializer, OrdemServicoSerializer,
    OrcamentoSerializer, FuncionarioSerializer
)


class CategoriaViewSet(BaseModelViewSet):
    # Otimização: prefetch_related para servicos
    queryset = Categoria.objects.prefetch_related('servicos').all()
    serializer_class = CategoriaSerializer


class ServicoViewSet(BaseModelViewSet):
    # Otimização: select_related para categoria
    queryset = Servico.objects.select_related('categoria').all()
    serializer_class = ServicoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria_id')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class ProfissionalViewSet(BaseModelViewSet):
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer


class FuncionarioViewSet(BaseModelViewSet):
    # IMPORTANTE: NÃO definir queryset como atributo de classe!
    # O queryset deve ser obtido dinamicamente no get_queryset()
    # para garantir que o middleware já setou o loja_id no contexto
    serializer_class = FuncionarioSerializer
    
    def _ensure_owner_funcionario(self):
        """
        Garante que o administrador da loja exista como funcionário.
        Cria automaticamente se não existir.
        """
        from stores.models import Store
        import logging
        logger = logging.getLogger(__name__)
        
        # Obter loja_id do contexto (setado pelo middleware)
        loja_id = getattr(self.request, 'loja_id', None)
        if not loja_id:
            logger.warning("⚠️ [FuncionarioViewSet SERVICOS] Nenhuma loja no contexto")
            return
        
        try:
            loja = Store.objects.get(id=loja_id)
            
            # Verificar se já existe funcionário admin para esta loja
            admin_exists = Funcionario.objects.filter(
                loja_id=loja_id,
                is_admin=True
            ).exists()
            
            if not admin_exists and loja.owner:
                # Criar funcionário admin automaticamente
                Funcionario.objects.create(
                    loja_id=loja_id,
                    nome=loja.owner.get_full_name() or loja.owner.username,
                    email=loja.owner.email,
                    telefone='',
                    cargo='Administrador',
                    is_admin=True
                )
                logger.info(f"✅ [FuncionarioViewSet SERVICOS] Admin criado para loja {loja.name}")
        except Exception as e:
            logger.error(f"❌ [FuncionarioViewSet SERVICOS] Erro ao criar admin: {e}")
    
    def list(self, request, *args, **kwargs):
        self._ensure_owner_funcionario()
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        # IMPORTANTE: Garantir que admin existe antes de filtrar
        self._ensure_owner_funcionario()
        # O BaseModelViewSet já aplica o filtro por loja_id
        return Funcionario.objects.all()


class AgendamentoViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = Agendamento.objects.select_related('cliente', 'servico', 'profissional').all()
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por data
        data = self.request.query_params.get('data')
        if data:
            queryset = queryset.filter(data=data)
        
        # Filtrar por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrar por cliente
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtrar por profissional
        profissional_id = self.request.query_params.get('profissional_id')
        if profissional_id:
            queryset = queryset.filter(profissional_id=profissional_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas do dashboard"""
        from django.db.models import Sum, Count
        from datetime import date
        
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        
        # Agendamentos hoje
        agendamentos_hoje = self.queryset.filter(data=hoje).count()
        
        # Ordens de serviço abertas
        ordens_abertas = OrdemServico.objects.filter(
            status__in=['aberta', 'em_andamento', 'aguardando_peca']
        ).count()
        
        # Orçamentos pendentes
        orcamentos_pendentes = Orcamento.objects.filter(status='pendente').count()
        
        # Receita mensal (agendamentos concluídos)
        receita = self.queryset.filter(
            data__gte=primeiro_dia_mes,
            data__lte=hoje,
            status='concluido'
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        return Response({
            'agendamentos_hoje': agendamentos_hoje,
            'ordens_abertas': ordens_abertas,
            'orcamentos_pendentes': orcamentos_pendentes,
            'receita_mensal': float(receita)
        })


class OrdemServicoViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = OrdemServico.objects.select_related('cliente', 'servico', 'profissional').all()
    serializer_class = OrdemServicoSerializer


class OrcamentoViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = Orcamento.objects.select_related('cliente', 'servico').all()
    serializer_class = OrcamentoSerializer
