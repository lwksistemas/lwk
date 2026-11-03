"""Coleta e registra métricas de capacidade do servidor ERP.

Grava uma linha JSON por coleta em um arquivo JSONL (append), para acompanhar o
crescimento (load, RAM, disco, conexões Postgres, fila django-q, nº de lojas)
sem tocar no banco. Pensado para rodar no cron a cada 15 min.

Uso:
    python manage.py registrar_metricas_capacidade
    python manage.py registrar_metricas_capacidade --arquivo /app/media/metricas_capacidade.jsonl
"""
from django.core.management.base import BaseCommand

from superadmin.capacidade_metrics import ARQUIVO_PADRAO, gravar_snapshot


class Command(BaseCommand):
    help = "Registra métricas de capacidade do servidor (load, RAM, disco, Postgres, fila, lojas)."

    def add_arguments(self, parser):
        parser.add_argument("--arquivo", type=str, default=ARQUIVO_PADRAO)

    def handle(self, *args, **options):
        arquivo = options["arquivo"]
        try:
            registro = gravar_snapshot(arquivo)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Falha ao gravar métricas: {exc}"))
            return

        cpus = registro.get("cpus") or 1
        load5 = registro.get("load_5m")
        if load5 is not None and load5 > cpus * 0.75:
            self.stdout.write(self.style.WARNING(
                f"Load 5m {load5} alto para {cpus} vCPU — avaliar aumentar workers/escala.",
            ))
        self.stdout.write(self.style.SUCCESS(
            f"Métrica registrada: load5={load5} mem={registro.get('mem_usada_pct')}% "
            f"disk={registro.get('disk_usada_pct')}% "
            f"pg={registro.get('pg_conexoes')}/{registro.get('pg_conexoes_max')} "
            f"fila={registro.get('fila_pendente')} lojas={registro.get('lojas_ativas')}",
        ))
