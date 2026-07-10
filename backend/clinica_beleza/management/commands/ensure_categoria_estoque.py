"""
Garante CategoriaEstoque + FK em ProdutoEstoque nos schemas das lojas Clínica da Beleza.

Aplica o equivalente à migration 0059 quando o release/migrate_all_lojas não rodou no tenant.

Uso:
    python manage.py ensure_categoria_estoque
    python manage.py ensure_categoria_estoque --slug clinicaharmonis
"""
from django.core.management.base import BaseCommand
from django.db import connection

from clinica_beleza.schema_ensure import column_exists, table_exists
from superadmin.models import Loja

CATEGORIAS_PADRAO = [
    ('injetavel', 'Injetável', 1),
    ('soroterapia', 'Soroterapia', 2),
    ('cosmético', 'Cosmético', 3),
    ('medicamentos', 'Medicamentos', 4),
    ('descartavel', 'Descartável', 5),
    ('equipamento', 'Equipamento', 6),
    ('outro', 'Outro', 7),
]

_ALIASES = {
    'cosmetico': 'cosmético',
    'Medicamentos': 'medicamentos',
    'medicamento': 'medicamentos',
}

CAT_TABLE = 'clinica_beleza_categoriaestoque'
PROD_TABLE = 'clinica_beleza_produtoestoque'
MIG_NAME = '0059_categoria_estoque'


