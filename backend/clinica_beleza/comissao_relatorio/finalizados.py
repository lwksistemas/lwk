"""Atendimentos finalizados entram na comissão mesmo sem pagamento.

O valor é o do serviço prestado. Se a cliente não paga, o prejuízo é da clínica.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Q

from .procedimentos import _procedimentos_vinculados_consulta

_STATUS_FORA = ("CANCELLED", "NO_SHOW")


def _valor_servico_atendimento(consulta, procedimentos: list[dict]) -> Decimal:
    """Taxa gravada na consulta mais os procedimentos. Não usa o valor recebido."""
    taxa = Decimal(0)
    if not getattr(consulta, "retorno_gratuito", False):
        taxa = Decimal(str(getattr(consulta, "valor_consulta", None) or 0))
    soma = sum((Decimal(str(p.get("valor") or 0)) for p in procedimentos), Decimal(0))
    return (taxa + soma).quantize(Decimal("0.01"))


def grupos_atendimentos_finalizados(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    professional_id: int | None = None,
) -> tuple[list[dict], dict]:
    """Uma linha por consulta concluída. O total é o serviço, não o caixa."""
    from ..models import Consulta, Payment

    qs = (
        Consulta.objects.filter(status="COMPLETED")
        .exclude(appointment__status__in=_STATUS_FORA)
        .select_related(
            "appointment__professional",
            "appointment__patient",
            "appointment__procedure",
            "appointment__convenio",
            "appointment__local_atendimento",
            "local_atendimento",
            "patient",
            "professional",
            "procedure",
            "convenio",
        )
        .prefetch_related("appointment__appointment_procedures__procedure")
    )
    if data_inicio:
        qs = qs.filter(appointment__date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(appointment__date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(
            Q(appointment__professional_id=professional_id) | Q(professional_id=professional_id),
        )

    consultas = list(qs.order_by("appointment__date", "id"))
    ids = [c.appointment_id for c in consultas if c.appointment_id]
    pagamentos: dict[int, list] = {}
    if ids:
        for payment in Payment.objects.filter(appointment_id__in=ids).exclude(status="CANCELLED"):
            pagamentos.setdefault(payment.appointment_id, []).append(payment)

    grupos: list[dict] = []
    consulta_map: dict = {}
    for consulta in consultas:
        appt = consulta.appointment
        if appt is None:
            continue
        profissional = appt.professional or consulta.professional
        if profissional is None:
            continue
        procedimentos = _procedimentos_vinculados_consulta(appt, consulta)
        amount = _valor_servico_atendimento(consulta, procedimentos)
        if amount <= 0 and not procedimentos:
            continue
        consulta_map[appt.id] = consulta
        grupos.append({
            "appointment": appt,
            "profissional": profissional,
            "payments": pagamentos.get(appt.id, []),
            "total_amount": amount,
        })
    return grupos, consulta_map
