"""Relatório de folgas, bloqueios e dias trabalhados por profissional."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from django.db.models import Prefetch
from django.db.models.functions import TruncDate

from .models import Appointment, BloqueioHorario, HorarioTrabalhoProfissional, Professional

_TIPOS_FOLGA = frozenset({"folga", "ferias"})
_STATUS_NAO_TRABALHOU = frozenset({"CANCELLED", "NO_SHOW"})
_DIAS_LABEL = {
    0: "Seg",
    1: "Ter",
    2: "Qua",
    3: "Qui",
    4: "Sex",
    5: "Sáb",
    6: "Dom",
}
_TIPO_LABEL = {
    "feriado": "Feriado",
    "ferias": "Férias",
    "folga": "Folga",
    "manutencao": "Manutenção",
    "evento": "Evento",
    "outros": "Outros",
}


def _iter_dias(inicio: date, fim: date):
    atual = inicio
    while atual <= fim:
        yield atual
        atual += timedelta(days=1)


def _dias_sobrepostos(data_inicio: date, data_fim: date, periodo_ini: date, periodo_fim: date) -> int:
    ini = max(data_inicio, periodo_ini)
    fim = min(data_fim, periodo_fim)
    if ini > fim:
        return 0
    return (fim - ini).days + 1


def _serializar_evento(bloqueio: BloqueioHorario, periodo_ini: date, periodo_fim: date) -> dict:
    tipo = (bloqueio.tipo or "outros").strip().lower()
    return {
        "id": bloqueio.id,
        "tipo": tipo,
        "tipo_label": _TIPO_LABEL.get(tipo, tipo or "Outros"),
        "titulo": (bloqueio.titulo or bloqueio.motivo or "").strip() or _TIPO_LABEL.get(tipo, "Bloqueio"),
        "data_inicio": bloqueio.data_inicio.isoformat() if bloqueio.data_inicio else None,
        "data_fim": bloqueio.data_fim.isoformat() if bloqueio.data_fim else None,
        "horario_inicio": bloqueio.horario_inicio.strftime("%H:%M") if bloqueio.horario_inicio else None,
        "horario_fim": bloqueio.horario_fim.strftime("%H:%M") if bloqueio.horario_fim else None,
        "dia_inteiro": not bool(bloqueio.horario_inicio),
        "observacoes": (bloqueio.observacoes or "").strip(),
        "dias_no_periodo": _dias_sobrepostos(
            bloqueio.data_inicio, bloqueio.data_fim, periodo_ini, periodo_fim,
        ),
        "profissional_id": bloqueio.professional_id,
        "profissional_nome": (
            bloqueio.professional.nome if getattr(bloqueio, "professional", None) else "Todos"
        ),
    }


def calcular_folgas_bloqueios(
    *,
    data_inicio: date | None,
    data_fim: date | None,
    professional_id: int | None = None,
) -> dict:
    if not data_inicio or not data_fim:
        hoje = date.today()
        data_inicio = date(hoje.year, hoje.month, 1)
        data_fim = hoje
    if data_fim < data_inicio:
        data_inicio, data_fim = data_fim, data_inicio

    profs_qs = (
        Professional.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "horarios_trabalho",
                queryset=HorarioTrabalhoProfissional.objects.filter(ativo=True).order_by("dia_semana"),
            )
        )
        .order_by("nome")
    )
    if professional_id:
        profs_qs = profs_qs.filter(pk=professional_id)
    profissionais = list(profs_qs)

    bloqueios_qs = (
        BloqueioHorario.objects.filter(
            is_active=True,
            data_inicio__lte=data_fim,
            data_fim__gte=data_inicio,
        )
        .select_related("professional")
        .order_by("data_inicio", "id")
    )
    if professional_id:
        bloqueios_qs = bloqueios_qs.filter(
            models_q_profissional_ou_geral(professional_id),
        )
    bloqueios = list(bloqueios_qs)

    # Dias com atendimento (agenda) por profissional
    appts = (
        Appointment.objects.filter(
            date__date__gte=data_inicio,
            date__date__lte=data_fim,
        )
        .exclude(status__in=_STATUS_NAO_TRABALHOU)
        .exclude(professional_id__isnull=True)
    )
    if professional_id:
        appts = appts.filter(professional_id=professional_id)
    dias_trabalho_map: dict[int, set[date]] = defaultdict(set)
    for row in appts.annotate(dia=TruncDate("date")).values("professional_id", "dia").distinct():
        pid = row["professional_id"]
        dia = row["dia"]
        if pid and dia:
            dias_trabalho_map[pid].add(dia if isinstance(dia, date) else dia)

    bloqueios_por_prof: dict[int | None, list] = defaultdict(list)
    for b in bloqueios:
        bloqueios_por_prof[b.professional_id].append(b)

    gerais = [_serializar_evento(b, data_inicio, data_fim) for b in bloqueios_por_prof.get(None, [])]

    lista_profissionais = []
    total_trabalhados = 0
    total_escala = 0
    total_folga = 0
    total_bloqueio = 0

    for prof in profissionais:
        dias_semana = sorted({h.dia_semana for h in prof.horarios_trabalho.all()})
        dias_escala = sum(1 for d in _iter_dias(data_inicio, data_fim) if d.weekday() in dias_semana)
        dias_trabalhados = len(dias_trabalho_map.get(prof.id, set()))

        eventos_prof = list(bloqueios_por_prof.get(prof.id, []))
        # Bloqueios gerais também afetam o profissional
        eventos_relevantes = eventos_prof + list(bloqueios_por_prof.get(None, []))

        dias_folga = 0
        dias_bloqueio = 0
        for b in eventos_relevantes:
            n = _dias_sobrepostos(b.data_inicio, b.data_fim, data_inicio, data_fim)
            tipo = (b.tipo or "outros").strip().lower()
            if tipo in _TIPOS_FOLGA:
                dias_folga += n
            else:
                dias_bloqueio += n

        eventos_serializados = [
            _serializar_evento(b, data_inicio, data_fim) for b in eventos_prof
        ]

        lista_profissionais.append({
            "professional_id": prof.id,
            "nome": prof.nome,
            "dias_semana_trabalho": [_DIAS_LABEL.get(d, str(d)) for d in dias_semana],
            "dias_escala": dias_escala,
            "dias_trabalhados": dias_trabalhados,
            "dias_folga": dias_folga,
            "dias_bloqueio": dias_bloqueio,
            "eventos": eventos_serializados,
        })
        total_trabalhados += dias_trabalhados
        total_escala += dias_escala
        total_folga += dias_folga
        total_bloqueio += dias_bloqueio

    return {
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "profissionais": lista_profissionais,
        "bloqueios_gerais": gerais,
        "totais": {
            "profissionais": len(lista_profissionais),
            "dias_escala": total_escala,
            "dias_trabalhados": total_trabalhados,
            "dias_folga": total_folga,
            "dias_bloqueio": total_bloqueio,
            "bloqueios_gerais": len(gerais),
        },
    }


def models_q_profissional_ou_geral(professional_id: int):
    from django.db.models import Q

    return Q(professional_id=professional_id) | Q(professional_id__isnull=True)
