"""Protocolo montado na ficha da cliente: vários procedimentos, desconto e sessões na agenda."""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, InvalidOperation

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


CAMPOS_ETAPAS = (
    "materiais_necessarios",
    "preparacao",
    "execucao",
    "pos_procedimento",
    "contraindicacoes",
    "cuidados_especiais",
)


def etapas_do_pedido(data) -> dict:
    origem = data or {}
    return {chave: str(origem.get(chave) or "").strip() for chave in CAMPOS_ETAPAS}


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


def _normalizar_procedimento(item) -> dict:
    if isinstance(item, dict):
        procedure = item.get("procedure", item)
        tipo = (item.get("desconto_tipo") or "").strip().lower()
        valor = item.get("desconto_valor") or 0
    else:
        procedure = item
        tipo = ""
        valor = 0
    if tipo not in ("", "percentual", "fixo"):
        raise AgendaValidationError("Escolha desconto em reais ou em porcentagem.")
    return {"procedure": procedure, "desconto_tipo": tipo, "desconto_valor": valor}


def _validar_itens(procedimentos, produtos):
    procedimentos = [_normalizar_procedimento(item) for item in (procedimentos or [])]
    if not procedimentos:
        raise AgendaValidationError("Inclua ao menos um procedimento.")
    vistos = set()
    for item in procedimentos:
        procedure = item["procedure"]
        if procedure.id in vistos:
            raise AgendaValidationError("Cada procedimento entra uma vez no protocolo.")
        if not getattr(procedure, "is_active", True):
            raise AgendaValidationError(f"O procedimento {procedure.nome} está inativo.")
        vistos.add(procedure.id)

    produtos = list(produtos or [])
    produtos_vistos = set()
    for item in produtos:
        produto = item["produto"]
        try:
            quantidade = Decimal(str(item["quantidade"]).replace(",", "."))
        except (InvalidOperation, TypeError, ValueError):
            raise AgendaValidationError("A quantidade do produto por sessão precisa ser maior que zero.")
        if quantidade <= 0:
            raise AgendaValidationError("A quantidade do produto por sessão precisa ser maior que zero.")
        if produto.id in produtos_vistos:
            raise AgendaValidationError("Cada produto entra uma vez por sessão.")
        if not getattr(produto, "is_active", True):
            raise AgendaValidationError(f"O produto {produto.nome} está inativo.")
        item["quantidade"] = quantidade
        produtos_vistos.add(produto.id)
    return procedimentos, produtos


def _linhas_de_preco(patient, procedimentos):
    from .convenio_service import resolver_preco_procedimento

    convenio = None
    convenio_paciente = getattr(patient, "convenio", None)
    if convenio_paciente is not None and getattr(convenio_paciente, "is_active", False):
        convenio = convenio_paciente
    linhas = []
    for item in procedimentos:
        procedure = item["procedure"]
        preco = Decimal(str(resolver_preco_procedimento(convenio, procedure) or 0)).quantize(Decimal("0.01"))
        linhas.append({
            "procedure": procedure,
            "preco": preco,
            "desconto_tipo": item.get("desconto_tipo") or "",
            "desconto_valor": item.get("desconto_valor") or 0,
        })
    return convenio, linhas


def _conta_do_pacote(linhas, escopo: str, desconto_tipo: str, desconto_valor) -> dict:
    from .protocolo_comercial import preco_da_promocao

    modo = "individual" if (escopo or "").strip().lower() == "individual" else "total"
    return preco_da_promocao(linhas, modo, desconto_tipo, desconto_valor), modo


_STATUS_IGNORADO = ("CANCELLED", "NO_SHOW")
_STATUS_IMPEDE_EXCLUSAO = ("CONFIRMED", "IN_PROGRESS", "COMPLETED")


def protocolo_pode_editar(status_agendamentos) -> bool:
    """O pacote só muda de composição enquanto não há sessão viva na agenda."""
    return not any(status not in _STATUS_IGNORADO for status in status_agendamentos)


