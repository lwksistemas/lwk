from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, datetime, timedelta
from core.views import BaseModelViewSet, BaseFuncionarioViewSet
from core.mixins import ClienteSearchMixin
from core.throttling import DashboardRateThrottle
from .models import (
    Cliente, Profissional, Procedimento, Agendamento, Funcionario,
    ProtocoloProcedimento, EvolucaoPaciente, AnamnesesTemplate, Anamnese,
    HorarioFuncionamento, BloqueioAgenda, Consulta
)
from .serializers import (
    ClienteSerializer, ProfissionalSerializer, ProcedimentoSerializer,
    AgendamentoSerializer, FuncionarioSerializer, ProtocoloProcedimentoSerializer,
    EvolucaoPacienteSerializer, AnamnesesTemplateSerializer, AnamneseSerializer,
    HorarioFuncionamentoSerializer, BloqueioAgendaSerializer, ClienteBuscaSerializer,
    ConsultaSerializer, HistoricoLoginSerializer, CategoriaFinanceiraSerializer,
    TransacaoSerializer
)


class ClienteViewSet(ClienteSearchMixin, BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    search_serializer_class = ClienteBuscaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Busca clientes por nome, telefone ou email"""
        return ClienteSearchMixin.buscar(self, request)


class ProfissionalViewSet(BaseModelViewSet):
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]


class ProcedimentoViewSet(BaseModelViewSet):
    queryset = Procedimento.objects.all()
    serializer_class = ProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, 'query_params', self.request.GET)
        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset


class ProtocoloProcedimentoViewSet(BaseModelViewSet):
    queryset = ProtocoloProcedimento.objects.all()
    serializer_class = ProtocoloProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, 'query_params', self.request.GET)
        procedimento_id = params.get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class AgendamentoViewSet(BaseModelViewSet):
    queryset = Agendamento.objects.select_related('cliente', 'profissional', 'procedimento')
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, 'query_params', self.request.GET)
        
        # Filtros
        data = params.get('data')
        if data:
            queryset = queryset.filter(data=data)
        
        status_param = params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        cliente_id = params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        profissional_id = params.get('profissional_id')
        if profissional_id:
            queryset = queryset.filter(profissional_id=profissional_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def calendario(self, request):
        """Retorna agendamentos para visualização em calendário"""
        params = getattr(request, 'query_params', request.GET)
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        
        if not data_inicio or not data_fim:
            return Response({'error': 'data_inicio e data_fim são obrigatórios'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Usar get_queryset() para respeitar filtros (ex.: profissional_id) e isolamento por loja
        qs = self.get_queryset()
        agendamentos = qs.filter(
            data__gte=data_inicio,
            data__lte=data_fim
        ).order_by('data', 'horario')
        
        serializer = self.get_serializer(agendamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """Retorna próximos agendamentos"""
        hoje = date.today()
        agendamentos = self.queryset.filter(
            data__gte=hoje,
            status__in=['agendado', 'confirmado']
        ).order_by('data', 'horario')[:10]
        
        serializer = self.get_serializer(agendamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas do dashboard"""
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        
        stats = {
            'agendamentos_hoje': self.queryset.filter(data=hoje).count(),
            'agendamentos_mes': self.queryset.filter(
                data__gte=primeiro_dia_mes,
                data__lte=hoje
            ).count(),
            'receita_mensal': float(
                self.queryset.filter(
                    data__gte=primeiro_dia_mes,
                    data__lte=hoje,
                    status='concluido'
                ).aggregate(total=Sum('valor'))['total'] or 0
            ),
            'clientes_ativos': Cliente.objects.filter(is_active=True).count(),
            'procedimentos_ativos': Procedimento.objects.filter(is_active=True).count()
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'], throttle_classes=[DashboardRateThrottle])
    def dashboard(self, request):
        """
        Retorna estatísticas + próximos agendamentos em uma única resposta (menos round-trips).
        Rate limited: 10 requisições por minuto para prevenir loops infinitos.
        """
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        qs = self.queryset

        stats = {
            'agendamentos_hoje': qs.filter(data=hoje).count(),
            'agendamentos_mes': qs.filter(data__gte=primeiro_dia_mes, data__lte=hoje).count(),
            'receita_mensal': float(
                qs.filter(
                    data__gte=primeiro_dia_mes,
                    data__lte=hoje,
                    status='concluido'
                ).aggregate(total=Sum('valor'))['total'] or 0
            ),
            'clientes_ativos': Cliente.objects.filter(is_active=True).count(),
            'procedimentos_ativos': Procedimento.objects.filter(is_active=True).count(),
        }

        agendamentos = qs.filter(
            data__gte=hoje,
            status__in=['agendado', 'confirmado']
        ).order_by('data', 'horario')[:10]
        serializer = self.get_serializer(agendamentos, many=True)

        return Response({
            'estatisticas': stats,
            'proximos': serializer.data,
        })


class EvolucaoPacienteViewSet(BaseModelViewSet):
    queryset = EvolucaoPaciente.objects.select_related('cliente', 'profissional', 'agendamento')
    serializer_class = EvolucaoPacienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = getattr(self.request, "query_params", self.request.GET).get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class AnamnesesTemplateViewSet(BaseModelViewSet):
    queryset = AnamnesesTemplate.objects.select_related('procedimento')
    serializer_class = AnamnesesTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        procedimento_id = getattr(self.request, "query_params", self.request.GET).get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class AnamneseViewSet(BaseModelViewSet):
    queryset = Anamnese.objects.select_related('cliente', 'template', 'agendamento')
    serializer_class = AnamneseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = getattr(self.request, "query_params", self.request.GET).get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class HorarioFuncionamentoViewSet(BaseModelViewSet):
    queryset = HorarioFuncionamento.objects.all()
    serializer_class = HorarioFuncionamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(is_active=True).order_by('dia_semana')


class BloqueioAgendaViewSet(BaseModelViewSet):
    queryset = BloqueioAgenda.objects.select_related('profissional')
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, "query_params", self.request.GET)
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        profissional_id = params.get('profissional_id')

        # Apenas bloqueios ativos
        queryset = queryset.filter(is_active=True)
        
        if data_inicio and data_fim:
            queryset = queryset.filter(
                data_inicio__lte=data_fim,
                data_fim__gte=data_inicio
            )

        # Se filtrar por profissional, incluir bloqueios do profissional E bloqueios globais (profissional null)
        if profissional_id:
            queryset = queryset.filter(Q(profissional_id=profissional_id) | Q(profissional__isnull=True))
        
        return queryset


class FuncionarioViewSet(BaseFuncionarioViewSet):
    serializer_class = FuncionarioSerializer
    model_class = Funcionario
    cargo_padrao = 'Administrador'
    permission_classes = [IsAuthenticated]


class ConsultaViewSet(BaseModelViewSet):
    serializer_class = ConsultaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Usar loja_id do header da requisição (não depender de thread-local em produção)
        loja_id = self.request.headers.get('X-Loja-ID') or getattr(
            self.request, 'META', {}
        ).get('HTTP_X_LOJA_ID')
        if not loja_id:
            from tenants.middleware import get_current_loja_id
            loja_id = get_current_loja_id()
        if not loja_id:
            return Consulta.objects.none()
        try:
            loja_id = int(loja_id)
        except (ValueError, TypeError):
            return Consulta.objects.none()

        # Filtrar explicitamente por loja_id (all_without_filter + filter evita 404 em DELETE)
        base = Consulta.objects.all_without_filter().filter(loja_id=loja_id).select_related(
            'cliente', 'profissional', 'procedimento', 'agendamento'
        )

        params = getattr(self.request, 'query_params', self.request.GET)
        if params.get('cliente_id'):
            base = base.filter(cliente_id=params.get('cliente_id'))
        if params.get('profissional_id'):
            base = base.filter(profissional_id=params.get('profissional_id'))
        if params.get('status'):
            base = base.filter(status=params.get('status'))

        return base

    @action(detail=True, methods=['post'])
    def iniciar_consulta(self, request, pk=None):
        """Inicia uma consulta (muda status para em_andamento)"""
        consulta = self.get_object()
        
        if consulta.status != 'agendada':
            return Response(
                {'error': 'Consulta deve estar agendada para ser iniciada'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consulta.status = 'em_andamento'
        consulta.data_inicio = timezone.now()
        consulta.save()
        
        serializer = self.get_serializer(consulta)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def finalizar_consulta(self, request, pk=None):
        """Finaliza uma consulta (muda status para concluida)"""
        consulta = self.get_object()
        
        if consulta.status != 'em_andamento':
            return Response(
                {'error': 'Consulta deve estar em andamento para ser finalizada'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consulta.status = 'concluida'
        consulta.data_fim = timezone.now()
        
        # Atualizar dados do pagamento se fornecidos
        valor_pago = request.data.get('valor_pago')
        forma_pagamento = request.data.get('forma_pagamento')
        observacoes = request.data.get('observacoes_gerais')
        
        if valor_pago is not None:
            consulta.valor_pago = valor_pago
        if forma_pagamento:
            consulta.forma_pagamento = forma_pagamento
        if observacoes:
            consulta.observacoes_gerais = observacoes
        
        consulta.save()
        
        # Atualizar status do agendamento
        consulta.agendamento.status = 'concluido'
        consulta.agendamento.save()
        
        serializer = self.get_serializer(consulta)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def sync_from_agendamentos(self, request):
        """
        Cria Consulta para Agendamentos que ainda não têm.
        Assim agendamentos já cadastrados passam a aparecer na Lista de Consultas.
        """
        from tenants.middleware import get_current_loja_id

        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'error': 'Contexto de loja não definido (X-Loja-ID)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Agendamentos da loja que ainda não têm Consulta
        agendamentos_sem_consulta = Agendamento.objects.filter(
            loja_id=loja_id
        ).exclude(
            id__in=Consulta.objects.values_list('agendamento_id', flat=True)
        )

        criadas = 0
        for ag in agendamentos_sem_consulta:
            Consulta.objects.get_or_create(
                agendamento=ag,
                defaults={
                    'cliente_id': ag.cliente_id,
                    'profissional_id': ag.profissional_id,
                    'procedimento_id': ag.procedimento_id,
                    'status': 'agendada',
                    'valor_consulta': ag.valor,
                    'loja_id': loja_id,
                }
            )
            criadas += 1

        return Response({'criadas': criadas, 'message': f'{criadas} consulta(s) criada(s) a partir de agendamentos.'})

    @action(detail=False, methods=['get'])
    def em_andamento(self, request):
        """Retorna consultas em andamento"""
        consultas = self.queryset.filter(status='em_andamento')
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def hoje(self, request):
        """Retorna consultas de hoje"""
        hoje = date.today()
        consultas = self.queryset.filter(agendamento__data=hoje)
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)



class HistoricoLoginViewSet(BaseModelViewSet):
    """
    ViewSet para Histórico de Login
    Lista ações dos usuários com filtros por data, usuário e ação
    """
    serializer_class = HistoricoLoginSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Retorna histórico filtrado por loja
        Suporta filtros por: usuario, acao, data_inicio, data_fim
        """
        from clinica_estetica.models import HistoricoLogin
        
        queryset = HistoricoLogin.objects.all().order_by('-created_at')
        params = getattr(self.request, 'query_params', self.request.GET)
        
        # Filtro por usuário
        usuario = params.get('usuario')
        if usuario:
            queryset = queryset.filter(usuario__icontains=usuario)
        
        # Filtro por ação
        acao = params.get('acao')
        if acao:
            queryset = queryset.filter(acao=acao)
        
        # Filtro por período
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        if data_inicio:
            queryset = queryset.filter(created_at__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(created_at__lte=data_fim)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Cria registro de histórico
        Captura IP automaticamente da requisição
        """
        # Capturar IP do cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Capturar User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Adicionar ao request.data
        data = request.data.copy()
        data['ip_address'] = ip_address
        data['user_agent'] = user_agent
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class CategoriaFinanceiraViewSet(BaseModelViewSet):
    """
    ViewSet para Categorias Financeiras
    CRUD completo com filtros
    """
    serializer_class = CategoriaFinanceiraSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtros: tipo, is_active
        """
        from clinica_estetica.models import CategoriaFinanceira
        
        queryset = CategoriaFinanceira.objects.all().order_by('tipo', 'nome')
        params = getattr(self.request, 'query_params', self.request.GET)
        
        # Filtro por tipo
        tipo = params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Filtro por ativo
        is_active = params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class TransacaoViewSet(BaseModelViewSet):
    """
    ViewSet para Transações Financeiras
    Com ações customizadas e relatórios
    """
    serializer_class = TransacaoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtros: tipo, status, categoria, data_inicio, data_fim
        """
        from clinica_estetica.models import Transacao
        
        queryset = Transacao.objects.select_related('categoria', 'cliente').order_by('-data_vencimento')
        params = getattr(self.request, 'query_params', self.request.GET)
        
        # Filtro por tipo
        tipo = params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Filtro por status
        status_param = params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtro por categoria
        categoria_id = params.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        # Filtro por período
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        if data_inicio:
            queryset = queryset.filter(data_vencimento__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_vencimento__lte=data_fim)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Adiciona created_by automaticamente
        """
        user = self.request.user
        created_by = user.get_full_name() or user.username
        serializer.save(created_by=created_by)
    
    @action(detail=True, methods=['post'])
    def marcar_como_pago(self, request, pk=None):
        """
        Marca transação como paga
        """
        transacao = self.get_object()
        
        forma_pagamento = request.data.get('forma_pagamento')
        data_pagamento = request.data.get('data_pagamento')
        valor_pago = request.data.get('valor_pago', transacao.valor)
        
        if not forma_pagamento:
            return Response(
                {'error': 'Forma de pagamento é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transacao.status = 'pago'
        transacao.forma_pagamento = forma_pagamento
        transacao.valor_pago = valor_pago
        
        if data_pagamento:
            transacao.data_pagamento = data_pagamento
        else:
            from django.utils import timezone
            transacao.data_pagamento = timezone.now().date()
        
        transacao.save()
        
        serializer = self.get_serializer(transacao)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela transação
        """
        transacao = self.get_object()
        
        if transacao.status == 'pago':
            return Response(
                {'error': 'Não é possível cancelar uma transação já paga'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transacao.status = 'cancelado'
        transacao.save()
        
        serializer = self.get_serializer(transacao)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def resumo(self, request):
        """
        Retorna resumo financeiro do período
        """
        from clinica_estetica.models import Transacao
        from django.db.models import Sum, Q, Count
        from django.utils import timezone
        from decimal import Decimal
        
        params = getattr(request, 'query_params', request.GET)
        
        # Período (padrão: mês atual)
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        
        if not data_inicio or not data_fim:
            hoje = timezone.now().date()
            data_inicio = hoje.replace(day=1)
            # Último dia do mês
            if hoje.month == 12:
                data_fim = hoje.replace(year=hoje.year + 1, month=1, day=1) - timezone.timedelta(days=1)
            else:
                data_fim = hoje.replace(month=hoje.month + 1, day=1) - timezone.timedelta(days=1)
        
        # Queries otimizadas
        transacoes = Transacao.objects.filter(
            data_vencimento__gte=data_inicio,
            data_vencimento__lte=data_fim
        )
        
        # Receitas
        receitas = transacoes.filter(tipo='receita')
        total_receitas = receitas.aggregate(total=Sum('valor'))['total'] or Decimal('0')
        receitas_pagas = receitas.filter(status='pago').aggregate(total=Sum('valor_pago'))['total'] or Decimal('0')
        receitas_pendentes = receitas.filter(status='pendente').aggregate(total=Sum('valor'))['total'] or Decimal('0')
        
        # Despesas
        despesas = transacoes.filter(tipo='despesa')
        total_despesas = despesas.aggregate(total=Sum('valor'))['total'] or Decimal('0')
        despesas_pagas = despesas.filter(status='pago').aggregate(total=Sum('valor_pago'))['total'] or Decimal('0')
        despesas_pendentes = despesas.filter(status='pendente').aggregate(total=Sum('valor'))['total'] or Decimal('0')
        
        # Saldo
        saldo = receitas_pagas - despesas_pagas
        
        # Atrasados
        hoje = timezone.now().date()
        atrasados = transacoes.filter(
            status='pendente',
            data_vencimento__lt=hoje
        )
        transacoes_atrasadas = atrasados.count()
        valor_atrasado = atrasados.aggregate(total=Sum('valor'))['total'] or Decimal('0')
        
        resumo = {
            'total_receitas': float(total_receitas),
            'total_despesas': float(total_despesas),
            'saldo': float(saldo),
            'receitas_pendentes': float(receitas_pendentes),
            'despesas_pendentes': float(despesas_pendentes),
            'receitas_pagas': float(receitas_pagas),
            'despesas_pagas': float(despesas_pagas),
            'transacoes_atrasadas': transacoes_atrasadas,
            'valor_atrasado': float(valor_atrasado),
        }
        
        from clinica_estetica.serializers import TransacaoResumoSerializer
        serializer = TransacaoResumoSerializer(resumo)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def fluxo_caixa(self, request):
        """
        Retorna fluxo de caixa diário do período
        """
        from clinica_estetica.models import Transacao
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import timedelta
        from decimal import Decimal
        
        params = getattr(request, 'query_params', request.GET)
        
        # Período (padrão: últimos 30 dias)
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
        
        if params.get('data_inicio'):
            data_inicio = params.get('data_inicio')
        if params.get('data_fim'):
            data_fim = params.get('data_fim')
        
        # Agrupar por data
        transacoes = Transacao.objects.filter(
            data_vencimento__gte=data_inicio,
            data_vencimento__lte=data_fim,
            status='pago'
        ).values('data_pagamento').annotate(
            receitas=Sum('valor_pago', filter=Q(tipo='receita')),
            despesas=Sum('valor_pago', filter=Q(tipo='despesa'))
        ).order_by('data_pagamento')
        
        # Formatar resposta
        fluxo = []
        for item in transacoes:
            receitas = float(item['receitas'] or Decimal('0'))
            despesas = float(item['despesas'] or Decimal('0'))
            fluxo.append({
                'data': item['data_pagamento'],
                'receitas': receitas,
                'despesas': despesas,
                'saldo': receitas - despesas
            })
        
        return Response(fluxo)
