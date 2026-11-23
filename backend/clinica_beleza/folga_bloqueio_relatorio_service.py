"""Relatório de folgas, bloqueios e dias trabalhados por profissional."""
from __future__ import annotations

import unicodedata
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


def _normalizar_texto(valor: str | None) -> str:
    texto = unicodedata.normalize("NFD", valor or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower().strip()


def inferir_tipo_bloqueio(*, tipo: str | None, titulo: str | None = None, motivo: str | None = None) -> str:
    """Mapeia tipo do banco ou título/motivo da agenda (ex.: 'Férias do profissional')."""
    bruto = (tipo or "").strip().lower()
    if bruto and bruto != "outros":
        return bruto

    texto = _normalizar_texto(f"{titulo or ''} {motivo or ''}")
    if "ferias" in texto:
        return "ferias"
    if "folga" in texto:
        return "folga"
    if "feriado" in texto:
        return "feriado"
    if "manutenc" in texto:
        return "manutencao"
    if "evento" in texto:
        return "evento"
    if "reuniao" in texto:
        return "outros"
    return bruto or "outros"


def _parse_iso_date(valor: str | None) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(valor[:10])
    except ValueError:
        return None


def consolidar_eventos_dia_inteiro(eventos: list[dict]) -> list[dict]:
    """Junta dias consecutivos de mesmo tipo/título (ex.: férias 01–15) numa linha só."""
    if not eventos:
        return []

    dia_inteiro: list[dict] = []
    demais: list[dict] = []
    for ev in eventos:
        if ev.get("dia_inteiro"):
            dia_inteiro.append(ev)
        else:
            demais.append(ev)

    dia_inteiro.sort(key=lambda e: (e.get("data_inicio") or "", e.get("id") or 0))
    consolidados: list[dict] = []
    atual: dict | None = None

    for ev in dia_inteiro:
        ini = _parse_iso_date(ev.get("data_inicio"))
        fim = _parse_iso_date(ev.get("data_fim")) or ini
        if not ini or not fim:
            consolidados.append(ev)
            continue

        if atual is None:
            atual = {
                **ev,
                "data_inicio": ini.isoformat(),
                "data_fim": fim.isoformat(),
                "ids": [ev.get("id")],
                "dias_no_periodo": int(ev.get("dias_no_periodo") or 0),
            }
            continue

        atual_fim = _parse_iso_date(atual.get("data_fim"))
        mesma_chave = (
            (atual.get("tipo") or "") == (ev.get("tipo") or "")
            and (atual.get("titulo") or "") == (ev.get("titulo") or "")
            and (atual.get("profissional_id") if "profissional_id" in atual else None)
            == (ev.get("profissional_id") if "profissional_id" in ev else None)
        )
        continua = atual_fim is not None and ini == atual_fim + timedelta(days=1)

        if mesma_chave and continua:
            atual["data_fim"] = fim.isoformat()
            atual["dias_no_periodo"] = int(atual.get("dias_no_periodo") or 0) + int(
                ev.get("dias_no_periodo") or 0
            )
            ids = list(atual.get("ids") or [])
            ids.append(ev.get("id"))
            atual["ids"] = ids
        else:
            consolidados.append(atual)
            atual = {
                **ev,
                "data_inicio": ini.isoformat(),
                "data_fim": fim.isoformat(),
                "ids": [ev.get("id")],
                "dias_no_periodo": int(ev.get("dias_no_periodo") or 0),
            }

    if atual is not None:
        consolidados.append(atual)

    demais.sort(key=lambda e: (e.get("data_inicio") or "", e.get("horario_inicio") or "", e.get("id") or 0))
    saida = consolidados + demais
    saida.sort(key=lambda e: (e.get("data_inicio") or "", 0 if e.get("dia_inteiro") else 1, e.get("id") or 0))
    return saida


def _contar_dias_por_categoria(bloqueios: list[BloqueioHorario], periodo_ini: date, periodo_fim: date) -> tuple[int, int]:
    dias_folga: set[date] = set()
    dias_bloqueio: set[date] = set()
    for b in bloqueios:
        tipo = inferir_tipo_bloqueio(tipo=b.tipo, titulo=b.titulo, motivo=b.motivo)
        destino = dias_folga if tipo in _TIPOS_FOLGA else dias_bloqueio
        for dia in _iter_dias(b.data_inicio, b.data_fim):
            if periodo_ini <= dia <= periodo_fim:
                destino.add(dia)
    return len(dias_folga), len(dias_bloqueio)


def _serializar_evento(bloqueio: BloqueioHorario, periodo_ini: date, periodo_fim: date) -> dict:
    tipo = inferir_tipo_bloqueio(
        tipo=bloqueio.tipo,
        titulo=bloqueio.titulo,
        motivo=bloqueio.motivo,
    )
    return {
        "id": bloqueio.id,
        "ids": [bloqueio.id],
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

    gerais_raw = list(bloqueios_por_prof.get(None, []))
    gerais = consolidar_eventos_dia_inteiro(
        [_serializar_evento(b, data_inicio, data_fim) for b in gerais_raw]
    )
    gerais_folga, gerais_bloqueio = _contar_dias_por_categoria(gerais_raw, data_inicio, data_fim)

    lista_profissionais = []
    total_trabalhados = 0
    total_escala = 0
    total_folga = gerais_folga
    total_bloqueio = gerais_bloqueio

    for prof in profissionais:
        dias_semana = sorted({h.dia_semana for h in prof.horarios_trabalho.all()})
        dias_escala = sum(1 for d in _iter_dias(data_inicio, data_fim) if d.weekday() in dias_semana)
        dias_trabalhados = len(dias_trabalho_map.get(prof.id, set()))

        eventos_prof = list(bloqueios_por_prof.get(prof.id, []))
        dias_folga, dias_bloqueio = _contar_dias_por_categoria(eventos_prof, data_inicio, data_fim)

        eventos_serializados = consolidar_eventos_dia_inteiro(
            [_serializar_evento(b, data_inicio, data_fim) for b in eventos_prof]
        )

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