def motivo_impede_exclusao(status_agendamentos, tem_pagamento: bool) -> str:
    if any(status in _STATUS_IMPEDE_EXCLUSAO for status in status_agendamentos):
        return "Este protocolo já teve sessão com a cliente presente. Ele permanece no prontuário."
    if tem_pagamento:
        return "Este protocolo já tem pagamento. Ele permanece no prontuário."
    return ""


def criar_protocolo_personalizado(
    *,
    patient,
    procedimentos,
    produtos,
    desconto_tipo: str,
    desconto_valor,
    desconto_escopo: str = "total",
    sessoes: int,
    intervalo_quantidade: int,
    intervalo_unidade: str,
    tempo_minutos: int,
    nome: str = "",
    etapas: dict | None = None,
    request=None,
) -> dict:
    """Grava o pacote da cliente. Profissional, agenda e pagamento ficam para depois."""
    from .agenda_service import _bloquear_se_paciente_inadimplente
    from .models import ProtocoloContrato, ProtocoloContratoProcedimento, ProtocoloContratoProduto

    if not patient:
        raise AgendaValidationError("Selecione a cliente.")
    if intervalo_unidade not in UNIDADES_INTERVALO:
        raise AgendaValidationError("Escolha o intervalo em dias, semanas ou meses.")
    if int(sessoes) < 1:
        raise AgendaValidationError("O protocolo precisa de ao menos uma sessão.")
    if int(intervalo_quantidade) < 1:
        raise AgendaValidationError("Informe o intervalo entre as sessões.")
    if int(tempo_minutos) < 1:
        raise AgendaValidationError("Informe a duração de cada atendimento, em minutos.")

    procedimentos, produtos = _validar_itens(procedimentos, produtos)
    _convenio, linhas = _linhas_de_preco(patient, procedimentos)
    conta, modo = _conta_do_pacote(linhas, desconto_escopo, desconto_tipo, desconto_valor)
    _bloquear_se_paciente_inadimplente(patient, request=request)

    titulo = (nome or "").strip() or "Protocolo personalizado"
    loja_id = patient.loja_id
    tipo_gravado = "" if modo == "individual" else (desconto_tipo or "").strip().lower()
    valor_gravado = conta["desconto"] if modo == "individual" else Decimal(str(desconto_valor or 0)).quantize(Decimal("0.01"))

    with transaction.atomic():
        contrato = ProtocoloContrato.objects.create(
            protocol=None,
            patient=patient,
            professional=None,
            local_atendimento=None,
            forma_cobranca="",
            nome=titulo,
            valor_bruto=conta["bruto"],
            desconto_escopo=modo,
            desconto_tipo=tipo_gravado,
            desconto_valor=valor_gravado,
            valor_total=conta["liquido"],
            tempo_minutos=int(tempo_minutos),
            intervalo_quantidade=int(intervalo_quantidade),
            intervalo_unidade=intervalo_unidade,
            data_inicio=None,
            sessoes=int(sessoes),
            loja_id=loja_id,
            **etapas_do_pedido(etapas),
        )
        for linha in conta["linhas"]:
            ProtocoloContratoProcedimento.objects.create(
                contrato=contrato,
                procedure=linha["procedure"],
                valor=linha["preco"],
                desconto_tipo=linha["desconto_tipo"] if modo == "individual" else "",
                desconto_valor=linha["desconto_valor"] if modo == "individual" else Decimal("0.00"),
                loja_id=loja_id,
            )
        for item in produtos:
            ProtocoloContratoProduto.objects.create(
                contrato=contrato,
                produto=item["produto"],
                quantidade=Decimal(str(item["quantidade"])).quantize(Decimal("0.01")),
                loja_id=loja_id,
            )

    return {
        "contrato_id": contrato.id,
        "nome": titulo,
        "valor_bruto": str(conta["bruto"]),
        "desconto": str(conta["desconto"]),
        "valor_total": str(conta["liquido"]),
    }


