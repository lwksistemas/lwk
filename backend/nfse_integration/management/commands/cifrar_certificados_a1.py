"""Cifra o .pfx das duas empresas que emitem boleto e nota: LWK Sistemas e Felix Representações.

As outras lojas não entram. O código novo lê blob cifrado e blob antigo.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.utils import ProgrammingError

from core.db_config import ensure_loja_database_config
from core.encryption import bytes_cifrados, encrypt_bytes
from superadmin.models import Loja


def cifrar_campos(obj, campos, using: str) -> int:
    alterados = []
    for campo in campos:
        raw = getattr(obj, campo, None)
        if not raw:
            continue
        data = bytes(raw)
        if not data or bytes_cifrados(data):
            continue
        setattr(obj, campo, encrypt_bytes(data))
        alterados.append(campo)
    if not alterados:
        return 0
    obj.save(using=using, update_fields=alterados)
    return 1


class Command(BaseCommand):
    help = "Cifra o certificado A1 da LWK Sistemas e da Felix Representações."

    def handle(self, *args, **options):
        total = self._lwk() + self._felix()
        self.stdout.write(self.style.SUCCESS(f"Certificados cifrados: {total}"))

    def _lwk(self) -> int:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig

        n = 0
        for config in SuperadminNFSeConfig.objects.using("default").all():
            n += cifrar_campos(
                config,
                ("nacional_certificado", "issnet_certificado"),
                "default",
            )
        self.stdout.write(f"LWK Sistemas: {n}")
        return n

    def _felix(self) -> int:
        lojas = list(
            Loja.objects.filter(is_active=True, database_created=True).filter(
                Q(nome__icontains="felix") & Q(nome__icontains="represent"),
            ),
        )
        if not lojas:
            self.stdout.write(self.style.WARNING("Felix Representações não encontrada. Nada cifrado nela."))
            return 0
        if len(lojas) > 1:
            nomes = ", ".join(loja.nome for loja in lojas)
            self.stdout.write(self.style.ERROR(f"Mais de uma loja Felix: {nomes}. Nada cifrado."))
            return 0
        loja = lojas[0]
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            self.stdout.write(self.style.ERROR(f"{loja.nome}: banco indisponível"))
            return 0
        try:
            from crm_vendas.models_config import CRMConfig
            from tenants.middleware import set_current_loja_id, set_current_tenant_db

            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            n = 0
            for config in CRMConfig.objects.all_without_filter().using(db_name):
                n += cifrar_campos(config, ("issnet_certificado",), db_name)
        except ProgrammingError:
            self.stdout.write(self.style.WARNING(f"{loja.nome}: tabela de nota ainda não existe"))
            return 0
        self.stdout.write(f"{loja.nome}: {n}")
        return n
