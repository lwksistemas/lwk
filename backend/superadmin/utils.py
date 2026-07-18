"""Utilitários do superadmin.
"""
import contextlib
import logging

from django.db import connection

logger = logging.getLogger(__name__)


def _clear_user_fk_refs(cursor, user_id: int) -> None:
    """Remove ou anula todas as FKs de ``public`` que apontam para ``auth_user.id``.

    Necessário porque DELETE raw em ``auth_user`` não passa pelo ORM Django
    (``on_delete=SET_NULL`` / CASCADE do model). A tabela real de sessão é
    ``user_sessions`` (não ``superadmin_usersession``).
    """
    cursor.execute(
        """
        SELECT
            tc.table_name,
            kcu.column_name,
            c.is_nullable
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema = tc.table_schema
        JOIN information_schema.columns AS c
          ON c.table_schema = tc.table_schema
         AND c.table_name = tc.table_name
         AND c.column_name = kcu.column_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
          AND ccu.table_schema = 'public'
          AND ccu.table_name = 'auth_user'
          AND ccu.column_name = 'id'
        """,
    )
    for table_name, column_name, is_nullable in cursor.fetchall():
        if table_name in ("auth_user_groups", "auth_user_user_permissions"):
            continue
        try:
            if is_nullable == "YES":
                cursor.execute(
                    f'UPDATE "{table_name}" SET "{column_name}" = NULL WHERE "{column_name}" = %s',
                    [user_id],
                )
            else:
                cursor.execute(
                    f'DELETE FROM "{table_name}" WHERE "{column_name}" = %s',
                    [user_id],
                )
        except Exception as exc:  # noqa: BLE001 — tabela/coluna pode ser especial
            logger.warning(
                "delete_user_raw: falha ao limpar %s.%s user_id=%s: %s",
                table_name,
                column_name,
                user_id,
                exc,
            )


def delete_user_raw(user_id):
    """Remove usuário via SQL direto, evitando user.delete() que acessa
    tabelas como stores_store (app stores legado) que podem não existir.

    Ordem: limpar FKs (descoberta + lista conhecida) → JWT → groups → auth_user.
    Usado em: remove_owner_if_orphan (signal), limpar_orfaos (command).
    """
    with connection.cursor() as cursor:
        # Lista explícita (cobre DBs sem information_schema completo / nomes legados).
        tabelas_user_fk = [
            ("stores_store", "owner_id"),
            ("user_sessions", "user_id"),  # UserSession.db_table real
            ("superadmin_usersession", "user_id"),  # nome antigo incorreto (legado)
            ("superadmin_profissionalusuario", "user_id"),
            ("superadmin_vendedorusuario", "user_id"),
            ("superadmin_historico_acesso_global", "user_id"),
            ("notificacoes_notification", "user_id"),
            ("push_pushsubscription", "user_id"),
            ("django_admin_log", "user_id"),
        ]
        for tabela, coluna in tabelas_user_fk:
            with contextlib.suppress(Exception):
                cursor.execute(
                    f'DELETE FROM "{tabela}" WHERE "{coluna}" = %s',
                    [user_id],
                )

        # SET NULL onde o model Django espera (FK nullable).
        for tabela, coluna in (
            ("superadmin_violacoes_seguranca", "user_id"),
            ("superadmin_violacoes_seguranca", "resolvido_por_id"),
        ):
            with contextlib.suppress(Exception):
                cursor.execute(
                    f'UPDATE "{tabela}" SET "{coluna}" = NULL WHERE "{coluna}" = %s',
                    [user_id],
                )

        # Rede de segurança: qualquer outra FK pública para auth_user.
        with contextlib.suppress(Exception):
            _clear_user_fk_refs(cursor, user_id)

        # JWT blacklist (rest_framework_simplejwt) — antes de apagar auth_user
        for sql in (
            """
            DELETE FROM token_blacklist_blacklistedtoken
            WHERE token_id IN (
                SELECT id FROM token_blacklist_outstandingtoken WHERE user_id = %s
            )
            """,
            "DELETE FROM token_blacklist_outstandingtoken WHERE user_id = %s",
        ):
            with contextlib.suppress(Exception):
                cursor.execute(sql, [user_id])
        cursor.execute("DELETE FROM auth_user_groups WHERE user_id = %s", [user_id])
        cursor.execute(
            "DELETE FROM auth_user_user_permissions WHERE user_id = %s",
            [user_id],
        )
        cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])
