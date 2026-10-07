"""Protocolo montado na ficha da cliente: vários procedimentos, desconto e sessões na agenda."""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal

from django.db import transaction
from django.utils import timezone

from .agenda_service import AgendaValidationError
from .protocolo_comercial import (
    FORMAS_COBRANCA,
    LIMITE_BUSCA_HORARIO,
    UNIDADES_INTERVALO,
    datas_das_sessoes,
    dividir_valor_protocolo,
    encaixar_horarios,
    intervalos_ocupados_profissional,
)


def aplicar_desconto_protocolo(bruto, tipo: str, valor) -> tuple[Decimal, Decimal]:
    """Devolve o desconto e o líquido. Porcentagem de 0 a 100. Valor fixo não passa da soma."""
    total = Decimal(str(bruto or 0)).quantize(Decimal("0.01"))
    informado = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    tipo = (tipo or "").strip().lower()
    if tipo == "percentual":
        if informado < 0 or informado > 100:
            raise AgendaValidationError("A porcentagem do desconto fica entre 0 e 100.")
        desconto = (total * informado / Decimal(100)).quantize(Decimal("0.01"))
    elif tipo == "fixo":
        if informado < 0:
            raise AgendaValidationError("O desconto não pode ser negativo.")
        desconto = min(informado, total)
    else:
        raise AgendaValidationError("Escolha desconto em reais ou em porcentagem.")
    return desconto, (total - desconto).quantize(Decimal("0.01"))


def repartir_valor(total, pesos) -> list[Decimal]:
    """Divide o valor da sessão na proporção dos procedimentos. O resto fica no último."""
    liquido = Decimal(str(total or 0)).quantize(Decimal("0.01"))
    pesos = [Decimal(str(item or 0)) for item in pesos]
    if not pesos:
        return []
    soma = sum(pesos, Decimal(0))
    if soma <= 0:
        base = (liquido / Decimal(len(pesos))).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        partes = [base] * len(pesos)
        partes[-1] = (liquido - base * (len(pesos) - 1)).quantize(Decimal("0.01"))
        return partes
    partes = []
    acumulado = Decimal(0)
    for indice, peso in enumerate(pesos):
        if indice == len(pesos) - 1:
            partes.append((liquido - acumulado).quantize(Decimal("0.01")))
        else:
            parte = (liquido * peso / soma).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            partes.append(parte)
            acumulado += parte
    return partes


