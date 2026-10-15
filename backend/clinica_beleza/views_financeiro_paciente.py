"""Prazos criados pelo admin e procedimentos anteriores ao sistema."""
from datetime import date

from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Patient, PrazoPagamentoClinica, ProcedimentoAnterior, ProcedimentoAnteriorRecebimento
from .permissions import CLINICA_ADMIN
from .prazo_service import validar_regra_prazo
from .procedimento_anterior_service import (
    FORMAS_RECEBIMENTO,
    saldo_anterior,
    validar_lancamento_anterior,
    validar_recebimento,
)
from .views_base import GetObjectMixin


def _hoje() -> date:
    return timezone.localdate()


def _valores_recebidos(procedimento) -> list:
    cache = getattr(procedimento, "_prefetched_objects_cache", {}).get("recebimentos")
    if cache is not None:
        return [item.valor for item in cache]
    return list(procedimento.recebimentos.values_list("valor", flat=True))


def _prazo_payload(opcao: PrazoPagamentoClinica) -> dict:
    if opcao.modo == "DIAS_APOS" and opcao.dias:
        regra = f"{opcao.dias} dias após finalizar a consulta"
    elif opcao.modo == "DIA_FIXO" and opcao.dia_mes:
        regra = f"Dia {opcao.dia_mes} do mês"
    elif opcao.modo == "SEMANAL":
        regra = "Semanal, 7 dias após finalizar a consulta"
    else:
        regra = ""
    return {
        "id": opcao.id,
        "nome": opcao.nome,
        "modo": opcao.modo,
        "dias": opcao.dias,
        "dia_mes": opcao.dia_mes,
        "regra": regra,
    }


def _recebimento_payload(item: ProcedimentoAnteriorRecebimento) -> dict:
    return {
        "id": item.id,
        "valor": item.valor,
        "data": item.data.isoformat(),
        "payment_method": item.payment_method,
        "payment_method_label": FORMAS_RECEBIMENTO.get(item.payment_method, item.payment_method),
    }


def _procedimento_payload(item: ProcedimentoAnterior) -> dict:
    recebidos = _valores_recebidos(item)
    saldo = saldo_anterior(item.valor, item.valor_pago, recebidos)
    recebimentos = getattr(item, "_prefetched_objects_cache", {}).get("recebimentos")
    if recebimentos is None:
        recebimentos = item.recebimentos.all()
    return {
        "id": item.id,
        "data_procedimento": item.data_procedimento.isoformat(),
        "nome": item.nome,
        "valor": item.valor,
        "valor_pago": item.valor_pago,
        "data_pagamento": item.data_pagamento.isoformat() if item.data_pagamento else None,
        "data_vencimento": item.data_vencimento.isoformat() if item.data_vencimento else None,
        "saldo": saldo,
        "quitado": saldo <= 0,
        "recebimentos": [_recebimento_payload(r) for r in recebimentos],
    }


def _parse_data(raw, campo: str) -> date:
    if isinstance(raw, date):
        return raw
    texto = (raw or "").strip() if isinstance(raw, str) else ""
    if not texto:
        raise ValueError(f"Informe {campo}.")
    try:
        return date.fromisoformat(texto[:10])
    except ValueError as exc:
        raise ValueError(f"Data inválida em {campo}.") from exc