class Command(BaseCommand):
    help = 'Cria categorias de estoque e converte ProdutoEstoque.categoria para FK.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        lojas = (
            Loja.objects.filter(is_active=True, database_created=True)
            .exclude(database_name='')
            .exclude(database_name__isnull=True)
            .select_related('tipo_loja')
        )
        ok = skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue
            tipo = (getattr(getattr(loja, 'tipo_loja', None), 'nome', '') or '').lower()
            is_clinica = any(x in tipo for x in ('beleza', 'estetica', 'estética'))
            if not slug_filter and not is_clinica and loja.database_name not in (
                'loja_22239255889', 'loja_37302743000126',
            ):
                continue
            schema = (loja.database_name or '').replace('-', '_')
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema}", public')
                    if not table_exists(cursor, PROD_TABLE):
                        self.stdout.write(self.style.WARNING(f'  skip {loja.slug}: sem estoque'))
                        skip += 1
                        continue

                    changed = self._ensure_schema(cursor, loja.id)
                    self._mark_migration(cursor)
                    connection.commit()
                    ok += 1
                    msg = 'atualizado' if changed else 'já ok'
                    self.stdout.write(self.style.SUCCESS(f'  OK {loja.slug} ({msg})'))
            except Exception as e:
                skip += 1
                try:
                    connection.rollback()
                except Exception:
                    pass
                self.stdout.write(self.style.ERROR(f'  ERRO {loja.slug}: {e}'))

        try:
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public')
        except Exception:
            pass
        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s), {skip} ignorada(s)/erro.'))

    def _ensure_schema(self, cursor, loja_id: int) -> bool:
        changed = False
        if not table_exists(cursor, CAT_TABLE):
            cursor.execute(f"""
                CREATE TABLE {CAT_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    loja_id INTEGER NOT NULL,
                    nome VARCHAR(100) NOT NULL,
                    slug VARCHAR(50) NOT NULL,
                    cor VARCHAR(7) NOT NULL DEFAULT '#8B3D52',
                    ordem INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cursor.execute(f"""
                CREATE UNIQUE INDEX IF NOT EXISTS cb_estoque_cat_loja_slug_uniq
                ON {CAT_TABLE} (loja_id, slug)
            """)
            cursor.execute(f'CREATE INDEX IF NOT EXISTS {CAT_TABLE}_loja_id_idx ON {CAT_TABLE} (loja_id)')
            changed = True
            self.stdout.write(f'    + tabela {CAT_TABLE}')

        # Seed categorias padrão
        for slug, nome, ordem in CATEGORIAS_PADRAO:
            cursor.execute(
                f"""
                INSERT INTO {CAT_TABLE} (loja_id, nome, slug, cor, ordem, is_active, created_at, updated_at)
                SELECT %s, %s, %s, '#8B3D52', %s, TRUE, NOW(), NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM {CAT_TABLE} WHERE loja_id=%s AND slug=%s
                )
                """,
                [loja_id, nome, slug, ordem, loja_id, slug],
            )

        has_fk = column_exists(cursor, PROD_TABLE, 'categoria_id')
        has_char = column_exists(cursor, PROD_TABLE, 'categoria')
        has_tmp = column_exists(cursor, PROD_TABLE, 'categoria_slug_tmp')
        slug_col = 'categoria_slug_tmp' if has_tmp else ('categoria' if has_char and not has_fk else None)

        if slug_col and not has_fk:
            cursor.execute(f"""
                ALTER TABLE {PROD_TABLE}
                ADD COLUMN IF NOT EXISTS categoria_id BIGINT NULL
                REFERENCES {CAT_TABLE}(id) ON DELETE SET NULL
            """)
            cursor.execute(f'SELECT id, {slug_col} FROM {PROD_TABLE} WHERE categoria_id IS NULL')
            rows = cursor.fetchall()
            slug_to_id = {}
            cursor.execute(f'SELECT id, slug FROM {CAT_TABLE} WHERE loja_id=%s', [loja_id])
            for cid, slug in cursor.fetchall():
                slug_to_id[slug] = cid
            for pid, raw in rows:
                raw = (raw or '').strip()
                raw = _ALIASES.get(raw, raw) or 'outro'
                cat_id = slug_to_id.get(raw) or slug_to_id.get('outro')
                if cat_id:
                    cursor.execute(
                        f'UPDATE {PROD_TABLE} SET categoria_id=%s WHERE id=%s',
                        [cat_id, pid],
                    )
            cursor.execute(f'ALTER TABLE {PROD_TABLE} DROP COLUMN IF EXISTS {slug_col}')
            if slug_col != 'categoria':
                cursor.execute(f'ALTER TABLE {PROD_TABLE} DROP COLUMN IF EXISTS categoria')
            changed = True
            self.stdout.write('    + convertida coluna categoria → categoria_id')
        elif has_fk and (has_char or has_tmp):
            src = 'categoria_slug_tmp' if has_tmp else 'categoria'
            cursor.execute(f'SELECT id, {src} FROM {PROD_TABLE} WHERE categoria_id IS NULL')
            rows = cursor.fetchall()
            slug_to_id = {}
            cursor.execute(f'SELECT id, slug FROM {CAT_TABLE} WHERE loja_id=%s', [loja_id])
            for cid, slug in cursor.fetchall():
                slug_to_id[slug] = cid
            for pid, raw in rows:
                raw = (raw or '').strip()
                raw = _ALIASES.get(raw, raw) or 'outro'
                cat_id = slug_to_id.get(raw) or slug_to_id.get('outro')
                if cat_id:
                    cursor.execute(
                        f'UPDATE {PROD_TABLE} SET categoria_id=%s WHERE id=%s',
                        [cat_id, pid],
                    )
            cursor.execute(f'ALTER TABLE {PROD_TABLE} DROP COLUMN IF EXISTS categoria_slug_tmp')
            if has_char:
                # só dropa se ainda for texto (não a FK)
                cursor.execute(f"""
                    SELECT data_type FROM information_schema.columns
                    WHERE table_name=%s AND column_name='categoria'
                """, [PROD_TABLE])
                row = cursor.fetchone()
                if row and row[0] in ('character varying', 'varchar', 'text'):
                    cursor.execute(f'ALTER TABLE {PROD_TABLE} DROP COLUMN IF EXISTS categoria')
            changed = True
            self.stdout.write('    + finalizada conversão categoria FK')
        elif has_fk:
            cursor.execute(
                f"""
                UPDATE {PROD_TABLE} p
                SET categoria_id = c.id
                FROM {CAT_TABLE} c
                WHERE p.categoria_id IS NULL
                  AND c.loja_id = %s AND c.slug = 'outro'
                """,
                [loja_id],
            )

        return changed

    def _mark_migration(self, cursor):
        cursor.execute(
            """
            INSERT INTO django_migrations (app, name, applied)
            SELECT 'clinica_beleza', %s, NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM django_migrations
                WHERE app = 'clinica_beleza' AND name = %s
            )
            """,
            [MIG_NAME, MIG_NAME],
        )
