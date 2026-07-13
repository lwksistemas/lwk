import logging

from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from core.logging_utils import mask_email

logger = logging.getLogger(__name__)

from .helpers import _limpar_arquivos_orfaos_loja

# ---------------------------------------------------------------------------
# Helpers privados do signal de exclusão
# ---------------------------------------------------------------------------

def _setup_db_alias(instance):
    """Configura e retorna o db_alias da loja, ou None se não disponível."""
    from django.conf import settings
    db_name = getattr(instance, "database_name", None)
    if not db_name:
        return None
    import os
    if "postgres" in os.environ.get("DATABASE_URL", "").lower() and db_name not in settings.DATABASES:
        try:
            from core.db_config import ensure_loja_database_config
            ensure_loja_database_config(db_name, conn_max_age=0)
        except Exception as e:
            logger.warning(f"   ⚠️ Não foi possível configurar banco da loja {db_name}: {e}")
    return db_name if db_name in settings.DATABASES else None


def _delete_evolution_whatsapp(loja_id):
    """Remove instância Evolution (WhatsApp Web) da loja."""
    try:
        from whatsapp.evolution_cleanup import delete_evolution_for_loja
        delete_evolution_for_loja(loja_id)
    except Exception as e:
        logger.warning(f"   ⚠️ Erro ao remover Evolution: {e}")


def _delete_asaas_assinatura(instance):
    """Remove LojaAssinatura por slug (evita órfãos)."""
    try:
        from asaas_integration.models import LojaAssinatura
        n = LojaAssinatura.objects.filter(loja_slug=instance.slug).count()
        LojaAssinatura.objects.filter(loja_slug=instance.slug).delete()
        if n:
            logger.info(f"   ✅ {n} assinatura(s) Asaas (loja_slug) removida(s)")
    except Exception as e:
        logger.warning(f"   ⚠️ Erro ao remover LojaAssinatura por slug: {e}")


def _delete_crm_data(loja_id, db_alias):
    """Deleta todos os dados CRM Vendas da loja."""
    from crm_vendas.models import Atividade, Conta, Contato, Lead, Oportunidade, Vendedor

    def _delete(model, nome):
        try:
            qs = model.objects.all_without_filter().filter(loja_id=loja_id) if hasattr(model.objects, "all_without_filter") else model.objects.filter(loja_id=loja_id)
            if db_alias:
                qs = qs.using(db_alias)
            count = qs.count()
            qs.delete()
            logger.info(f"   ✅ {count} {nome} (CRM Vendas) deletados")
        except Exception as e:
            if "does not exist" in str(e).lower():
                logger.debug(f"   ℹ️ Schema vazio: {nome} não existem (ok)")
            else:
                logger.warning(f"   ⚠️ Erro ao deletar {nome} CRM Vendas: {e}")

    for model, nome in [
        (Atividade, "atividades"), (Oportunidade, "oportunidades"), (Lead, "leads"),
        (Contato, "contatos"), (Conta, "contas"), (Vendedor, "vendedores"),
    ]:
        _delete(model, nome)


def _delete_clinica_beleza_data(loja_id, db_alias):
    """Deleta todos os dados Clínica da Beleza da loja."""
    if db_alias:
        from superadmin.tenant_cleanup import delete_clinica_beleza_tenant_data
        delete_clinica_beleza_tenant_data(db_alias, loja_id)
        return

    from clinica_beleza.models import (
        Appointment,
        BloqueioHorario,
        CampanhaPromocao,
        HorarioTrabalhoProfissional,
        Patient,
        Payment,
        Procedure,
        Professional,
    )

    def _delete(model, nome):
        try:
            qs = model.objects.all_without_filter().filter(loja_id=loja_id) if hasattr(model.objects, "all_without_filter") else model.objects.filter(loja_id=loja_id)
            count = qs.count()
            qs.delete()
            logger.info(f"   ✅ {count} {nome} (Clínica da Beleza) deletados")
        except Exception as e:
            err = str(e).lower()
            if "does not exist" in err or "undefinedcolumn" in err:
                logger.debug(f"   ℹ️ {nome}: schema parcial (ok)")
            else:
                logger.warning(f"   ⚠️ Erro ao deletar {nome} Clínica da Beleza: {e}")

    for model, nome in [
        (Payment, "pagamentos"), (Appointment, "agendamentos"),
        (BloqueioHorario, "bloqueios horário"),
        (HorarioTrabalhoProfissional, "horários trabalho profissional"),
        (CampanhaPromocao, "campanhas promoção"), (Procedure, "procedimentos"),
        (Professional, "profissionais"), (Patient, "pacientes"),
    ]:
        _delete(model, nome)


