"""Alertas de capacidade (JSON state + e-mail com cooldown)."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.utils import timezone

from superadmin.capacidade_metrics import (
    ARQUIVO_PADRAO,
    _parse_ts,
    cpu_pct,
    ler_historico,
    servidor_id_registro,
)

logger = logging.getLogger(__name__)

ARQUIVO_ALERTAS = os.path.join(
    getattr(settings, "MEDIA_ROOT", "/app/media"),
    "alertas_capacidade.json",
)
COOLDOWN = timedelta(hours=6)
STREAK = 3  # ~45 min com coleta a cada 15 min


def _agora() -> datetime:
    return timezone.now()


def _carregar_estado() -> dict[str, Any]:
    if not os.path.exists(ARQUIVO_ALERTAS):
        return {"ativos": [], "enviados": {}}
    try:
        with open(ARQUIVO_ALERTAS) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {"ativos": [], "enviados": {}}
        data.setdefault("ativos", [])
        data.setdefault("enviados", {})
        return data
    except Exception:
        return {"ativos": [], "enviados": {}}


def _salvar_estado(estado: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(ARQUIVO_ALERTAS) or ".", exist_ok=True)
    with open(ARQUIVO_ALERTAS, "w") as fh:
        json.dump(estado, fh, ensure_ascii=False, indent=2)


def _destinatarios() -> list[str]:
    emails = list(getattr(settings, "SECURITY_NOTIFICATION_EMAILS", []) or [])
    if not emails and getattr(settings, "ADMINS", None):
        emails = [email for _name, email in settings.ADMINS if email]
    env = (os.environ.get("SUPERADMIN_EMAIL") or "").strip()
    if env and env not in emails:
        emails.append(env)
    return [e for e in emails if e]


def _pode_notificar(estado: dict[str, Any], chave: str) -> bool:
    raw = (estado.get("enviados") or {}).get(chave)
    if not raw:
        return True
    ts = _parse_ts(raw)
    if ts is None:
        return True
    return _agora() - ts >= COOLDOWN


def _notificar(assunto: str, corpo: str) -> bool:
    destinatarios = _destinatarios()
    if not destinatarios:
        logger.info("Capacidade: sem destinatários de e-mail para alerta")
        return False
    try:
        from core.email_delivery import send_system_mail

        send_system_mail(assunto, corpo, destinatarios, fail_silently=True)
        return True
    except Exception:
        logger.exception("Falha ao e-mail de capacidade")
        return False


def _streak_acima(pontos: list[dict[str, Any]], campo: str, limiar: float, *, usar_cpu: bool = False) -> bool:
    if len(pontos) < STREAK:
        return False
    recentes = pontos[-STREAK:]
    for p in recentes:
        if usar_cpu:
            v = cpu_pct(p)
        else:
            from superadmin.capacidade_metrics import _num

            v = _num(p.get(campo))
        if v is None or v < limiar:
            return False
    return True


def _avaliar_registro(r: dict[str, Any], historico_sid: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sid = servidor_id_registro(r)
    alertas: list[dict[str, Any]] = []
    status = (r.get("status") or "ok").lower()
    if status == "unavailable":
        alertas.append({
            "servidor": sid,
            "tipo": "indisponivel",
            "nivel": "critico",
            "mensagem": f"{sid} sem resposta de métricas.",
        })
        return alertas

    from superadmin.capacidade_metrics import _num

    disk = _num(r.get("disk_usada_pct"))
    if disk is not None:
        if disk >= 85:
            alertas.append({
                "servidor": sid,
                "tipo": "disco",
                "nivel": "critico",
                "mensagem": f"{sid}: disco em {disk}% (crítico ≥85%).",
            })
        elif disk >= 70:
            alertas.append({
                "servidor": sid,
                "tipo": "disco",
                "nivel": "atencao",
                "mensagem": f"{sid}: disco em {disk}% (atenção ≥70%).",
            })

    if _streak_acima(historico_sid, "mem_usada_pct", 85):
        alertas.append({
            "servidor": sid,
            "tipo": "ram",
            "nivel": "critico",
            "mensagem": f"{sid}: RAM ≥85% nas últimas {STREAK} amostras.",
        })
    elif _streak_acima(historico_sid, "mem_usada_pct", 70):
        alertas.append({
            "servidor": sid,
            "tipo": "ram",
            "nivel": "atencao",
            "mensagem": f"{sid}: RAM ≥70% nas últimas {STREAK} amostras.",
        })

    if _streak_acima(historico_sid, "cpu_pct", 85, usar_cpu=True):
        alertas.append({
            "servidor": sid,
            "tipo": "cpu",
            "nivel": "critico",
            "mensagem": f"{sid}: CPU (load) ≥85% sustentado (~45 min).",
        })
    elif _streak_acima(historico_sid, "cpu_pct", 70, usar_cpu=True):
        alertas.append({
            "servidor": sid,
            "tipo": "cpu",
            "nivel": "atencao",
            "mensagem": f"{sid}: CPU (load) ≥70% sustentado (~45 min).",
        })

    fila = _num(r.get("fila_pendente"))
    if fila is not None and fila >= 200:
        alertas.append({
            "servidor": sid,
            "tipo": "fila",
            "nivel": "critico",
            "mensagem": f"{sid}: fila django-q com {int(fila)} pendentes.",
        })
    elif fila is not None and fila >= 50:
        alertas.append({
            "servidor": sid,
            "tipo": "fila",
            "nivel": "atencao",
            "mensagem": f"{sid}: fila django-q acumulando ({int(fila)} pendentes).",
        })
    return alertas


def avaliar_e_registrar_alertas(registros: list[dict[str, Any]], *, arquivo: str | None = None) -> list[dict[str, Any]]:
    path = arquivo or ARQUIVO_PADRAO
    estado = _carregar_estado()
    ativos: list[dict[str, Any]] = []
    agora_iso = timezone.localtime(_agora()).isoformat()

    # Coleta parada: último raw no arquivo
    todos = ler_historico(dias=2, arquivo=path)
    if todos:
        ultimo_ts = _parse_ts(todos[-1].get("ts") or "")
        if ultimo_ts and _agora() - ultimo_ts > timedelta(minutes=45):
            ativos.append({
                "servidor": "todos",
                "tipo": "coleta_parada",
                "nivel": "critico",
                "mensagem": "Coleta de capacidade parada (>45 min sem amostra).",
                "ts": agora_iso,
            })

    for r in registros:
        sid = servidor_id_registro(r)
        hist = [p for p in todos if servidor_id_registro(p) == sid][-STREAK:]
        # Inclui o registro atual no streak se ainda não estiver
        if not hist or hist[-1].get("ts") != r.get("ts"):
            hist = hist + [r]
        for alerta in _avaliar_registro(r, hist):
            alerta["ts"] = agora_iso
            ativos.append(alerta)

    # Notifica novos com cooldown
    for alerta in ativos:
        chave = f"{alerta['servidor']}:{alerta['tipo']}:{alerta['nivel']}"
        if not _pode_notificar(estado, chave):
            continue
        ok = _notificar(
            f"[LWK Capacidade] {alerta['nivel'].upper()} — {alerta['servidor']}",
            f"{alerta['mensagem']}\n\nPainel: https://lwksistemas.com.br/superadmin/dashboard/capacidade\n",
        )
        if ok:
            estado.setdefault("enviados", {})[chave] = agora_iso

    estado["ativos"] = ativos
    estado["atualizado_em"] = agora_iso
    _salvar_estado(estado)
    return ativos


def listar_alertas_ativos() -> dict[str, Any]:
    estado = _carregar_estado()
    return {
        "ativos": estado.get("ativos") or [],
        "atualizado_em": estado.get("atualizado_em"),
    }
