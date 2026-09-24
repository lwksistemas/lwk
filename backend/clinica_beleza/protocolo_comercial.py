"""Divisão do valor, datas das sessões e agendamento do protocolo."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import ROUND_DOWN, Decimal

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from .bloqueio_utils import intervalos_sobrepoem

UNIDADES_INTERVALO = ("dias", "semanas", "meses")
FORMAS_COBRANCA = ("POR_CONSULTA", "TOTAL")
_STATUS_LIVRE = ("CANCELLED", "NO_SHOW")


class ProtocoloAgendaConflito(Exception):
    """Nenhuma sessão é gravada quando algum horário está ocupado ou bloqueado."""

    def __init__(self, conflitos: list[dict]):
        self.conflitos = conflitos
        super().__init__("Horário ocupado ou bloqueado. Ajuste a data da primeira sessão.")


def dividir_valor_protocolo(valor, sessoes: int, forma: str) -> list[Decimal]:
    """Por consulta: partes iguais e o resto de centavos na última sessão.
    Valor total: o pacote inteiro na primeira sessão e zero nas seguintes.
    """
    total = Decimal(str(valor)).quantize(Decimal("0.01"))
    if sessoes < 1:
        raise ValueError("O protocolo precisa de ao menos uma sessão.")
    if forma == "TOTAL":
        return [total] + [Decimal("0.00")] * (sessoes - 1)
    if forma != "POR_CONSULTA":
        raise ValueError("Forma de cobrança inválida.")
    base = (total / Decimal(sessoes)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    partes = [base] * sessoes
    partes[-1] = (total - base * (sessoes - 1)).quantize(Decimal("0.01"))
    return partes


def datas_das_sessoes(inicio: datetime, sessoes: int, quantidade: int, unidade: str) -> list[datetime]:
    """A primeira sessão é a data informada. As seguintes avançam o intervalo."""
    if sessoes < 1:
        raise ValueError("O protocolo precisa de ao menos uma sessão.")
    if quantidade < 1:
        raise ValueError("Informe o intervalo entre as sessões.")
    if unidade == "dias":
        passo = relativedelta(days=quantidade)
    elif unidade == "semanas":
        passo = relativedelta(weeks=quantidade)
    elif unidade == "meses":
        passo = relativedelta(months=quantidade)
    else:
        raise ValueError("Unidade do intervalo inválida.")
    return [inicio + (passo * indice) for indice in range(sessoes)]


def _ciente(dt: datetime) -> datetime:
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _rotulo_quando(dt: datetime) -> str:
    return timezone.localtime(dt).strftime("%d/%m/%Y %H:%M")


def copiar_produtos_protocolo_na_consulta(consulta) -> None:
    """Copia os produtos do protocolo para a consulta, sem baixar o estoque."""
    appointment = getattr(consulta, "appointment", None)
    contrato_id = getattr(appointment, "protocolo_contrato_id", None) if appointment else None
    if not contrato_id:
        return
    contrato = appointment.protocolo_contrato
    linhas = contrato.protocol.produtos.select_related("produto").all()
    ja = set(consulta.produtos_estoque.values_list("produto_id", flat=True))
    from .models import ConsultaProdutoUtilizado

    for linha in linhas:
        if linha.produto_id in ja:
            continue
        ConsultaProdutoUtilizado.objects.create(
            consulta=consulta,
            produto_id=linha.produto_id,
            quantidade=linha.quantidade,
            estoque_baixado=False,
            loja_id=consulta.loja_id,
        )


def agendar_protocolo(
    *,
    protocol,
    patient,
    professional,
    local_atendimento,
    data_inicio: datetime,
    forma_cobranca: str,
    request=None,
) -> dict:
    """Cria o contrato e as N sessões. Se houver conflito, não grava nada."""
    from .agenda_service import (
        AgendaValidationError,
        _bloquear_se_paciente_inadimplente,
        validar_regras_agendamento,
    )
    from .models import Appointment, AppointmentProcedure, ProtocoloContrato

    if not protocol.is_active:
        raise AgendaValidationError("Protocolo inativo.")
    if not professional:
        raise AgendaValidationError("Selecione o profissional.")
    if not patient:
        raise AgendaValidationError("Selecione o paciente.")
    if not local_atendimento:
        raise AgendaValidationError("Selecione o local de atendimento.")
    if forma_cobranca not in FORMAS_COBRANCA:
        raise AgendaValidationError("Escolha pagar por consulta ou o valor total.")

    sessoes = int(protocol.sessoes or 0)
    if sessoes < 1:
        raise AgendaValidationError("O protocolo precisa de ao menos uma sessão.")
    duracao = int(protocol.tempo_estimado or 0)
    if duracao < 1:
        raise AgendaValidationError("Informe a duração de cada sessão, em minutos.")

    _bloquear_se_paciente_inadimplente(patient, request=request)
    inicio = _ciente(data_inicio)
    datas = [
        _ciente(item)
        for item in datas_das_sessoes(
            inicio,
            sessoes,
            int(protocol.intervalo_quantidade or 1),
            protocol.intervalo_unidade,
        )
    ]
    partes = dividir_valor_protocolo(protocol.valor, sessoes, forma_cobranca)
    slots = []
    for indice, quando in enumerate(datas):
        fim = quando + timedelta(minutes=duracao)
        slots.append({"sessao": indice + 1, "inicio": quando, "fim": fim, "valor": partes[indice]})

    conflitos = _conflitos_das_sessoes(slots, professional)
    if conflitos:
        raise ProtocoloAgendaConflito(conflitos)
    for slot in slots:
        validar_regras_agendamento(
            "AGENDAMENTO_CRIADO",
            professional,
            slot["inicio"],
            slot["fim"],
            appointment_id=None,
        )

    with transaction.atomic():
        contrato = ProtocoloContrato.objects.create(
            protocol=protocol,
            patient=patient,
            professional=professional,
            local_atendimento=local_atendimento,
            forma_cobranca=forma_cobranca,
            valor_total=Decimal(str(protocol.valor or 0)).quantize(Decimal("0.01")),
            data_inicio=slots[0]["inicio"],
            sessoes=sessoes,
            loja_id=protocol.loja_id,
        )
        criados = []
        for slot in slots:
            appointment = Appointment.objects.create(
                date=slot["inicio"],
                status="SCHEDULED",
                patient=patient,
                professional=professional,
                procedure=protocol.procedure,
                local_atendimento=local_atendimento,
                duracao_minutos=duracao,
                protocolo_contrato=contrato,
                sessao_numero=slot["sessao"],
                notes=f"Protocolo {protocol.nome} — sessão {slot['sessao']} de {sessoes}",
                loja_id=protocol.loja_id,
            )
            AppointmentProcedure.objects.create(
                appointment=appointment,
                procedure=protocol.procedure,
                duracao_minutos=duracao,
                valor=slot["valor"],
                ordem=0,
                loja_id=protocol.loja_id,
            )
            criados.append(
                {
                    "id": appointment.id,
                    "sessao": slot["sessao"],
                    "date": timezone.localtime(slot["inicio"]).isoformat(),
                    "valor": str(slot["valor"]),
                }
            )
    return {"contrato_id": contrato.id, "agendamentos": criados}


def _conflitos_das_sessoes(slots: list[dict], professional) -> list[dict]:
    from .agenda_service import bloqueio_impede_agendamento
    from .models import Appointment

    conflitos = []
    for indice, slot in enumerate(slots):
        for outro in slots[indice + 1 :]:
            if intervalos_sobrepoem(slot["inicio"], slot["fim"], outro["inicio"], outro["fim"]):
                conflitos.append(
                    {
                        "sessao": slot["sessao"],
                        "inicio": timezone.localtime(slot["inicio"]).isoformat(),
                        "motivo": (
                            f"Sessão {slot['sessao']} ({_rotulo_quando(slot['inicio'])}) "
                            "se sobrepõe a outra sessão. Aumente o intervalo ou reduza a duração."
                        ),
                    }
                )
                break
        if bloqueio_impede_agendamento(slot["inicio"], slot["fim"], professional.id):
            conflitos.append(
                {
                    "sessao": slot["sessao"],
                    "inicio": timezone.localtime(slot["inicio"]).isoformat(),
                    "motivo": f"Sessão {slot['sessao']} em {_rotulo_quando(slot['inicio'])}: horário bloqueado.",
                }
            )

    if not slots:
        return conflitos
    existentes = (
        Appointment.objects.filter(professional_id=professional.id, date__lt=slots[-1]["fim"])
        .exclude(status__in=_STATUS_LIVRE)
        .filter(date__gte=slots[0]["inicio"] - timedelta(days=2))
    )
    for appointment in existentes:
        fim_existente = appointment.date + timedelta(minutes=appointment.get_duracao_efetiva())
        for slot in slots:
            if intervalos_sobrepoem(slot["inicio"], slot["fim"], appointment.date, fim_existente):
                conflitos.append(
                    {
                        "sessao": slot["sessao"],
                        "inicio": timezone.localtime(slot["inicio"]).isoformat(),
                        "motivo": (
                            f"Sessão {slot['sessao']} em {_rotulo_quando(slot['inicio'])}: "
                            "já existe agendamento neste horário."
                        ),
                    }
                )
    return conflitos
