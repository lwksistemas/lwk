"""
Garante colunas Evolution em whatsapp_whatsappconfig nos schemas das lojas.

Uso:
    python manage.py ensure_whatsapp_evolution_fields
    python manage.py ensure_whatsapp_evolution_fields --slug novaimagem
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


COLUMNS = (
    ('whatsapp_provider', "VARCHAR(20) NOT NULL DEFAULT 'meta'"),
    ('evolution_instance_name', 'VARCHAR(64) NOT NULL DEFAULT \'\'' ),
    ('whatsapp_connection_status', "VARCHAR(20) NOT NULL DEFAULT 'disconnected'"),
    ('whatsapp_connected_phone', 'VARCHAR(32) NOT NULL DEFAULT \'\'' ),
    ('whatsapp_connected_at', 'TIMESTAMPTZ NULL'),
    ('enviar_proposta_whatsapp', 'BOOLEAN NOT NULL DEFAULT TRUE'),
    ('enviar_contrato_whatsapp', 'BOOLEAN NOT NULL DEFAULT TRUE'),
    ('enviar_termo_consentimento_whatsapp', 'BOOLEAN NOT NULL DEFAULT TRUE'),
    ('mensagem_confirmacao_agenda', 'TEXT NOT NULL DEFAULT \'\'' ),
)


class Command(BaseCommand):
    help = 'Adiciona campos WhatsApp Web (Evolution) em whatsapp_whatsappconfig por loja.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = skip = 0

        for loja in lojas:
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
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, 'whatsapp_whatsappconfig'):
                        self.stdout.write(self.style.WARNING(
                            f'{loja.slug}: tabela whatsapp_whatsappconfig ausente — rode migrate na loja'
                        ))
                        skip += 1
                        continue
                    for col, ddl in COLUMNS:
                        if not column_exists(cursor, 'whatsapp_whatsappconfig', col):
                            cursor.execute(
                                f'ALTER TABLE whatsapp_whatsappconfig ADD COLUMN {col} {ddl}'
                            )
                            self.stdout.write(f'{loja.slug}: coluna {col} adicionada')
                try:
                    call_command('migrate', 'whatsapp', '0005_whatsapp_evolution_web', database=db_name, verbosity=0)
                except Exception:
                    pass
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'{loja.slug}: {exc}'))
                skip += 1

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) OK, {skip} pulada(s).'))