def _gravar_itens(contrato, linhas, produtos, loja_id, modo: str):
    from .models import ProtocoloContratoProcedimento, ProtocoloContratoProduto

    contrato.procedimentos.all().delete()
    contrato.produtos_sessao.all().delete()
    for linha in linhas:
        ProtocoloContratoProcedimento.objects.create(
            contrato=contrato,
            procedure=linha["procedure"],
            valor=linha["preco"],
            desconto_tipo=(linha.get("desconto_tipo") or "") if modo == "individual" else "",
            desconto_valor=(linha.get("desconto_valor") or Decimal("0.00")) if modo == "individual" else Decimal("0.00"),
            loja_id=loja_id,
        )
    for item in produtos:
        ProtocoloContratoProduto.objects.create(
            contrato=contrato,
            produto=item["produto"],
            quantidade=Decimal(str(item["quantidade"])).quantize(Decimal("0.01")),
            loja_id=loja_id,
        )


def atualizar_protocolo_personalizado(
    contrato,
    *,
    procedimentos,
    produtos,
    desconto_tipo: str,
    desconto_valor,
    desconto_escopo: str = "total",
    sessoes: int,
    intervalo_quantidade: int,
    intervalo_unidade: str,
    tempo_minutos: int,
    nome: str = "",
    etapas: dict | None = None,
    request=None,
) -> dict:
    """Atualiza o pacote que ainda não foi para a agenda."""
    from .agenda_service import _bloquear_se_paciente_inadimplente

    if getattr(contrato, "protocol_id", None):
        raise AgendaValidationError("Este protocolo é do catálogo da clínica.")
    status = list(contrato.agendamentos.values_list("status", flat=True))
    if not protocolo_pode_editar(status):
        raise AgendaValidationError(
            "Este protocolo já está na agenda. Exclua o pacote para tirar as sessões que ainda não foram atendidas."
        )
    if intervalo_unidade not in UNIDADES_INTERVALO:
        raise AgendaValidationError("Escolha o intervalo em dias, semanas ou meses.")
    if int(sessoes) < 1:
        raise AgendaValidationError("O protocolo precisa de ao menos uma sessão.")
    if int(intervalo_quantidade) < 1:
        raise AgendaValidationError("Informe o intervalo entre as sessões.")
    if int(tempo_minutos) < 1:
        raise AgendaValidationError("Informe a duração de cada atendimento, em minutos.")

    procedimentos, produtos = _validar_itens(procedimentos, produtos)
    _convenio, linhas = _linhas_de_preco(contrato.patient, procedimentos)
    conta, modo = _conta_do_pacote(linhas, desconto_escopo, desconto_tipo, desconto_valor)
    _bloquear_se_paciente_inadimplente(contrato.patient, request=request)
    titulo = (nome or "").strip() or "Protocolo personalizado"
    tipo_gravado = "" if modo == "individual" else (desconto_tipo or "").strip().lower()
    valor_gravado = conta["desconto"] if modo == "individual" else Decimal(str(desconto_valor or 0)).quantize(Decimal("0.01"))

    with transaction.atomic():
        contrato.nome = titulo
        contrato.valor_bruto = conta["bruto"]
        contrato.desconto_escopo = modo
        contrato.desconto_tipo = tipo_gravado
        contrato.desconto_valor = valor_gravado
        contrato.valor_total = conta["liquido"]
        contrato.tempo_minutos = int(tempo_minutos)
        contrato.intervalo_quantidade = int(intervalo_quantidade)
        contrato.intervalo_unidade = intervalo_unidade
        contrato.sessoes = int(sessoes)
        for chave, texto in etapas_do_pedido(etapas).items():
            setattr(contrato, chave, texto)
        contrato.save()
        _gravar_itens(contrato, conta["linhas"], produtos, contrato.loja_id, modo)

    return {
        "contrato_id": contrato.id,
        "nome": titulo,
        "valor_bruto": str(conta["bruto"]),
        "desconto": str(conta["desconto"]),
        "valor_total": str(conta["liquido"]),
    }


