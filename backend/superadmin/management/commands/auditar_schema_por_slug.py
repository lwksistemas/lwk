"""
Audita schemas PostgreSQL por loja conforme o tipo de app (CRM, clínica, etc.).

Diferente de verificar_schema_loja (focado em tabelas CRM), este comando valida
apenas os apps esperados para o slug do TipoLoja.

Uso:
  python manage.py auditar_schema_por_slug --slug 41449198000172
  python manage.py auditar_schema_por_slug --slug a --slug b --all-active

Heroku:
  heroku run "python backend/manage.py auditar_schema_por_slug --slug 37302743000126" -a lwksistemas
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from superadmin.services.database_schema_service import (
    TIPO_LOJA_EXTRA_APPS,
    get_apps_esperados_para_loja,
)
from superadmin.services.schema_audit_service import (
    contar_tabelas_app_no_schema,
    prefixos_tabela_para_app,
)


class Command(BaseCommand):
    help = 'Audita schema isolado por loja (apps esperados conforme tipo, não só CRM)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            action='append',
            dest='slugs',
            default=None,
            help='Slug(s) da loja (CNPJ ou slug custom). Repita --slug para várias.',
        )
        parser.add_argument(
            '--all-active',
            action='store_true',
            help='Auditar todas as lojas ativas com database_created=True',
        )

    def handle(self, *args, **options):
        slugs = options.get('slugs')
        all_active = options.get('all_active')

        if not slugs and not all_active:
            self.stdout.write(
                self.style.ERROR('Informe --slug <slug> (um ou mais) ou --all-active.')
            )
            return

        default_engine = (settings.DATABASES.get('default') or {}).get('ENGINE', '')
        usando_pg = 'postgresql' in default_engine
        if not usando_pg:
            self.stdout.write(
                self.style.WARNING(
                    'DATABASE default não é PostgreSQL; a auditoria de schema por nome '
                    'é principalmente para produção (Heroku).'
                )
            )

        if not os.environ.get('DATABASE_URL') and usando_pg:
            self.stdout.write(
                self.style.WARNING('DATABASE_URL ausente; conexão por loja pode falhar.')
            )

        qs = Loja.objects.select_related('tipo_loja').order_by('slug')
        if slugs:
            qs = qs.filter(slug__in=slugs)
        else:
            qs = qs.filter(is_active=True, database_created=True)

        lojas = list(qs)
        if not lojas:
            self.stdout.write(self.style.WARNING('Nenhuma loja encontrada para os filtros.'))
            return

        self.stdout.write('\n' + '=' * 88)
        self.stdout.write('AUDITORIA DE SCHEMA POR LOJA (apps esperados = tipo de app)')
        self.stdout.write('=' * 88 + '\n')

        for loja in lojas:
            self._auditar_loja(loja, usando_pg)

        self.stdout.write('\n' + '=' * 88 + '\n')

    def _auditar_loja(self, loja, usando_pg: bool):
        tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'unknown'
        nome_tipo = loja.tipo_loja.nome if loja.tipo_loja else '—'
        schema_name = (loja.database_name or '').replace('-', '_')
        apps_esperados = get_apps_esperados_para_loja(loja)

        self.stdout.write(f"\n● {loja.nome}")
        self.stdout.write(f"  id={loja.id}  slug={loja.slug}  database_name={loja.database_name}")
        self.stdout.write(
            f"  tipo: {nome_tipo}  (slug tipo: {tipo_slug})  database_created={loja.database_created}"
        )

        if tipo_slug != 'unknown' and tipo_slug not in TIPO_LOJA_EXTRA_APPS:
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠ Slug de tipo não mapeado em TIPO_LOJA_EXTRA_APPS — "
                    f"só stores/products serão esperados além do vazio."
                )
            )

        self.stdout.write(f"  Apps esperados no schema: {', '.join(apps_esperados)}")

        if not loja.database_name:
            self.stdout.write(self.style.ERROR('  ❌ database_name vazio.'))
            return

        if usando_pg:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = %s
                    """,
                    [schema_name],
                )
                schema_ok = cursor.fetchone() is not None
            if not schema_ok:
                self.stdout.write(self.style.ERROR(f'  ❌ Schema PostgreSQL "{schema_name}" não existe.'))
                return
            self.stdout.write(self.style.SUCCESS(f'  ✅ Schema "{schema_name}" existe.'))

        if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
            self.stdout.write(
                self.style.ERROR(
                    f'  ❌ Não foi possível configurar conexão para "{loja.database_name}".'
                )
            )
            return

        conn = connections[loja.database_name]
        try:
            conn.ensure_connection()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Erro ao conectar: {e}'))
            return

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                """,
                [schema_name],
            )
            total_tabelas = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                  AND table_name NOT LIKE 'django_%%'
                """,
                [schema_name],
            )
            tabelas_negocio = cur.fetchone()[0]

        self.stdout.write(
            f'  Tabelas no schema: {total_tabelas} total ({tabelas_negocio} negócio, excl. django_*)'
        )

        if tabelas_negocio == 0:
            self.stdout.write(self.style.ERROR('  ❌ Nenhuma tabela de negócio no schema.'))
            return

        tudo_ok = True
        for app in apps_esperados:
            pfx_display = ', '.join(f'`{p}*`' for p in prefixos_tabela_para_app(app))
            n_tab = contar_tabelas_app_no_schema(conn, schema_name, app)
            with conn.cursor() as cur:
                cur.execute(
                    'SET search_path TO %s, public',
                    [schema_name],
                )
                cur.execute(
                    """
                    SELECT COUNT(*) FROM django_migrations WHERE app = %s
                    """,
                    [app],
                )
                n_mig = cur.fetchone()[0]

            if n_tab > 0 and n_mig > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ {app}: {n_tab} tabela(s) ({pfx_display}), {n_mig} migration(s) registrada(s)"
                    )
                )
            elif n_tab > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ {app}: {n_tab} tabela(s) mas django_migrations vazio ou incompleto ({n_mig})"
                    )
                )
            elif n_mig > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ {app}: {n_mig} migration(s) mas nenhuma tabela ({pfx_display})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ❌ {app}: sem tabelas ({pfx_display}) e sem migrations registradas — FALTANDO"
                    )
                )
                tudo_ok = False

        if tudo_ok and tabelas_negocio > 0:
            self.stdout.write(self.style.SUCCESS('  → Resumo: OK para os apps esperados deste tipo.'))
        elif not tudo_ok:
            self.stdout.write(
                self.style.ERROR(
                    '  → Resumo: FALHA — rode migrate ou DatabaseSchemaService.aplicar_migrations(loja).'
                )
            )

        if loja.database_name in connections:
            try:
                connections[loja.database_name].close()
            except Exception:
                pass
