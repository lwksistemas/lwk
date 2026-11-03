"""Coleta, agregação e leitura de métricas de capacidade (JSONL)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import connection
from django.utils import timezone


def _json_safe(obj: Any) -> Any:
    """Converte valores para JSON (Decimal, datetime, etc.)."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj

RAW_HORAS = 48
RETENCAO_DIAS = 30
ARQUIVO_PADRAO = os.path.join(
    getattr(settings, "MEDIA_ROOT", "/app/media"),
    "metricas_capacidade.jsonl",
)
ARQUIVO_API = os.path.join(
    getattr(settings, "MEDIA_ROOT", "/app/media"),
    "metricas_api.jsonl",
)
MAX_LINHAS_API = 8000


def arquivo_metricas() -> str:
    return ARQUIVO_PADRAO


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) else None


def _parse_ts(ts_raw: str) -> datetime | None:
    try:
        ts = datetime.fromisoformat(ts_raw)
        if timezone.is_naive(ts):
            ts = timezone.make_aware(ts, timezone.get_current_timezone())
        return ts
    except Exception:
        return None


def servidor_id_registro(r: dict[str, Any]) -> str:
    rs = (r.get("servidor") or r.get("host") or "lwksistemas-nova").strip()
    if rs in ("api", ""):
        return "lwksistemas-nova"
    return rs


def cpu_pct(registro: dict[str, Any]) -> float | None:
    load = _num(registro.get("load_5m"))
    cpus = _num(registro.get("cpus")) or 0
    if load is None or cpus <= 0:
        return None
    return round(min(100.0, (load / cpus) * 100.0), 1)


def _load_average() -> dict[str, float | None]:
    try:
        l1, l5, l15 = os.getloadavg()
        return {"load_1m": round(l1, 2), "load_5m": round(l5, 2), "load_15m": round(l15, 2)}
    except (OSError, AttributeError):
        return {"load_1m": None, "load_5m": None, "load_15m": None}


def _memoria() -> dict[str, Any]:
    try:
        info: dict[str, int] = {}
        with open("/proc/meminfo") as fh:
            for linha in fh:
                partes = linha.split(":")
                if len(partes) == 2:
                    info[partes[0].strip()] = int(partes[1].strip().split()[0])
        total = info.get("MemTotal", 0) // 1024
        disp = info.get("MemAvailable", 0) // 1024
        usada = total - disp
        pct = round(usada / total * 100, 1) if total else None
        return {"mem_total_mb": total, "mem_usada_mb": usada, "mem_usada_pct": pct}
    except Exception:
        return {"mem_total_mb": None, "mem_usada_mb": None, "mem_usada_pct": None}


def _cpus() -> int | None:
    try:
        return os.cpu_count()
    except Exception:
        return None


def _disco(path: str = "/") -> dict[str, Any]:
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        livre = st.f_bavail * st.f_frsize
        usada = total - livre
        total_gb = round(total / (1024**3), 1)
        livre_gb = round(livre / (1024**3), 1)
        usada_gb = round(usada / (1024**3), 1)
        pct = round((usada / total) * 100, 1) if total else None
        return {
            "disk_path": path,
            "disk_total_gb": total_gb,
            "disk_livre_gb": livre_gb,
            "disk_usada_gb": usada_gb,
            "disk_usada_pct": pct,
        }
    except Exception:
        return {
            "disk_path": path,
            "disk_total_gb": None,
            "disk_livre_gb": None,
            "disk_usada_gb": None,
            "disk_usada_pct": None,
        }


