"""Métricas de host da VM whatsappnova (Magalu BV2-4-100).

Exposto só em loopback; o nginx publica /host-metrics com Bearer token.
"""
from __future__ import annotations

import hmac
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)
API_TOKEN = (os.environ.get("CAPACIDADE_HOST_TOKEN") or os.environ.get("MEDIA_API_TOKEN") or "").strip()
DISK_PATH = os.environ.get("CAPACIDADE_DISK_PATH", "/")
PROC = "/host/proc" if os.path.isdir("/host/proc") else "/proc"


def _load_mem() -> dict:
    out: dict = {}
    try:
        with open(f"{PROC}/loadavg") as fh:
            parts = fh.read().split()
        out["load_1m"] = round(float(parts[0]), 2)
        out["load_5m"] = round(float(parts[1]), 2)
        out["load_15m"] = round(float(parts[2]), 2)
    except (OSError, IndexError, ValueError):
        try:
            l1, l5, l15 = os.getloadavg()
            out["load_1m"] = round(l1, 2)
            out["load_5m"] = round(l5, 2)
            out["load_15m"] = round(l15, 2)
        except (OSError, AttributeError):
            pass
    try:
        out["cpus"] = os.cpu_count()
    except Exception:
        pass
    try:
        info = {}
        with open(f"{PROC}/meminfo") as fh:
            for linha in fh:
                partes = linha.split(":")
                if len(partes) == 2:
                    info[partes[0].strip()] = int(partes[1].strip().split()[0])
        total = info.get("MemTotal", 0) // 1024
        disp = info.get("MemAvailable", 0) // 1024
        usada = total - disp
        out["mem_total_mb"] = total
        out["mem_usada_mb"] = usada
        out["mem_usada_pct"] = round(usada / total * 100, 1) if total else None
    except OSError:
        pass
    return out


def _disco(path: str) -> dict:
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        livre = st.f_bavail * st.f_frsize
        usada = total - livre
        return {
            "disk_total_gb": round(total / (1024**3), 1),
            "disk_livre_gb": round(livre / (1024**3), 1),
            "disk_usada_gb": round(usada / (1024**3), 1),
            "disk_usada_pct": round((usada / total) * 100, 1) if total else None,
            "free_gb": round(livre / (1024**3), 1),
            "total_gb": round(total / (1024**3), 1),
            "used_gb": round(usada / (1024**3), 1),
            "used_pct": round((usada / total) * 100, 1) if total else None,
        }
    except OSError:
        return {}


@app.get("/host-metrics")
@app.get("/health")
def host_metrics():
    header = request.headers.get("Authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    if not API_TOKEN or not token or not hmac.compare_digest(token, API_TOKEN):
        return jsonify({"status": "unauthorized"}), 401
    corpo = {
        "status": "ok",
        "servidor": "whatsappnova",
        "nome": "whatsappnova",
        "ts": datetime.now(timezone.utc).astimezone().isoformat(),
        **_load_mem(),
        **_disco(DISK_PATH),
    }
    return jsonify(corpo)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100)
