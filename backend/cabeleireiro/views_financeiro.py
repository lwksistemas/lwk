"""Views financeiras do salão — resumo, payments, recibo, comissões."""
from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.http import HttpResponse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .comissao_relatorio import calcular_comissoes_salao, gerar_pdf_comissoes_salao
from .comissao_utils import calcular_comissao_agendamento
from .models import Agendamento, Payment
from .serializers import PaymentSerializer


class LojaInfoView(APIView):
    """GET /cabeleireiro/loja-info/ — dados da loja para recibo impresso."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Mesmo payload da clínica (nome, CPF/CNPJ, endereço, tel, e-mail).
        from clinica_beleza.utils import LojaContextHelper

        info = LojaContextHelper.get_loja_owner_info()
        if info is None:
            return Response(
                {"error": "Contexto de loja não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(info)


class PaymentListView(APIView):
    """GET /cabeleireiro/payments/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Payment.objects.select_related(
                "agendamento",
                "agendamento__cliente",
                "agendamento__profissional",
                "agendamento__servico",
            )
            .order_by("-created_at")
        )
        if s := request.query_params.get("status"):
            qs = qs.filter(status=s)
        if d := request.query_params.get("date"):
            qs = qs.filter(payment_date__date=d)
        if p := request.query_params.get("profissional") or request.query_params.get("professional"):
            qs = qs.filter(agendamento__profissional_id=p)
        return Response(PaymentSerializer(qs[:200], many=True).data)


class PaymentEnviarReciboView(APIView):
    """POST /cabeleireiro/payments/<id>/enviar-recibo/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from .recibo_service import enviar_recibo_pagamento

        try:
            payment = Payment.objects.select_related(
                "agendamento",
                "agendamento__cliente",
                "agendamento__profissional",
                "agendamento__servico",
            ).get(pk=pk)
        except Payment.DoesNotExist:
            return Response({"error": "Pagamento não encontrado"}, status=status.HTTP_404_NOT_FOUND)

        canal = (request.data.get("canal") or "").strip()
        if canal not in ("email", "whatsapp"):
            return Response(
                {"error": 'Canal deve ser "email" ou "whatsapp".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ok, msg = enviar_recibo_pagamento(payment, canal=canal)
        if ok:
            return Response({"success": True, "message": msg})
        return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)


class ReciboPdfPublicView(APIView):
    """GET /cabeleireiro/payments/<id>/recibo-pdf/<token>/

    Aceita cache (rápido) ou regenera via token HMAC se o worker não tiver o PDF
    (staging com locmem / multi-réplica).
    """

    permission_classes = []
    authentication_classes = []

    def get(self, request, pk, token):
        from django.core.cache import cache as django_cache

        from .recibo_service import (
            gerar_pdf_recibo_payment,
            parse_recibo_pdf_token,
        )

        cached = django_cache.get(f"recibo_pdf_salao_{token}")
        if isinstance(cached, dict) and cached.get("payment_id") == pk and cached.get("pdf"):
            response = HttpResponse(cached["pdf"], content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="recibo_{pk}.pdf"'
            return response

        loja_id = parse_recibo_pdf_token(token, expected_payment_id=pk)
        if not loja_id:
            return Response(
                {"error": "Recibo expirado ou inválido."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            from superadmin.models import Loja
            from tenants.middleware import (
                _configure_tenant_db_for_loja,
                set_current_loja_id,
                set_current_tenant_db,
            )

            loja = Loja.objects.filter(id=loja_id).first()
            if not loja:
                return Response(
                    {"error": "Recibo expirado ou inválido."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if not _configure_tenant_db_for_loja(loja, request=None):
                return Response(
                    {"error": "Recibo expirado ou inválido."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            try:
                payment = Payment.objects.select_related(
                    "agendamento",
                    "agendamento__cliente",
                    "agendamento__profissional",
                    "agendamento__servico",
                ).get(pk=pk, loja_id=loja_id)
                pdf_bytes = gerar_pdf_recibo_payment(payment)
            finally:
                set_current_loja_id(None)
                set_current_tenant_db("default")
        except Payment.DoesNotExist:
            return Response(
                {"error": "Recibo expirado ou inválido."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception:
            return Response(
                {"error": "Recibo expirado ou inválido."},
                status=status.HTTP_404_NOT_FOUND,
            )

        django_cache.set(
            f"recibo_pdf_salao_{token}",
            {"payment_id": pk, "pdf": pdf_bytes},
            600,
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="recibo_{pk}.pdf"'
        return response


class FinanceiroResumoView(APIView):
    """GET /cabeleireiro/financeiro/resumo/?mes=&ano="""

    permission_classes = [IsAuthenticated]

    def get(self, request):
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

        paid = Payment.objects.filter(status=Payment.STATUS_PAID)

        def _sum_amount(qs):
            return float(qs.aggregate(total=Sum("amount"))["total"] or 0)

        faturamento = _sum_amount(
            paid.filter(payment_date__date__gte=first_day, payment_date__date__lte=period_end),
        )
        comissao_mes = float(
            paid.filter(payment_date__date__gte=first_day, payment_date__date__lte=period_end).aggregate(
                total=Sum("comissao_valor"),
            )["total"]
            or 0,
        )
        # A receber: agendamentos ativos sem payment PAID, valor do serviço
        pagos_ids = Payment.objects.filter(status=Payment.STATUS_PAID).values_list("agendamento_id", flat=True)
        a_receber = float(
            Agendamento.objects.filter(is_active=True)
            .exclude(status__in=(Agendamento.STATUS_CANCELLED, Agendamento.STATUS_NO_SHOW))
            .exclude(id__in=pagos_ids)
            .aggregate(total=Sum("valor"))["total"]
            or 0,
        )

        return Response(
            {
                "caixa_diario": _sum_amount(paid.filter(payment_date__date=today)),
                "total_mes": faturamento,
                "contas_a_receber": a_receber,
                "comissao_mes": comissao_mes,
                "faturamento": faturamento,
                "despesas": comissao_mes,
                "lucro": faturamento - comissao_mes,
                "filter": {"mes": mes, "ano": ano},
            },
        )


class RelatorioComissoesView(APIView):
    """GET /cabeleireiro/relatorios/comissoes/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        data_inicio, data_fim, prof_id, err = _parse_periodo_comissoes(request)
        if err:
            return err
        return Response(calcular_comissoes_salao(data_inicio, data_fim, profissional_id=prof_id))


