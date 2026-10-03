"""Resumo das métricas de capacidade coletadas (picos, médias, tendência).

Lê o JSONL gerado por registrar_metricas_capacidade e mostra, para a janela
escolhida: pico e média de load/RAM/conexões/fila, e uma leitura de folga.

Uso:
    python manage.py resumo_metricas_capacidade
    python manage.py resumo_metricas_capacidade --horas 24
"""
import json
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

ARQUIVO_PADRAO = os.path.join(getattr(settings, "MEDIA_ROOT", "/app/media"), "metricas_capacidade.jsonl")


def _num(v):
    return v if isinstance(v, (int, float)) else None


class Command(BaseCommand):
    help = "Mostra resumo (picos/médias) das métricas de capacidade."

    def add_arguments(self, parser):
        parser.add_argument("--arquivo", type=str, default=ARQUIVO_PADRAO)
        parser.add_argument("--horas", type=int, default=168, help="Janela em horas (padrão: 168 = 7 dias)")

    def handle(self, *args, **options):
        arquivo = options["arquivo"]
        horas = options["horas"]
        if not os.path.exists(arquivo):
            self.stdout.write(self.style.WARNING(f"Sem dados ainda em {arquivo}."))
            return

        corte = timezone.now() - timedelta(hours=horas)
        registros = []
        with open(arquivo) as fh:
            for linha in fh:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    r = json.loads(linha)
                    ts = datetime.fromisoformat(r["ts"])
                    if ts >= corte:
                        registros.append(r)
                except Exception:
                    continue

        if not registros:
            self.stdout.write(self.style.WARNING(f"Nenhum registro nas últimas {horas}h."))
            return

        def pico(campo):
            vals = [_num(r.get(campo)) for r in registros if _num(r.get(campo)) is not None]
            return max(vals) if vals else None

        def media(campo):
            vals = [_num(r.get(campo)) for r in registros if _num(r.get(campo)) is not None]
            return round(sum(vals) / len(vals), 1) if vals else None

        ultimo = registros[-1]
        cpus = ultimo.get("cpus") or 1
        n = len(registros)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"=== Capacidade — últimas {horas}h ({n} amostras) ===",
        ))
        self.stdout.write(f"  Servidor: {cpus} vCPU | {ultimo.get('mem_total_mb')} MB RAM")
        self.stdout.write(f"  Lojas ativas (último): {ultimo.get('lojas_ativas')}")
        self.stdout.write("")
        self.stdout.write(f"  Load 5m   — pico {pico('load_5m')} | média {media('load_5m')} | teto saudável ~{round(cpus * 0.75, 1)}")
        self.stdout.write(f"  RAM       — pico {pico('mem_usada_pct')}% | média {media('mem_usada_pct')}%")
        self.stdout.write(f"  PG conexões — pico {pico('pg_conexoes')} / {ultimo.get('pg_conexoes_max')}")
        self.stdout.write(f"  Fila django-q — pico pendente {pico('fila_pendente')} | falhas 24h (último) {ultimo.get('fila_falhas_24h')}")

        # Leitura de folga
        self.stdout.write("")
        load_pico = pico("load_5m") or 0
        ram_pico = pico("mem_usada_pct") or 0
        pg_pico = pico("pg_conexoes") or 0
        pg_max = ultimo.get("pg_conexoes_max") or 1
        alertas = []
        if load_pico > cpus * 0.75:
            alertas.append(f"Load de pico {load_pico} passou de 75% dos {cpus} vCPU — avaliar +workers ou escalar.")
        if ram_pico > 85:
            alertas.append(f"RAM de pico {ram_pico}% alta.")
        if pg_pico > pg_max * 0.8:
            alertas.append(f"Conexões Postgres no pico ({pg_pico}/{pg_max}) perto do limite — subir max_connections.")
        if alertas:
            for a in alertas:
                self.stdout.write(self.style.WARNING(f"  ⚠️ {a}"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✅ Folga confortável nos picos. Dá para crescer."))
