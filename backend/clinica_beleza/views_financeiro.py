"""Views de Pagamentos e Financeiro — Clínica da Beleza
"""
from decimal import Decimal, InvalidOperation

from django.db.models import Case, DecimalField, F, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce, Greatest
from django.utils.timezone import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CategoriaDespesa, Despesa, Payment
from .models.financeiro import CATEGORIAS_DESPESA_PADRAO, PaymentParcela
from .pagination import paginate_queryset
from .permissions import CLINICA_FINANCEIRO
from .serializers.financeiro import (
    CategoriaDespesaSerializer,
    DespesaSerializer,
    PaymentParcelaSerializer,
    PaymentSerializer,
)
from .views_base import GetObjectMixin, resolve_loja_id_from_request

_DEC = DecimalField(max_digits=14, decimal_places=2)


def _payments_visiveis_financeiro(qs=None):
    """Financeiro só mostra lançamentos de consultas finalizadas.
    Rascunhos (DRAFT) do Receber ficam só na consulta até Finalizar.
    """
    if qs is None:
        qs = Payment.objects.all()
    return qs.exclude(status="DRAFT").filter(
        Q(appointment__consulta__status="COMPLETED") | Q(appointment__consulta__isnull=True),
    )


def somar_contas_a_receber(qs=None) -> float:
    """Soma saldo_devedor de PENDING/PARTIAL em 1 query (sem N+1 por parcela)."""
    base = _payments_visiveis_financeiro(qs).filter(status__in=("PENDING", "PARTIAL"))
    pago_sub = (
        PaymentParcela.objects.filter(payment_id=OuterRef("pk"), status="PAID")
        .values("payment_id")
        .annotate(s=Sum("valor"))
        .values("s")[:1]
    )
    agregado = (
        base.annotate(
            _pago_parc=Subquery(pago_sub, output_field=_DEC),
            _total=Coalesce(F("valor_total"), F("amount"), Value(0), output_field=_DEC),
        )
        .annotate(
            _pago=Case(
                When(_pago_parc__isnull=False, then=F("_pago_parc")),
                When(
                    status__in=("PARTIAL", "PAID", "DRAFT"),
                    then=Coalesce(F("amount"), Value(0), output_field=_DEC),
                ),
                default=Value(0),
                output_field=_DEC,
            ),
        )
        .annotate(_saldo=Greatest(F("_total") - F("_pago"), Value(0), output_field=_DEC))
        .aggregate(t=Sum("_saldo"))
    )
    return float(agregado["t"] or 0)


def _garantir_categorias_despesa_padrao(loja_id: int) -> None:
    if CategoriaDespesa.objects.exists():
        return
    for nome in CATEGORIAS_DESPESA_PADRAO:
        CategoriaDespesa.objects.create(loja_id=loja_id, nome=nome)


