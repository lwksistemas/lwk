"""Corrige migrations inconsistentes em schemas de lojas.

- Marca stores.0001_initial quando faltando.
- Marca superadmin.0001_initial quando whatsapp.0002* já está aplicada
  (histórico legado; não cria tabelas superadmin_* no tenant).

Uso:
    python manage.py corrigir_migrations_inconsistentes
"""
import logging

from django.core.management.base import BaseCommand
from django.db import connections

from superadmin.models import Loja

logger = logging.getLogger(__name__)


def _migration_applied(cursor, app: str, name: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = %s AND name = %s
        );
        """,
        [app, name],
    )
    return bool(cursor.fetchone()[0])


def _fake_mark(cursor, app: str, name: str) -> None:
    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        VALUES (%s, %s, NOW());
        """,
        [app, name],
    )


def _whatsapp_0002_applied(cursor) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'whatsapp' AND name LIKE '0002%%'
        );
        """,
    )
    return bool(cursor.fetchone()[0])


class Command(BaseCommand):
    help = "Corrige migrations inconsistentes em schemas de lojas"

    def handle(self, *args, **options):
        lojas = list(Loja.objects.using("default").all())

        if not lojas:
            self.stdout.write(self.style.WARNING("Nenhuma loja encontrada"))
            return

        self.stdout.write(f"Encontradas {len(lojas)} loja(s)")

        corrigidas = 0
        for loja in lojas:
            db_name = loja.database_name
            schema_name = db_name.replace("-", "_")

            try:
                from core.db_config import ensure_loja_database_config
                if not ensure_loja_database_config(db_name, conn_max_age=0):
                    continue

                conn = connections[db_name]
                conn.ensure_connection()

                with conn.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}", public;')
                    mudou = False

                    if not _migration_applied(cursor, "stores", "0001_initial"):
                        _fake_mark(cursor, "stores", "0001_initial")
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✅ Loja {loja.nome} (ID: {loja.id}): stores.0001_initial marcada",
                        ))
                        mudou = True

                    # WhatsApp 0002 depende de superadmin.0001 no histórico Django,
                    # mas as tabelas superadmin ficam no public — só alinhar django_migrations.
                    if _whatsapp_0002_applied(cursor) and not _migration_applied(
                        cursor, "superadmin", "0001_initial",
                    ):
                        _fake_mark(cursor, "superadmin", "0001_initial")
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✅ Loja {loja.nome} (ID: {loja.id}): superadmin.0001_initial marcada (dep. whatsapp)",
                        ))
                        mudou = True

                    if mudou:
                        corrigidas += 1
                    else:
                        self.stdout.write(f"  ℹ️  Loja {loja.nome} (ID: {loja.id}): Já corrigida")

                conn.close()

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"  ❌ Loja {loja.nome} (ID: {loja.id}): Erro - {e}",
                ))
                logger.exception("Erro ao corrigir loja %s", loja.id)

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Processamento concluído: {corrigidas} loja(s) corrigida(s)",
        ))