class RelatorioComissoesPdfView(APIView):
    """GET /cabeleireiro/relatorios/comissoes/pdf/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        data_inicio, data_fim, prof_id, err = _parse_periodo_comissoes(request)
        if err:
            return err
        resultado = calcular_comissoes_salao(data_inicio, data_fim, profissional_id=prof_id)
        pdf = gerar_pdf_comissoes_salao(resultado, data_inicio, data_fim)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="comissoes_salao.pdf"'
        return response


def _parse_periodo_comissoes(request):
    today = now().date()
    try:
        di = request.query_params.get("data_inicio") or today.replace(day=1).isoformat()
        df = request.query_params.get("data_fim") or today.isoformat()
        data_inicio = date.fromisoformat(di[:10])
        data_fim = date.fromisoformat(df[:10])
    except ValueError:
        return None, None, None, Response(
            {"error": "Datas inválidas. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if data_fim < data_inicio:
        return None, None, None, Response(
            {"error": "data_fim deve ser >= data_inicio."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    prof_raw = request.query_params.get("profissional_id") or request.query_params.get("professional_id")
    prof_id = None
    if prof_raw:
        try:
            prof_id = int(prof_raw)
        except (TypeError, ValueError):
            return None, None, None, Response(
                {"error": "profissional_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    return data_inicio, data_fim, prof_id, None


def receber_agendamento(agendamento: Agendamento, *, payment_method: str, amount: Decimal, desconto: Decimal = Decimal("0")) -> Payment:
    """Cria/atualiza Payment PAID e marca agendamento DONE."""
    if agendamento.status in (Agendamento.STATUS_CANCELLED, Agendamento.STATUS_NO_SHOW):
        raise ValueError("Agendamento cancelado ou no-show não pode receber pagamento.")

    existing = (
        Payment.objects.filter(agendamento=agendamento, status=Payment.STATUS_PAID)
        .order_by("-id")
        .first()
    )
    if existing:
        raise ValueError("Este agendamento já possui pagamento registrado.")

    method = (payment_method or Payment.METHOD_CASH).strip().upper()
    valid_methods = {c[0] for c in Payment.PAYMENT_METHOD_CHOICES}
    if method not in valid_methods:
        raise ValueError("Forma de pagamento inválida.")

    if amount <= 0:
        raise ValueError("Valor deve ser maior que zero.")

    desconto = max(Decimal(str(desconto or 0)), Decimal("0"))
    valor_total = Decimal(str(agendamento.valor or amount))
    pct, comissao = calcular_comissao_agendamento(agendamento, valor_base=amount)

    payment = Payment.objects.create(
        agendamento=agendamento,
        amount=amount,
        valor_total=valor_total,
        payment_method=method,
        status=Payment.STATUS_PAID,
        payment_date=now(),
        desconto=desconto,
        comissao_percentual=pct,
        comissao_valor=comissao,
        notes=f"Desconto: R$ {desconto:.2f}" if desconto > 0 else "",
    )
    if agendamento.status != Agendamento.STATUS_DONE:
        agendamento.status = Agendamento.STATUS_DONE
        agendamento.save(update_fields=["status", "updated_at"])
    return payment
