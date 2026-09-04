"""Agenda: datas, slots, recepção e disparo de confirmação."""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta

from .config_service import agenda_janela
from .models import Consulta

logger = logging.getLogger(__name__)

CAMPOS_RECEPCAO = (
    "numero_prontuario",
    "nome",
    "nome_social",
    "cpf",
    "rg",
    "rne",
    "passaporte",
    "pais_emissor",
    "nome_mae",
    "telefone_fixo",
    "telefone",
    "email",
    "quem_indicou",
    "alergias",
)


def parse_iso_date(raw: str, default: date | None = None) -> date:
    fallback = default or datetime.now().date()
    texto = (raw or "").strip()
    if not texto:
        return fallback
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return fallback


def parse_periodo(raw_de: str, raw_ate: str, hoje: date | None = None) -> tuple[date, date]:
    ref = hoje or datetime.now().date()
    return parse_iso_date(raw_de, ref.replace(day=1)), parse_iso_date(raw_ate, ref)


def slots_livres(dia: date, inicio: time, fim_hora: time, passo: int, ocupados: set[str]) -> list[str]:
    livres: list[str] = []
    cursor = datetime.combine(dia, inicio)
    fim = datetime.combine(dia, fim_hora)
    delta = timedelta(minutes=passo or 15)
    while cursor < fim:
        hhmm = cursor.strftime("%H:%M")
        if hhmm not in ocupados:
            livres.append(hhmm)
        cursor += delta
    return livres


def horarios_ocupados(dia: date) -> set[str]:
    return {
        c.hora.strftime("%H:%M")
        for c in Consulta.objects.filter(is_active=True, data=dia).exclude(status="desmarcado")
    }


def horarios_livres_janela(dia: date) -> list[dict]:
    inicio, fim, passo = agenda_janela()
    return [
        {
            "data": d.isoformat(),
            "horarios": slots_livres(d, inicio, fim, passo, horarios_ocupados(d)),
        }
        for d in (dia, dia + timedelta(days=1))
    ]


def nome_usuario(user) -> str:
    full = ""
    if hasattr(user, "get_full_name"):
        full = (user.get_full_name() or "").strip()
    first = (getattr(user, "first_name", "") or "").strip()
    username = (getattr(user, "username", "") or "").strip()
    return full or first or username


def disparar_confirmacao_consulta(consulta: Consulta) -> None:
    try:
        from whatsapp.confirmacao_agenda_service import disparar_confirmacao_se_hoje

        from .whatsapp_agenda import ConsultaWhatsAppAdapter

        disparar_confirmacao_se_hoje(ConsultaWhatsAppAdapter(consulta))
    except Exception:
        logger.exception("WhatsApp confirmação clínica geral consulta %s", getattr(consulta, "id", None))


def aplicar_recepcao(consulta: Consulta, dados: dict) -> Consulta:
    paciente = consulta.paciente
    for campo in CAMPOS_RECEPCAO:
        if campo in dados:
            setattr(paciente, campo, dados.get(campo) or "")
    paciente.save()
    if "convenio" in dados:
        consulta.convenio = dados.get("convenio") or consulta.convenio
    consulta.status = "recepcionado"
    consulta.save(update_fields=["convenio", "status", "updated_at"])
    return consulta


def aplicar_checkin(consulta: Consulta) -> Consulta:
    consulta.status = "checkin"
    consulta.save(update_fields=["status", "updated_at"])
    return consulta


def cancelar_consulta(consulta: Consulta) -> Consulta:
    consulta.is_active = False
    consulta.status = "desmarcado"
    consulta.save(update_fields=["is_active", "status", "updated_at"])
    return consulta
