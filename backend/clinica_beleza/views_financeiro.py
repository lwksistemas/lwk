"""
Views de Pagamentos e Financeiro — Clínica da Beleza
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_FINANCEIRO
from rest_framework import status
from django.utils.timezone import now
from django.db.models import Sum

from .models import Payment
from .serializers import PaymentSerializer
from .pagination import paginate_queryset


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


class PaymentDetailView(APIView):
    """GET /clinica-beleza/payments/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_FINANCEIRO

    def _get(self, pk):
        return Payment.objects.select_related(
            'appointment', 'appointment__patient',
            'appointment__professional', 'appointment__procedure',
        ).get(pk=pk)

    def get(self, request, pk):
        try:
            return Response(PaymentSerializer(self._get(pk)).data)
        except Payment.DoesNotExist:
            return Response({'error': 'Pagamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
            serializer = PaymentSerializer(payment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Payment.DoesNotExist:
            return Response({'error': 'Pagamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            Payment.objects.get(pk=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Payment.DoesNotExist:
            return Response({'error': 'Pagamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


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
        despesas = comissao_mes

        return Response({
            'caixa_diario': _sum(Payment.objects.filter(status='PAID', payment_date__date=today)),
            'total_mes': faturamento,
            'contas_a_receber': contas_a_receber,
            'comissao_mes': comissao_mes,
            'faturamento': faturamento,
            'despesas': despesas,
            'lucro': faturamento - despesas,
            'filter': {'mes': mes, 'ano': ano},
        })
