"""
Garante tabelas do módulo financeiro CRM (migration 0064) nos schemas das lojas.

Uso:
    python manage.py ensure_crm_financeiro_tabelas
    python manage.py ensure_crm_financeiro_tabelas --slug vendasbeta
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from crm_vendas.schema_service import configurar_schema_crm_loja
from superadmin.models import Loja

TABLE_GRUPO = 'crm_financeiro_grupo'
TABLE_LANCAMENTO = 'crm_financeiro_lancamento'
TABLE_RECORRENCIA = 'crm_financeiro_recorrencia'


def _aplicar_recorrencia_sql(cursor, schema_name: str) -> bool:
    """Cria tabela/coluna da migration 0065 sem rodar migrate completo."""
    cursor.execute(f'SET search_path TO "{schema_name}", public')
    if not table_exists(cursor, TABLE_GRUPO) or not table_exists(cursor, TABLE_LANCAMENTO):
        return False

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{schema_name}".{TABLE_RECORRENCIA} (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            tipo VARCHAR(10) NOT NULL,
            descricao VARCHAR(200) NOT NULL,
            valor NUMERIC(12, 2) NOT NULL,
            frequencia VARCHAR(12) NOT NULL DEFAULT 'mensal',
            proximo_vencimento DATE NOT NULL,
            data_fim DATE NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            observacoes TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            grupo_id BIGINT NULL REFERENCES "{schema_name}".{TABLE_GRUPO}(id) ON DELETE SET NULL,
            vendedor_id BIGINT NOT NULL REFERENCES "{schema_name}".crm_vendas_vendedor(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        f"""
        ALTER TABLE "{schema_name}".{TABLE_LANCAMENTO}
        ADD COLUMN IF NOT EXISTS recorrencia_id BIGINT NULL
        REFERENCES "{schema_name}".{TABLE_RECORRENCIA}(id) ON DELETE SET NULL
        """
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS crm_finance_loja_id_recorr_idx
        ON "{schema_name}".{TABLE_RECORRENCIA} (loja_id, is_active, proximo_vencimento)
        """
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS crm_finance_loja_id_rec_v_idx
        ON "{schema_name}".{TABLE_RECORRENCIA} (loja_id, vendedor_id, tipo)
        """
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS {TABLE_RECORRENCIA}_loja_id_idx
        ON "{schema_name}".{TABLE_RECORRENCIA} (loja_id)
        """
    )
    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'crm_vendas', '0065_financeiro_recorrencia', NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'crm_vendas' AND name = '0065_financeiro_recorrencia'
        )
        """
    )
    return table_exists(cursor, TABLE_RECORRENCIA)


class Command(BaseCommand):
    help = 'Aplica migrations financeiro CRM (0064+) em lojas que ainda não têm as tabelas.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        ok = skip = fixed = 0

        lojas = Loja.objects.filter(is_active=True, database_created=True).select_related('tipo_loja')
        for loja in lojas:
            tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip()
            if tipo_slug != 'crm-vendas':
                continue
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue

            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f'Pulando {loja.slug}: DB indisponível'))
                skip += 1
                continue

            schema_name = db_name.replace('-', '_')
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}", public')
                    tem_grupo = table_exists(cursor, TABLE_GRUPO)
                    tem_lanc = table_exists(cursor, TABLE_LANCAMENTO)
                    tem_rec = table_exists(cursor, TABLE_RECORRENCIA)

                if tem_grupo and tem_lanc and tem_rec:
                    self.stdout.write(f'{loja.slug}: tabelas financeiro OK')
                    ok += 1
                    continue

                if tem_grupo and tem_lanc and not tem_rec:
                    with conn.cursor() as cursor:
                        if _aplicar_recorrencia_sql(cursor, schema_name):
                            fixed += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'{loja.slug}: tabela recorrência criada (SQL)')
                            )
                            continue

                self.stdout.write(
                    self.style.WARNING(
                        f'{loja.slug}: faltam tabelas (grupo={tem_grupo}, lancamento={tem_lanc}, '
                        f'recorrencia={tem_rec}) — aplicando migrations'
                    )
                )
                if configurar_schema_crm_loja(loja):
                    fixed += 1
                    self.stdout.write(self.style.SUCCESS(f'{loja.slug}: schema financeiro corrigido'))
                else:
                    with conn.cursor() as cursor:
                        if _aplicar_recorrencia_sql(cursor, schema_name):
                            fixed += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'{loja.slug}: recorrência criada via SQL (fallback)')
                            )
                        else:
                            skip += 1
                            self.stdout.write(self.style.ERROR(f'{loja.slug}: falha ao corrigir schema'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'{loja.slug}: {exc}'))
                skip += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Concluído: {ok} OK, {fixed} corrigida(s), {skip} pulada(s)/falha(s).'
            )
        )
