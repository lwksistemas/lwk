"""
Views de Pagamentos e Financeiro — Clínica da Beleza
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_FINANCEIRO
from rest_framework import status
from django.utils.timezone import now
from django.db.models import Sum

from .models import CategoriaDespesa, Despesa, Payment
from .models.financeiro import CATEGORIAS_DESPESA_PADRAO
from .serializers.financeiro import CategoriaDespesaSerializer, DespesaSerializer, PaymentSerializer
from .pagination import paginate_queryset
from .views_base import GetObjectMixin, resolve_loja_id_from_request


def _garantir_categorias_despesa_padrao(loja_id: int) -> None:
    if CategoriaDespesa.objects.exists():
        return
    for nome in CATEGORIAS_DESPESA_PADRAO:
        CategoriaDespesa.objects.create(loja_id=loja_id, nome=nome)


class PaymentListView(APIView):
    """
    GET /clinica-beleza/payments/
    POST /clinica-beleza/payments/
    """
    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        queryset = Payment.objects.select_related(
            'appointment', 'appointment__patient',
            'appointment__professional', 'appointment__procedure',
        ).order_by('-created_at')
        if s := request.query_params.get('status'):
            queryset = queryset.filter(status=s)
        if d := request.query_params.get('date'):
            queryset = queryset.filter(payment_date__date=d)
        if p := request.query_params.get('professional'):
            queryset = queryset.filter(appointment__professional_id=p)
        return paginate_queryset(queryset, request, PaymentSerializer)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/payments/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_FINANCEIRO
    model_class = Payment
    not_found_message = 'Pagamento não encontrado'
    select_related_fields = (
        'appointment', 'appointment__patient',
        'appointment__professional', 'appointment__procedure',
    )

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(PaymentSerializer(obj).data)

    def put(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        serializer = PaymentSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FinanceiroResumoView(APIView):
    """
    GET /clinica-beleza/financeiro/resumo/
    Resumo: caixa diário, total mês, contas a receber, comissões.
    Query: mes, ano (opcional — padrão mês atual).
    """
    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        from datetime import date
        import calendar

        today = now().date()
        try:
            ano = int(request.query_params.get('ano') or today.year)
            mes = int(request.query_params.get('mes') or today.month)
            if not (1 <= mes <= 12):
                raise ValueError
        except (ValueError, TypeError):
            ano, mes = today.year, today.month

        first_day = date(ano, mes, 1)
        last_day = date(ano, mes, calendar.monthrange(ano, mes)[1])
        period_end = today if (ano == today.year and mes == today.month) else last_day

        def _sum(qs):
            return float(qs.aggregate(total=Sum('amount'))['total'] or 0)

        faturamento = _sum(Payment.objects.filter(
            status='PAID',
            payment_date__date__gte=first_day,
            payment_date__date__lte=period_end,
        ))
        contas_a_receber = _sum(Payment.objects.filter(status='PENDING'))
        comissao_mes = float(
            Payment.objects.filter(
                status='PAID',
                payment_date__date__gte=first_day,
                payment_date__date__lte=period_end,
            ).aggregate(total=Sum('comissao_valor'))['total'] or 0
        )

        def _sum_despesa(qs):
            return float(qs.aggregate(total=Sum('valor'))['total'] or 0)

        despesas_operacionais = _sum_despesa(Despesa.objects.filter(
            status='PAID',
            data_pagamento__gte=first_day,
            data_pagamento__lte=period_end,
        ))
        despesas_pendentes = _sum_despesa(Despesa.objects.filter(status='PENDING'))
        despesas_total = comissao_mes + despesas_operacionais

        return Response({
            'caixa_diario': _sum(Payment.objects.filter(status='PAID', payment_date__date=today)),
            'total_mes': faturamento,
            'contas_a_receber': contas_a_receber,
            'comissao_mes': comissao_mes,
            'despesas_operacionais': despesas_operacionais,
            'despesas_pendentes': despesas_pendentes,
            'faturamento': faturamento,
            'despesas': despesas_total,
            'lucro': faturamento - despesas_total,
            'filter': {'mes': mes, 'ano': ano},
        })


class CategoriaDespesaListView(APIView):
    """GET/POST /clinica-beleza/despesas/categorias/"""
    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if loja_id:
            _garantir_categorias_despesa_padrao(loja_id)
        qs = CategoriaDespesa.objects.filter(is_active=True).order_by('nome')
        return Response(CategoriaDespesaSerializer(qs, many=True).data)

    def post(self, request):
        loja_id = resolve_loja_id_from_request(request)
        serializer = CategoriaDespesaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(loja_id=loja_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DespesaListView(APIView):
    """GET/POST /clinica-beleza/despesas/"""
    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        qs = Despesa.objects.select_related('categoria').order_by('-data_vencimento', '-created_at')
        if s := request.query_params.get('status'):
            qs = qs.filter(status=s)
        if c := request.query_params.get('categoria'):
            qs = qs.filter(categoria_id=c)
        if d := request.query_params.get('date'):
            qs = qs.filter(data_vencimento=d)
        if d := request.query_params.get('data_pagamento'):
            qs = qs.filter(data_pagamento=d)
        return paginate_queryset(qs, request, DespesaSerializer)

    def post(self, request):
        loja_id = resolve_loja_id_from_request(request)
        serializer = DespesaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(loja_id=loja_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DespesaDetailView(GetObjectMixin, APIView):
    """GET/PUT/DELETE /clinica-beleza/despesas/<id>/"""
    permission_classes = CLINICA_FINANCEIRO
    model_class = Despesa
    not_found_message = 'Despesa não encontrada'
    select_related_fields = ('categoria',)

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(DespesaSerializer(obj).data)

    def put(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        serializer = DespesaSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