def _delete_tenant_data(instance, loja_id, db_alias, tipo_loja_nome):
    """Deleta dados específicos do tipo de app da loja."""
    if tipo_loja_nome == "CRM Vendas":
        _delete_crm_data(loja_id, db_alias)
    elif tipo_loja_nome == "Clínica da Beleza":
        _delete_clinica_beleza_data(loja_id, db_alias)
    elif tipo_loja_nome:
        logger.info(
            f"   ℹ️ Tipo {tipo_loja_nome!r}: sem exclusão linha-a-linha neste signal; "
            "schema tenant será removido por DROP SCHEMA CASCADE.",
        )


def _delete_user_sessions(instance):
    """Deleta sessões do usuário owner."""
    try:
        from superadmin.models import UserSession
        owner_id = instance.owner_id
        if owner_id:
            count = UserSession.objects.filter(user_id=owner_id).count()
            UserSession.objects.filter(user_id=owner_id).delete()
            logger.info(f"   ✅ {count} sessões deletadas")
    except Exception as e:
        logger.warning(f"   ⚠️ Erro ao deletar sessões: {e}")


def _drop_postgres_schema(instance):
    """Exclui o schema PostgreSQL da loja com CASCADE."""
    import os
    if "postgres" not in os.environ.get("DATABASE_URL", "").lower():
        logger.info("   ℹ️ Não está usando PostgreSQL, schema não será removido")
        return
    try:
        from django.db import connection
        schema_name = instance.database_name.replace("-", "_")
        if not schema_name or schema_name == "public":
            logger.warning(f"   ⚠️ Schema inválido ou público, não será removido: {schema_name}")
            return
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                [schema_name],
            )
            if cursor.fetchone():
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                logger.info(f"   ✅ Schema PostgreSQL removido: {schema_name}")
            else:
                logger.info(f"   ℹ️ Schema PostgreSQL não existe: {schema_name}")
    except Exception as e:
        logger.error(f"   ❌ Erro ao remover schema PostgreSQL: {e}")
        import traceback
        logger.error(traceback.format_exc())


def _safety_net_default_tables(loja_id):
    """Rede de segurança: limpa tabelas do schema public com loja_id."""
    try:
        from django.db import connection, transaction

        from superadmin.orfaos_config import TABELAS_LOJA_ID_DEFAULT, tabela_existe_em_public
        for tabela, coluna in TABELAS_LOJA_ID_DEFAULT:
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    if not tabela_existe_em_public(cursor, tabela):
                        continue
                    cursor.execute(f"DELETE FROM {tabela} WHERE {coluna} = %s", [loja_id])
                    if cursor.rowcount:
                        logger.info(f"   ✅ Safety net: {cursor.rowcount} linha(s) em {tabela} removida(s)")
            except Exception as e:
                logger.warning(f"   ⚠️ Safety net {tabela}: {e}")
    except Exception as e:
        logger.warning(f"   ⚠️ Erro na rede de segurança TABELAS_LOJA_ID_DEFAULT: {e}")


def _cleanup_db_config(instance):
    """Remove configuração do banco de settings.DATABASES."""
    from django.conf import settings
    db_name = getattr(instance, "database_name", None)
    if db_name and db_name in settings.DATABASES:
        try:
            del settings.DATABASES[db_name]
            logger.info(f"   ✅ Config do banco removida do settings: {db_name}")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao remover config do banco: {e}")


# ---------------------------------------------------------------------------

