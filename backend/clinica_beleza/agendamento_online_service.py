"""Regras de negócio do Agendamento Online."""
from __future__ import annotations

from datetime import datetime, timedelta, time
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .agenda_service import AgendaValidationError, validar_disponibilidade_janela
from .duracao_consulta import calcular_duracao_novo_agendamento, tempo_consulta_base_minutos
from .models import (
    AgendamentoOnlineConfig,
    AgendamentoOnlineHorario,
    AgendamentoOnlineProcedimento,
    AgendamentoOnlineProfissional,
    Appointment,
    CategoriaProcedimento,
    HorarioTrabalhoProfissional,
    Patient,
    Procedure,
    Professional,
)


class AgendamentoOnlineError(Exception):
    def __init__(self, message: str, code: str = "erro"):
        self.message = message
        self.code = code
        super().__init__(message)


def get_or_create_config(loja_id: int) -> AgendamentoOnlineConfig:
    cfg, _ = AgendamentoOnlineConfig.objects.get_or_create(loja_id=loja_id)
    return cfg


def config_publica_ativa(loja_id: int) -> AgendamentoOnlineConfig | None:
    from superadmin.plano_features import loja_plano_permite_agendamento_online

    ok, _ = loja_plano_permite_agendamento_online(loja_id)
    if not ok:
        return None
    cfg = AgendamentoOnlineConfig.objects.filter(loja_id=loja_id, ativo=True).first()
    return cfg


def _hm(t: time) -> str:
    return t.strftime("%H:%M")


def _parse_hm(value: str) -> time:
    h, m = (value or "00:00")[:5].split(":")
    return time(int(h), int(m))


def periodos_online_do_dia(professional: Professional, dia: datetime.date) -> list[tuple[time, time]]:
    """Janelas em que o cliente pode marcar (já descontando almoço se usar expediente)."""
    vinculo = AgendamentoOnlineProfissional.objects.filter(
        professional=professional, liberado=True, bloqueado_temporariamente=False,
    ).first()
    if not vinculo:
        return []

    weekday = dia.weekday()  # 0=segunda
    if vinculo.usar_horarios_exclusivos:
        return [
            (h.hora_inicio, h.hora_fim)
            for h in vinculo.horarios.filter(dia_semana=weekday, ativo=True).order_by("hora_inicio")
            if h.hora_fim > h.hora_inicio
        ]

    ht = HorarioTrabalhoProfissional.objects.filter(
        professional=professional, dia_semana=weekday, ativo=True,
    ).first()
    if not ht:
        return []
    periodos = []
    if ht.intervalo_inicio and ht.intervalo_fim and ht.intervalo_fim > ht.intervalo_inicio:
        if ht.intervalo_inicio > ht.hora_entrada:
            periodos.append((ht.hora_entrada, ht.intervalo_inicio))
        if ht.hora_saida > ht.intervalo_fim:
            periodos.append((ht.intervalo_fim, ht.hora_saida))
    else:
        periodos.append((ht.hora_entrada, ht.hora_saida))
    return [(a, b) for a, b in periodos if b > a]


def duracao_slot(professional: Professional, procedure: Procedure | None) -> int:
    return calcular_duracao_novo_agendamento(
        professional=professional,
        procedure=procedure,
        procedures_list=[procedure] if procedure else None,
    )


def gerar_slots_dia(
    *,
    professional: Professional,
    procedure: Procedure,
    dia: datetime.date,
    config: AgendamentoOnlineConfig,
) -> list[str]:
    """Lista de HH:MM disponíveis no dia, considerando duração e conflitos."""
    tz = timezone.get_current_timezone()
    agora = timezone.localtime()
    periodos = periodos_online_do_dia(professional, dia)
    if not periodos:
        return []

    if not config.permitir_mesmo_dia and dia == agora.date():
        return []

    duracao = duracao_slot(professional, procedure)
    step = max(5, int(config.intervalo_slots_minutos or 30))
    minimo = agora + timedelta(hours=int(config.antecedencia_minima_horas or 0))
    slots = []

    for ini_t, fim_t in periodos:
        cursor = datetime.combine(dia, ini_t, tzinfo=tz)
        fim_periodo = datetime.combine(dia, fim_t, tzinfo=tz)
        while cursor + timedelta(minutes=duracao) <= fim_periodo:
            if cursor >= minimo:
                fim = cursor + timedelta(minutes=duracao)
                try:
                    validar_disponibilidade_janela(
                        professional, cursor, fim, appointment_id=None, evento="AGENDAMENTO_CRIADO",
                    )
                    slots.append(cursor.strftime("%H:%M"))
                except AgendaValidationError:
                    pass
            cursor += timedelta(minutes=step)
    return slots


