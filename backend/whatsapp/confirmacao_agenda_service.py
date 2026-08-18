"""Quando enviar o link de confirmação da agenda.

O admin escolhe os dias de antecedência (ex.: 3 e 1). O worker envia em
cada um desses dias. Se o horário for marcado depois do dia da regra
(ex.: consulta hoje com "1 dia antes"), envia na última chance.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from django.db import IntegrityError
from django.utils import timezone

logger = logging.getLogger(__name__)

ANTECEDENCIA_MIN = 1
ANTECEDENCIA_MAX = 30
DEFAULT_ANTECEDENCIAS = [1]
MODULO_CLINICA = "clinica_beleza"
MODULO_SALAO = "cabeleireiro"

# Link de confirmação da agenda: só Clínica da Beleza e salão.
# CRM Vendas (Felix) usa WhatsApp para proposta/contrato/tarefas, não esta tabela.
SLUGS_CONFIRMACAO_AGENDA = frozenset({
    "clinica-beleza",
    "clinica-da-beleza",
    "clinica-estetica",
    "clinica-de-estetica",
    "cabeleireiro",
})


def loja_usa_confirmacao_agenda(loja) -> bool:
    slug = (getattr(getattr(loja, "tipo_loja", None), "slug", None) or "").strip().lower()
    return slug in SLUGS_CONFIRMACAO_AGENDA


class AntecedenciaInvalida(ValueError):
    pass


def normalizar_antecedencias(raw) -> list[int]:
    """Aceita lista, tupla ou string '3,1'. Vazio = nenhum envio automático."""
    if raw is None:
        return list(DEFAULT_ANTECEDENCIAS)
    if isinstance(raw, str):
        raw = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    if not isinstance(raw, (list, tuple)):
        raise AntecedenciaInvalida("Informe os dias de antecedência (ex.: 3 e 1).")
    dias: list[int] = []
    for item in raw:
        try:
            n = int(item)
        except (TypeError, ValueError) as exc:
            raise AntecedenciaInvalida("Cada antecedência deve ser um número de dias.") from exc
        if n < ANTECEDENCIA_MIN or n > ANTECEDENCIA_MAX:
            raise AntecedenciaInvalida(
                f"Antecedência deve ser entre {ANTECEDENCIA_MIN} e {ANTECEDENCIA_MAX} dias.",
            )
        if n not in dias:
            dias.append(n)
    return sorted(dias, reverse=True)


def antecedencias_da_config(config) -> list[int]:
    if config is None:
        return list(DEFAULT_ANTECEDENCIAS)
    raw = getattr(config, "confirmacao_antecedencias_dias", None)
    try:
        return normalizar_antecedencias(raw)
    except AntecedenciaInvalida:
        return list(DEFAULT_ANTECEDENCIAS)


def _data_local(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value, timezone.get_current_timezone())
        return value.date()
    if isinstance(value, date):
        return value
    return None


def data_consulta_local(agendamento) -> date | None:
    return _data_local(getattr(agendamento, "date", None))


def dias_ate_consulta(agendamento, *, hoje=None) -> int | None:
    data = data_consulta_local(agendamento)
    if data is None:
        return None
    if hoje is None:
        hoje = timezone.localtime(timezone.now()).date()
    return (data - hoje).days


def regras_do_dia(
    antecedencias: list[int],
    dias_ate: int,
    *,
    data_consulta: date | None = None,
    criado_em=None,
    hoje: date | None = None,
) -> list[int]:
    """Regras cujo envio cai hoje.

    Dia exato (dias_ate == D) sempre dispara.
    Catch-up: se o worker perdeu o dia D, envia atrasado — só se o agendamento
    já existia naquele dia. Não dispara regra passada na criação (ex.: marcado
    há 2 dias com regra de 3 dias).
    Última chance: se a consulta já está dentro da menor antecedência e o
    horário foi marcado depois do dia dela (ex.: "1 dia antes" + consulta hoje),
    dispara só a menor regra.
    """
    if dias_ate < 0:
        return []
    disparar: list[int] = []
    criado = _data_local(criado_em)
    for d in antecedencias:
        if dias_ate == d:
            disparar.append(d)
            continue
        if (
            data_consulta is None
            or criado is None
            or hoje is None
            or not (0 <= dias_ate < d)
        ):
            continue
        dia_da_regra = data_consulta - timedelta(days=d)
        if criado <= dia_da_regra <= hoje:
            disparar.append(d)
    if (
        not disparar
        and criado is not None
        and data_consulta is not None
        and antecedencias
        and 0 <= dias_ate < min(antecedencias)
    ):
        menor = min(antecedencias)
        if criado > data_consulta - timedelta(days=menor):
            disparar.append(menor)
    return disparar


def _modulo_agendamento(agendamento) -> str:
    modulo = (getattr(agendamento, "whatsapp_modulo", None) or MODULO_CLINICA).strip().lower()
    if modulo in ("cabeleireiro", "salao"):
        return MODULO_SALAO
    return MODULO_CLINICA


def ja_enviou_regra(appointment_id: int, regra_dias: int, *, modulo: str = MODULO_CLINICA) -> bool:
    from .models import WhatsAppConfirmacaoEnvio

    return WhatsAppConfirmacaoEnvio.objects.filter(
        appointment_id=appointment_id,
        regra_dias=regra_dias,
        modulo=modulo,
    ).exists()


def registrar_envio(appointment_id: int, regra_dias: int, *, modulo: str = MODULO_CLINICA) -> bool:
    """Reserva o envio desta regra. True se esta chamada deve enviar."""
    from .models import WhatsAppConfirmacaoEnvio

    try:
        WhatsAppConfirmacaoEnvio.objects.create(
            appointment_id=appointment_id,
            regra_dias=regra_dias,
            modulo=modulo,
        )
        return True
    except IntegrityError:
        return False


def liberar_envio(appointment_id: int, regra_dias: int, *, modulo: str = MODULO_CLINICA) -> None:
    from .models import WhatsAppConfirmacaoEnvio

    WhatsAppConfirmacaoEnvio.objects.filter(
        appointment_id=appointment_id,
        regra_dias=regra_dias,
        modulo=modulo,
    ).delete()


def enviar_confirmacao_da_regra(agendamento, regra_dias: int, *, config, user=None) -> bool:
    """Envia o link se a regra ainda não foi disparada para este agendamento."""
    from .services import enviar_confirmacao_agendamento

    ap_id = getattr(agendamento, "id", None)
    if not ap_id:
        return False
    modulo = _modulo_agendamento(agendamento)
    if not registrar_envio(ap_id, regra_dias, modulo=modulo):
        return False
    ok, err = enviar_confirmacao_agendamento(agendamento, user=user, config=config)
    if not ok:
        logger.warning(
            "Confirmação agenda %s regra %sd falhou: %s",
            ap_id, regra_dias, err,
        )
        liberar_envio(ap_id, regra_dias, modulo=modulo)
        return False
    return True


def processar_agendamento_hoje(agendamento, *, config, hoje=None, user=None) -> int:
    """Envia as regras cujo dia é hoje. Retorna quantidade enviada."""
    if not config or not getattr(config, "enviar_confirmacao", False):
        return 0
    if not getattr(config, "whatsapp_ativo", False):
        return 0
    dias_ate = dias_ate_consulta(agendamento, hoje=hoje)
    if dias_ate is None:
        return 0
    if hoje is None:
        hoje = timezone.localtime(timezone.now()).date()
    enviados = 0
    for regra in regras_do_dia(
        antecedencias_da_config(config),
        dias_ate,
        data_consulta=data_consulta_local(agendamento),
        criado_em=getattr(agendamento, "created_at", None),
        hoje=hoje,
    ):
        if enviar_confirmacao_da_regra(agendamento, regra, config=config, user=user):
            enviados += 1
    return enviados


def disparar_confirmacao_se_hoje(agendamento, *, user=None) -> int:
    """Na criação: envia só se hoje já é um dia de envio (regra exata ou última chance)."""
    from tenants.middleware import get_current_loja_id
    from whatsapp.models import WhatsAppConfig

    patient = getattr(agendamento, "patient", None)
    if patient is not None and not getattr(patient, "allow_whatsapp", True):
        return 0
    loja_id = getattr(agendamento, "loja_id", None) or get_current_loja_id()
    if not loja_id:
        return 0
    try:
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    except Exception:
        logger.exception("WhatsApp config confirmação loja_id=%s", loja_id)
        return 0
    return processar_agendamento_hoje(agendamento, config=config, user=user)


def janela_datas(antecedencias: list[int], *, hoje=None) -> tuple[date, date] | None:
    """Datas de consulta que podem receber envio hoje."""
    if not antecedencias:
        return None
    if hoje is None:
        hoje = timezone.localtime(timezone.now()).date()
    return hoje, hoje + timedelta(days=max(antecedencias))