@receiver(pre_delete, sender="superadmin.Loja")
def delete_all_loja_data(sender, instance, **kwargs):
    """Deleta TODOS os dados relacionados quando uma loja é excluída.

    IMPORTANTE (v993): NÃO usar transaction.atomic() neste signal. O pre_delete
    já roda dentro da transação do loja.delete(). Transações aninhadas criam
    savepoints e podem causar rollback silencioso, impedindo a exclusão da loja.

    Sempre tenta DROP SCHEMA (PostgreSQL) e rede TABELAS_LOJA_ID_DEFAULT, mesmo sem tipo_loja.
    Deleta em cascata (quando tipo_loja está definido):
    - Funcionários/Vendedores
    - Clientes
    - Agendamentos
    - Profissionais
    - Procedimentos
    - Leads
    - Sessões de usuários

    IMPORTANTE:
    - NÃO deleta o owner aqui (feito na views.py após a exclusão da loja)
    - Usa getattr para acessar tipo_loja de forma segura

    Args:
        sender: Modelo Loja
        instance: Instância da loja sendo deletada
        **kwargs: Argumentos adicionais do signal

    """
    loja_id = instance.id
    loja_nome = instance.nome
    tipo_loja_nome = getattr(instance.tipo_loja, "nome", None) if instance.tipo_loja else None

    logger.info(f"🗑️ Iniciando exclusão em cascata para loja: {loja_nome} (ID: {loja_id})")
    if not tipo_loja_nome:
        logger.warning(
            f"⚠️ Tipo de app não disponível para {loja_nome} (ID {loja_id}): "
            "sem DELETE linha-a-linha por modelo; execução segue para DROP SCHEMA / rede de segurança.",
        )

    try:
        db_alias = _setup_db_alias(instance)
        _delete_evolution_whatsapp(loja_id)
        _delete_asaas_assinatura(instance)
        _delete_tenant_data(instance, loja_id, db_alias, tipo_loja_nome)
        _delete_user_sessions(instance)
        logger.info("   ℹ️ Pagamentos Asaas serão removidos pela views.py")
        _drop_postgres_schema(instance)
        _safety_net_default_tables(loja_id)
        _cleanup_db_config(instance)
        _limpar_arquivos_orfaos_loja(instance)
        logger.info(f"✅ Exclusão em cascata concluída para loja: {loja_nome}")
    except Exception as e:
        logger.error(f"❌ Erro durante exclusão em cascata da loja {loja_nome}: {e}")
        import traceback
        logger.error(traceback.format_exc())


@receiver(post_delete, sender="superadmin.Loja")
def remove_owner_if_orphan(sender, instance, **kwargs):
    """Após excluir uma loja, remove o usuário proprietário se ele ficar órfão
    (não for dono de mais nenhuma loja). Evita usuários órfãos que bloqueiam
    criar nova loja com o mesmo login.

    IMPORTANTE: Usa transaction.on_commit() para executar APÓS o commit do delete.
    Caso contrário, se user.delete() falhar (ex: tabela stores_store inexistente),
    a transação do PostgreSQL seria abortada e o delete da loja seria revertido.
    """
    from django.db import transaction

    owner_id = getattr(instance, "owner_id", None)
    loja_slug = getattr(instance, "slug", "unknown")
    loja_nome = getattr(instance, "nome", "unknown")

    logger.info(f"🔍 Signal remove_owner_if_orphan: Loja excluída: {loja_nome} (slug: {loja_slug}, owner_id: {owner_id})")

    if not owner_id:
        logger.warning(f"   ⚠️ owner_id não encontrado para loja {loja_slug}")
        return

    def _remover_owner_apos_commit():
        from django.contrib.auth.models import User

        from superadmin.models import Loja
        from superadmin.utils import delete_user_raw

        logger.info(f"   🔍 Verificando se owner {owner_id} ficou órfão após exclusão da loja {loja_slug}...")

        # Verificar se owner possui outras lojas
        outras_lojas = Loja.objects.filter(owner_id=owner_id).count()
        if outras_lojas > 0:
            logger.info(f"   ℹ️  Owner {owner_id} possui {outras_lojas} loja(s) ativa(s). Não será removido.")
            return

        logger.info(f"   🔍 Owner {owner_id} não possui outras lojas. Verificando se pode ser removido...")

        try:
            user = User.objects.filter(id=owner_id).first()
            if not user:
                logger.warning(f"   ⚠️ Usuário {owner_id} não encontrado no banco de dados")
                return

            if user.is_superuser:
                logger.info(f"   ℹ️  Usuário {user.username} é superuser. Não será removido.")
                return

            logger.info(
                "Removendo usuário órfão: user_id=%s, username=%s, email=%s",
                owner_id,
                user.username,
                mask_email(user.email),
            )
            delete_user_raw(owner_id)
            logger.info(f"   ✅ Usuário órfão removido com sucesso: {user.username}")

        except Exception as e:
            logger.error(f"   ❌ Erro ao remover owner órfão {owner_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())

    logger.info("   📝 Agendando remoção de owner órfão para após commit da transação...")
    transaction.on_commit(_remover_owner_apos_commit)