class PrazoPagamentoClinicaListView(APIView):
    """GET/POST /clinica-beleza/prazos-pagamento/ — prazos criados pelo administrador."""

    permission_classes = CLINICA_ADMIN

    def get(self, request):
        itens = PrazoPagamentoClinica.objects.all().order_by("nome", "id")
        return Response([_prazo_payload(item) for item in itens])

    def post(self, request):
        nome = (request.data.get("nome") or "").strip()
        if not nome:
            return Response({"nome": "Dê um nome a este prazo."}, status=status.HTTP_400_BAD_REQUEST)
        if len(nome) > 80:
            return Response(
                {"nome": "O nome do prazo pode ter no máximo 80 caracteres."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            modo, dias, dia_mes = validar_regra_prazo(
                request.data.get("modo"),
                request.data.get("dias"),
                request.data.get("dia_mes"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            opcao = PrazoPagamentoClinica.objects.create(
                nome=nome, modo=modo, dias=dias, dia_mes=dia_mes,
            )
        except IntegrityError:
            return Response(
                {"nome": "Já existe um prazo com este nome."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(_prazo_payload(opcao), status=status.HTTP_201_CREATED)


class PrazoPagamentoClinicaDetailView(GetObjectMixin, APIView):
    """DELETE /clinica-beleza/prazos-pagamento/<id>/"""

    permission_classes = CLINICA_ADMIN
    model_class = PrazoPagamentoClinica
    not_found_message = "Prazo não encontrado"

    def delete(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProcedimentoAnteriorListView(GetObjectMixin, APIView):
    """GET/POST /clinica-beleza/patients/<patient_id>/procedimentos-anteriores/"""

    permission_classes = CLINICA_ADMIN
    model_class = Patient
    not_found_message = "Paciente não encontrado"

    def get(self, request, patient_id):
        patient, err = self.object_or_404(patient_id)
        if err:
            return err
        itens = (
            ProcedimentoAnterior.objects
            .filter(patient=patient)
            .prefetch_related("recebimentos")
            .order_by("-data_procedimento", "-id")
        )
        return Response([_procedimento_payload(item) for item in itens])

    def post(self, request, patient_id):
        patient, err = self.object_or_404(patient_id)
        if err:
            return err
        try:
            data_procedimento = _parse_data(request.data.get("data_procedimento"), "a data do procedimento")
            pago_informado = request.data.get("valor_pago")
            data_pagamento = None
            if pago_informado not in (None, "", 0, "0", "0.00", "0,00"):
                data_pagamento = _parse_data(request.data.get("data_pagamento"), "a data do pagamento")
            nome, valor, valor_pago, data_pagamento, vencimento = validar_lancamento_anterior(
                data_procedimento,
                request.data.get("nome"),
                request.data.get("valor"),
                pago_informado,
                _hoje(),
                data_pagamento,
                patient,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        item = ProcedimentoAnterior.objects.create(
            patient=patient,
            data_procedimento=data_procedimento,
            nome=nome,
            valor=valor,
            valor_pago=valor_pago,
            data_pagamento=data_pagamento,
            data_vencimento=vencimento,
        )
        return Response(_procedimento_payload(item), status=status.HTTP_201_CREATED)


class ProcedimentoAnteriorDetailView(GetObjectMixin, APIView):
    """DELETE /clinica-beleza/patients/<patient_id>/procedimentos-anteriores/<pk>/"""

    permission_classes = CLINICA_ADMIN
    model_class = Patient
    not_found_message = "Paciente não encontrado"

    def delete(self, request, patient_id, pk):
        patient, err = self.object_or_404(patient_id)
        if err:
            return err
        item = ProcedimentoAnterior.objects.filter(patient=patient, pk=pk).first()
        if item is None:
            return Response({"error": "Procedimento não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProcedimentoAnteriorReceberView(GetObjectMixin, APIView):
    """POST /clinica-beleza/patients/<patient_id>/procedimentos-anteriores/<pk>/receber/"""

    permission_classes = CLINICA_ADMIN
    model_class = Patient
    not_found_message = "Paciente não encontrado"

    def post(self, request, patient_id, pk):
        patient, err = self.object_or_404(patient_id)
        if err:
            return err
        item = (
            ProcedimentoAnterior.objects
            .filter(patient=patient, pk=pk)
            .prefetch_related("recebimentos")
            .first()
        )
        if item is None:
            return Response({"error": "Procedimento não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        saldo = saldo_anterior(item.valor, item.valor_pago, _valores_recebidos(item))
        try:
            data_recebimento = _parse_data(request.data.get("data"), "a data do recebimento")
            valor, forma = validar_recebimento(
                saldo,
                request.data.get("valor"),
                data_recebimento,
                _hoje(),
                item.data_procedimento,
                request.data.get("payment_method"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        ProcedimentoAnteriorRecebimento.objects.create(
            procedimento=item,
            valor=valor,
            data=data_recebimento,
            payment_method=forma,
        )
        item = (
            ProcedimentoAnterior.objects
            .filter(pk=item.pk)
            .prefetch_related("recebimentos")
            .get()
        )
        return Response(_procedimento_payload(item), status=status.HTTP_201_CREATED)