def _postgres() -> dict[str, Any]:
    """Conexões e tamanho do cluster — consultas leves."""
    out: dict[str, Any] = {
        "pg_conexoes": None,
        "pg_conexoes_max": None,
        "pg_ativas": None,
        "pg_ociosas": None,
        "pg_idle_in_transaction": None,
        "pg_tamanho_gb": None,
        "pg_lentas_disponivel": False,
        "pg_lentas": [],
    }
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT count(*) FROM pg_stat_activity")
            out["pg_conexoes"] = cur.fetchone()[0]
            cur.execute("SELECT setting::int FROM pg_settings WHERE name = 'max_connections'")
            out["pg_conexoes_max"] = cur.fetchone()[0]
            cur.execute(
                """
                SELECT
                  count(*) FILTER (WHERE state = 'active'),
                  count(*) FILTER (WHERE state = 'idle'),
                  count(*) FILTER (WHERE state = 'idle in transaction')
                FROM pg_stat_activity
                """
            )
            ativas, ociosas, idle_tx = cur.fetchone()
            out["pg_ativas"] = ativas
            out["pg_ociosas"] = ociosas
            out["pg_idle_in_transaction"] = idle_tx
            cur.execute(
                "SELECT coalesce(sum(pg_database_size(datname)), 0) FROM pg_database WHERE datallowconn"
            )
            bytes_total = cur.fetchone()[0] or 0
            out["pg_tamanho_gb"] = round(bytes_total / (1024**3), 2)
            try:
                cur.execute(
                    """
                    SELECT query, mean_exec_time, calls
                    FROM pg_stat_statements
                    ORDER BY mean_exec_time DESC
                    LIMIT 5
                    """
                )
                out["pg_lentas_disponivel"] = True
                out["pg_lentas"] = [
                    {
                        "query": (row[0] or "")[:120],
                        "mean_ms": round(float(row[1] or 0), 1),
                        "calls": int(row[2] or 0),
                    }
                    for row in cur.fetchall()
                ]
            except Exception:
                out["pg_lentas_disponivel"] = False
    except Exception:
        pass
    return out


def _fila() -> dict[str, Any]:
    try:
        from core.task_queue import queue_status

        st = queue_status()
        return {
            "fila_pendente": st.get("queued"),
            "fila_workers": st.get("workers_alive"),
            "fila_falhas_24h": st.get("failures_24h"),
            "fila_em_execucao": st.get("running"),
            "fila_sucesso_24h": st.get("success_24h"),
            "fila_idade_pendente_s": st.get("oldest_queued_age_s"),
            "fila_tempo_medio_s": st.get("avg_runtime_s"),
            "fila_nivel": st.get("health_level"),
        }
    except Exception:
        return {
            "fila_pendente": None,
            "fila_workers": None,
            "fila_falhas_24h": None,
            "fila_em_execucao": None,
            "fila_sucesso_24h": None,
            "fila_idade_pendente_s": None,
            "fila_tempo_medio_s": None,
            "fila_nivel": None,
        }


def _lojas() -> dict[str, Any]:
    try:
        from superadmin.models import Loja

        total = Loja.objects.count()
        ativas = Loja.objects.filter(is_active=True).count()
        return {"lojas_total": total, "lojas_ativas": ativas}
    except Exception:
        return {"lojas_total": None, "lojas_ativas": None}


def coletar_snapshot() -> dict[str, Any]:
    """Snapshot atual do host da API (mesmo shape gravado no JSONL)."""
    media_root = getattr(settings, "MEDIA_ROOT", "/app/media") or "/app/media"
    disco_raiz = _disco("/")
    disco_media = _disco(media_root)
    mesmo_fs = (
        disco_raiz.get("disk_total_gb") is not None
        and disco_raiz.get("disk_total_gb") == disco_media.get("disk_total_gb")
        and disco_raiz.get("disk_livre_gb") == disco_media.get("disk_livre_gb")
    )
    registro: dict[str, Any] = {
        "ts": timezone.localtime(timezone.now()).isoformat(),
        "host": "lwksistemas-nova",
        "servidor": "lwksistemas-nova",
        "nome": "lwksistemas-nova",
        "cpus": _cpus(),
        **_load_average(),
        **_memoria(),
        **disco_raiz,
        **_postgres(),
        **_fila(),
        **_lojas(),
        **resumo_api_recente(),
    }
    if not mesmo_fs:
        registro["disk_media_path"] = disco_media.get("disk_path")
        registro["disk_media_total_gb"] = disco_media.get("disk_total_gb")
        registro["disk_media_livre_gb"] = disco_media.get("disk_livre_gb")
        registro["disk_media_usada_pct"] = disco_media.get("disk_usada_pct")
    return registro


