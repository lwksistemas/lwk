"""
Views de Convênios — Clínica da Beleza
"""
from decimal import Decimal, InvalidOperation

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Convenio, ConvenioProcedimentoPreco, Procedure
from .serializers import ConvenioSerializer, ConvenioListSerializer, ConvenioPrecoSerializer
from .serializers.convenios import gerar_codigo_convenio
from .permissions import CLINICA_MEMBER
from .pagination import paginate_queryset
from .views_base import GetObjectMixin
class ConvenioListView(APIView):
    """
    GET /clinica-beleza/convenios/ — lista convênios ativos
    POST /clinica-beleza/convenios/ — cria convênio
    """
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        incluir_inativos = request.query_params.get('todos') == '1'
        qs = Convenio.objects.all().order_by('nome')
        if not incluir_inativos:
            qs = qs.filter(is_active=True)
        for c in Convenio.objects.filter(codigo='').only('id', 'codigo')[:100]:
            c.codigo = gerar_codigo_convenio(c)
            c.save(update_fields=['codigo', 'updated_at'])
        return paginate_queryset(qs, request, ConvenioListSerializer)

    def post(self, request):
        data = {k: v for k, v in request.data.items() if k != 'codigo'}
        serializer = ConvenioSerializer(data=data)
        if serializer.is_valid():
            convenio = serializer.save()
            if not convenio.codigo:
                convenio.codigo = gerar_codigo_convenio(convenio)
                convenio.save(update_fields=['codigo', 'updated_at'])
            return Response(ConvenioSerializer(convenio).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConvenioDetailView(GetObjectMixin, APIView):
    """
    GET / PUT / DELETE /clinica-beleza/convenios/<pk>/
    """
    permission_classes = CLINICA_MEMBER
    model_class = Convenio
    not_found_message = 'Convênio não encontrado'

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(ConvenioSerializer(obj).data)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = ConvenioSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save(update_fields=['is_active', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConvenioPrecosView(GetObjectMixin, APIView):
    """
    GET /clinica-beleza/convenios/<pk>/precos/ — mapa de preços por procedimento
    PUT /clinica-beleza/convenios/<pk>/precos/ — salva preços em lote
    Body PUT: { "precos": [ { "procedure": 1, "modo": "fixo", "preco": "700.00" }, ... ] }
    modo: "fixo" (R$) ou "percentual" (% sobre particular). preco vazio remove a regra.
    """
    permission_classes = CLINICA_MEMBER
    model_class = Convenio
    not_found_message = 'Convênio não encontrado'

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        rows = ConvenioProcedimentoPreco.objects.filter(
            convenio=obj, is_active=True,
        ).select_related('procedure').order_by('procedure__nome')
        return Response(ConvenioPrecoSerializer(rows, many=True).data)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        itens = request.data.get('precos')
        if not isinstance(itens, list):
            return Response(
                {'error': 'Envie "precos" como lista de { procedure, preco }.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        procedure_ids = [item.get('procedure') for item in itens if item.get('procedure')]
        procedures = {
            p.id: p for p in Procedure.objects.filter(id__in=procedure_ids, is_active=True)
        }
        for item in itens:
            proc_id = item.get('procedure')
            if not proc_id or proc_id not in procedures:
                continue
            preco_raw = item.get('preco')
            if preco_raw in (None, ''):
                ConvenioProcedimentoPreco.objects.filter(
                    convenio=obj, procedure_id=proc_id,
                ).update(is_active=False)
                continue
            modo = item.get('modo') or 'fixo'
            if modo not in ('fixo', 'percentual'):
                return Response(
                    {'error': f'Modo inválido para procedimento {proc_id}. Use fixo ou percentual.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                preco = Decimal(str(preco_raw))
            except (InvalidOperation, TypeError):
                return Response(
                    {'error': f'Valor inválido para procedimento {proc_id}.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if modo == 'percentual' and (preco <= 0 or preco > 100):
                return Response(
                    {'error': f'Percentual deve estar entre 0 e 100 (procedimento {proc_id}).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if modo == 'fixo' and preco < 0:
                return Response(
                    {'error': f'Valor fixo não pode ser negativo (procedimento {proc_id}).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ConvenioProcedimentoPreco.objects.update_or_create(
                convenio=obj,
                procedure_id=proc_id,
                loja_id=obj.loja_id,
                defaults={'preco': preco, 'modo': modo, 'is_active': True},
            )
        rows = ConvenioProcedimentoPreco.objects.filter(
            convenio=obj, is_active=True,
        ).select_related('procedure').order_by('procedure__nome')
        return Response(ConvenioPrecoSerializer(rows, many=True).data)
