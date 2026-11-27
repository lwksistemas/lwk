"""Comando para aplicar migrations em todos os schemas das lojas
✅ OTIMIZADO: Fecha conexões após cada loja para evitar "too many connections"
"""
import os
import time

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connections

from superadmin.models import Loja


class Command(BaseCommand):
    help = (
        "Aplica migrations nos schemas das lojas. "
        "Use --apps clinica_beleza para não tocar em CRM/outros tipos. "
        "Termina com erro (exit ≠ 0) se alguma loja falhar."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apps",
            action="append",
            dest="apps",
            help="App(s) Django a migrar (vírgula ou repetir a flag). Ex.: clinica_beleza",
        )
        parser.add_argument(
            "--tipo",
            action="append",
            dest="tipos",
            help="Só lojas deste tipo_loja.slug (vírgula ou repetir). Ex.: clinica-beleza",
        )

    def handle(self, *args, **options):
        from superadmin.tenant_deploy import (
            deve_rodar_fix_colunas_crm,
            filtrar_apps_loja,
            parse_apps_option,
            slugs_tipo_que_usam_algum,
        )
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        filtro_apps = parse_apps_option(options.get("apps"))
        filtro_tipos = parse_apps_option(options.get("tipos"))
        if filtro_apps:
            self.stdout.write(f"🔧 Migrations só dos apps: {', '.join(filtro_apps)}\n")
        else:
            self.stdout.write("🔧 Aplicando migrations em todas as lojas...\n")
        if filtro_tipos:
            self.stdout.write(f"🔧 Só tipos: {', '.join(filtro_tipos)}\n")

        max_retries = 3
        retry_delay = 2
        lojas = None

        for attempt in range(max_retries):
            try:
                qs = Loja.objects.select_related("tipo_loja").all()
                if filtro_apps:
                    qs = qs.filter(tipo_loja__slug__in=slugs_tipo_que_usam_algum(filtro_apps))
                if filtro_tipos:
                    qs = qs.filter(tipo_loja__slug__in=filtro_tipos)
                lojas = list(qs)
                self.stdout.write(f"📊 Total de lojas: {len(lojas)}\n")
                break
            except OperationalError as e:
                if "timeout" in str(e).lower() and attempt < max_retries - 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ Timeout ao buscar lojas (tentativa {attempt + 1}/{max_retries}). "
                            f"Tentando novamente em {retry_delay}s...",
                        ),
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise CommandError(
                        f"Falha ao buscar lojas após {max_retries} tentativas: {e}",
                    ) from e

        if not lojas:
            self.stdout.write(self.style.WARNING("Nenhuma loja encontrada — nada a migrar."))
            return

        DATABASE_URL = os.environ.get("DATABASE_URL")
        if not DATABASE_URL:
            raise CommandError("DATABASE_URL não configurada")

        falhas: list[str] = []

        for loja in lojas:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Loja: {loja.nome} (ID: {loja.id})")
            self.stdout.write(f"Database: {loja.database_name}")

            apps_to_migrate = filtrar_apps_loja(loja, filtro_apps or None)
            if not apps_to_migrate:
                self.stdout.write("⏭️  Loja não usa o(s) app(s) pedido(s) — pulada")
                continue

            from core.db_config import ensure_loja_database_config
            from superadmin.services.migration_history_repair import repair_inconsistent_history

            if ensure_loja_database_config(loja.database_name, conn_max_age=0):
                self.stdout.write("✅ Banco configurado")
            try:
                recorded = repair_inconsistent_history(connections[loja.database_name])
                if recorded:
                    nomes = ", ".join(f"{app}.{name}" for app, name in recorded)
                    self.stdout.write(self.style.WARNING(f"  🔧 Histórico alinhado: {nomes}"))
            except Exception as repair_err:
                self.stdout.write(self.style.WARNING(f"  ⚠️ Reparar histórico: {repair_err}"))

            set_current_tenant_db(loja.database_name)
            set_current_loja_id(loja.id)
            try:
                for app in apps_to_migrate:
                    app_ok = False
                    last_err: Exception | None = None
                    for attempt in range(max_retries):
                        try:
                            self.stdout.write(f"  Migrando {app}... (tentativa {attempt + 1})")
                            call_command(
                                "migrate",
                                app,
                                "--database", loja.database_name,
                                verbosity=0,
                            )
                            self.stdout.write(self.style.SUCCESS(f"  ✅ {app} migrado"))
                            app_ok = True
                            break
                        except OperationalError as e:
                            last_err = e
                            if "timeout" in str(e).lower() and attempt < max_retries - 1:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"  ⚠️ Timeout em {app} (tentativa {attempt + 1}/{max_retries}). "
                                        f"Tentando novamente em {retry_delay}s...",
                                    ),
                                )
                                time.sleep(retry_delay)
                            else:
                                break
                        except Exception as e:
                            last_err = e
                            break
                    if not app_ok:
                        msg = f"{loja.slug or loja.id}/{app}: {last_err}"
                        falhas.append(msg)
                        self.stdout.write(self.style.ERROR(f"  ❌ Erro em {app}: {last_err}"))
            finally:
                set_current_tenant_db("default")
                set_current_loja_id(None)
                if loja.database_name in connections:
                    try:
                        connections[loja.database_name].close()
                        self.stdout.write(f"✅ Conexões fechadas para {loja.database_name}")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"⚠️ Erro ao fechar conexões: {e}"))
                if loja.database_name in settings.DATABASES:
                    del settings.DATABASES[loja.database_name]
                    self.stdout.write("✅ Banco removido das configurações")

        if deve_rodar_fix_colunas_crm(filtro_apps or None):
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write("🔧 Verificando colunas em schemas com CRM...")
            try:
                call_command("fix_google_event_id_column", verbosity=1)
                call_command("fix_duracao_minutos_column", verbosity=1)
                call_command("fix_vendedor_column", verbosity=1)
            except Exception as e:
                falhas.append(f"fix_columns: {e}")
                self.stdout.write(self.style.ERROR(f"  ❌ fix columns: {e}"))

        self.stdout.write(f"\n{'='*60}")
        if falhas:
            resumo = "; ".join(falhas[:10])
            if len(falhas) > 10:
                resumo += f" (+{len(falhas) - 10} outras)"
            raise CommandError(
                f"migrate_all_lojas falhou em {len(falhas)} passo(s): {resumo}",
            )
        self.stdout.write(self.style.SUCCESS("\n✅ Processo concluído!"))