def _ler_todos(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: list[dict[str, Any]] = []
    with open(path) as fh:
        for linha in fh:
            linha = linha.strip()
            if not linha:
                continue
            try:
                r = json.loads(linha)
                if r.get("ts"):
                    out.append(r)
            except Exception:
                continue
    return out


def _avg(vals: list[float]) -> float | None:
    return round(sum(vals) / len(vals), 2) if vals else None


def _max(vals: list[float]) -> float | None:
    return round(max(vals), 2) if vals else None


def _agregar_hora(amostras: list[dict[str, Any]], hora: datetime, sid: str) -> dict[str, Any]:
    loads = [v for v in (_num(a.get("load_5m")) for a in amostras) if v is not None]
    rams = [v for v in (_num(a.get("mem_usada_pct")) for a in amostras) if v is not None]
    disks = [v for v in (_num(a.get("disk_usada_pct")) for a in amostras) if v is not None]
    pgs = [v for v in (_num(a.get("pg_conexoes")) for a in amostras) if v is not None]
    ultimo = amostras[-1]
    return {
        "ts": timezone.localtime(hora).isoformat(),
        "servidor": sid,
        "host": sid,
        "nome": sid,
        "agregado": True,
        "cpus": ultimo.get("cpus"),
        "load_5m": _avg(loads),
        "load_5m_max": _max(loads),
        "mem_usada_pct": _avg(rams),
        "mem_usada_pct_max": _max(rams),
        "disk_usada_pct": _avg(disks),
        "disk_usada_pct_max": _max(disks),
        "disk_livre_gb": ultimo.get("disk_livre_gb"),
        "disk_total_gb": ultimo.get("disk_total_gb"),
        "mem_total_mb": ultimo.get("mem_total_mb"),
        "pg_conexoes": _avg(pgs),
        "pg_conexoes_max": ultimo.get("pg_conexoes_max"),
        "fila_pendente": ultimo.get("fila_pendente"),
        "lojas_ativas": ultimo.get("lojas_ativas"),
        "lojas_total": ultimo.get("lojas_total"),
        "wa_instancias": ultimo.get("wa_instancias"),
        "wa_conectadas": ultimo.get("wa_conectadas"),
        "status": ultimo.get("status") or "ok",
    }


def agregar_e_retener(arquivo: str | None = None) -> int:
    """Mantém raw 48h + agregados horários até 30 dias."""
    path = arquivo or ARQUIVO_PADRAO
    agora = timezone.now()
    corte_raw = agora - timedelta(hours=RAW_HORAS)
    corte_retencao = agora - timedelta(days=RETENCAO_DIAS)
    registros = _ler_todos(path)
    raw: list[dict[str, Any]] = []
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for r in registros:
        ts = _parse_ts(r.get("ts") or "")
        if ts is None or ts < corte_retencao:
            continue
        sid = servidor_id_registro(r)
        r = {**r, "servidor": sid}
        if ts >= corte_raw and not r.get("agregado"):
            raw.append(r)
            continue
        if r.get("agregado"):
            # Mantém agregados já gravados na janela 48h–30d
            if ts < corte_raw:
                raw.append(r)
            continue
        hora = ts.replace(minute=0, second=0, microsecond=0)
        key = (sid, hora.isoformat())
        buckets.setdefault(key, []).append(r)

    agregados = [
        _agregar_hora(amostras, datetime.fromisoformat(hora_iso), sid)
        for (sid, hora_iso), amostras in buckets.items()
        if amostras
    ]
    # Evita duplicar hora se já existe agregado
    horas_ag = {(servidor_id_registro(a), (_parse_ts(a["ts"]) or agora).replace(minute=0, second=0, microsecond=0).isoformat()) for a in raw if a.get("agregado")}
    for a in agregados:
        ts = _parse_ts(a["ts"])
        if ts is None:
            continue
        key = (a["servidor"], ts.replace(minute=0, second=0, microsecond=0).isoformat())
        if key in horas_ag:
            continue
        if ts < corte_raw:
            raw.append(a)

    raw.sort(key=lambda x: x.get("ts") or "")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        for r in raw:
            fh.write(json.dumps(_json_safe(r), ensure_ascii=False) + "\n")
    return len(raw)


def rotacionar_arquivo(arquivo: str) -> None:
    """Compat: agora a retenção é por tempo via agregar_e_retener."""
    agregar_e_retener(arquivo)


def gravar_snapshot(arquivo: str | None = None) -> dict[str, Any]:
    path = arquivo or ARQUIVO_PADRAO
    registro = coletar_snapshot()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(_json_safe(registro), ensure_ascii=False) + "\n")
    agregar_e_retener(path)
    return registro


