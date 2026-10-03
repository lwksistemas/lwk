"""Relatório de falhas de envio WhatsApp por loja.

Agrupa as falhas (WhatsAppLog.status='falhou') por MOTIVO e por NÚMERO,
ajudando a distinguir número inválido (recorrente) de erro pontual de envio.

Uso:
    python manage.py relatorio_falhas_whatsapp --slug clinicaharmonis
    python manage.py relatorio_falhas_whatsapp --slug clinicaharmonis --dias 30
    python manage.py relatorio_falhas_whatsapp            # todas as lojas ativas
    python manage.py relatorio_falhas_whatsapp --csv /tmp/falhas.csv
"""
import csv
import re
from collections import Counter, defaultdict
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from whatsapp.models import WhatsAppLog


def _motivo(response) -> str:
    """Extrai um motivo legível e normalizado do campo response do log."""
    if isinstance(response, dict):
        err = (response.get("error") or response.get("message") or "").strip()
    elif isinstance(response, str):
        err = response.strip()
    else:
        err = ""
    if not err:
        return "Sem detalhe de erro"
    low = err.lower()
    if "não encontrado no whatsapp" in low or "nao encontrado no whatsapp" in low:
        return "Número sem WhatsApp / inválido"
    if "connection closed" in low or "desconect" in low:
        return "WhatsApp Web desconectado no momento do envio"
    if "bad request" in low:
        return "Requisição recusada pela Evolution (Bad Request)"
    if "timeout" in low or "timed out" in low:
        return "Timeout na Evolution"
    # Trunca motivos longos/variáveis para agrupar
    return re.sub(r"\s+", " ", err)[:80]


class Command(BaseCommand):
    help = "Relatório de falhas de envio WhatsApp por loja (agrupado por motivo e número)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Apenas esta loja (slug ou atalho)")
        parser.add_argument("--dias", type=int, default=30, help="Janela em dias (padrão: 30)")
        parser.add_argument("--csv", type=str, help="Exporta o detalhamento para um arquivo CSV")

    def handle(self, *args, **options):
        slug = (options.get("slug") or "").strip().lower()
        dias = options["dias"]
        csv_path = options.get("csv")
        desde = timezone.now() - timedelta(days=dias)

        lojas = Loja.objects.filter(is_active=True, database_created=True)
        if slug:
            lojas = [
                loja for loja in lojas
                if slug in ((loja.slug or "").lower(), (getattr(loja, "atalho", None) or "").lower())
            ]

        csv_rows: list[dict] = []
        total_geral = 0

        for loja in lojas:
            db = getattr(loja, "database_name", None)
            if not db or not ensure_loja_database_config(db, conn_max_age=0):
                continue
            try:
                falhas = list(
                    WhatsAppLog.objects.using(db)
                    .filter(loja_id=loja.id, status="falhou", created_at__gte=desde)
                    .order_by("-created_at")
                    .values("created_at", "telefone", "mensagem", "response"),
                )
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"{loja.slug}: indisponível ({exc})"))
                continue

            if not falhas:
                continue

            total_geral += len(falhas)
            por_motivo = Counter()
            por_numero: dict[str, int] = defaultdict(int)
            for f in falhas:
                m = _motivo(f["response"])
                por_motivo[m] += 1
                por_numero[f["telefone"] or "(sem número)"] += 1
                csv_rows.append({
                    "loja": loja.nome,
                    "slug": loja.slug,
                    "data": f["created_at"].strftime("%Y-%m-%d %H:%M"),
                    "telefone": f["telefone"],
                    "motivo": m,
                    "mensagem": (f["mensagem"] or "")[:120],
                })

            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"=== {loja.nome} ({loja.slug}) — {len(falhas)} falhas nos últimos {dias} dias ===",
            ))
            self.stdout.write("  Por motivo:")
            for motivo, qtd in por_motivo.most_common():
                self.stdout.write(f"    {qtd:4d}  {motivo}")
            self.stdout.write("  Números com mais falhas:")
            for numero, qtd in sorted(por_numero.items(), key=lambda kv: -kv[1])[:10]:
                self.stdout.write(f"    {qtd:4d}  {numero}")

        self.stdout.write("")
        if total_geral == 0:
            self.stdout.write(self.style.SUCCESS(f"Nenhuma falha nos últimos {dias} dias."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Total: {total_geral} falhas."))

        if csv_path and csv_rows:
            with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=["loja", "slug", "data", "telefone", "motivo", "mensagem"])
                writer.writeheader()
                writer.writerows(csv_rows)
            self.stdout.write(self.style.SUCCESS(f"CSV salvo em {csv_path} ({len(csv_rows)} linhas)."))
