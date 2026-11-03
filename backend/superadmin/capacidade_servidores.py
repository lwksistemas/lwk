"""Inventário Magalu Cloud + coleta remota de capacidade por VM."""
from __future__ import annotations

import logging
import os
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

from .capacidade_metrics import coletar_snapshot

logger = logging.getLogger(__name__)

# Nomes = exatamente como no console Magalu (virtual-machine).
SERVIDORES: list[dict[str, Any]] = [
    {
        "id": "lwksistemas-nova",
        "nome": "lwksistemas-nova",
        "papel": "API, ERP, Postgres e frontends",
        "tipo_magalu": "BV8-16-150",
        "ipv4": "201.23.81.50",
        "fonte": "local",
    },
    {
        "id": "midia01",
        "nome": "midia01",
        "papel": "Servidor de mídia (imagens/PDFs)",
        "tipo_magalu": "BV1-4-100",
        "ipv4": "201.23.87.251",
        "fonte": "midia",
    },
    {
        "id": "whatsappnova",
        "nome": "whatsappnova",
        "papel": "Evolution API (WhatsApp)",
        "tipo_magalu": "BV2-4-100",
        "ipv4": "169.150.0.111",
        "fonte": "whatsapp",
    },
]

SERVIDOR_IDS = {s["id"] for s in SERVIDORES}


def listar_servidores() -> list[dict[str, Any]]:
    return [
        {
            "id": s["id"],
            "nome": s["nome"],
            "papel": s["papel"],
            "tipo_magalu": s["tipo_magalu"],
            "ipv4": s["ipv4"],
        }
        for s in SERVIDORES
    ]


def _meta(servidor: dict[str, Any]) -> dict[str, Any]:
    return {
        "servidor": servidor["id"],
        "nome": servidor["nome"],
        "papel": servidor["papel"],
        "tipo_magalu": servidor["tipo_magalu"],
        "ipv4": servidor["ipv4"],
    }


def _token_capacidade() -> str:
    from core.media_storage import MEDIA_API_TOKEN

    return (
        (getattr(settings, "CAPACIDADE_HOST_TOKEN", None) or "").strip()
        or (os.environ.get("CAPACIDADE_HOST_TOKEN") or "").strip()
        or (MEDIA_API_TOKEN or "").strip()
    )


def _normalizar_remoto(data: dict[str, Any], servidor: dict[str, Any]) -> dict[str, Any]:
    """Unifica shape do /health da mídia e do host-metrics do WhatsApp."""
    disk_pct = data.get("disk_usada_pct")
    if disk_pct is None:
        disk_pct = data.get("used_pct")
    livre = data.get("disk_livre_gb")
    if livre is None:
        livre = data.get("free_gb")
    total = data.get("disk_total_gb")
    if total is None:
        total = data.get("total_gb")
    usada_gb = data.get("disk_usada_gb")
    if usada_gb is None:
        usada_gb = data.get("used_gb")
    return {
        "ts": data.get("ts") or timezone.localtime(timezone.now()).isoformat(),
        "host": servidor["id"],
        **_meta(servidor),
        "cpus": data.get("cpus"),
        "load_1m": data.get("load_1m"),
        "load_5m": data.get("load_5m"),
        "load_15m": data.get("load_15m"),
        "mem_total_mb": data.get("mem_total_mb"),
        "mem_usada_mb": data.get("mem_usada_mb"),
        "mem_usada_pct": data.get("mem_usada_pct"),
        "disk_total_gb": total,
        "disk_livre_gb": livre,
        "disk_usada_gb": usada_gb,
        "disk_usada_pct": disk_pct,
        "tenants": data.get("tenants"),
        "status": data.get("status") or "ok",
        "fonte": servidor["fonte"],
    }


def _get_json(url: str, token: str) -> dict[str, Any]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=8)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


def coletar_midia01() -> dict[str, Any]:
    servidor = next(s for s in SERVIDORES if s["id"] == "midia01")
    base = (getattr(settings, "MEDIA_SERVER_URL", None) or "https://media.lwksistemas.com.br").rstrip("/")
    url = f"{base}/health"
    token = _token_capacidade()
    try:
        data = _get_json(url, token)
        if not token or (data.get("free_gb") is None and data.get("used_pct") is None and data.get("cpus") is None):
            # Health público sem token — sem métricas de host.
            return {
                **_meta(servidor),
                "ts": timezone.localtime(timezone.now()).isoformat(),
                "status": "partial",
                "error": "Token de mídia ausente ou health sem métricas de host",
                "fonte": "midia",
            }
        return _normalizar_remoto(data, servidor)
    except Exception as e:
        logger.warning("coleta midia01: %s", e)
        return {
            **_meta(servidor),
            "ts": timezone.localtime(timezone.now()).isoformat(),
            "status": "unavailable",
            "error": str(e),
            "fonte": "midia",
        }


def coletar_whatsappnova() -> dict[str, Any]:
    servidor = next(s for s in SERVIDORES if s["id"] == "whatsappnova")
    base = (
        getattr(settings, "CAPACIDADE_WHATSAPP_URL", None)
        or getattr(settings, "EVOLUTION_API_URL", None)
        or "https://evolution.lwksistemas.com.br"
    ).rstrip("/")
    # Preferência: /host-metrics (agente); fallback documentado.
    url = f"{base}/host-metrics"
    token = (
        (getattr(settings, "CAPACIDADE_WHATSAPP_TOKEN", None) or "").strip()
        or _token_capacidade()
    )
    try:
        data = _get_json(url, token)
        return _normalizar_remoto(data, servidor)
    except Exception as e:
        logger.warning("coleta whatsappnova: %s", e)
        return {
            **_meta(servidor),
            "ts": timezone.localtime(timezone.now()).isoformat(),
            "status": "unavailable",
            "error": str(e),
            "fonte": "whatsapp",
            "dica": "Suba o serviço host-metrics na VM whatsappnova (deploy/evolution/host-metrics).",
        }


def coletar_lwksistemas_nova() -> dict[str, Any]:
    servidor = next(s for s in SERVIDORES if s["id"] == "lwksistemas-nova")
    snap = coletar_snapshot()
    snap.update(_meta(servidor))
    snap["fonte"] = "local"
    snap["status"] = "ok"
    return snap


def coletar_por_servidor(servidor_id: str) -> dict[str, Any]:
    sid = (servidor_id or "lwksistemas-nova").strip()
    if sid not in SERVIDOR_IDS:
        raise ValueError(f"Servidor desconhecido: {servidor_id}")
    if sid == "midia01":
        return coletar_midia01()
    if sid == "whatsappnova":
        return coletar_whatsappnova()
    return coletar_lwksistemas_nova()


def coletar_todos() -> list[dict[str, Any]]:
    return [coletar_por_servidor(s["id"]) for s in SERVIDORES]
