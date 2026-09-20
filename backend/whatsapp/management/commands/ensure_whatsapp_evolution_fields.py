"""Garante colunas Evolution em whatsapp_whatsappconfig nos schemas das lojas.

Uso:
    python manage.py ensure_whatsapp_evolution_fields
    python manage.py ensure_whatsapp_evolution_fields --slug novaimagem
"""
import contextlib

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from whatsapp.confirmacao_agenda_service import loja_usa_confirmacao_agenda

COLUMNS = (
    ("whatsapp_provider", "VARCHAR(20) NOT NULL DEFAULT 'meta'"),
    ("evolution_instance_name", "VARCHAR(64) NOT NULL DEFAULT ''" ),
    ("whatsapp_connection_status", "VARCHAR(20) NOT NULL DEFAULT 'disconnected'"),
    ("whatsapp_connected_phone", "VARCHAR(32) NOT NULL DEFAULT ''" ),
    ("whatsapp_connected_at", "TIMESTAMPTZ NULL"),
    ("enviar_proposta_whatsapp", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("enviar_contrato_whatsapp", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("enviar_termo_consentimento_whatsapp", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("mensagem_confirmacao_agenda", "TEXT NOT NULL DEFAULT ''" ),
    ("mensagem_cobranca", "TEXT NOT NULL DEFAULT ''" ),
    ("confirmacao_antecedencias_dias", "JSONB NOT NULL DEFAULT '[1]'::jsonb"),
)

ENVIO_TABLE = "whatsapp_whatsappconfirmacaoenvio"
MIGRATION_CONFIRMACAO = "0008_confirmacao_antecedencias"


class Command(BaseCommand):
    help = "Adiciona campos WhatsApp Web (Evolution) em whatsapp_whatsappconfig por loja."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True).select_related("tipo_loja")
        ok = skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f"Pulando {loja.slug}: DB indisponível"))
                skip += 1
                continue
            criar_envio_table = loja_usa_confirmacao_agenda(loja)
            tabela_ausente = False
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    # Defesa em profundidade: garante que current_schema() é o schema da
                    # loja atual. Sem isso, reuso de conexão pode deixar o search_path
                    # apontando para outro schema (public), fazendo column_exists avaliar
                    # a tabela errada e o ALTER não ser aplicado nas demais lojas.
                    schema = db_name.replace("-", "_")
                    cursor.execute(f'SET search_path TO "{schema}", public')

                    if not table_exists(cursor, "whatsapp_whatsappconfig"):
                        self.stdout.write(self.style.WARNING(
                            f"{loja.slug}: tabela whatsapp_whatsappconfig ausente — rode migrate na loja",
                        ))
                        tabela_ausente = True
                    else:
                        for col, ddl in COLUMNS:
                            if not column_exists(cursor, "whatsapp_whatsappconfig", col):
                                cursor.execute(
                                    f"ALTER TABLE whatsapp_whatsappconfig ADD COLUMN {col} {ddl}",
                                )
                                self.stdout.write(f"{loja.slug}: coluna {col} adicionada")
                        if criar_envio_table and not table_exists(cursor, ENVIO_TABLE):
                            cursor.execute(f"""
                                CREATE TABLE {ENVIO_TABLE} (
                                    id BIGSERIAL PRIMARY KEY,
                                    appointment_id INTEGER NOT NULL,
                                    modulo VARCHAR(32) NOT NULL DEFAULT 'clinica_beleza',
                                    regra_dias SMALLINT NOT NULL,
                                    enviado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
                                )
                            """)
                            cursor.execute(
                                f"CREATE UNIQUE INDEX IF NOT EXISTS whatsapp_confirmacao_envio_unico "
                                f"ON {ENVIO_TABLE} (modulo, appointment_id, regra_dias)",
                            )
                            cursor.execute(
                                f"CREATE INDEX IF NOT EXISTS wa_conf_envio_appt_idx "
                                f"ON {ENVIO_TABLE} (modulo, appointment_id)",
                            )
                            self.stdout.write(f"{loja.slug}: tabela {ENVIO_TABLE} criada")
                if tabela_ausente:
                    skip += 1
                    continue
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"{loja.slug}: {exc}"))
                skip += 1
                continue
            finally:
                # Fecha o socket da loja ao fim de cada iteração (Padrão A). Sem isso, a
                # conexão fica cacheada em `connections` e a próxima loja pode reusá-la
                # com o search_path errado.
                with contextlib.suppress(Exception):
                    connections[db_name].close()

            # migrate FORA do bloco de conexão aberta e após fechar o socket da loja,
            # para não deixar a conexão em estado que afete a próxima iteração.
            with contextlib.suppress(Exception):
                call_command("migrate", "whatsapp", MIGRATION_CONFIRMACAO, database=db_name, verbosity=0)
                connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok} loja(s) OK, {skip} pulada(s)."))
