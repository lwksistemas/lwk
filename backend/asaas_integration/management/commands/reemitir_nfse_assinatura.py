"""Reemite NFS-e de assinatura para um pagamento já confirmado (ex.: falha E058/E061)."""
from django.core.management.base import BaseCommand, CommandError

from superadmin.models import PagamentoLoja


class Command(BaseCommand):
    help = "Reemite NFS-e de assinatura para pagamento Asaas ou loja (superadmin)"

    def add_arguments(self, parser):
        parser.add_argument("--payment-id", help="ID do pagamento no Asaas (ex.: pay_xxx)")
        parser.add_argument("--loja-slug", help="Slug ou documento da loja (usa último pagamento pago)")
        parser.add_argument("--pagamento-id", type=int, help="ID interno de PagamentoLoja")

    def handle(self, *args, **options):
        pagamento = self._resolver_pagamento(options)
        if pagamento.status != "pago":
            raise CommandError(f"Pagamento {pagamento.id} não está pago (status={pagamento.status})")

        from asaas_integration.nfse_assinatura_service import emitir_nfse_assinatura

        self.stdout.write(
            f'Emitindo NFS-e: loja={pagamento.loja.slug}, pagamento={pagamento.id}, '
            f'asaas={pagamento.asaas_payment_id or "-"}',
        )
        resultado = emitir_nfse_assinatura(pagamento)
        if resultado.get("success"):
            self.stdout.write(self.style.SUCCESS(
                f'NFS-e emitida: {resultado.get("numero_nf") or resultado.get("message")}',
            ))
        else:
            raise CommandError(resultado.get("error") or "Falha desconhecida na emissão")

    def _resolver_pagamento(self, options) -> PagamentoLoja:
        if options.get("pagamento_id"):
            try:
                return PagamentoLoja.objects.select_related("loja", "loja__owner").get(
                    id=options["pagamento_id"],
                )
            except PagamentoLoja.DoesNotExist as exc:
                raise CommandError(f'PagamentoLoja id={options["pagamento_id"]} não encontrado') from exc

        if options.get("payment_id"):
            pagamento = PagamentoLoja.objects.select_related("loja", "loja__owner").filter(
                asaas_payment_id=options["payment_id"],
            ).first()
            if not pagamento:
                raise CommandError(f'Pagamento Asaas {options["payment_id"]} não encontrado')
            return pagamento

        if options.get("loja_slug"):
            slug = options["loja_slug"]
            from superadmin.models import Loja
            loja = Loja.objects.filter(slug=slug).first()
            if not loja:
                loja = Loja.objects.filter(atalho__iexact=slug).first()
            if not loja:
                doc = slug.replace(".", "").replace("/", "").replace("-", "")
                loja = Loja.objects.filter(cpf_cnpj__icontains=doc).first()
            if not loja:
                raise CommandError(f"Loja não encontrada: {slug}")
            pagamento = (
                PagamentoLoja.objects.select_related("loja", "loja__owner")
                .filter(loja=loja, status="pago")
                .order_by("-data_pagamento", "-id")
                .first()
            )
            if not pagamento:
                raise CommandError(f"Nenhum pagamento pago encontrado para loja {loja.slug}")
            return pagamento

        raise CommandError("Informe --payment-id, --pagamento-id ou --loja-slug")
