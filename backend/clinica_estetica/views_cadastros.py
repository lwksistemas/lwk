from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from core.views import BaseModelViewSet, BaseFuncionarioViewSet
from core.mixins import ClienteSearchMixin
from .models import (
    Cliente, Profissional, Procedimento, Funcionario,
    ProtocoloProcedimento, EvolucaoPaciente, AnamnesesTemplate, Anamnese,
    HorarioFuncionamento, HorarioTrabalhoProfissional,
)
from .serializers import (
    ClienteSerializer, ProfissionalSerializer, ProcedimentoSerializer,
    FuncionarioSerializer, ProtocoloProcedimentoSerializer,
    EvolucaoPacienteSerializer, AnamnesesTemplateSerializer, AnamneseSerializer,
    HorarioFuncionamentoSerializer, HorarioTrabalhoProfissionalSerializer,
    ClienteBuscaSerializer,
)


class ClienteViewSet(ClienteSearchMixin, BaseModelViewSet):
    serializer_class = ClienteSerializer
    search_serializer_class = ClienteBuscaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Retorna queryset filtrado por loja e is_active
        IMPORTANTE: Não usar queryset como atributo de classe para evitar cache
        """
        queryset = Cliente.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Cliente, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Busca clientes por nome, telefone ou email"""
        return ClienteSearchMixin.buscar(self, request)


class ProfissionalViewSet(BaseModelViewSet):
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retorna queryset filtrado por loja e is_active"""
        queryset = Profissional.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Profissional, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset


class HorarioTrabalhoProfissionalView(APIView):
    """
    Dias e horários de atendimento do profissional.
    GET /api/clinica/profissionais/<id>/horarios-trabalho/  → lista
    PUT /api/clinica/profissionais/<id>/horarios-trabalho/  → substitui todos
    Body PUT: [{"dia_semana": 0, "hora_entrada": "08:00", "hora_saida": "18:00", "intervalo_inicio": null, "intervalo_fim": null, "ativo": true}]
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            profissional = Profissional.objects.get(pk=pk)
        except Profissional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        queryset = HorarioTrabalhoProfissional.objects.filter(profissional_id=pk).order_by('dia_semana')
        serializer = HorarioTrabalhoProfissionalSerializer(queryset, many=True)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            profissional = Profissional.objects.get(pk=pk)
        except Profissional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Envie uma lista de horários. Ex.: [{"dia_semana": 0, "hora_entrada": "08:00", "hora_saida": "18:00", "ativo": true}]'},
                status=status.HTTP_400_BAD_REQUEST
            )
        HorarioTrabalhoProfissional.objects.filter(profissional_id=pk).delete()
        created = []
        for item in request.data:
            item = dict(item)
            serializer = HorarioTrabalhoProfissionalSerializer(data=item)
            if serializer.is_valid():
                obj = serializer.save(profissional=profissional)
                if not getattr(obj, 'loja_id', None) and getattr(profissional, 'loja_id', None):
                    obj.loja_id = profissional.loja_id
                    obj.save(update_fields=['loja_id'])
                created.append(HorarioTrabalhoProfissionalSerializer(obj).data)
            else:
                HorarioTrabalhoProfissional.objects.filter(profissional_id=pk).delete()
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(created, status=status.HTTP_200_OK)


class ProcedimentoViewSet(BaseModelViewSet):
    serializer_class = ProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna queryset filtrado por loja e categoria"""
        queryset = Procedimento.objects.all()
        
        # Aplicar filtro is_active do BaseModelViewSet
        if hasattr(Procedimento, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        params = getattr(self.request, 'query_params', self.request.GET)
        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset


class ProtocoloProcedimentoViewSet(BaseModelViewSet):
    serializer_class = ProtocoloProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna queryset filtrado por loja e procedimento"""
        queryset = ProtocoloProcedimento.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(ProtocoloProcedimento, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        params = getattr(self.request, 'query_params', self.request.GET)
        procedimento_id = params.get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class FuncionarioViewSet(BaseFuncionarioViewSet):
    serializer_class = FuncionarioSerializer
    model_class = Funcionario
    cargo_padrao = 'Administrador'
    permission_classes = [IsAuthenticated]


class EvolucaoPacienteViewSet(BaseModelViewSet):
    serializer_class = EvolucaoPacienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna queryset filtrado por loja e cliente"""
        queryset = EvolucaoPaciente.objects.select_related('cliente', 'profissional', 'agendamento')
        
        # Aplicar filtro is_active
        if hasattr(EvolucaoPaciente, 'is_active'):
            queryset = queryset.filter(is_active=True)
        cliente_id = getattr(self.request, "query_params", self.request.GET).get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class AnamnesesTemplateViewSet(BaseModelViewSet):
    serializer_class = AnamnesesTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna queryset filtrado por loja e procedimento"""
        queryset = AnamnesesTemplate.objects.select_related('procedimento')
        
        # Aplicar filtro is_active
        if hasattr(AnamnesesTemplate, 'is_active'):
            queryset = queryset.filter(is_active=True)
        procedimento_id = getattr(self.request, "query_params", self.request.GET).get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class AnamneseViewSet(BaseModelViewSet):
    serializer_class = AnamneseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna queryset filtrado por loja e cliente"""
        queryset = Anamnese.objects.select_related('cliente', 'template', 'agendamento')
        cliente_id = getattr(self.request, "query_params", self.request.GET).get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class HorarioFuncionamentoViewSet(BaseModelViewSet):
    serializer_class = HorarioFuncionamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna horários ativos ordenados por dia da semana"""
        return HorarioFuncionamento.objects.filter(is_active=True).order_by('dia_semana')
