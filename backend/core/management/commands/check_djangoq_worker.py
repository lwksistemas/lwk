"""Verifica se o worker Django-Q (qcluster) está ativo e saudável.

Uso:
    python manage.py check_djangoq_worker
    python manage.py check_djangoq_worker --warn-backlog 100
    python manage.py check_djangoq_worker --critical-backlog 500
"""
from __future__ import annotations

import sys

from django.core.management.base import BaseCommand

from core.task_queue import queue_health_level, queue_status


class Command(BaseCommand):
    help = "Verifica saúde do worker Django-Q e fila de tarefas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--warn-backlog",
            type=int,
            default=100,
            help="Número de tarefas na fila para considerar degraded (padrão: 100).",
        )
        parser.add_argument(
            "--critical-backlog",
            type=int,
            default=500,
            help="Número de tarefas na fila para considerar unhealthy (padrão: 500).",
        )
        parser.add_argument(
            "--exit-code",
            action="store_true",
            default=False,
            help="Retorna código de saída 1 se fila não estiver saudável.",
        )

    def handle(self, *args, **options):
        status = queue_status()
        health = queue_health_level(status)

        self.stdout.write(f"Fila habilitada: {status.get('enabled', False)}")
        self.stdout.write(f"Broker: {status.get('broker', 'unknown')}")
        self.stdout.write(f"Papel (role): {status.get('role', 'unknown')}")
        self.stdout.write(f"Tarefas na fila: {status.get('queued', 'N/A')}")
        self.stdout.write(f"Clusters ativos: {status.get('clusters', 'N/A')}")
        self.stdout.write(f"Workers vivos: {status.get('workers_alive', 'N/A')}")

        failures = status.get("failures_24h")
        if failures is not None:
            self.stdout.write(f"Falhas 24h: {failures}")

        if status.get("error"):
            self.stdout.write(self.style.ERROR(f"Erro ao consultar fila: {status['error']}"))

        if not status.get("enabled"):
            self.stdout.write(self.style.WARNING("Fila Django-Q desabilitada (USE_TASK_QUEUE=false)."))
            return

        if status.get("workers_alive", 0) == 0:
            self.stdout.write(
                self.style.ERROR(
                    "⚠️  Nenhum worker Django-Q ativo. Schedules (backup, notificações, etc.) não estão rodando."
                )
            )
            if options["exit_code"]:
                sys.exit(1)
            return

        if health == "unhealthy":
            self.stdout.write(
                self.style.ERROR(
                    f"⚠️  Fila unhealthy: {status.get('queued', 0)} tarefas acumuladas."
                )
            )
            if options["exit_code"]:
                sys.exit(1)
        elif health == "degraded":
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Fila degraded: {status.get('queued', 0)} tarefas acumuladas."
                )
            )
            if options["exit_code"]:
                sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("✅ Worker Django-Q ativo e fila saudável."))
