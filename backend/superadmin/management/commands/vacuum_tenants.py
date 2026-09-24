"""VACUUM ANALYZE automático nos schemas das lojas ativas.

Por que é necessário:
  O autovacuum padrão do Postgres usa autovacuum_vacuum_scale_factor=0.2,
  ou seja, só dispara quando 20% das linhas estão mortas. Para tabelas com
  poucas linhas vivas (ex.: whatsapp_whatsappconfig = 1 linha), 20% de 1
  arredonda para zero e o autovacuum nunca dispara — gerando acúmulo de
  dead tuples que degrada performance e desperdiça espaço.

  Este comando roda semanalmente via executar_cron_lwks e corrige isso.

Tabelas alvo:
  Todas as tabelas dos apps tenant (clinica_beleza_*, whatsapp_*,
  crm_vendas_*, nfse_integration_*) em cada schema loja_<cnpj>.
  VACUUM ANALYZE não bloqueia leituras nem escritas.
"""
import logging

from django.core.management.base import BaseCommand
from django.db import connection, connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

logger = logging.getLogger(__name__)

# Prefixos de tabela que fazem parte dos apps tenant e acumulam bloat
_PREFIXOS_TENANT = (
    "clinica_beleza_",
    "whatsapp_",
    "crm_vendas_",
    "crm_financeiro_",
    "nfse_integration_",
    "cabeleireiro_",
    "hotel_",
    "restaurante_",
    "agenda_base_",
)


def _tabelas_tenant_no_schema(schema: str) -> list[str]:
    """Lista tabelas do schema que correspondem aos apps tenant."""
    with connection.cursor() as c:
        c.execute(
            """
            SELECT tablename FROM pg_tables
            WHERE schemaname = %s
              AND tablename ~ %s
            ORDER BY tablename
            """,
            [schema, "^(" + "|".join(_PREFIXOS_TENANT) + ")"],
        )
        return [r[0] for r in c.fetchall()]


class Command(BaseCommand):
    help = "VACUUM ANALYZE nas tabelas tenant de todos os schemas de loja ativos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            type=str,
            default="",
            help="Processar apenas a loja com este slug (padrão: todas as ativas).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Lista as tabelas que seriam processadas sem executar o VACUUM.",
        )

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        dry_run = options.get("dry_run", False)

        lojas = Loja.objects.filter(is_active=True, database_created=True)
        if slug_filter:
            lojas = lojas.filter(slug__iexact=slug_filter)

        total_tabelas = 0
        lojas_ok = 0
        lojas_skip = 0

        for loja in lojas:
            db_name = loja.database_name
            if not db_name:
                lojas_skip += 1
                continue

            # Garante que o alias de conexão da loja existe em settings.DATABASES
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                self.stdout.write(
                    self.style.WARNING(f"  skip {loja.slug}: DB indisponível")
                )
                lojas_skip += 1
                continue

            schema = db_name.replace("-", "_")
            tabelas = _tabelas_tenant_no_schema(schema)

            if not tabelas:
                self.stdout.write(f"  {loja.slug}: sem tabelas tenant — skip")
                lojas_skip += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"  [dry-run] {loja.slug} ({schema}): {len(tabelas)} tabelas"
                )
                total_tabelas += len(tabelas)
                lojas_ok += 1
                continue

            # VACUUM ANALYZE exige autocommit (não pode rodar dentro de transação)
            conn = connections[db_name]
            try:
                conn.ensure_connection()
                raw = conn.connection
                old_level = raw.isolation_level
                raw.set_isolation_level(0)  # AUTOCOMMIT

                vacuumadas = 0
                erros = 0
                with raw.cursor() as cur:
                    cur.execute(f'SET search_path TO "{schema}", public')
                    for tabela in tabelas:
                        try:
                            cur.execute(f"VACUUM ANALYZE {tabela}")
                            vacuumadas += 1
                        except Exception as exc:
                            logger.warning(
                                "vacuum_tenants %s.%s: %s", schema, tabela, exc
                            )
                            erros += 1

                raw.set_isolation_level(old_level)
                total_tabelas += vacuumadas
                lojas_ok += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  {loja.slug}: {vacuumadas} tabelas OK"
                        + (f", {erros} erros" if erros else "")
                    )
                )
            except Exception as exc:
                logger.exception("vacuum_tenants loja %s: %s", loja.slug, exc)
                lojas_skip += 1
            finally:
                try:
                    connections[db_name].close()
                except Exception:
                    pass

        prefixo = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefixo}vacuum_tenants: {lojas_ok} loja(s) OK, "
                f"{lojas_skip} ignorada(s), {total_tabelas} tabela(s) processada(s)."
            )
        )