def dias_com_vaga(
    *,
    professional: Professional,
    procedure: Procedure,
    config: AgendamentoOnlineConfig,
) -> list[str]:
    tz = timezone.get_current_timezone()
    hoje = timezone.localtime().date()
    fim = hoje + timedelta(days=int(config.dias_futuros or 30))
    saida = []
    dia = hoje if config.permitir_mesmo_dia else hoje + timedelta(days=1)
    while dia <= fim:
        if gerar_slots_dia(professional=professional, procedure=procedure, dia=dia, config=config):
            saida.append(dia.isoformat())
        dia += timedelta(days=1)
    return saida


def procedimentos_liberados(loja_id: int):
    return (
        AgendamentoOnlineProcedimento.objects.filter(liberado=True, procedure__is_active=True)
        .select_related("procedure")
        .prefetch_related("profissionais")
        .order_by("ordem", "id")
    )


def categorias_com_procedimentos(loja_id: int) -> list[dict]:
    procs = list(procedimentos_liberados(loja_id))
    slugs = {p.procedure.categoria for p in procs if p.procedure.categoria}
    cats = {
        c.slug: c
        for c in CategoriaProcedimento.objects.filter(is_active=True, slug__in=slugs)
    }
    contagem: dict[str, int] = {}
    for p in procs:
        slug = p.procedure.categoria or "outro"
        contagem[slug] = contagem.get(slug, 0) + 1
    saida = []
    for slug, n in contagem.items():
        cat = cats.get(slug)
        saida.append({
            "slug": slug,
            "nome": cat.nome if cat else slug.replace("_", " ").title(),
            "cor": getattr(cat, "cor", None) or "#EC4899",
            "ordem": getattr(cat, "ordem", 999) if cat else 999,
            "quantidade": n,
            "descricao": "",
            "imagem_url": "",
        })
    saida.sort(key=lambda x: (x["ordem"], x["nome"]))
    return saida


def serializar_procedimento_publico(vinculo: AgendamentoOnlineProcedimento) -> dict:
    p = vinculo.procedure
    data = {
        "id": p.id,
        "nome": p.nome,
        "descricao": getattr(p, "descricao", "") or "",
        "categoria": p.categoria or "",
        "duracao_minutos": int(p.duracao_minutos or 0),
        "exibir_valor": bool(vinculo.exibir_valor),
    }
    if vinculo.exibir_valor:
        data["preco"] = str(p.preco) if p.preco is not None else None
    else:
        data["preco"] = None
        data["preco_rotulo"] = "Sob consulta"
    return data


def profissionais_para_procedimento(vinculo: AgendamentoOnlineProcedimento):
    qs = AgendamentoOnlineProfissional.objects.filter(
        liberado=True,
        bloqueado_temporariamente=False,
        professional__is_active=True,
        professional__is_profissional=True,
    ).select_related("professional")
    ids = list(vinculo.profissionais.values_list("id", flat=True))
    if ids:
        qs = qs.filter(professional_id__in=ids)
    return qs


def serializar_profissional_publico(vinculo: AgendamentoOnlineProfissional) -> dict:
    p = vinculo.professional
    return {
        "id": p.id,
        "nome": p.nome,
        "especialidade": p.especialidade or "",
        "foto_url": getattr(p, "foto_url", None) or "",
        "tempo_consulta_minutos": tempo_consulta_base_minutos(p),
    }


