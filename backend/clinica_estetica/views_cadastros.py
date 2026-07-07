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
    queryset = Procedimento.objects.all()
    serializer_class = ProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        categoria = self.request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria=categoria)
        return qs


class ProtocoloProcedimentoViewSet(BaseModelViewSet):
    queryset = ProtocoloProcedimento.objects.all()
    serializer_class = ProtocoloProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        procedimento_id = self.request.query_params.get('procedimento_id')
        if procedimento_id:
            qs = qs.filter(procedimento_id=procedimento_id)
        return qs


class FuncionarioViewSet(BaseFuncionarioViewSet):
    serializer_class = FuncionarioSerializer
    model_class = Funcionario
    cargo_padrao = 'Administrador'
    permission_classes = [IsAuthenticated]


class EvolucaoPacienteViewSet(BaseModelViewSet):
    queryset = EvolucaoPaciente.objects.select_related('cliente', 'profissional', 'agendamento').all()
    serializer_class = EvolucaoPacienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        return qs


class AnamnesesTemplateViewSet(BaseModelViewSet):
    queryset = AnamnesesTemplate.objects.select_related('procedimento').all()
    serializer_class = AnamnesesTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        procedimento_id = self.request.query_params.get('procedimento_id')
        if procedimento_id:
            qs = qs.filter(procedimento_id=procedimento_id)
        return qs


class AnamneseViewSet(BaseModelViewSet):
    queryset = Anamnese.objects.select_related('cliente', 'template', 'agendamento').all()
    serializer_class = AnamneseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        return qs


class HorarioFuncionamentoViewSet(BaseModelViewSet):
    serializer_class = HorarioFuncionamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna horários ativos ordenados por dia da semana"""
        return HorarioFuncionamento.objects.filter(is_active=True).order_by('dia_semana')