class PaymentListView(APIView):
    """GET /clinica-beleza/payments/
    POST /clinica-beleza/payments/
    """

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        queryset = _payments_visiveis_financeiro(
            Payment.objects.select_related(
                "appointment", "appointment__patient",
                "appointment__professional", "appointment__procedure",
            ).prefetch_related(
                "appointment__appointment_procedures__procedure",
            ),
        ).order_by("-created_at")
        if s := request.query_params.get("status"):
            queryset = queryset.filter(status=s)
        if d := request.query_params.get("date"):
            queryset = queryset.filter(payment_date__date=d)
        if p := request.query_params.get("professional"):
            queryset = queryset.filter(appointment__professional_id=p)
        return paginate_queryset(queryset, request, PaymentSerializer)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(GetObjectMixin, APIView):
    """GET/PUT/DELETE /clinica-beleza/payments/<id>/

    CRUD genérico de pagamento (API/admin). O frontend da clínica usa
    listagem + parcelas; não remove — útil para correções manuais/scripts.
    """

    permission_classes = CLINICA_FINANCEIRO
    model_class = Payment
    not_found_message = "Pagamento não encontrado"
    select_related_fields = (
        "appointment", "appointment__patient",
        "appointment__professional", "appointment__procedure",
    )
    prefetch_related_fields = ("appointment__appointment_procedures__procedure",)

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(PaymentSerializer(obj).data)

    def put(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        consulta = getattr(getattr(obj, "appointment", None), "consulta", None)
        if consulta is not None and consulta.status != "COMPLETED":
            return Response(
                {
                    "error": (
                        "Pagamento de consulta não finalizada só pode ser alterado "
                        "pelo Receber da consulta."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
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


class PaymentParcelaView(APIView):
    """GET  /clinica-beleza/payments/<id>/parcelas/ — lista parcelas de um pagamento
    POST /clinica-beleza/payments/<id>/parcelas/ — registra nova entrada parcial
    """

    permission_classes = CLINICA_FINANCEIRO

    def _get_payment(self, pk):
        try:
            return (
                Payment.objects
                .select_related("appointment", "appointment__consulta")
                .get(pk=pk)
            ), None
        except Payment.DoesNotExist:
            return None, Response({"error": "Pagamento não encontrado"}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        payment, err = self._get_payment(pk)
        if err:
            return err
        parcelas = payment.parcelas.all()
        return Response({
            "valor_total": float(payment.valor_total_efetivo),
            "valor_pago": float(payment.valor_pago_parcelas),
            "saldo_devedor": float(payment.saldo_devedor),
            "status": payment.status,
            "parcelas": PaymentParcelaSerializer(parcelas, many=True).data,
        })

    def post(self, request, pk):
        payment, err = self._get_payment(pk)
        if err:
            return err

        if payment.status == "CANCELLED":
            return Response({"error": "Pagamento cancelado."}, status=status.HTTP_400_BAD_REQUEST)
        if payment.status == "PAID":
            return Response({"error": "Pagamento já está quitado."}, status=status.HTTP_400_BAD_REQUEST)
        # DRAFT quitado (saldo 0) também bloqueia nova parcela via financeiro
        if payment.status == "DRAFT":
            try:
                saldo = Decimal(str(payment.saldo_devedor or 0))
            except (InvalidOperation, TypeError, ValueError):
                saldo = Decimal(0)
            if saldo <= 0:
                return Response(
                    {"error": "Pagamento já quitado na consulta. Corrija pelo Receber ou finalize."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            valor = Decimal(str(request.data.get("valor") or "0"))
        except InvalidOperation:
            return Response({"error": "Valor inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if valor <= 0:
            return Response({"error": "Valor deve ser maior que zero."}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = (request.data.get("payment_method") or "CASH").strip()
        payment_date = request.data.get("payment_date") or now().date().isoformat()
        observacoes = request.data.get("observacoes") or ""

        consulta = getattr(getattr(payment, "appointment", None), "consulta", None)
        if consulta is not None and consulta.status != "COMPLETED":
            return Response(
                {
                    "error": (
                        "Pagamento do dia da consulta é pelo Receber. "
                        "Complemento em outro dia só no Financeiro após finalizar a consulta."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if consulta is None:
            return Response(
                {
                    "error": (
                        "Não é possível registrar parcela neste pagamento. "
                        "Finalize a consulta ou use o Receber."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Consulta finalizada: baixa / complemento em qualquer data pelo Financeiro
        parcela = PaymentParcela.objects.create(
            payment=payment,
            valor=valor,
            payment_method=payment_method,
            payment_date=payment_date,
            observacoes=observacoes,
            loja_id=payment.loja_id,
        )
        total_pago = payment.valor_pago_parcelas
        total_devedor = payment.valor_total_efetivo
        if total_pago >= total_devedor:
            payment.status = "PAID"
            payment.amount = total_pago
            payment.payment_date = now()
        else:
            payment.status = "PARTIAL"
            payment.amount = total_pago
        payment.save(update_fields=["status", "amount", "payment_date", "updated_at"])

        return Response({
            "parcela": PaymentParcelaSerializer(parcela).data if parcela else None,
            "valor_total": float(payment.valor_total_efetivo),
            "valor_pago": float(payment.valor_pago_parcelas),
            "saldo_devedor": float(payment.saldo_devedor),
            "status": payment.status,
        }, status=status.HTTP_201_CREATED)


class PaymentEnviarReciboView(GetObjectMixin, APIView):
    """POST /clinica-beleza/payments/<id>/enviar-recibo/ — envia recibo por email ou WhatsApp."""

    permission_classes = CLINICA_FINANCEIRO
    model_class = Payment
    not_found_message = "Pagamento não encontrado"
    select_related_fields = (
        "appointment",
        "appointment__patient",
        "appointment__local_atendimento",
        "appointment__consulta",
        "appointment__consulta__local_atendimento",
    )

    def post(self, request, pk):
        from .recibo_service import enviar_recibo_pagamento

        payment, err = self.object_or_404(pk)
        if err:
            return err

        canal = (request.data.get("canal") or "").strip()
        if canal not in ("email", "whatsapp"):
            return Response({"error": 'Canal deve ser "email" ou "whatsapp".'}, status=status.HTTP_400_BAD_REQUEST)

        ok, msg = enviar_recibo_pagamento(payment, canal=canal)
        if ok:
            return Response({"success": True, "message": msg})
        return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)


class ReciboPdfPublicView(APIView):
    """GET /clinica-beleza/payments/<id>/recibo-pdf/<token>/ — retorna PDF público (para WhatsApp)."""

    permission_classes = []
    authentication_classes = []

    def get(self, request, pk, token):
        from django.core.cache import cache as django_cache
        from django.http import HttpResponse

        cache_key = f"recibo_pdf_{token}"
        cached = django_cache.get(cache_key)
        if not cached:
            return Response({"error": "Recibo expirado ou inválido."}, status=status.HTTP_404_NOT_FOUND)

        # Token amarrado ao payment id — cache legado (só bytes) é rejeitado
        if not isinstance(cached, dict) or cached.get("payment_id") != pk:
            return Response({"error": "Recibo expirado ou inválido."}, status=status.HTTP_404_NOT_FOUND)
        pdf_bytes = cached.get("pdf")
        if not pdf_bytes:
            return Response({"error": "Recibo expirado ou inválido."}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="recibo_{pk}.pdf"'
        return response


class FinanceiroResumoView(APIView):
    """GET /clinica-beleza/financeiro/resumo/
    Resumo: caixa diário, total mês, contas a receber, comissões.
    Query: mes, ano (opcional — padrão mês atual).
    """

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        import calendar
        from datetime import date

        today = now().date()
        try:
            ano = int(request.query_params.get("ano") or today.year)
            mes = int(request.query_params.get("mes") or today.month)
            if not (1 <= mes <= 12):
                raise ValueError
        except (ValueError, TypeError):
            ano, mes = today.year, today.month

        first_day = date(ano, mes, 1)
        last_day = date(ano, mes, calendar.monthrange(ano, mes)[1])
        period_end = today if (ano == today.year and mes == today.month) else last_day

        def _sum(qs):
            return float(qs.aggregate(total=Sum("amount"))["total"] or 0)

        faturamento = _sum(_payments_visiveis_financeiro(Payment.objects.filter(
            status="PAID",
            payment_date__date__gte=first_day,
            payment_date__date__lte=period_end,
        )))
        # Contas a receber: 1 agregação SQL (evita N+1 em parcelas)
        contas_a_receber = somar_contas_a_receber()
        comissao_mes = float(
            _payments_visiveis_financeiro(Payment.objects.filter(
                status="PAID",
                payment_date__date__gte=first_day,
                payment_date__date__lte=period_end,
            )).aggregate(total=Sum("comissao_valor"))["total"] or 0,
        )

        def _sum_despesa(qs):
            return float(qs.aggregate(total=Sum("valor"))["total"] or 0)

        despesas_operacionais = _sum_despesa(Despesa.objects.filter(
            status="PAID",
            data_pagamento__gte=first_day,
            data_pagamento__lte=period_end,
        ))
        despesas_pendentes = _sum_despesa(Despesa.objects.filter(status="PENDING"))
        despesas_total = comissao_mes + despesas_operacionais

        return Response({
            "caixa_diario": _sum(_payments_visiveis_financeiro(
                Payment.objects.filter(status="PAID", payment_date__date=today),
            )),
            "total_mes": faturamento,
            "contas_a_receber": contas_a_receber,
            "comissao_mes": comissao_mes,
            "despesas_operacionais": despesas_operacionais,
            "despesas_pendentes": despesas_pendentes,
            "faturamento": faturamento,
            "despesas": despesas_total,
            "lucro": faturamento - despesas_total,
            "filter": {"mes": mes, "ano": ano},
        })


class CategoriaDespesaListView(APIView):
    """GET/POST /clinica-beleza/despesas/categorias/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if loja_id:
            _garantir_categorias_despesa_padrao(loja_id)
        qs = CategoriaDespesa.objects.filter(is_active=True).order_by("nome")
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
        qs = Despesa.objects.select_related("categoria").order_by("-data_vencimento", "-created_at")
        if s := request.query_params.get("status"):
            qs = qs.filter(status=s)
        if c := request.query_params.get("categoria"):
            qs = qs.filter(categoria_id=c)
        if d := request.query_params.get("date"):
            qs = qs.filter(data_vencimento=d)
        if d := request.query_params.get("data_pagamento"):
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
    not_found_message = "Despesa não encontrada"
    select_related_fields = ("categoria",)

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
