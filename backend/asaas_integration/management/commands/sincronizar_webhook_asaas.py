"""Grava o token do webhook LWK no cadastro Asaas (authToken)."""
from django.core.management.base import BaseCommand

from asaas_integration.webhook_asaas_sync import sincronizar_token_webhook_asaas


class Command(BaseCommand):
    help = "Alinha o authToken do webhook LWK no painel Asaas com o token gravado no LWK"

    def handle(self, *args, **options):
        out = sincronizar_token_webhook_asaas()
        if out.get("success"):
            self.stdout.write(self.style.SUCCESS(
                f"Token gravado no webhook Asaas (id={out.get('webhook_id')})",
            ))
            return
        self.stderr.write(self.style.ERROR(out.get("error") or "Falha ao sincronizar webhook Asaas"))
