"""Comando para aplicar migrations em todas as lojas ativas.

Uso:
    python manage.py migrate_all_lojas [app_label]
    python manage.py migrate_all_lojas ecommerce
"""
import re

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.migrations.exceptions import InconsistentMigrationHistory

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


class Command(BaseCommand):
    help = "Aplica migrations em todas as lojas ativas"

    def _column_exists(self, database: str, table: str, column: str) -> bool:
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                  FROM information_schema.columns
                 WHERE table_name = %s
                   AND column_name = %s
                 LIMIT 1
                """,
                [table, column],
            )
            return cursor.fetchone() is not None

    def _force_mark_migration_applied(self, database: str, app: str, name: str) -> bool:
        """Em lojas legadas, já houve casos de `django_migrations` ficar incompleto (ex.: falta auth.0001),
        causando InconsistentMigrationHistory e bloqueando qualquer `migrate`.

        Esta rotina "repara" o histórico inserindo a migration como aplicada se ela não existir.
        """
        with connections[database].cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s LIMIT 1",
                [app, name],
            )
            if cursor.fetchone():
                return False

            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
                [app, name],
            )
            return True

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            nargs="?",
            help="App específico para migrar (opcional)",
        )
        parser.add_argument(
            "--fake",
            action="store_true",
            help="Marca migrations como aplicadas sem executar",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Retorna erro se alguma loja falhar (padrão: continua e exit 0 para o release)",
        )

    def handle(self, *args, **options):
        app_label = options.get("app_label")
        fake = options.get("fake", False)

        # Buscar todas as lojas ativas
        lojas = Loja.objects.filter(is_active=True, database_created=True)

        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"APLICANDO MIGRATIONS EM {lojas.count()} LOJAS")
        self.stdout.write(f"{'='*80}\n")

        sucesso = 0
        erros = 0

        for loja in lojas:
            try:
                self.stdout.write(f"\n📦 Loja: {loja.nome} ({loja.database_name})")

                # Garantir que database está configurado
                if not ensure_loja_database_config(loja.database_name):
                    self.stdout.write(
                        self.style.ERROR("  ❌ Erro ao configurar database"),
                    )
                    erros += 1
                    continue

                # Aplicar migrations
                migrate_args = [app_label] if app_label else []
                migrate_kwargs = {
                    "database": loja.database_name,
                    "verbosity": 1,
                    "interactive": False,
                }

                if fake:
                    migrate_kwargs["fake"] = True

                # ✅ Reparos preventivos para lojas legadas
                # Django contenttypes 0002_remove_content_type_name remove a coluna "name".
                # Em bases muito antigas essa coluna pode já não existir, então a migration quebra.
                try:
                    if not self._column_exists(loja.database_name, "django_content_type", "name"):
                        self._force_mark_migration_applied(
                            loja.database_name, "contenttypes", "0002_remove_content_type_name",
                        )
                except Exception:
                    # Best-effort: se tabela ainda não existe, deixa o migrate criar normalmente
                    pass

                try:
                    call_command("migrate", *migrate_args, **migrate_kwargs)
                except InconsistentMigrationHistory as e:
                    # Algumas lojas antigas ficaram com histórico fora de ordem (ex.: stores.0001 antes de auth.0001).
                    # Nesses casos, as tabelas normalmente já existem; então alinhar o histórico com fake-initial/fake
                    # e tentar novamente para permitir o deploy em esquema isolado.
                    msg = str(e)
                    if "applied before its dependency auth.0001_initial" in msg and not fake:
                        self.stdout.write(self.style.WARNING("  ⚠️ Histórico inconsistente detectado. Tentando corrigir (auth/contenttypes fake-initial)..."))
                        # 1) Reparar histórico (marcar deps como aplicadas) — necessário porque o Django bloqueia migrate
                        #    quando encontra migrations aplicadas sem deps registradas.
                        repaired = False
                        repaired = self._force_mark_migration_applied(loja.database_name, "contenttypes", "0001_initial") or repaired
                        repaired = self._force_mark_migration_applied(loja.database_name, "auth", "0001_initial") or repaired
                        if repaired:
                            self.stdout.write(self.style.WARNING("  ⚠️ Histórico reparado em django_migrations (auth/contenttypes)."))

                        # 2) Rodar migrate dessas deps com fake-initial (se tabelas já existem) e tentar novamente
                        call_command("migrate", "contenttypes", database=loja.database_name, interactive=False, verbosity=0, fake_initial=True)
                        call_command("migrate", "auth", database=loja.database_name, interactive=False, verbosity=0, fake_initial=True)
                        call_command("migrate", *migrate_args, **migrate_kwargs)
                    elif "dependency contenttypes.0002_remove_content_type_name" in msg and not fake:
                        self.stdout.write(self.style.WARNING("  ⚠️ Dependência contenttypes.0002 faltando no histórico. Reparando e tentando novamente..."))
                        self._force_mark_migration_applied(
                            loja.database_name, "contenttypes", "0002_remove_content_type_name",
                        )
                        call_command("migrate", *migrate_args, **migrate_kwargs)
                    else:
                        # Tentativa genérica: se a mensagem trouxer "dependency app.migration", reparar o histórico.
                        m = re.search(r"dependency\s+([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", msg)
                        if m and not fake:
                            dep_app, dep_name = m.group(1), m.group(2)
                            self.stdout.write(self.style.WARNING(f"  ⚠️ Dependência faltando no histórico: {dep_app}.{dep_name}. Reparando..."))
                            self._force_mark_migration_applied(loja.database_name, dep_app, dep_name)
                            call_command("migrate", *migrate_args, **migrate_kwargs)
                        else:
                            raise
                except Exception as e:
                    # Caso legado: contenttypes.0002 tenta remover coluna "name" que já não existe.
                    # Isso bloqueia o migrate inteiro. Quando detectado, marcar a migration como aplicada e tentar de novo.
                    msg = str(e)
                    if 'column "name" of relation "django_content_type" does not exist' in msg and not fake:
                        self.stdout.write(self.style.WARNING("  ⚠️ contenttypes sem coluna name. Marcando contenttypes.0002 como aplicada e tentando novamente..."))
                        self._force_mark_migration_applied(loja.database_name, "contenttypes", "0002_remove_content_type_name")
                        call_command("migrate", *migrate_args, **migrate_kwargs)
                    else:
                        raise

                self.stdout.write(
                    self.style.SUCCESS("  ✅ Migrations aplicadas com sucesso"),
                )
                sucesso += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Erro: {e!s}"),
                )
                erros += 1

        # Resumo
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("RESUMO")
        self.stdout.write(f"{'='*80}")
        self.stdout.write(f"✅ Sucesso: {sucesso}")
        self.stdout.write(f"❌ Erros: {erros}")
        self.stdout.write(f"📊 Total: {lojas.count()}\n")

        if erros > 0:
            self.stderr.write(
                self.style.WARNING(
                    f"⚠️ {erros} loja(s) com erro — ensure_all e corrigir_schema_* tentarão corrigir no release.",
                ),
            )
            if options.get("strict"):
                from django.core.management.base import CommandError
                raise CommandError(f"migrate_all_lojas: {erros} loja(s) com erro")
