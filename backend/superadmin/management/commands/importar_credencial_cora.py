"""Grava o certificado da Cora cifrado. Não imprime a chave."""

import zipfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from superadmin.models import CoraConfig


class Command(BaseCommand):
    help = "Importa client-id e o zip certificate.pem + private-key.key da Cora"

    def add_arguments(self, parser):
        parser.add_argument("--zip", required=True, help="Caminho do zip baixado na Cora")
        parser.add_argument("--client-id", required=True)

    def handle(self, *args, **options):
        caminho = Path(options["zip"])
        if not caminho.is_file():
            raise CommandError("Zip não encontrado.")
        with zipfile.ZipFile(caminho) as arquivo:
            nomes = {Path(nome).name: nome for nome in arquivo.namelist()}
            if "certificate.pem" not in nomes or "private-key.key" not in nomes:
                raise CommandError("O zip precisa ter certificate.pem e private-key.key.")
            certificado = arquivo.read(nomes["certificate.pem"]).decode("utf-8")
            chave = arquivo.read(nomes["private-key.key"]).decode("utf-8")
        if "BEGIN CERTIFICATE" not in certificado or "PRIVATE KEY" not in chave:
            raise CommandError("Certificado ou chave inválidos.")
        config = CoraConfig.get_config()
        config.client_id = options["client_id"].strip()[:80]
        config.gravar_segredo("certificate_pem", certificado)
        config.gravar_segredo("private_key_pem", chave)
        config.enabled = True
        config.save()
        self.stdout.write(self.style.SUCCESS("Credencial Cora gravada. A chave não foi exibida."))