def criar_protocolo_personalizado(
    *,
    patient,
    professional,
    local_atendimento,
    procedimentos,
    produtos,
    data_inicio,
    forma_cobranca: str,
    desconto_tipo: str,
    desconto_valor,
    sessoes: int,
    intervalo_quantidade: int,
    intervalo_unidade: str,
    tempo_minutos: int,
    nome: str = "",
    observacao: str = "",
    request=None,
) -> dict:
    """Grava o pacote da cliente e cria as sessões. Horário ocupado vai para o próximo livre."""
    from .agenda_service import (
        _bloquear_se_paciente_inadimplente,
        registrar_criacao_agendamento,
        validar_regras_agendamento,
    )
    from .convenio_service import resolver_preco_procedimento
    from .models import (
        Appointment,
        AppointmentProcedure,
        ProtocoloContrato,
        ProtocoloContratoProcedimento,
        ProtocoloContratoProduto,
    )

    if not professional:
        from .consulta_service.messages import MSG_PROFISSIONAL_OBRIGATORIO

        raise AgendaValidationError(MSG_PROFISSIONAL_OBRIGATORIO)
    if not patient:
        raise AgendaValidationError("Selecione a cliente.")
    if not local_atendimento:
        raise AgendaValidationError("Selecione o local de atendimento.")
    if forma_cobranca not in FORMAS_COBRANCA:
        raise AgendaValidationError("Escolha pagar na primeira sessão ou dividir pelas sessões.")
    if intervalo_unidade not in UNIDADES_INTERVALO:
        raise AgendaValidationError("Escolha o intervalo em dias, semanas ou meses.")
    if int(sessoes) < 1:
        raise AgendaValidationError("O protocolo precisa de ao menos uma sessão.")
    if int(intervalo_quantidade) < 1:
        raise AgendaValidationError("Informe o intervalo entre as sessões.")
    if int(tempo_minutos) < 1:
        raise AgendaValidationError("Informe a duração de cada atendimento, em minutos.")

    procedimentos = list(procedimentos or [])
    if not procedimentos:
        raise AgendaValidationError("Inclua ao menos um procedimento.")
    vistos = set()
    for procedure in procedimentos:
        if procedure.id in vistos:
            raise AgendaValidationError("Cada procedimento entra uma vez no protocolo.")
        if not getattr(procedure, "is_active", True):
            raise AgendaValidationError(f"O procedimento {procedure.nome} está inativo.")
        vistos.add(procedure.id)

    produtos = list(produtos or [])
    produtos_vistos = set()
    for item in produtos:
        produto = item["produto"]
        quantidade = Decimal(str(item["quantidade"]))
        if quantidade <= 0:
            raise AgendaValidationError("A quantidade do produto por sessão precisa ser maior que zero.")
        if produto.id in produtos_vistos:
            raise AgendaValidationError("Cada produto entra uma vez por sessão.")
        if not getattr(produto, "is_active", True):
            raise AgendaValidationError(f"O produto {produto.nome} está inativo.")
        produtos_vistos.add(produto.id)

    convenio = None
    convenio_paciente = getattr(patient, "convenio", None)
    if convenio_paciente is not None and getattr(convenio_paciente, "is_active", False):
        convenio = convenio_paciente

    linhas = []
    for procedure in procedimentos:
        preco = Decimal(str(resolver_preco_procedimento(convenio, procedure) or 0)).quantize(Decimal("0.01"))
        linhas.append((procedure, preco))
    bruto = sum((preco for _, preco in linhas), Decimal("0.00")).quantize(Decimal("0.01"))
    desconto, liquido = aplicar_desconto_protocolo(bruto, desconto_tipo, desconto_valor)
    _bloquear_se_paciente_inadimplente(patient, request=request)

    from .protocolo_comercial import _ciente

    inicio = _ciente(data_inicio)
    datas = [
        _ciente(item)
        for item in datas_das_sessoes(inicio, int(sessoes), int(intervalo_quantidade), intervalo_unidade)
    ]
    partes = dividir_valor_protocolo(liquido, int(sessoes), forma_cobranca)
    encaixes = encaixar_horarios(
        datas,
        int(tempo_minutos),
        intervalos_ocupados_profissional(professional, datas[0], datas[-1] + LIMITE_BUSCA_HORARIO),
    )
    slots = []
    for indice, encaixe in enumerate(encaixes):
        slots.append({
            "sessao": indice + 1,
            "inicio": encaixe["inicio"],
            "fim": encaixe["fim"],
            "valor": partes[indice],
            "ajustado": encaixe["ajustado"],
        })
    for slot in slots:
        validar_regras_agendamento(
            "AGENDAMENTO_CRIADO",
            professional,
            slot["inicio"],
            slot["fim"],
            appointment_id=None,
        )

    titulo = (nome or "").strip() or "Protocolo personalizado"
    observacao = (observacao or "").strip()
    primeiro = linhas[0][0]
    loja_id = patient.loja_id

    with transaction.atomic():
        contrato = ProtocoloContrato.objects.create(
            protocol=None,
            patient=patient,
            professional=professional,
            local_atendimento=local_atendimento,
            forma_cobranca=forma_cobranca,
            nome=titulo,
            valor_bruto=bruto,
            desconto_tipo=(desconto_tipo or "").strip().lower(),
            desconto_valor=Decimal(str(desconto_valor or 0)).quantize(Decimal("0.01")),
            valor_total=liquido,
            tempo_minutos=int(tempo_minutos),
            intervalo_quantidade=int(intervalo_quantidade),
            intervalo_unidade=intervalo_unidade,
            data_inicio=slots[0]["inicio"],
            sessoes=int(sessoes),
            loja_id=loja_id,
        )
        for procedure, preco in linhas:
            ProtocoloContratoProcedimento.objects.create(
                contrato=contrato,
                procedure=procedure,
                valor=preco,
                loja_id=loja_id,
            )
        for item in produtos:
            ProtocoloContratoProduto.objects.create(
                contrato=contrato,
                produto=item["produto"],
                quantidade=Decimal(str(item["quantidade"])).quantize(Decimal("0.01")),
                loja_id=loja_id,
            )
        criados = []
        pesos = [preco for _, preco in linhas]
        for slot in slots:
            notes = f"{titulo} — sessão {slot['sessao']} de {sessoes}"
            if slot["ajustado"]:
                notes = f"{notes}\nHorário ajustado para o próximo horário livre."
            if observacao:
                notes = f"{notes}\n{observacao}"
            appointment = Appointment.objects.create(
                date=slot["inicio"],
                status="SCHEDULED",
                patient=patient,
                professional=professional,
                procedure=primeiro,
                local_atendimento=local_atendimento,
                convenio=convenio,
                duracao_minutos=int(tempo_minutos),
                protocolo_contrato=contrato,
                sessao_numero=slot["sessao"],
                notes=notes,
                loja_id=loja_id,
            )
            registrar_criacao_agendamento(
                appointment,
                getattr(request, "user", None) if request is not None else None,
                request=request,
            )
            valores = repartir_valor(slot["valor"], pesos)
            for ordem, ((procedure, _preco), valor_linha) in enumerate(zip(linhas, valores)):
                AppointmentProcedure.objects.create(
                    appointment=appointment,
                    procedure=procedure,
                    duracao_minutos=int(tempo_minutos),
                    valor=valor_linha,
                    ordem=ordem,
                    loja_id=loja_id,
                )
            criados.append(
                {
                    "id": appointment.id,
                    "sessao": slot["sessao"],
                    "date": timezone.localtime(slot["inicio"]).isoformat(),
                    "valor": str(slot["valor"]),
                    "ajustado": slot["ajustado"],
                }
            )

    return {
        "contrato_id": contrato.id,
        "nome": titulo,
        "valor_bruto": str(bruto),
        "desconto": str(desconto),
        "valor_total": str(liquido),
        "agendamentos": criados,
    }
