"""Comando para detectar e limpar dados órfãos no sistema.

Verifica:
1. Arquivos de banco SQLite sem loja correspondente
2. Schemas PostgreSQL sem loja correspondente
3. Usuários sem lojas (órfãos)
4. Sessões de usuários inexistentes
5. Dados em tabelas com loja_id inválido
6. Configurações de banco em settings.DATABASES sem loja
7. Dados em tabelas com loja_id inválido (safety net)
8. Arquivos órfãos (backups, NF-e, HistoricoBackup)

Uso:
    python manage.py limpar_orfaos --dry-run  # Apenas listar
    python manage.py limpar_orfaos --execute  # Executar limpeza
"""
import contextlib
import logging
import os
import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Detecta e remove dados órfãos (arquivos, schemas, usuários, sessões)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas listar órfãos sem remover",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Executar limpeza de órfãos",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        execute = options["execute"]

        if not dry_run and not execute:
            self.stdout.write(self.style.ERROR("❌ Use --dry-run para listar ou --execute para limpar"))
            return

        mode = "🔍 MODO ANÁLISE (dry-run)" if dry_run else "🗑️ MODO EXECUÇÃO"
        self.stdout.write(self.style.WARNING(f"\n{mode}\n"))

        from superadmin.models import Loja, ProfissionalUsuario, UserSession, VendedorUsuario

        lojas_ids = set(Loja.objects.values_list("id", flat=True))
        lojas_db_names = set(Loja.objects.values_list("database_name", flat=True))
        loja_slugs = set(Loja.objects.values_list("slug", flat=True))
        usuarios_ids = set(User.objects.values_list("id", flat=True))

        self._step1_sqlite(execute, lojas_db_names)
        self._step2_postgres_schemas(execute, lojas_db_names)
        self._step3_usuarios(execute)
        self._step4_sessoes(execute, UserSession, usuarios_ids)
        self._step5_vinculos(execute, lojas_ids, usuarios_ids, ProfissionalUsuario, VendedorUsuario)
        self._step6_db_configs(execute, lojas_db_names)
        self._step7_loja_id_invalido(execute)
        self._step8_arquivos(execute, loja_slugs, lojas_ids)
        self._step9_evolution(execute, lojas_ids)

        self.stdout.write(self.style.HTTP_INFO("\n" + "="*60))
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 Análise concluída. Use --execute para limpar."))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Limpeza concluída!"))
        self.stdout.write(self.style.HTTP_INFO("="*60 + "\n"))

    def _step1_sqlite(self, execute, lojas_db_names):
        self.stdout.write(self.style.HTTP_INFO("\n1️⃣ Verificando arquivos SQLite órfãos..."))
        arquivos_orfaos = [
            fn for fn in os.listdir(settings.BASE_DIR)
            if fn.startswith("db_loja_") and fn.endswith(".sqlite3")
            and fn.replace("db_", "").replace(".sqlite3", "") not in lojas_db_names
            and fn.replace("db_", "").replace(".sqlite3", "") != "loja_template"
        ]
        if not arquivos_orfaos:
            self.stdout.write(self.style.SUCCESS("   ✅ Nenhum arquivo SQLite órfão"))
            return
        self.stdout.write(self.style.WARNING(f"   ⚠️ Encontrados {len(arquivos_orfaos)} arquivos órfãos:"))
        for arquivo in arquivos_orfaos:
            self.stdout.write(f"      - {arquivo}")
            if execute:
                try:
                    os.remove(settings.BASE_DIR / arquivo)
                    self.stdout.write(self.style.SUCCESS("         ✅ Removido"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"         ❌ Erro: {e}"))

    def _step2_postgres_schemas(self, execute, lojas_db_names):
        self.stdout.write(self.style.HTTP_INFO("\n2️⃣ Verificando schemas PostgreSQL órfãos..."))
        if "postgres" not in os.environ.get("DATABASE_URL", "").lower():
            self.stdout.write(self.style.SUCCESS("   ℹ️ Não está usando PostgreSQL"))
            return
        lojas_schemas = {n.replace("-", "_") for n in lojas_db_names}
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name LIKE 'loja_%'
                AND schema_name NOT IN ('public', 'information_schema')
            """)
            schemas_existentes = [row[0] for row in cursor.fetchall()]
        schemas_orfaos = [s for s in schemas_existentes if s not in lojas_schemas]
        if not schemas_orfaos:
            self.stdout.write(self.style.SUCCESS("   ✅ Nenhum schema PostgreSQL órfão"))
            return
        self.stdout.write(self.style.WARNING(f"   ⚠️ Encontrados {len(schemas_orfaos)} schemas órfãos:"))
        for schema in schemas_orfaos:
            self.stdout.write(f"      - {schema}")
            if execute:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                    self.stdout.write(self.style.SUCCESS("         ✅ Removido"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"         ❌ Erro: {e}"))

    def _step3_usuarios(self, execute):
        self.stdout.write(self.style.HTTP_INFO("\n3️⃣ Verificando usuários órfãos..."))
        from superadmin.orfaos_config import get_usuarios_orfaos_queryset
        usuarios_orfaos = get_usuarios_orfaos_queryset()
        if not usuarios_orfaos.exists():
            self.stdout.write(self.style.SUCCESS("   ✅ Nenhum usuário órfão"))
            return
        self.stdout.write(self.style.WARNING(f"   ⚠️ Encontrados {usuarios_orfaos.count()} usuários órfãos:"))
        user_ids = list(usuarios_orfaos.values_list("id", flat=True))
        user_info = {u.id: (u.username, u.email) for u in usuarios_orfaos}
        for user_id in user_ids:
            username, email = user_info.get(user_id, ("?", "?"))
            self.stdout.write(f"      - {username} (ID: {user_id}, Email: {email})")
            if execute:
                try:
                    from superadmin.utils import delete_user_raw
                    delete_user_raw(user_id)
                    self.stdout.write(self.style.SUCCESS("         ✅ Removido"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"         ❌ Erro: {e}"))

    def _step4_sessoes(self, execute, UserSession, usuarios_ids):
        self.stdout.write(self.style.HTTP_INFO("\n4️⃣ Verificando sessões órfãs..."))
        sessoes_orfas = UserSession.objects.exclude(user_id__in=usuarios_ids)
        if not sessoes_orfas.exists():
            self.stdout.write(self.style.SUCCESS("   ✅ Nenhuma sessão órfã"))
            return
        count = sessoes_orfas.count()
        self.stdout.write(self.style.WARNING(f"   ⚠️ Encontradas {count} sessões órfãs"))
        if execute:
            sessoes_orfas.delete()
            self.stdout.write(self.style.SUCCESS(f"      ✅ {count} sessões removidas"))

    def _step5_vinculos(self, execute, lojas_ids, usuarios_ids, ProfissionalUsuario, VendedorUsuario):
        self.stdout.write(self.style.HTTP_INFO("\n5️⃣ Verificando vínculos profissional/vendedor órfãos..."))
        for label, qs in (
            ("ProfissionalUsuario (user inexistente)", ProfissionalUsuario.objects.exclude(user_id__in=usuarios_ids)),
            ("ProfissionalUsuario (loja inexistente)", ProfissionalUsuario.objects.exclude(loja_id__in=lojas_ids)),
            ("VendedorUsuario (user inexistente)", VendedorUsuario.objects.exclude(user_id__in=usuarios_ids)),
            ("VendedorUsuario (loja inexistente)", VendedorUsuario.objects.exclude(loja_id__in=lojas_ids)),
        ):
            if not qs.exists():
                self.stdout.write(self.style.SUCCESS(f"   ✅ {label}: nenhum"))
                continue
            count = qs.count()
            self.stdout.write(self.style.WARNING(f"   ⚠️ {label}: {count}"))
            if execute:
                qs.delete()
                self.stdout.write(self.style.SUCCESS(f"      ✅ {count} removidos"))

    def _step6_db_configs(self, execute, lojas_db_names):
        self.stdout.write(self.style.HTTP_INFO("\n6️⃣ Verificando configurações de banco órfãs..."))
        IGNORAR = {"default", "suporte", "loja_template"}
        configs_orfas = [
            db for db in settings.DATABASES
            if db.startswith("loja_") and db not in IGNORAR and db not in lojas_db_names
        ]
        if not configs_orfas:
            self.stdout.write(self.style.SUCCESS("   ✅ Nenhuma configuração órfã"))
            return
        self.stdout.write(self.style.WARNING(f"   ⚠️ Encontradas {len(configs_orfas)} configurações órfãs:"))
        for db_name in configs_orfas:
            self.stdout.write(f"      - {db_name}")
            if execute:
                try:
                    del settings.DATABASES[db_name]
                    self.stdout.write(self.style.SUCCESS("         ✅ Removido do settings"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"         ❌ Erro: {e}"))

    def _step7_loja_id_invalido(self, execute):
        self.stdout.write(self.style.HTTP_INFO("\n7️⃣ Verificando dados com loja_id inválido..."))
        from superadmin.orfaos_config import TABELAS_LOJA_ID_DEFAULT, tabela_existe_em_public
        total_orfaos = 0
        for tabela, coluna in TABELAS_LOJA_ID_DEFAULT:
            try:
                with connection.cursor() as cursor:
                    if not tabela_existe_em_public(cursor, tabela):
                        continue
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {tabela} WHERE {coluna} IS NOT NULL AND {coluna} NOT IN (SELECT id FROM superadmin_loja)"
                    )
                    count = cursor.fetchone()[0]
                    if count > 0:
                        total_orfaos += count
                        self.stdout.write(self.style.WARNING(f"   ⚠️ {tabela}: {count} registros órfãos"))
                        if execute:
                            cursor.execute(
                                f"DELETE FROM {tabela} WHERE {coluna} NOT IN (SELECT id FROM superadmin_loja)"
                            )
                            self.stdout.write(self.style.SUCCESS(f"      ✅ {count} registros removidos"))
            except Exception as e:
                if "does not exist" not in str(e).lower():
                    self.stdout.write(self.style.ERROR(f"   ❌ Erro em {tabela}: {e}"))
        if total_orfaos == 0:
            self.stdout.write(self.style.SUCCESS("   ✅ Nenhum dado com loja_id inválido"))

    def _step8_arquivos(self, execute, loja_slugs, loja_ids_set):
        self.stdout.write(self.style.HTTP_INFO("\n8️⃣ Verificando arquivos órfãos..."))
        base_dir = Path(settings.BASE_DIR)
        media_root = Path(getattr(settings, "MEDIA_ROOT", base_dir / "media"))
        self._step8a_historico_backup(execute, loja_ids_set)
        self._step8b_backup_dirs(execute, base_dir, loja_slugs)
        self._step8c_nfe_files(execute, media_root, loja_ids_set)

    def _step8a_historico_backup(self, execute, loja_ids_set):
        try:
            from superadmin.models import ConfiguracaoBackup, HistoricoBackup
            hist_orfaos = HistoricoBackup.objects.exclude(loja_id__in=loja_ids_set)
            cfg_orfaos = ConfiguracaoBackup.objects.exclude(loja_id__in=loja_ids_set)
            hist_count, cfg_count = hist_orfaos.count(), cfg_orfaos.count()
            if hist_count or cfg_count:
                self.stdout.write(self.style.WARNING(f"   ⚠️ HistoricoBackup órfãos: {hist_count}, ConfiguracaoBackup: {cfg_count}"))
                if execute:
                    hist_orfaos.delete()
                    cfg_orfaos.delete()
                    self.stdout.write(self.style.SUCCESS(f"      ✅ {hist_count} HistoricoBackup e {cfg_count} ConfiguracaoBackup removidos"))
            else:
                self.stdout.write(self.style.SUCCESS("   ✅ Nenhum HistoricoBackup/ConfiguracaoBackup órfão"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ℹ️ HistoricoBackup/ConfiguracaoBackup: {e}"))

    def _step8b_backup_dirs(self, execute, base_dir, loja_slugs):
        backups_base = base_dir / "backups"
        if not backups_base.exists():
            self.stdout.write(self.style.SUCCESS("   ✅ Diretório backups não existe"))
            return
        dirs_orfaos = [d for d in backups_base.iterdir() if d.is_dir() and d.name not in loja_slugs and d.name != "loja_template"]
        if not dirs_orfaos:
            self.stdout.write(self.style.SUCCESS("   ✅ Nenhum diretório backups órfão"))
            return
        self.stdout.write(self.style.WARNING(f"   ⚠️ Diretórios backups órfãos: {[d.name for d in dirs_orfaos]}"))
        if execute:
            for d in dirs_orfaos:
                try:
                    shutil.rmtree(d)
                    self.stdout.write(self.style.SUCCESS(f"      ✅ Removido: backups/{d.name}"))
                except OSError as e:
                    self.stdout.write(self.style.ERROR(f"      ❌ Erro em backups/{d.name}: {e}"))

    def _step8c_nfe_files(self, execute, media_root, loja_ids_set):
        nfe_base = media_root / "nfe_restaurante"
        if not nfe_base.exists():
            self.stdout.write(self.style.SUCCESS("   ✅ Diretório nfe_restaurante não existe"))
            return
        arquivos_orfaos_nfe = []
        for f in nfe_base.rglob("*"):
            if not f.is_file() or "loja_" not in f.name:
                continue
            try:
                parts = f.name.split("_")
                if len(parts) >= 2 and parts[0] == "loja" and parts[1].isdigit() and int(parts[1]) not in loja_ids_set:
                    arquivos_orfaos_nfe.append(f)
            except ValueError:
                pass
        if not arquivos_orfaos_nfe:
            self.stdout.write(self.style.SUCCESS("   ✅ Nenhum arquivo NF-e órfão"))
            return
        self.stdout.write(self.style.WARNING(f"   ⚠️ Arquivos NF-e órfãos: {len(arquivos_orfaos_nfe)}"))
        if execute:
            for f in arquivos_orfaos_nfe:
                with contextlib.suppress(OSError):
                    f.unlink()
            self.stdout.write(self.style.SUCCESS(f"      ✅ {len(arquivos_orfaos_nfe)} arquivo(s) NF-e removido(s)"))

    def _step9_evolution(self, execute, loja_ids_set):
        self.stdout.write(self.style.HTTP_INFO("\n9️⃣ Verificando instâncias Evolution órfãs..."))
        try:
            from whatsapp.evolution_cleanup import find_orphan_evolution_instances
            from whatsapp.evolution_client import evolution_configured
            if not evolution_configured():
                self.stdout.write(self.style.SUCCESS("   ℹ️ Evolution não configurado — pulando"))
                return
            ev_orphans = find_orphan_evolution_instances(loja_ids_set)
            if not ev_orphans:
                self.stdout.write(self.style.SUCCESS("   ✅ Nenhuma instância Evolution órfã"))
                return
            self.stdout.write(self.style.WARNING(f"   ⚠️ {len(ev_orphans)} instância(s) órfã(s):"))
            for row in ev_orphans:
                self.stdout.write(f"      - {row['instance_name']} (loja_id={row['loja_id']})")
            if execute:
                from whatsapp.evolution_cleanup import delete_orphan_evolution_instances
                results = delete_orphan_evolution_instances(loja_ids_set)
                ok = sum(1 for r in results if r.get("ok"))
                self.stdout.write(self.style.SUCCESS(f"      ✅ {ok} removida(s) no Evolution"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ℹ️ Evolution: {e}"))