def registrar_metricas_periodicas(arquivo: str | None = None) -> list[dict[str, Any]]:
    """Job django-q (~15 min): grava uma linha JSONL por VM Magalu + alertas."""
    from superadmin.capacidade_servidores import coletar_todos

    path = arquivo or ARQUIVO_PADRAO
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    registros = coletar_todos()
    # Enriquece whatsappnova com contagens agregadas (sem PII).
    try:
        from superadmin.capacidade_whatsapp import metricas_whatsapp_agregadas

        wa = metricas_whatsapp_agregadas()
        for r in registros:
            if servidor_id_registro(r) == "whatsappnova":
                r.update(wa)
    except Exception:
        pass

    with open(path, "a") as fh:
        for registro in registros:
            slim = {k: v for k, v in registro.items() if k not in ("dica", "pg_lentas")}
            fh.write(json.dumps(_json_safe(slim), ensure_ascii=False) + "\n")
    agregar_e_retener(path)

    try:
        from superadmin.capacidade_alertas import avaliar_e_registrar_alertas

        avaliar_e_registrar_alertas(registros, arquivo=path)
    except Exception:
        pass
    return registros


def _resumo_campo(pontos: list[dict[str, Any]], campo: str, campo_max: str | None = None) -> dict[str, float | None]:
    vals = [v for v in (_num(p.get(campo)) for p in pontos) if v is not None]
    max_vals = vals
    if campo_max:
        max_extra = [v for v in (_num(p.get(campo_max)) for p in pontos) if v is not None]
        max_vals = max_extra or vals
    atual = _num(pontos[-1].get(campo)) if pontos else None
    return {
        "atual": atual,
        "media": _avg(vals),
        "max": _max(max_vals),
    }


def ler_historico(
    *,
    dias: int = 7,
    arquivo: str | None = None,
    servidor: str | None = None,
) -> list[dict[str, Any]]:
    path = arquivo or ARQUIVO_PADRAO
    if not os.path.exists(path):
        return []
    dias = max(1, min(int(dias or 7), 30))
    corte = timezone.now() - timedelta(days=dias)
    sid = (servidor or "").strip() or None
    out: list[dict[str, Any]] = []
    for r in _ler_todos(path):
        ts = _parse_ts(r.get("ts") or "")
        if ts is None or ts < corte:
            continue
        rs = servidor_id_registro(r)
        if sid and rs != sid:
            continue
        out.append({**r, "servidor": rs})
    return out


