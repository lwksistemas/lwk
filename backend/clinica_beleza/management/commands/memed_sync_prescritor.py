"""Sincroniza (cria/atualiza) um prescritor na Memed a partir do cadastro de um
profissional de uma loja. Útil para testar o auto-cadastro e confirmar com o
suporte da Memed o formato do endpoint de criação de prescritor.

Uso:
    python manage.py memed_sync_prescritor --slug beleza --professional 4 --force
    python manage.py memed_sync_prescritor --slug beleza --cpf 12345678901 --force
    python manage.py memed_sync_prescritor --slug beleza --professional 4 --recadastrar

--force ignora a flag MEMED_AUTO_CADASTRO (envia mesmo com ela desligada).
--recadastrar exclui o cadastro atual e cria de novo (resolve o status "Inativo":
    um cadastro novo entra "Em análise", que libera a prescrição). Irreversível na
    Memed — só use quando o prescritor não tiver histórico a preservar.
"""
import re

from django.core.management.base import BaseCommand, CommandError

from clinica_beleza.memed_service import (
    atualizar_prescritor,
    consultar_status_memed,
    external_id_prescritor,
    recadastrar_prescritor,
    sincronizar_prescritor,
)
from clinica_beleza.models import Professional
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = "Cria/atualiza um prescritor na Memed a partir do cadastro do profissional."

    def add_arguments(self, parser):
        parser.add_argument("--slug", required=True, help="Slug, atalho ou CPF/CNPJ da loja.")
        parser.add_argument("--professional", type=int, help="ID do profissional na loja.")
        parser.add_argument("--cpf", help="CPF do profissional (alternativa ao --professional).")
        parser.add_argument("--force", action="store_true", help="Ignora a flag MEMED_AUTO_CADASTRO.")
        parser.add_argument(
            "--update",
            action="store_true",
            help="Atualiza (PATCH) o cadastro existente na Memed. Se não existir, cria.",
        )
        parser.add_argument(
            "--recadastrar",
            action="store_true",
            help="Exclui e recria o cadastro (resolve 'Inativo'). IRREVERSÍVEL na Memed.",
        )

    def _resolver_loja(self, ident: str) -> Loja:
        ident = (ident or "").strip()
        loja = (
            Loja.objects.using("default").filter(slug__iexact=ident).first()
            or Loja.objects.using("default").filter(atalho__iexact=ident).first()
        )
        if not loja:
            so_digitos = "".join(c for c in ident if c.isdigit())
            if so_digitos:
                loja = Loja.objects.using("default").filter(cpf_cnpj=so_digitos).first()
        if not loja:
            raise CommandError(f'Loja não encontrada para "{ident}".')
        return loja

    def handle(self, *args, **options):
        loja = self._resolver_loja(options["slug"])
        if not loja.database_name:
            raise CommandError(f"Loja {loja.slug} não tem schema configurado.")
        ensure_loja_database_config(loja.database_name)
        set_current_loja_id(loja.id)
        set_current_tenant_db(loja.database_name)

        qs = Professional.objects.using(loja.database_name).filter(loja_id=loja.id)
        if options.get("professional"):
            prof = qs.filter(pk=options["professional"]).first()
        elif options.get("cpf"):
            cpf = re.sub(r"\D", "", options["cpf"])
            prof = next((p for p in qs if re.sub(r"\D", "", p.cpf or "") == cpf), None)
        else:
            raise CommandError("Informe --professional <id> ou --cpf <cpf>.")

        if not prof:
            raise CommandError("Profissional não encontrado na loja informada.")

        self.stdout.write(f"Profissional: {prof.nome} (id={prof.id}) — external_id={external_id_prescritor(prof)}")
        if options.get("recadastrar"):
            st_antes = consultar_status_memed(prof)
            self.stdout.write(f"Status antes: {st_antes.get('status') or st_antes.get('label')}")
            resultado = recadastrar_prescritor(prof)
            self.stdout.write(self.style.MIGRATE_HEADING("=== Resultado (recadastro) ==="))
            self.stdout.write(f"DELETE: {resultado.get('delete')}")
            self.stdout.write(f"CREATE: {resultado.get('create')}")
            st_depois = consultar_status_memed(prof)
            status_final = st_depois.get("status") or st_depois.get("label")
            self.stdout.write(self.style.SUCCESS(f"Status depois: {status_final}"))
            return
        if options.get("update"):
            # PATCH: atualiza cadastro existente (ex.: corrigir board CRM -> COREN).
            resultado = atualizar_prescritor(prof)
            # Se o prescritor ainda não existe na Memed, cai para criação.
            if resultado.get("not_found"):
                self.stdout.write(self.style.WARNING("Prescritor não existe na Memed — criando via POST..."))
                resultado = sincronizar_prescritor(prof, force=True)
        else:
            resultado = sincronizar_prescritor(prof, force=options.get("force", False))
        self.stdout.write(self.style.MIGRATE_HEADING("=== Resultado ==="))
        self.stdout.write(str(resultado))
        if resultado.get("ok"):
            self.stdout.write(self.style.SUCCESS("Prescritor sincronizado com a Memed."))
        elif resultado.get("skipped"):
            self.stdout.write(self.style.WARNING(f"Ignorado: {resultado['skipped']} (use --force se necessário)."))
        else:
            self.stdout.write(self.style.ERROR("Falha ao sincronizar — veja o detalhe acima."))
