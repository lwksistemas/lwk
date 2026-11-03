"""Coleta e leitura de métricas de capacidade do host da API (JSONL + snapshot)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.db import connection
from django.utils import timezone

MAX_LINHAS = 3000
ARQUIVO_PADRAO = os.path.join(
    getattr(settings, "MEDIA_ROOT", "/app/media"),
    "metricas_capacidade.jsonl",
)


def arquivo_metricas() -> str:
    return ARQUIVO_PADRAO


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
    """Uso de disco via statvfs (GB e %)."""
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
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT count(*) FROM pg_stat_activity")
            ativas = cur.fetchone()[0]
            cur.execute("SELECT setting::int FROM pg_settings WHERE name = 'max_connections'")
            maxc = cur.fetchone()[0]
        return {"pg_conexoes": ativas, "pg_conexoes_max": maxc}
    except Exception:
        return {"pg_conexoes": None, "pg_conexoes_max": None}


def _fila() -> dict[str, Any]:
    try:
        from core.task_queue import queue_status

        st = queue_status()
        return {
            "fila_pendente": st.get("queued"),
            "fila_workers": st.get("workers_alive"),
            "fila_falhas_24h": st.get("failures_24h"),
        }
    except Exception:
        return {"fila_pendente": None, "fila_workers": None, "fila_falhas_24h": None}


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
    # Se MEDIA_ROOT está no mesmo filesystem, não duplicar campos.
    mesmo_fs = (
        disco_raiz.get("disk_total_gb") is not None
        and disco_raiz.get("disk_total_gb") == disco_media.get("disk_total_gb")
        and disco_raiz.get("disk_livre_gb") == disco_media.get("disk_livre_gb")
    )
    registro: dict[str, Any] = {
        "ts": timezone.localtime(timezone.now()).isoformat(),
        "host": "api",
        "cpus": _cpus(),
        **_load_average(),
        **_memoria(),
        **disco_raiz,
        **_postgres(),
        **_fila(),
        **_lojas(),
    }
    if not mesmo_fs:
        registro["disk_media_path"] = disco_media.get("disk_path")
        registro["disk_media_total_gb"] = disco_media.get("disk_total_gb")
        registro["disk_media_livre_gb"] = disco_media.get("disk_livre_gb")
        registro["disk_media_usada_pct"] = disco_media.get("disk_usada_pct")
    return registro


def rotacionar_arquivo(arquivo: str) -> None:
    if not os.path.exists(arquivo):
        return
    with open(arquivo) as fh:
        linhas = fh.readlines()
    if len(linhas) > MAX_LINHAS:
        with open(arquivo, "w") as fh:
            fh.writelines(linhas[-MAX_LINHAS:])


def gravar_snapshot(arquivo: str | None = None) -> dict[str, Any]:
    path = arquivo or ARQUIVO_PADRAO
    registro = coletar_snapshot()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(registro, ensure_ascii=False) + "\n")
    rotacionar_arquivo(path)
    return registro


def ler_historico(*, dias: int = 7, arquivo: str | None = None) -> list[dict[str, Any]]:
    path = arquivo or ARQUIVO_PADRAO
    if not os.path.exists(path):
        return []
    dias = max(1, min(int(dias or 7), 30))
    corte = timezone.now() - timedelta(days=dias)
    out: list[dict[str, Any]] = []
    with open(path) as fh:
        for linha in fh:
            linha = linha.strip()
            if not linha:
                continue
            try:
                r = json.loads(linha)
                ts_raw = r.get("ts")
                if not ts_raw:
                    continue
                ts = datetime.fromisoformat(ts_raw)
                if timezone.is_naive(ts):
                    ts = timezone.make_aware(ts, timezone.get_current_timezone())
                if ts >= corte:
                    out.append(r)
            except Exception:
                continue
    return out
