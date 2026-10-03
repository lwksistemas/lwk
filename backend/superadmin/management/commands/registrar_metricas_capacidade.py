"""Coleta e registra métricas de capacidade do servidor ERP.

Grava uma linha JSON por coleta em um arquivo JSONL (append), para acompanhar o
crescimento (load, RAM, conexões Postgres, fila django-q, nº de lojas) sem tocar
no banco. Pensado para rodar no cron a cada 15 min.

Uso:
    python manage.py registrar_metricas_capacidade
    python manage.py registrar_metricas_capacidade --arquivo /app/media/metricas_capacidade.jsonl
"""
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

# Mantém o arquivo enxuto: ~2.900 linhas = ~30 dias a cada 15 min.
MAX_LINHAS = 3000
ARQUIVO_PADRAO = os.path.join(getattr(settings, "MEDIA_ROOT", "/app/media"), "metricas_capacidade.jsonl")


class Command(BaseCommand):
    help = "Registra métricas de capacidade do servidor (load, RAM, Postgres, fila, lojas)."

    def add_arguments(self, parser):
        parser.add_argument("--arquivo", type=str, default=ARQUIVO_PADRAO)

    def _load_average(self):
        try:
            l1, l5, l15 = os.getloadavg()
            return {"load_1m": round(l1, 2), "load_5m": round(l5, 2), "load_15m": round(l15, 2)}
        except (OSError, AttributeError):
            return {"load_1m": None, "load_5m": None, "load_15m": None}

    def _memoria(self):
        """Lê /proc/meminfo (MemTotal/MemAvailable) em MB. Best-effort."""
        try:
            info = {}
            with open("/proc/meminfo") as fh:
                for linha in fh:
                    partes = linha.split(":")
                    if len(partes) == 2:
                        info[partes[0].strip()] = int(partes[1].strip().split()[0])  # kB
            total = info.get("MemTotal", 0) // 1024
            disp = info.get("MemAvailable", 0) // 1024
            usada = total - disp
            pct = round(usada / total * 100, 1) if total else None
            return {"mem_total_mb": total, "mem_usada_mb": usada, "mem_usada_pct": pct}
        except Exception:
            return {"mem_total_mb": None, "mem_usada_mb": None, "mem_usada_pct": None}

    def _cpus(self):
        try:
            return os.cpu_count()
        except Exception:
            return None

    def _postgres(self):
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT count(*) FROM pg_stat_activity")
                ativas = cur.fetchone()[0]
                cur.execute("SELECT setting::int FROM pg_settings WHERE name = 'max_connections'")
                maxc = cur.fetchone()[0]
            return {"pg_conexoes": ativas, "pg_conexoes_max": maxc}
        except Exception:
            return {"pg_conexoes": None, "pg_conexoes_max": None}

    def _fila(self):
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

    def _lojas(self):
        try:
            from superadmin.models import Loja
            total = Loja.objects.count()
            ativas = Loja.objects.filter(is_active=True).count()
            return {"lojas_total": total, "lojas_ativas": ativas}
        except Exception:
            return {"lojas_total": None, "lojas_ativas": None}

    def _rotacionar(self, arquivo):
        """Mantém no máximo MAX_LINHAS (descarta as mais antigas)."""
        try:
            if not os.path.exists(arquivo):
                return
            with open(arquivo) as fh:
                linhas = fh.readlines()
            if len(linhas) > MAX_LINHAS:
                with open(arquivo, "w") as fh:
                    fh.writelines(linhas[-MAX_LINHAS:])
        except Exception as exc:
            self.stderr.write(f"rotação falhou: {exc}")

    def handle(self, *args, **options):
        arquivo = options["arquivo"]
        registro = {
            "ts": timezone.localtime(timezone.now()).isoformat(),
            "cpus": self._cpus(),
            **self._load_average(),
            **self._memoria(),
            **self._postgres(),
            **self._fila(),
            **self._lojas(),
        }

        try:
            os.makedirs(os.path.dirname(arquivo), exist_ok=True)
            with open(arquivo, "a") as fh:
                fh.write(json.dumps(registro, ensure_ascii=False) + "\n")
            self._rotacionar(arquivo)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Falha ao gravar métricas: {exc}"))
            return

        # Alerta leve no log quando load passa de ~75% dos núcleos (sinal de escalar).
        cpus = registro.get("cpus") or 1
        load5 = registro.get("load_5m")
        if load5 is not None and load5 > cpus * 0.75:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Load 5m {load5} alto para {cpus} vCPU — avaliar aumentar workers/escala.",
            ))
        self.stdout.write(self.style.SUCCESS(
            f"Métrica registrada: load5={load5} mem={registro.get('mem_usada_pct')}% "
            f"pg={registro.get('pg_conexoes')}/{registro.get('pg_conexoes_max')} "
            f"fila={registro.get('fila_pendente')} lojas={registro.get('lojas_ativas')}",
        ))
