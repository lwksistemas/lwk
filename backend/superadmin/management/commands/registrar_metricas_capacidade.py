"""Coleta e registra métricas de capacidade das VMs Magalu.

Grava uma linha JSON por servidor em JSONL (append). Cron ~15 min.

Uso:
    python manage.py registrar_metricas_capacidade
"""
from django.core.management.base import BaseCommand

from superadmin.capacidade_metrics import ARQUIVO_PADRAO, rotacionar_arquivo
from superadmin.capacidade_servidores import coletar_todos
import json
import os


class Command(BaseCommand):
    help = "Registra métricas de capacidade (lwksistemas-nova, midia01, whatsappnova)."

    def add_arguments(self, parser):
        parser.add_argument("--arquivo", type=str, default=ARQUIVO_PADRAO)

    def handle(self, *args, **options):
        arquivo = options["arquivo"]
        try:
            os.makedirs(os.path.dirname(arquivo) or ".", exist_ok=True)
            registros = coletar_todos()
            with open(arquivo, "a") as fh:
                for registro in registros:
                    # Não persistir erro/dica longos a cada ciclo se unavailable — mantém status.
                    slim = {k: v for k, v in registro.items() if k not in ("dica",)}
                    fh.write(json.dumps(slim, ensure_ascii=False) + "\n")
            rotacionar_arquivo(arquivo)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Falha ao gravar métricas: {exc}"))
            return

        for registro in registros:
            nome = registro.get("nome") or registro.get("servidor")
            st = registro.get("status") or "ok"
            self.stdout.write(
                f"{nome}: status={st} load5={registro.get('load_5m')} "
                f"mem={registro.get('mem_usada_pct')}% disk={registro.get('disk_usada_pct')}%"
            )
        self.stdout.write(self.style.SUCCESS(f"Métricas registradas ({len(registros)} servidores)."))