def buscar_ou_criar_paciente_seguro(
    *,
    loja_id: int,
    nome: str,
    telefone: str,
    email: str = "",
    data_nascimento=None,
) -> Patient:
    """Evita duplicata por telefone; não expõe lista de pacientes."""
    digits = "".join(c for c in (telefone or "") if c.isdigit())
    if len(digits) < 10:
        raise AgendamentoOnlineError("Informe um celular válido com DDD.", "telefone")
    sufixo = digits[-9:]
    existente = None
    for candidato in Patient.objects.filter(is_active=True, telefone__icontains=sufixo[-8:]).order_by("id")[:20]:
        cand_digits = "".join(c for c in (candidato.telefone or "") if c.isdigit())
        if cand_digits == digits or cand_digits[-9:] == digits[-9:]:
            existente = candidato
            break
    if existente:
        mudou = False
        if nome and not existente.nome:
            existente.nome = nome.strip()
            mudou = True
        if email and not getattr(existente, "email", None):
            existente.email = email.strip()
            mudou = True
        if mudou:
            existente.save()
        return existente
    return Patient.objects.create(
        nome=nome.strip(),
        telefone=telefone.strip(),
        email=(email or "").strip() or None,
        data_nascimento=data_nascimento,
        loja_id=loja_id,
        is_active=True,
    )


@transaction.atomic
def criar_agendamento_online(
    *,
    loja_id: int,
    config: AgendamentoOnlineConfig,
    professional_id: int,
    procedure_id: int,
    date_start: datetime,
    nome: str,
    telefone: str,
    email: str = "",
    observacoes: str = "",
    data_nascimento=None,
) -> Appointment:
    vinculo_proc = (
        AgendamentoOnlineProcedimento.objects.filter(
            procedure_id=procedure_id, liberado=True, procedure__is_active=True,
        )
        .select_related("procedure")
        .first()
    )
    if not vinculo_proc:
        raise AgendamentoOnlineError("Procedimento indisponível para agendamento online.")

    vinculo_prof = (
        AgendamentoOnlineProfissional.objects.filter(
            professional_id=professional_id,
            liberado=True,
            bloqueado_temporariamente=False,
            professional__is_active=True,
        )
        .select_related("professional")
        .first()
    )
    if not vinculo_prof:
        raise AgendamentoOnlineError("Profissional indisponível para agendamento online.")

    ids_ok = list(vinculo_proc.profissionais.values_list("id", flat=True))
    if ids_ok and professional_id not in ids_ok:
        raise AgendamentoOnlineError("Este profissional não realiza o procedimento escolhido.")

    professional = vinculo_prof.professional
    procedure = vinculo_proc.procedure
    duracao = duracao_slot(professional, procedure)
    date_end = date_start + timedelta(minutes=duracao)

    # Slot precisa estar na janela online do dia
    dia = timezone.localtime(date_start).date()
    hm = timezone.localtime(date_start).strftime("%H:%M")
    if hm not in gerar_slots_dia(
        professional=professional, procedure=procedure, dia=dia, config=config,
    ):
        raise AgendamentoOnlineError("Horário indisponível. Escolha outro horário.")

    validar_disponibilidade_janela(
        professional, date_start, date_end, appointment_id=None, evento="AGENDAMENTO_CRIADO",
    )

    patient = buscar_ou_criar_paciente_seguro(
        loja_id=loja_id,
        nome=nome,
        telefone=telefone,
        email=email,
        data_nascimento=data_nascimento,
    )

    status = (
        "SCHEDULED"
        if config.modo_confirmacao == AgendamentoOnlineConfig.MODO_SECRETARIA
        else "SCHEDULED"
    )
    # Ambos começam como SCHEDULED; modo secretaria = pendente de aprovação operacional
    # (status legado PENDING ainda existe; usamos SCHEDULED + origem online).

    from .agenda_service import criar_agendamento
    from .convenio_service import criar_appointment_procedures

    appointment = criar_agendamento(
        {
            "date": date_start,
            "status": status,
            "patient": patient,
            "professional": professional,
            "procedure": procedure,
            "notes": (observacoes or "").strip() or None,
            "duracao_minutos": duracao,
            "origem": Appointment.ORIGEM_ONLINE,
            "_procedures_list": [procedure],
        },
        user=None,
        request=None,
    )
    if appointment.origem != Appointment.ORIGEM_ONLINE:
        appointment.origem = Appointment.ORIGEM_ONLINE
        appointment.save(update_fields=["origem", "updated_at"])
    if not appointment.appointment_procedures.exists():
        criar_appointment_procedures(appointment, [procedure])
    return appointment
