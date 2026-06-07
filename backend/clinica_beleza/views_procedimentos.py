"""
Views de Procedimentos — Clínica da Beleza
"""
import logging
from decimal import Decimal, InvalidOperation

from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_MEMBER
from rest_framework import status

from .models import Convenio, ConvenioProcedimentoPreco, Procedure
from .serializers import ProcedureSerializer, ConvenioListSerializer, ConvenioPrecoSerializer
from .pagination import paginate_queryset
from .views_base import GetObjectMixin, map_field_names

logger = logging.getLogger(__name__)

_PROCEDURE_FIELD_MAP = {
    'name': 'nome',
    'description': 'descricao',
    'price': 'preco',
    'duration': 'duracao_minutos',
    'duration_minutes': 'duracao_minutos',
    'active': 'is_active',
    'category': 'categoria',
}


def _map_procedure_data(raw_data):
    return map_field_names(raw_data, _PROCEDURE_FIELD_MAP)


class ProcedureListView(APIView):
    """
    GET /clinica-beleza/procedures/
    POST /clinica-beleza/procedures/
    """
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        categoria = (request.query_params.get('categoria') or '').strip()
        queryset = Procedure.objects.all().order_by('nome')
        if active_only:
            queryset = queryset.filter(is_active=True)
        if categoria:
            queryset = queryset.filter(categoria__icontains=categoria)
        return paginate_queryset(queryset, request, ProcedureSerializer)

    def post(self, request):
        data = _map_procedure_data(request.data)
        serializer = ProcedureSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error('POST procedures errors=%s', serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProcedureDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/procedures/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_MEMBER
    model_class = Procedure
    not_found_message = 'Procedimento não encontrado'

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(ProcedureSerializer(obj).data)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        data = _map_procedure_data(request.data)
        serializer = ProcedureSerializer(obj, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _sincronizar_preco_particular_procedure(procedure):
    """Atualiza procedure.preco a partir da coluna Particular na tabela de convênios."""
    row = ConvenioProcedimentoPreco.objects.filter(
        procedure=procedure,
        is_active=True,
        convenio__is_active=True,
        convenio__nome__icontains='particular',
        modo='fixo',
    ).first()
    if row:
        procedure.preco = row.preco
        procedure.save(update_fields=['preco', 'updated_at'])


def _salvar_precos_convenio_procedure(procedure, itens):
    """Grava preços fixos por convênio para um procedimento."""
    convenio_ids = [item.get('convenio') for item in itens if item.get('convenio')]
    convenios = {
        c.id: c for c in Convenio.objects.filter(id__in=convenio_ids, is_active=True)
    }
    for item in itens:
        conv_id = item.get('convenio')
        if not conv_id or conv_id not in convenios:
            continue
        convenio = convenios[conv_id]
        preco_raw = item.get('preco')
        if preco_raw in (None, ''):
            ConvenioProcedimentoPreco.objects.filter(
                convenio=convenio, procedure=procedure,
            ).update(is_active=False)
            continue
        try:
            preco = Decimal(str(preco_raw))
        except (InvalidOperation, TypeError):
            raise ValueError(f'Valor inválido para convênio {conv_id}.')
        if preco < 0:
            raise ValueError(f'Valor não pode ser negativo (convênio {conv_id}).')
        ConvenioProcedimentoPreco.objects.update_or_create(
            convenio=convenio,
            procedure=procedure,
            loja_id=procedure.loja_id,
            defaults={'preco': preco, 'modo': 'fixo', 'is_active': True},
        )
    _sincronizar_preco_particular_procedure(procedure)


class ProcedimentoConvenioPrecosMatrixView(APIView):
    """
    GET /clinica-beleza/procedures/convenio-precos-matrix/
    Matriz de preços: convênios ativos + valores por (procedimento, convênio).
    """
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        convenios = Convenio.objects.filter(is_active=True).order_by('nome')
        rows = ConvenioProcedimentoPreco.objects.filter(
            is_active=True,
            convenio__is_active=True,
            procedure__is_active=True,
            modo='fixo',
        ).values('procedure_id', 'convenio_id', 'preco')
        precos = [
            {
                'procedure': r['procedure_id'],
                'convenio': r['convenio_id'],
                'preco': str(r['preco']),
            }
            for r in rows
        ]
        return Response({
            'convenios': ConvenioListSerializer(convenios, many=True).data,
            'precos': precos,
        })


class ProcedurePrecosConvenioView(GetObjectMixin, APIView):
    """
    GET /clinica-beleza/procedures/<pk>/precos-convenio/
    PUT — body: { "precos": [ { "convenio": 1, "preco": "700.00" }, ... ] }
    """
    permission_classes = CLINICA_MEMBER
    model_class = Procedure
    not_found_message = 'Procedimento não encontrado'

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        convenios = Convenio.objects.filter(is_active=True).order_by('nome')
        rows = {
            r.convenio_id: r
            for r in ConvenioProcedimentoPreco.objects.filter(
                procedure=obj, is_active=True, convenio__is_active=True,
            ).select_related('convenio')
        }
        out = []
        for conv in convenios:
            row = rows.get(conv.id)
            if row:
                out.append({
                    'convenio': conv.id,
                    'convenio_codigo': conv.codigo,
                    'convenio_nome': conv.nome,
                    'modo': row.modo,
                    'preco': str(row.preco),
                    'preco_efetivo': float(row.calcular_preco_efetivo(obj)),
                })
            else:
                out.append({
                    'convenio': conv.id,
                    'convenio_codigo': conv.codigo,
                    'convenio_nome': conv.nome,
                    'modo': 'fixo',
                    'preco': None,
                    'preco_efetivo': None,
                })
        return Response(out)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        itens = request.data.get('precos')
        if not isinstance(itens, list):
            return Response(
                {'error': 'Envie "precos" como lista de { convenio, preco }.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            _salvar_precos_convenio_procedure(obj, itens)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        rows = ConvenioProcedimentoPreco.objects.filter(
            procedure=obj, is_active=True, convenio__is_active=True,
        ).select_related('convenio').order_by('convenio__nome')
        return Response(ConvenioPrecoSerializer(rows, many=True).data)
