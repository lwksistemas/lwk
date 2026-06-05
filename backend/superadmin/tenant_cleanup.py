"""
Helpers para exclusão segura em schemas tenant (tabelas/colunas podem estar defasadas).
"""
import logging

logger = logging.getLogger(__name__)


def _is_missing_db_object(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        'does not exist' in msg
        or 'undefinedtable' in msg
        or 'undefinedcolumn' in msg
        or 'relation' in msg and 'does not exist' in msg
    )


def tenant_table_exists(db_alias: str, table: str) -> bool:
    from django.db import connections

    try:
        with connections[db_alias].cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = current_schema() AND table_name = %s
                LIMIT 1
                """,
                [table],
            )
            return cursor.fetchone() is not None
    except Exception:
        return False


def safe_delete_tenant_by_loja_id(db_alias: str, table: str, loja_id: int, label: str = '') -> int:
    """DELETE FROM table WHERE loja_id = %s; ignora tabela/coluna inexistente."""
    from django.db import connections

    label = label or table
    if not tenant_table_exists(db_alias, table):
        logger.debug('   ℹ️ %s: tabela ausente no schema (ok)', label)
        return 0
    try:
        with connections[db_alias].cursor() as cursor:
            cursor.execute(f'DELETE FROM {table} WHERE loja_id = %s', [loja_id])
            count = cursor.rowcount
            if count:
                logger.info('   ✅ %s %s deletado(s) (SQL)', count, label)
            return count
    except Exception as e:
        if _is_missing_db_object(e):
            logger.debug('   ℹ️ %s: objeto DB ausente (ok)', label)
            return 0
        logger.warning('   ⚠️ Erro ao deletar %s: %s', label, e)
        return 0


# Ordem aproximada (dependentes primeiro) — Clínica da Beleza
CLINICA_BELEZA_DELETE_ORDER = [
    ('clinica_beleza_payment', 'pagamentos'),
    ('clinica_beleza_prescricaomemed', 'prescrições Memed'),
    ('clinica_beleza_documentoclinico', 'documentos clínicos'),
    ('clinica_beleza_consultaevolucao', 'evoluções consulta'),
    ('clinica_beleza_consulta', 'consultas'),
    ('clinica_beleza_appointmentprocedure', 'procedimentos do agendamento'),
    ('clinica_beleza_movimentacaoestoque', 'movimentações estoque'),
    ('clinica_beleza_appointment', 'agendamentos'),
    ('clinica_beleza_professional_commissions', 'comissões profissional'),
    ('clinica_beleza_bloqueiohorario', 'bloqueios horário'),
    ('clinica_beleza_horariotrabalhoprofissional', 'horários trabalho'),
    ('clinica_beleza_campanhapromocao', 'campanhas promoção'),
    ('clinica_beleza_anamneses', 'anamneses'),
    ('clinica_beleza_procedureprotocol', 'protocolos procedimento'),
    ('clinica_beleza_procedure', 'procedimentos'),
    ('clinica_beleza_professional', 'profissionais'),
    ('clinica_beleza_patient', 'pacientes'),
    ('clinica_beleza_memed_timbrado', 'timbrado Memed'),
    ('clinica_beleza_locais_atendimento', 'locais atendimento'),
    ('clinica_beleza_produtoestoque', 'produtos estoque'),
]


def delete_clinica_beleza_tenant_data(db_alias: str, loja_id: int) -> None:
    """Remove dados da clínica no schema tenant via SQL (resiliente a migrations pendentes)."""
    for table, label in CLINICA_BELEZA_DELETE_ORDER:
        safe_delete_tenant_by_loja_id(db_alias, table, loja_id, label)
