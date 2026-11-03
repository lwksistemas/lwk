"""Amostra latência da API (~5%) para o painel de capacidade."""
from __future__ import annotations

import random
import time

SAMPLE_RATE = 0.05


class CapacidadeApiLatencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = getattr(request, "path", "") or ""
        if not path.startswith("/api/"):
            return self.get_response(request)
        # Evita ruído de health/static
        if any(x in path for x in ("/health", "/static", "/media")):
            return self.get_response(request)
        amostrar = random.random() < SAMPLE_RATE
        inicio = time.perf_counter() if amostrar else None
        response = self.get_response(request)
        if amostrar and inicio is not None:
            try:
                from superadmin.capacidade_metrics import gravar_amostra_api

                ms = (time.perf_counter() - inicio) * 1000
                gravar_amostra_api(ms, getattr(response, "status_code", 0) or 0, path)
            except Exception:
                pass
        return response
