"""Views de Pagamentos e Financeiro — Clínica da Beleza
"""
from django.http import HttpResponse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .financeiro_service import (
    alinhar_pendentes_com_parcela,
    aplicar_desconto_payment,
    criar_parcela_e_atualizar_payment,
    decimal_ou_none,
    erro_consulta_para_parcela,
    erro_excluir_payment,
    erro_status_para_parcela,
    garantir_categorias_despesa_padrao,
    montar_resumo_financeiro,
    queryset_payments_listagem,
)
from .models import CategoriaDespesa, Despesa, Payment
from .pagination import paginate_queryset
from .permissions import CLINICA_FINANCEIRO
from .serializers.financeiro import (
    CategoriaDespesaSerializer,
    DespesaSerializer,
    PaymentParcelaSerializer,
    PaymentSerializer,
)
from .throttles import PublicPdfThrottle
from .views_base import GetObjectMixin, resolve_loja_id_from_request


class PaymentListView(APIView):
    """GET /clinica-beleza/payments/
    POST /clinica-beleza/payments/
    """

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        alinhar_pendentes_com_parcela()
        queryset = queryset_payments_listagem(
            status=request.query_params.get("status"),
            date_filter=request.query_params.get("date"),
            professional_id=request.query_params.get("professional"),
        )
        return paginate_queryset(queryset, request, PaymentSerializer)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(GetObjectMixin, APIView):
    """GET/PUT/DELETE /clinica-beleza/payments/<id>/"""

    permission_classes = CLINICA_FINANCEIRO
    model_class = Payment
    not_found_message = "Pagamento não encontrado"
    select_related_fields = (
        "appointment", "appointment__patient",
        "appointment__professional", "appointment__procedure",
    )
    prefetch_related_fields = (
        "appointment__appointment_procedures__procedure",
        "parcelas",
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
        if motivo := erro_excluir_payment(obj):
            return Response({"error": motivo}, status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentParcelaView(GetObjectMixin, APIView):
    """GET/POST /clinica-beleza/payments/<id>/parcelas/"""

    permission_classes = CLINICA_FINANCEIRO
    model_class = Payment
    not_found_message = "Pagamento não encontrado"
    select_related_fields = ("appointment", "appointment__consulta")

    def get(self, request, pk):
        payment, err = self.object_or_404(pk)
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
        payment, err = self.object_or_404(pk)
        if err:
            return err

        if motivo := erro_status_para_parcela(payment):
            return Response({"error": motivo}, status=status.HTTP_400_BAD_REQUEST)

        valor = decimal_ou_none(request.data.get("valor"))
        if valor is None:
            return Response({"error": "Valor inválido."}, status=status.HTTP_400_BAD_REQUEST)

        desconto_param = request.data.get("desconto")
        has_desconto = bool(desconto_param and (decimal_ou_none(desconto_param) or 0) > 0)

        if valor <= 0 and not has_desconto:
            return Response({"error": "Valor deve ser maior que zero."}, status=status.HTTP_400_BAD_REQUEST)

        if motivo := erro_consulta_para_parcela(payment):
            return Response({"error": motivo}, status=status.HTTP_400_BAD_REQUEST)

        aplicar_desconto_payment(payment, desconto_param)
        parcela = criar_parcela_e_atualizar_payment(payment, valor, {
            "payment_method": (request.data.get("payment_method") or "CASH").strip(),
            "payment_date": request.data.get("payment_date") or now().date().isoformat(),
            "observacoes": request.data.get("observacoes") or "",
        })
        return Response({
            "parcela": PaymentParcelaSerializer(parcela).data if parcela else None,
            "valor_total": float(payment.valor_total_efetivo),
            "valor_pago": float(payment.valor_pago_parcelas),
            "saldo_devedor": float(payment.saldo_devedor),
            "status": payment.status,
        }, status=status.HTTP_201_CREATED)


class PaymentEnviarReciboView(GetObjectMixin, APIView):
    """POST /clinica-beleza/payments/<id>/enviar-recibo/"""

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
    """GET /clinica-beleza/payments/<id>/recibo-pdf/<token>/"""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [PublicPdfThrottle]

    def get(self, request, pk, token):
        from clinica_beleza.public_pdf import PREFIX_RECIBO, ler_pdf_publico

        cached = ler_pdf_publico(PREFIX_RECIBO, token)
        if not cached or cached.get("payment_id") != pk:
            return Response({"error": "Recibo expirado ou inválido."}, status=status.HTTP_404_NOT_FOUND)
        pdf_bytes = cached.get("pdf")
        if not pdf_bytes:
            return Response({"error": "Recibo expirado ou inválido."}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="recibo_{pk}.pdf"'
        return response


class FinanceiroResumoView(APIView):
    """GET /clinica-beleza/financeiro/resumo/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        today = now().date()
        try:
            ano = int(request.query_params.get("ano") or today.year)
            mes = int(request.query_params.get("mes") or today.month)
            if not (1 <= mes <= 12):
                raise ValueError
        except (ValueError, TypeError):
            ano, mes = today.year, today.month
        return Response(montar_resumo_financeiro(ano=ano, mes=mes, today=today))


class CategoriaDespesaListView(APIView):
    """GET/POST /clinica-beleza/despesas/categorias/"""

    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if loja_id:
            garantir_categorias_despesa_padrao(loja_id)
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