def excluir_protocolo_personalizado(contrato) -> None:
    """Apaga o pacote e as sessões que ainda não foram atendidas nem pagas."""
    from .models import Payment

    if getattr(contrato, "protocol_id", None):
        raise AgendaValidationError("Este protocolo é do catálogo da clínica.")
    agendamentos = list(contrato.agendamentos.all())
    status = [item.status for item in agendamentos]
    vivos = [item for item in agendamentos if item.status not in _STATUS_IGNORADO]
    tem_pagamento = Payment.objects.filter(
        appointment_id__in=[item.id for item in vivos],
    ).exclude(status="CANCELLED").exists() if vivos else False
    motivo = motivo_impede_exclusao(status, tem_pagamento)
    if motivo:
        raise AgendaValidationError(motivo)
    with transaction.atomic():
        for item in vivos:
            item.delete()
        contrato.delete()


def agendar_protocolo_personalizado(
    *,
    contrato,
    professional,
    local_atendimento,
    data_inicio,
    request=None,
) -> dict:
    """A secretaria escolhe a profissional e cria as sessões no horário livre dela."""
    from .agenda_service import registrar_criacao_agendamento, validar_regras_agendamento
    from .models import Appointment, AppointmentProcedure
    from .protocolo_comercial import _ciente

    if getattr(contrato, "protocol_id", None):
        raise AgendaValidationError("Este protocolo é do catálogo. Agende pelo procedimento.")
    if contrato.agendamentos.exists():
        raise AgendaValidationError("Este protocolo já está na agenda.")
    if not professional:
        raise AgendaValidationError("Selecione a profissional.")
    if not local_atendimento:
        raise AgendaValidationError("Selecione o local de atendimento.")
    if not contrato.tempo_minutos or not contrato.intervalo_quantidade or not contrato.intervalo_unidade:
        raise AgendaValidationError("O protocolo está sem duração ou intervalo.")

    linhas = list(contrato.procedimentos.select_related("procedure").order_by("id"))
    if not linhas:
        raise AgendaValidationError("O protocolo não tem procedimentos.")
    inicio = _ciente(data_inicio)
    datas = [
        _ciente(item)
        for item in datas_das_sessoes(
            inicio,
            int(contrato.sessoes),
            int(contrato.intervalo_quantidade),
            contrato.intervalo_unidade,
        )
    ]
    encaixes = encaixar_horarios(
        datas,
        int(contrato.tempo_minutos),
        intervalos_ocupados_profissional(professional, datas[0], datas[-1] + LIMITE_BUSCA_HORARIO),
    )
    slots = []
    for indice, encaixe in enumerate(encaixes):
        slots.append({
            "sessao": indice + 1,
            "inicio": encaixe["inicio"],
            "fim": encaixe["fim"],
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

    titulo = contrato.nome or "Protocolo personalizado"
    primeiro = linhas[0].procedure
    loja_id = contrato.loja_id
    convenio = None
    convenio_paciente = getattr(contrato.patient, "convenio", None)
    if convenio_paciente is not None and getattr(convenio_paciente, "is_active", False):
        convenio = convenio_paciente

    with transaction.atomic():
        contrato.professional = professional
        contrato.local_atendimento = local_atendimento
        contrato.data_inicio = slots[0]["inicio"]
        contrato.save(update_fields=["professional", "local_atendimento", "data_inicio"])
        criados = []
        for slot in slots:
            notes = f"{titulo} — sessão {slot['sessao']} de {contrato.sessoes}"
            if slot["ajustado"]:
                notes = f"{notes}\nHorário ajustado para o próximo horário livre."
            appointment = Appointment.objects.create(
                date=slot["inicio"],
                status="SCHEDULED",
                patient=contrato.patient,
                professional=professional,
                procedure=primeiro,
                local_atendimento=local_atendimento,
                convenio=convenio,
                duracao_minutos=int(contrato.tempo_minutos),
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
            for ordem, linha in enumerate(linhas):
                AppointmentProcedure.objects.create(
                    appointment=appointment,
                    procedure=linha.procedure,
                    duracao_minutos=int(contrato.tempo_minutos),
                    valor=Decimal("0.00"),
                    ordem=ordem,
                    loja_id=loja_id,
                )
            criados.append(
                {
                    "id": appointment.id,
                    "sessao": slot["sessao"],
                    "date": timezone.localtime(slot["inicio"]).isoformat(),
                    "ajustado": slot["ajustado"],
                }
            )

    return {
        "contrato_id": contrato.id,
        "nome": titulo,
        "valor_total": str(contrato.valor_total),
        "agendamentos": criados,
    }


def definir_pagamento_protocolo(contrato, forma: str, appointment_id=None) -> None:
    """Grava o valor total nesta sessão ou divide pelas sessões, no recebimento."""
    from .models import AppointmentProcedure

    atual = (getattr(contrato, "forma_cobranca", None) or "").strip()
    if atual in FORMAS_COBRANCA:
        return
    forma = (forma or "").strip()
    if forma not in FORMAS_COBRANCA:
        raise AgendaValidationError(
            "Escolha pagar tudo na primeira sessão ou dividir pelas sessões.",
        )
    if getattr(contrato, "protocol_id", None):
        raise AgendaValidationError("O pagamento deste protocolo já foi definido no agendamento.")
    linhas = list(contrato.procedimentos.order_by("id"))
    if not linhas:
        raise AgendaValidationError("O protocolo não tem procedimentos.")
    agendamentos = list(contrato.agendamentos.order_by("sessao_numero", "date"))
    if not agendamentos:
        raise AgendaValidationError("Agende o protocolo antes de definir o pagamento.")

    if (getattr(contrato, "desconto_escopo", "") or "") == "individual":
        conta, _modo = _conta_do_pacote(
            [
                {
                    "procedure": linha.procedure,
                    "preco": linha.valor,
                    "desconto_tipo": linha.desconto_tipo,
                    "desconto_valor": linha.desconto_valor,
                }
                for linha in linhas
            ],
            "individual",
            "",
            0,
        )
        pesos = [item["liquido"] for item in conta["linhas"]]
    else:
        pesos = [linha.valor for linha in linhas]
    try:
        alvo = int(appointment_id) if appointment_id else None
    except (TypeError, ValueError):
        alvo = None
    if forma == "TOTAL" and alvo:
        liquido = Decimal(str(contrato.valor_total or 0)).quantize(Decimal("0.01"))
        partes = [Decimal("0.00")] * int(contrato.sessoes)
        for item in agendamentos:
            if item.id != alvo:
                continue
            indice_total = (item.sessao_numero or 1) - 1
            if 0 <= indice_total < len(partes):
                partes[indice_total] = liquido
            break
    else:
        partes = dividir_valor_protocolo(contrato.valor_total, int(contrato.sessoes), forma)
    with transaction.atomic():
        contrato.forma_cobranca = forma
        contrato.save(update_fields=["forma_cobranca"])
        for appointment in agendamentos:
            indice = (appointment.sessao_numero or 1) - 1
            valor = partes[indice] if 0 <= indice < len(partes) else Decimal("0.00")
            valores = repartir_valor(valor, pesos)
            procs = {
                item.procedure_id: item
                for item in AppointmentProcedure.objects.filter(appointment=appointment)
            }
            for linha, valor_linha in zip(linhas, valores, strict=False):
                procedimento = procs.get(linha.procedure_id)
                if procedimento is None:
                    continue
                procedimento.valor = valor_linha
                procedimento.save(update_fields=["valor"])
