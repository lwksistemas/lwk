"""
Utilitários do superadmin.
"""
from django.db import connection


def delete_user_raw(user_id):
    """
    Remove usuário via SQL direto, evitando user.delete() que acessa
    tabelas como stores_store (app stores legado) que podem não existir.

    Ordem: deletar FKs antes de auth_user.
    Usado em: remove_owner_if_orphan (signal), limpar_orfaos (command).
    """
    with connection.cursor() as cursor:
        # (tabela, coluna_que_referencia_user)
        tabelas_user_fk = [
            ('stores_store', 'owner_id'),  # App stores legado; tabela pode não existir
            ('superadmin_usersession', 'user_id'),
            ('superadmin_profissionalusuario', 'user_id'),
            ('superadmin_vendedorusuario', 'user_id'),
            ('superadmin_historico_acesso_global', 'user_id'),
            ('notificacoes_notification', 'user_id'),
            ('push_pushsubscription', 'user_id'),
        ]
        for tabela, coluna in tabelas_user_fk:
            try:
                cursor.execute(
                    f'DELETE FROM {tabela} WHERE {coluna} = %s',
                    [user_id]
                )
            except Exception:
                pass  # Tabela pode não existir (ex: app não migrado)
        cursor.execute('DELETE FROM auth_user_groups WHERE user_id = %s', [user_id])
        cursor.execute(
            'DELETE FROM auth_user_user_permissions WHERE user_id = %s',
            [user_id]
        )
        cursor.execute('DELETE FROM auth_user WHERE id = %s', [user_id])
