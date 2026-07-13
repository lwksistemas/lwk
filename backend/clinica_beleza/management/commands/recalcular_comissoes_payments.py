"""Recalcula comissao_valor/comissao_percentual nos Payments com base nas regras atuais.

Uso:
    python manage.py recalcular_comissoes_payments
    python manage.py recalcular_comissoes_payments --slug beleza
"""
from contextlib import suppress
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.comissao_relatorio_service import calcular_comissao_payment_atendimento
from clinica_beleza.models import Consulta, Payment
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = "Recalcula comissões gravadas em Payment (financeiro da clínica)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        total_atualizados = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue
            if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f"  skip {loja.slug}: DB não configurado"))
                continue

            set_current_tenant_db(loja.database_name)
            set_current_loja_id(loja.id)

            consulta_map = {
                c.appointment_id: c
                for c in Consulta.objects.select_related("local_atendimento", "procedure").all()
            }
            atualizados = 0
            payments = Payment.objects.select_related(
                "appointment__professional", "appointment__procedure",
            ).prefetch_related("appointment__appointment_procedures__procedure")

            for payment in payments:
                appt = payment.appointment
                if not appt:
                    continue
                amount = Decimal(str(payment.amount or 0))
                consulta = consulta_map.get(appt.id)
                pct, val = calcular_comissao_payment_atendimento(
                    appointment=appt,
                    consulta=consulta,
                    amount=amount,
                )
                if payment.comissao_percentual != pct or payment.comissao_valor != val:
                    Payment.objects.filter(pk=payment.pk).update(
                        comissao_percentual=pct,
                        comissao_valor=val,
                    )
                    atualizados += 1

            total_atualizados += atualizados
            self.stdout.write(self.style.SUCCESS(
                f"  {loja.slug}: {atualizados} payment(s) atualizado(s)",
            ))
            with suppress(Exception):
                connections[loja.database_name].close()

        self.stdout.write(self.style.SUCCESS(f"Concluído: {total_atualizados} payment(s) no total."))
