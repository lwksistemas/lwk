"""Confirma pagamento PIX/boleto Asaas de uma loja e dispara senha + NFS-e.

Uso:
  python manage.py confirmar_pagamento_loja 22239255889
  python manage.py confirmar_pagamento_loja novaimagem --atalho
"""
from django.core.management.base import BaseCommand, CommandError

from superadmin.models import Loja, PagamentoLoja
from superadmin.sync_service import AsaasSyncService


class Command(BaseCommand):
    help = "Sincroniza pagamento Asaas da loja e confirma (senha provisória + NFS-e)"

    def add_arguments(self, parser):
        parser.add_argument("identificador", type=str, help="Slug ou atalho da loja")
        parser.add_argument(
            "--atalho",
            action="store_true",
            help="Buscar pelo atalho (URL amigável) em vez do slug/CNPJ",
        )

    def handle(self, *args, **options):
        ident = (options["identificador"] or "").strip()
        if options.get("atalho"):
            loja = Loja.objects.filter(atalho__iexact=ident).first()
        else:
            loja = Loja.objects.filter(slug__iexact=ident).first()
            if not loja:
                loja = Loja.objects.filter(atalho__iexact=ident).first()

        if not loja:
            raise CommandError(f"Loja '{ident}' não encontrada")

        financeiro = loja.financeiro
        self.stdout.write(f"Loja: {loja.nome} ({loja.slug})")
        self.stdout.write(f"Status pagamento: {financeiro.status_pagamento}")
        self.stdout.write(f"Asaas payment ID: {financeiro.asaas_payment_id or '—'}")
        self.stdout.write(f"Senha enviada: {financeiro.senha_enviada}")

        sync = AsaasSyncService()
        pagamentos = PagamentoLoja.objects.filter(loja=loja).exclude(asaas_payment_id="").order_by("-id")

        if not pagamentos.exists() and financeiro.asaas_payment_id:
            from superadmin.models import PagamentoLoja as PL
            pagamentos = PL.objects.filter(asaas_payment_id=financeiro.asaas_payment_id)

        if not pagamentos.exists():
            payment_id = (financeiro.asaas_payment_id or "").strip()
            if not payment_id:
                raise CommandError("Nenhum pagamento Asaas vinculado a esta loja")
            resultado = sync.asaas_service.consultar_status_pagamento(payment_id)
            if not resultado.get("success"):
                raise CommandError(resultado.get("error") or "Erro ao consultar Asaas")
            status = resultado.get("status", "")
            self.stdout.write(f"Status Asaas: {status}")
            if status in ("RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"):
                sync._process_payment_confirmed(
                    loja,
                    financeiro,
                    payment_id,
                    resultado.get("raw_payment") or {},
                )
            else:
                raise CommandError(f"Pagamento ainda não confirmado no Asaas: {status}")
        else:
            for pagamento in pagamentos[:3]:
                self.stdout.write(f"Sincronizando PagamentoLoja #{pagamento.id} ({pagamento.asaas_payment_id})…")
                sync.sync_payment_status(pagamento)

        financeiro.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f"\nConcluído — status={financeiro.status_pagamento}, "
            f"senha_enviada={financeiro.senha_enviada}",
        ))
