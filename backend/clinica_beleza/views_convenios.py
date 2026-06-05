"""
Views de Convênios — Clínica da Beleza
"""
from decimal import Decimal, InvalidOperation

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Convenio, ConvenioProcedimentoPreco, Procedure
from .serializers import ConvenioSerializer, ConvenioListSerializer, ConvenioPrecoSerializer
from .permissions import CLINICA_MEMBER
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
        return Response(ConvenioListSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ConvenioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
    Body PUT: { "precos": [ { "procedure": 1, "preco": "700.00" }, ... ] }
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
            try:
                preco = Decimal(str(preco_raw))
            except (InvalidOperation, TypeError):
                return Response(
                    {'error': f'Preço inválido para procedimento {proc_id}.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ConvenioProcedimentoPreco.objects.update_or_create(
                convenio=obj,
                procedure_id=proc_id,
                loja_id=obj.loja_id,
                defaults={'preco': preco, 'is_active': True},
            )
        rows = ConvenioProcedimentoPreco.objects.filter(
            convenio=obj, is_active=True,
        ).select_related('procedure').order_by('procedure__nome')
        return Response(ConvenioPrecoSerializer(rows, many=True).data)
