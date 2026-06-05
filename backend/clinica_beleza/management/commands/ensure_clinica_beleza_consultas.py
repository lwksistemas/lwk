"""
Garante tabelas de Consultas/Protocolos nos schemas das lojas (Clínica da Beleza).

Necessário quando migrate_all_lojas falha por histórico legado inconsistente.
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

SQL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS clinica_beleza_protocolos (
        id BIGSERIAL PRIMARY KEY,
        loja_id INTEGER NOT NULL,
        nome VARCHAR(200) NOT NULL,
        descricao TEXT NOT NULL DEFAULT '',
        preparacao TEXT NOT NULL DEFAULT '',
        execucao TEXT NOT NULL DEFAULT '',
        pos_procedimento TEXT NOT NULL DEFAULT '',
        tempo_estimado INTEGER NOT NULL DEFAULT 30 CHECK (tempo_estimado >= 0),
        materiais_necessarios TEXT NOT NULL DEFAULT '',
        contraindicacoes TEXT NOT NULL DEFAULT '',
        cuidados_especiais TEXT NOT NULL DEFAULT '',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        procedure_id BIGINT NOT NULL REFERENCES clinica_beleza_procedure(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS clinica_beleza_consultas (
        id BIGSERIAL PRIMARY KEY,
        loja_id INTEGER NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
        data_inicio TIMESTAMPTZ NULL,
        data_fim TIMESTAMPTZ NULL,
        observacoes_gerais TEXT NOT NULL DEFAULT '',
        protocolo_notas TEXT NOT NULL DEFAULT '',
        valor_consulta NUMERIC(10, 2) NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        appointment_id BIGINT NOT NULL UNIQUE REFERENCES clinica_beleza_appointment(id) ON DELETE CASCADE,
        patient_id BIGINT NOT NULL REFERENCES clinica_beleza_patient(id) ON DELETE CASCADE,
        procedure_id BIGINT NOT NULL REFERENCES clinica_beleza_procedure(id) ON DELETE CASCADE,
        professional_id BIGINT NULL REFERENCES clinica_beleza_professional(id) ON DELETE SET NULL,
        protocol_id BIGINT NULL REFERENCES clinica_beleza_protocolos(id) ON DELETE SET NULL,
        local_atendimento_id BIGINT NULL REFERENCES clinica_beleza_locais_atendimento(id) ON DELETE SET NULL,
        convenio_id BIGINT NULL REFERENCES clinica_beleza_convenios(id) ON DELETE SET NULL
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS clinica_bel_patient_fd5eeb_idx
        ON clinica_beleza_consultas (patient_id, status);
    """,
    """
    CREATE INDEX IF NOT EXISTS clinica_bel_loja_id_3a1eb9_idx
        ON clinica_beleza_consultas (loja_id, status);
    """,
    """
    CREATE TABLE IF NOT EXISTS clinica_beleza_anamneses (
        id BIGSERIAL PRIMARY KEY,
        loja_id INTEGER NOT NULL,
        queixa_principal TEXT NOT NULL DEFAULT '',
        historico_medico TEXT NOT NULL DEFAULT '',
        medicamentos_uso TEXT NOT NULL DEFAULT '',
        alergias TEXT NOT NULL DEFAULT '',
        condicoes_clinicas TEXT NOT NULL DEFAULT '',
        tipo_pele VARCHAR(100) NOT NULL DEFAULT '',
        pressao_arterial VARCHAR(20) NOT NULL DEFAULT '',
        peso NUMERIC(5, 2) NULL,
        altura NUMERIC(4, 2) NULL,
        observacoes TEXT NOT NULL DEFAULT '',
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        patient_id BIGINT NOT NULL UNIQUE REFERENCES clinica_beleza_patient(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS clinica_beleza_consulta_evolucoes (
        id BIGSERIAL PRIMARY KEY,
        loja_id INTEGER NOT NULL,
        descricao TEXT NOT NULL DEFAULT '',
        procedimento_realizado TEXT NOT NULL DEFAULT '',
        produtos_utilizados TEXT NOT NULL DEFAULT '',
        orientacoes TEXT NOT NULL DEFAULT '',
        protocolo_snapshot TEXT NOT NULL DEFAULT '',
        satisfacao SMALLINT NULL CHECK (satisfacao IS NULL OR (satisfacao >= 0 AND satisfacao <= 32767)),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        consulta_id BIGINT NOT NULL REFERENCES clinica_beleza_consultas(id) ON DELETE CASCADE,
        patient_id BIGINT NOT NULL REFERENCES clinica_beleza_patient(id) ON DELETE CASCADE,
        professional_id BIGINT NULL REFERENCES clinica_beleza_professional(id) ON DELETE SET NULL
    );
    """,
]

COLUMN_PATCHES = [
    (
        'clinica_beleza_consultas',
        'local_atendimento_id',
        'ALTER TABLE clinica_beleza_consultas ADD COLUMN local_atendimento_id BIGINT NULL '
        'REFERENCES clinica_beleza_locais_atendimento(id) ON DELETE SET NULL',
    ),
    (
        'clinica_beleza_consultas',
        'convenio_id',
        'ALTER TABLE clinica_beleza_consultas ADD COLUMN convenio_id BIGINT NULL '
        'REFERENCES clinica_beleza_convenios(id) ON DELETE SET NULL',
    ),
    (
        'clinica_beleza_patient',
        'convenio_id',
        'ALTER TABLE clinica_beleza_patient ADD COLUMN convenio_id BIGINT NULL '
        'REFERENCES clinica_beleza_convenios(id) ON DELETE SET NULL',
    ),
]


def _apply_patches(cursor):
    for table, column, sql in COLUMN_PATCHES:
        if table_exists(cursor, table) and not column_exists(cursor, table, column):
            cursor.execute(sql)


class Command(BaseCommand):
    help = 'Cria tabelas de consultas/protocolos da Clínica da Beleza nos bancos das lojas (IF NOT EXISTS).'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = 0
        skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue

            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                self.stdout.write(self.style.WARNING(f'SKIP loja={loja.id}: banco não configurado'))
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, 'clinica_beleza_appointment'):
                        skip += 1
                        self.stdout.write(self.style.WARNING(
                            f'SKIP loja={loja.id} ({loja.nome}): sem tabelas clinica_beleza'
                        ))
                        continue

                    for sql in SQL_STATEMENTS:
                        cursor.execute(sql)
                    _apply_patches(cursor)

                ok += 1
                self.stdout.write(self.style.SUCCESS(
                    f'OK loja={loja.id} ({loja.nome}) db={db_name}'
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id} ({loja.nome}): {exc}'))
            finally:
                try:
                    connections[db_name].close()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) OK, {skip} ignorada(s).'))
