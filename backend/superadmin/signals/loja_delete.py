import logging
import os
import shutil
from pathlib import Path

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from core.logging_utils import mask_email

logger = logging.getLogger(__name__)

from .helpers import _limpar_arquivos_orfaos_loja

@receiver(pre_delete, sender='superadmin.Loja')
def delete_all_loja_data(sender, instance, **kwargs):
    """
    Deleta TODOS os dados relacionados quando uma loja é excluída.
    
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
    # Acesso seguro ao tipo_loja para evitar KeyError
    tipo_loja_nome = getattr(instance.tipo_loja, 'nome', None) if instance.tipo_loja else None
    
    logger.info(f"🗑️ Iniciando exclusão em cascata para loja: {loja_nome} (ID: {loja_id})")
    if not tipo_loja_nome:
        logger.warning(
            f"⚠️ Tipo de app não disponível para {loja_nome} (ID {loja_id}): "
            "sem DELETE linha-a-linha por modelo; execução segue para DROP SCHEMA / rede de segurança."
        )

    try:
        # Alias do banco da loja: usar schema isolado (evita deletar no default e criar órfãos)
        from django.conf import settings
        db_alias = None
        db_name = getattr(instance, 'database_name', None)
        if db_name:
            import os
            DATABASE_URL = os.environ.get('DATABASE_URL', '')
            if 'postgres' in DATABASE_URL.lower() and db_name not in settings.DATABASES:
                try:
                    from core.db_config import ensure_loja_database_config
                    ensure_loja_database_config(db_name, conn_max_age=0)
                except Exception as e:
                    logger.warning(f"   ⚠️ Não foi possível configurar banco da loja {db_name}: {e}")
            if db_name in settings.DATABASES:
                db_alias = db_name

        # 0. Remover instância Evolution (WhatsApp Web)
        try:
            from whatsapp.evolution_cleanup import delete_evolution_for_loja

            delete_evolution_for_loja(loja_id)
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao remover Evolution: {e}")

        # 0b. Remover LojaAssinatura por slug (evita órfãos se loja for excluída fora da API)
        try:
            from asaas_integration.models import LojaAssinatura
            n = LojaAssinatura.objects.filter(loja_slug=instance.slug).count()
            LojaAssinatura.objects.filter(loja_slug=instance.slug).delete()
            if n:
                logger.info(f"   ✅ {n} assinatura(s) Asaas (loja_slug) removida(s)")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao remover LojaAssinatura por slug: {e}")
        
        # 1. Deletar funcionários/vendedores baseado no tipo de app (no schema da loja quando db_alias definido)
        if tipo_loja_nome == 'CRM Vendas':
            from crm_vendas.models import Atividade, Oportunidade, Lead, Contato, Conta, Vendedor
            _db = db_alias

            def _delete_crm(model, nome):
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    if _db:
                        qs = qs.using(_db)
                    count = qs.count()
                    qs.delete()
                    logger.info(f"   ✅ {count} {nome} (CRM Vendas) deletados")
                except Exception as e:
                    # Schema vazio (tabelas nunca criadas): esperado, não é erro
                    if 'does not exist' in str(e).lower():
                        logger.debug(f"   ℹ️ Schema vazio: {nome} não existem (ok)")
                    else:
                        logger.warning(f"   ⚠️ Erro ao deletar {nome} CRM Vendas: {e}")

            _delete_crm(Atividade, 'atividades')
            _delete_crm(Oportunidade, 'oportunidades')
            _delete_crm(Lead, 'leads')
            _delete_crm(Contato, 'contatos')
            _delete_crm(Conta, 'contas')
            _delete_crm(Vendedor, 'vendedores')

        elif tipo_loja_nome == 'Clínica da Beleza':
            if db_alias:
                from superadmin.tenant_cleanup import delete_clinica_beleza_tenant_data
                delete_clinica_beleza_tenant_data(db_alias, loja_id)
            else:
                from clinica_beleza.models import (
                    Patient, Professional, Procedure, Appointment, BloqueioHorario,
                    HorarioTrabalhoProfissional, Payment, CampanhaPromocao,
                )

                def _delete_clinica_beleza(model, nome):
                    try:
                        if hasattr(model.objects, 'all_without_filter'):
                            qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                        else:
                            qs = model.objects.filter(loja_id=loja_id)
                        count = qs.count()
                        qs.delete()
                        logger.info(f"   ✅ {count} {nome} (Clínica da Beleza) deletados")
                    except Exception as e:
                        err = str(e).lower()
                        if 'does not exist' in err or 'undefinedcolumn' in err:
                            logger.debug(f"   ℹ️ {nome}: schema parcial (ok)")
                        else:
                            logger.warning(f"   ⚠️ Erro ao deletar {nome} Clínica da Beleza: {e}")

                _delete_clinica_beleza(Payment, 'pagamentos')
                _delete_clinica_beleza(Appointment, 'agendamentos')
                _delete_clinica_beleza(BloqueioHorario, 'bloqueios horário')
                _delete_clinica_beleza(HorarioTrabalhoProfissional, 'horários trabalho profissional')
                _delete_clinica_beleza(CampanhaPromocao, 'campanhas promoção')
                _delete_clinica_beleza(Procedure, 'procedimentos')
                _delete_clinica_beleza(Professional, 'profissionais')
                _delete_clinica_beleza(Patient, 'pacientes')
            
        elif tipo_loja_nome:
            # Hotel, E-commerce e outros: sem ramo explícito acima — tabelas somem com DROP SCHEMA CASCADE.
            logger.info(
                f"   ℹ️ Tipo {tipo_loja_nome!r}: sem exclusão linha-a-linha neste signal; "
                "schema tenant será removido por DROP SCHEMA CASCADE."
            )

        # NOTA: A exclusão do owner é feita na views.py após a exclusão da loja
        # para evitar TransactionManagementError
        
        # 2. Deletar sessões do usuário (usando owner_id para evitar problemas de transação)
        try:
            from superadmin.models import UserSession
            owner_id = instance.owner_id
            if owner_id:
                sessoes_count = UserSession.objects.filter(user_id=owner_id).count()
                UserSession.objects.filter(user_id=owner_id).delete()
                logger.info(f"   ✅ {sessoes_count} sessões deletadas")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao deletar sessões: {e}")
        
        # 3. Verificar pagamentos Asaas relacionados (remoção feita na views.py)
        try:
            logger.info(f"   ℹ️ Pagamentos Asaas serão removidos pela views.py")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao verificar Asaas: {e}")
        
        # 4. Excluir schema PostgreSQL (CRÍTICO: prevenir schemas órfãos)
        try:
            from django.db import connection
            import os
            
            # Verificar se está usando PostgreSQL (produção)
            DATABASE_URL = os.environ.get('DATABASE_URL', '')
            if 'postgres' in DATABASE_URL.lower():
                # Obter nome do schema (database_name da loja)
                schema_name = instance.database_name.replace('-', '_')
                
                # Validar que não é schema público
                if schema_name and schema_name != 'public':
                    with connection.cursor() as cursor:
                        # Verificar se schema existe
                        cursor.execute(
                            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                            [schema_name]
                        )
                        schema_exists = cursor.fetchone()
                        
                        if schema_exists:
                            # Excluir schema com CASCADE (remove todas as tabelas)
                            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                            logger.info(f"   ✅ Schema PostgreSQL removido: {schema_name}")
                        else:
                            logger.info(f"   ℹ️ Schema PostgreSQL não existe: {schema_name}")
                else:
                    logger.warning(f"   ⚠️ Schema inválido ou público, não será removido: {schema_name}")
            else:
                logger.info(f"   ℹ️ Não está usando PostgreSQL, schema não será removido")
                
        except Exception as e:
            logger.error(f"   ❌ Erro ao remover schema PostgreSQL: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Não interrompe a exclusão da loja, apenas loga o erro
        
        # 5. Rede de segurança: limpar só tabelas do default (public) com loja_id.
        # Dados operacionais da loja estão no schema da loja (já limpos acima com .using());
        # no default ficam só superadmin/asaas (TABELAS_LOJA_ID_DEFAULT).
        # Cada tabela usa transaction.atomic() (savepoint) para que falha em uma (ex: tabela
        # inexistente) não aborte a transação principal do loja.delete()
        try:
            from django.db import connection, transaction
            from superadmin.orfaos_config import TABELAS_LOJA_ID_DEFAULT, tabela_existe_em_public
            for tabela, coluna in TABELAS_LOJA_ID_DEFAULT:
                try:
                    with transaction.atomic():
                        with connection.cursor() as cursor:
                            if not tabela_existe_em_public(cursor, tabela):
                                continue
                            cursor.execute(
                                f'DELETE FROM {tabela} WHERE {coluna} = %s',
                                [loja_id]
                            )
                            if cursor.rowcount:
                                logger.info(f"   ✅ Safety net: {cursor.rowcount} linha(s) em {tabela} removida(s)")
                except Exception as e:
                    logger.warning(f"   ⚠️ Safety net {tabela}: {e}")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro na rede de segurança TABELAS_LOJA_ID_DEFAULT: {e}")
        
        # 6. Remover config do banco de settings.DATABASES (evitar nome órfão no default)
        db_name = getattr(instance, 'database_name', None)
        if db_name and db_name in settings.DATABASES:
            try:
                del settings.DATABASES[db_name]
                logger.info(f"   ✅ Config do banco removida do settings: {db_name}")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao remover config do banco: {e}")

        # 7. Remover arquivos órfãos: diretório de backups e media da loja
        _limpar_arquivos_orfaos_loja(instance)
        
        logger.info(f"✅ Exclusão em cascata concluída para loja: {loja_nome}")
        
    except Exception as e:
        logger.error(f"❌ Erro durante exclusão em cascata da loja {loja_nome}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Não interrompe a exclusão da loja, apenas loga o erro


@receiver(post_delete, sender='superadmin.Loja')
def remove_owner_if_orphan(sender, instance, **kwargs):
    """
    Após excluir uma loja, remove o usuário proprietário se ele ficar órfão
    (não for dono de mais nenhuma loja). Evita usuários órfãos que bloqueiam
    criar nova loja com o mesmo login.

    IMPORTANTE: Usa transaction.on_commit() para executar APÓS o commit do delete.
    Caso contrário, se user.delete() falhar (ex: tabela stores_store inexistente),
    a transação do PostgreSQL seria abortada e o delete da loja seria revertido.
    """
    from django.db import transaction

    owner_id = getattr(instance, 'owner_id', None)
    loja_slug = getattr(instance, 'slug', 'unknown')
    loja_nome = getattr(instance, 'nome', 'unknown')
    
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

    logger.info(f"   📝 Agendando remoção de owner órfão para após commit da transação...")
    transaction.on_commit(_remover_owner_apos_commit)

