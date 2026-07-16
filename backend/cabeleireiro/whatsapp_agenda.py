"""WhatsApp confirmação de agenda do salão — adapter + envio (padrão clínica)."""
from __future__ import annotations

import logging
from datetime import datetime

from django.utils import timezone

logger = logging.getLogger(__name__)

WHATSAPP_MODULO = "cabeleireiro"
STATUS_ACIONAVEIS = frozenset({"SCHEDULED"})


class _EmptyProcedures:
    def exists(self):
        return False

    def values_list(self, *args, **kwargs):
        return []


class SalaoAgendamentoWhatsAppAdapter:
    """Expõe Agendamento com a mesma superfície duck-typed da Appointment da clínica."""

    whatsapp_modulo = WHATSAPP_MODULO

    def __init__(self, agendamento):
        self._ag = agendamento
        self.id = agendamento.id
        self.loja_id = agendamento.loja_id
        self.status = agendamento.status
        self.patient = agendamento.cliente
        self.professional = agendamento.profissional
        self.procedure = agendamento.servico
        self.procedures = _EmptyProcedures()
        naive = datetime.combine(agendamento.data, agendamento.hora_inicio)
        tz = timezone.get_current_timezone()
        self.date = timezone.make_aware(naive, tz) if timezone.is_naive(naive) else naive

    def get_status_display(self):
        return self._ag.get_status_display()


def get_whatsapp_config_loja():
    from whatsapp.config_service import get_or_create_whatsapp_config
    from tenants.middleware import get_current_loja_id
    from superadmin.models import Loja

    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    loja = Loja.objects.using("default").filter(pk=loja_id).first()
    if not loja:
        return None
    try:
        return get_or_create_whatsapp_config(loja)
    except Exception:
        logger.exception("WhatsApp config salão loja_id=%s", loja_id)
        return None


def enviar_confirmacao_agendamento_salao(agendamento, *, user=None):
    """Best-effort: envia confirmação WhatsApp se config/cliente permitirem.
    Retorna (ok, erro|None).
    """
    try:
        cliente = agendamento.cliente
        if not getattr(cliente, "allow_whatsapp", True):
            return False, "Cliente não permite WhatsApp."
        telefone = (getattr(cliente, "telefone", None) or "").strip()
        if not telefone:
            return False, "Cliente sem telefone cadastrado."

        config = get_whatsapp_config_loja()
        if not config:
            return False, "WhatsApp não configurado para esta loja."
        if not getattr(config, "enviar_confirmacao", False):
            return False, "Envio de confirmação desativado nas Configurações."
        if not getattr(config, "whatsapp_ativo", False):
            return False, "WhatsApp não está ativo. Ative em Configurações → WhatsApp."

        from whatsapp.services import enviar_confirmacao_agendamento

        adapter = SalaoAgendamentoWhatsAppAdapter(agendamento)
        ok, err = enviar_confirmacao_agendamento(adapter, user=user, config=config)
        if not ok:
            logger.warning("WhatsApp confirmação salão ag=%s: %s", agendamento.id, err)
        return ok, err
    except Exception as exc:
        logger.warning("WhatsApp confirmação salão ag=%s: %s", getattr(agendamento, "id", "?"), exc)
        return False, str(exc)


def serializar_agendamento_publico_salao(agendamento, loja_nome: str = "") -> dict:
    from clinica_beleza.agenda_display import format_agenda_data, format_agenda_hora

    adapter = SalaoAgendamentoWhatsAppAdapter(agendamento)
    pode_responder = agendamento.status in STATUS_ACIONAVEIS
    motivo_bloqueio = None
    if not pode_responder:
        if agendamento.status == "CLIENT_CONFIRMED":
            motivo_bloqueio = "confirmado"
        elif agendamento.status == "CANCELLED":
            motivo_bloqueio = "cancelado"
        else:
            motivo_bloqueio = "indisponivel"
    return {
        "appointment_id": agendamento.id,
        "paciente_nome": getattr(agendamento.cliente, "nome", "") or "",
        "profissional_nome": getattr(agendamento.profissional, "nome", "") if agendamento.profissional_id else "",
        "procedimento": getattr(agendamento.servico, "nome", "") if agendamento.servico_id else "Atendimento",
        "servico_label": "Serviço",
        "data": format_agenda_data(adapter),
        "hora": format_agenda_hora(adapter),
        "status": agendamento.status,
        "status_display": agendamento.get_status_display(),
        "clinica_nome": loja_nome,
        "loja_nome": loja_nome,
        "modulo": WHATSAPP_MODULO,
        "pode_responder": pode_responder,
        "motivo_bloqueio": motivo_bloqueio,
    }


def aplicar_resposta_confirmacao_salao(agendamento, acao: str):
    """Atualiza status do agendamento. Retorna (ok, message, already_done)."""
    from .models import Agendamento

    novo_status = (
        Agendamento.STATUS_CLIENT_CONFIRMED if acao == "confirmar" else Agendamento.STATUS_CANCELLED
    )
    if agendamento.status == novo_status:
        label = "confirmado" if acao == "confirmar" else "cancelado"
        return True, f"Este agendamento já estava {label}.", True

    if agendamento.status not in STATUS_ACIONAVEIS:
        return False, f"Não é possível alterar: status atual é {agendamento.get_status_display()}.", False

    agendamento.status = novo_status
    agendamento.save(update_fields=["status", "updated_at"])
    msg = (
        "Agendamento confirmado! Aguardamos você no horário marcado."
        if acao == "confirmar"
        else "Agendamento cancelado. Se precisar remarcar, entre em contato conosco."
    )
    return True, msg, False