def historico_completo(
    *,
    dias: int = 7,
    arquivo: str | None = None,
    servidor: str | None = None,
) -> dict[str, Any]:
    dias = max(1, min(int(dias or 7), 30))
    pontos = ler_historico(dias=dias, arquivo=arquivo, servidor=servidor)
    if not pontos:
        return {
            "dias": dias,
            "servidor": servidor or "lwksistemas-nova",
            "total": 0,
            "amostras": 0,
            "pontos": [],
            "resumo": {},
            "periodo_inicio": None,
            "periodo_fim": None,
            "dias_disponiveis": 0,
            "parcial": True,
            "desatualizado": True,
        }

    t0 = _parse_ts(pontos[0]["ts"])
    t1 = _parse_ts(pontos[-1]["ts"])
    dias_disp = round((t1 - t0).total_seconds() / 86400, 2) if t0 and t1 else 0
    # Série de CPU % para gráfico
    for p in pontos:
        if p.get("cpu_pct") is None:
            p["cpu_pct"] = cpu_pct(p)

    resumo = {
        "cpu_pct": _resumo_campo(pontos, "cpu_pct"),
        "load_5m": _resumo_campo(pontos, "load_5m", "load_5m_max"),
        "mem_usada_pct": _resumo_campo(pontos, "mem_usada_pct", "mem_usada_pct_max"),
        "disk_usada_pct": _resumo_campo(pontos, "disk_usada_pct", "disk_usada_pct_max"),
    }
    agora = timezone.now()
    desatualizado = bool(t1 and (agora - t1) > timedelta(minutes=45))
    return {
        "dias": dias,
        "servidor": servidor or "lwksistemas-nova",
        "total": len(pontos),
        "amostras": len(pontos),
        "pontos": pontos,
        "resumo": resumo,
        "periodo_inicio": pontos[0]["ts"],
        "periodo_fim": pontos[-1]["ts"],
        "dias_disponiveis": dias_disp,
        "parcial": dias_disp < (dias * 0.85) if dias > 1 else len(pontos) < 4,
        "desatualizado": desatualizado,
        "agregado": any(p.get("agregado") for p in pontos),
    }


def gravar_amostra_api(latency_ms: float, status_code: int, path: str) -> None:
    """Amostra de latência da API (middleware)."""
    os.makedirs(os.path.dirname(ARQUIVO_API) or ".", exist_ok=True)
    registro = {
        "ts": timezone.localtime(timezone.now()).isoformat(),
        "latency_ms": round(latency_ms, 1),
        "status": int(status_code),
        "path": (path or "")[:160],
    }
    with open(ARQUIVO_API, "a") as fh:
        fh.write(json.dumps(registro, ensure_ascii=False) + "\n")
    # Retém últimas linhas
    try:
        with open(ARQUIVO_API) as fh:
            linhas = fh.readlines()
        if len(linhas) > MAX_LINHAS_API:
            with open(ARQUIVO_API, "w") as fh:
                fh.writelines(linhas[-MAX_LINHAS_API:])
    except Exception:
        pass


def resumo_api_recente(horas: int = 24) -> dict[str, Any]:
    if not os.path.exists(ARQUIVO_API):
        return {
            "api_amostras": 0,
            "api_latency_media_ms": None,
            "api_latency_p95_ms": None,
            "api_5xx": 0,
            "api_rpm_estimado": None,
            "api_top_lentos": [],
        }
    corte = timezone.now() - timedelta(hours=horas)
    latencias: list[float] = []
    erros = 0
    por_path: dict[str, list[float]] = {}
    for r in _ler_todos(ARQUIVO_API):
        ts = _parse_ts(r.get("ts") or "")
        if ts is None or ts < corte:
            continue
        lat = _num(r.get("latency_ms"))
        if lat is None:
            continue
        latencias.append(lat)
        if int(r.get("status") or 0) >= 500:
            erros += 1
        p = (r.get("path") or "?")[:80]
        por_path.setdefault(p, []).append(lat)
    if not latencias:
        return {
            "api_amostras": 0,
            "api_latency_media_ms": None,
            "api_latency_p95_ms": None,
            "api_5xx": 0,
            "api_rpm_estimado": None,
            "api_top_lentos": [],
        }
    ordenada = sorted(latencias)
    p95 = ordenada[int(len(ordenada) * 0.95) - 1] if len(ordenada) >= 2 else ordenada[-1]
    top = sorted(
        (
            {"path": p, "media_ms": _avg(vals), "n": len(vals)}
            for p, vals in por_path.items()
        ),
        key=lambda x: x["media_ms"] or 0,
        reverse=True,
    )[:5]
    # Amostragem ~5% → estima rpm
    rpm = round((len(latencias) / max(horas, 1) / 60) / 0.05, 1)
    return {
        "api_amostras": len(latencias),
        "api_latency_media_ms": _avg(latencias),
        "api_latency_p95_ms": round(p95, 1),
        "api_5xx": erros,
        "api_rpm_estimado": rpm,
        "api_top_lentos": top,
    }
