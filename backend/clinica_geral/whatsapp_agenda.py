"""WhatsApp confirmação da Clínica — adapter, sem modelos da estética."""
from __future__ import annotations

import logging
from datetime import datetime

from django.utils import timezone

logger = logging.getLogger(__name__)

WHATSAPP_MODULO = "clinica_geral"
STATUS_ACIONAVEIS = frozenset({"agendado"})


class _EmptyProcedures:
    def exists(self):
        return False

    def values_list(self, *args, **kwargs):
        return []


class _PacienteProxy:
    def __init__(self, paciente):
        self._p = paciente
        self.name = paciente.nome_social or paciente.nome
        self.nome = paciente.nome
        self.phone = paciente.telefone
        self.telefone = paciente.telefone
        self.allow_whatsapp = True


class _TipoProxy:
    def __init__(self, consulta):
        self.nome = consulta.get_tipo_display()


class ConsultaWhatsAppAdapter:
    whatsapp_modulo = WHATSAPP_MODULO

    def __init__(self, consulta):
        self._ag = consulta
        self.id = consulta.id
        self.loja_id = consulta.loja_id
        self.status = consulta.status
        self.patient = _PacienteProxy(consulta.paciente)
        self.professional = None
        self.procedure = _TipoProxy(consulta)
        self.procedures = _EmptyProcedures()
        naive = datetime.combine(consulta.data, consulta.hora)
        tz = timezone.get_current_timezone()
        self.date = timezone.make_aware(naive, tz) if timezone.is_naive(naive) else naive
        self.created_at = consulta.created_at

    def get_status_display(self):
        return self._ag.get_status_display()


def serializar_consulta_publico(consulta, loja_nome: str = "") -> dict:
    adapter = ConsultaWhatsAppAdapter(consulta)
    pode = consulta.status in STATUS_ACIONAVEIS
    motivo = None
    if not pode:
        if consulta.status == "confirmado":
            motivo = "confirmado"
        elif consulta.status == "desmarcado":
            motivo = "cancelado"
        else:
            motivo = "indisponivel"
    return {
        "appointment_id": consulta.id,
        "paciente_nome": consulta.paciente.nome_social or consulta.paciente.nome,
        "profissional_nome": "",
        "procedimento": consulta.get_tipo_display(),
        "servico_label": "Consulta",
        "data": consulta.data.strftime("%d/%m/%Y"),
        "hora": consulta.hora.strftime("%H:%M"),
        "status": consulta.status,
        "status_display": consulta.get_status_display(),
        "clinica_nome": loja_nome,
        "loja_nome": loja_nome,
        "modulo": WHATSAPP_MODULO,
        "pode_responder": pode,
        "motivo_bloqueio": motivo,
        "date": adapter.date,
    }


def aplicar_resposta_confirmacao_consultorio(consulta, acao: str):
    novo = "confirmado" if acao == "confirmar" else "desmarcado"
    if consulta.status == novo:
        label = "confirmado" if acao == "confirmar" else "cancelado"
        return True, f"Este agendamento já estava {label}.", True
    if consulta.status not in STATUS_ACIONAVEIS:
        return False, f"Não é possível alterar: status atual é {consulta.get_status_display()}.", False
    consulta.status = novo
    if novo == "desmarcado":
        consulta.is_active = False
        consulta.save(update_fields=["status", "is_active", "updated_at"])
    else:
        consulta.save(update_fields=["status", "updated_at"])
    msg = (
        "Agendamento confirmado! Aguardamos você no horário marcado."
        if acao == "confirmar"
        else "Agendamento cancelado. Se precisar remarcar, entre em contato conosco."
    )
    return True, msg, False
