"""
Service para limpeza de dados ao excluir uma loja
Centraliza toda a lógica de exclusão em um único lugar
"""
import logging
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


class LojaCleanupService:
    """
    Service responsável por limpar todos os dados relacionados a uma loja
    quando ela é excluída do sistema.
    """
    
    def __init__(self, loja):
        self.loja = loja
        self.loja_id = loja.id
        self.loja_nome = loja.nome
        self.loja_slug = loja.slug
        self.database_name = loja.database_name
        self.database_created = loja.database_created
        self.owner = loja.owner
        self.owner_id = loja.owner.id
        
        # Resultados da limpeza
        self.results = {
            'loja_nome': self.loja_nome,
            'loja_slug': self.loja_slug,
            'loja_removida': False,
            'suporte': {},
            'logs_auditoria': {},
            'banco_dados': {},
            'asaas': {'api': {}, 'local': {}},
            'usuario_proprietario': {},
            'usuarios_staff': {},
            'evolution': {},
            'limpeza_completa': False
        }
    
    def cleanup_all(self):
        """
        Executa toda a limpeza de dados da loja
        Retorna dicionário com detalhes da operação
        """
        try:
            self.cleanup_evolution()
            self.cleanup_support_tickets()
            self.cleanup_logs_and_alerts()
            self.cleanup_payments()
            self.cleanup_fk_references()
            self.cleanup_lockout()
            self.cleanup_staff_users()
            self.cleanup_database_file()
            self.cleanup_owner_user()
            
            self.results['loja_removida'] = True
            self.results['limpeza_completa'] = True
            
            return self.results
            
        except Exception as e:
            logger.error(f"Erro na limpeza da loja {self.loja_slug}: {e}")
            raise
    
    def cleanup_evolution(self):
        """Remove instância WhatsApp (Evolution API) da loja."""
        try:
            from whatsapp.evolution_cleanup import delete_evolution_for_loja

            self.results['evolution'] = delete_evolution_for_loja(self.loja_id)
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover Evolution: {e}")
            self.results['evolution'] = {'ok': False, 'error': str(e)}

    def cleanup_staff_users(self):
        """
        Remove contas de profissionais/vendedores vinculados só a esta loja.
        """
        from django.contrib.auth import get_user_model

        from superadmin.models import Loja, ProfissionalUsuario, VendedorUsuario
        from superadmin.utils import delete_user_raw

        User = get_user_model()

        removidos = []
        pulados = []

        try:
            prof_links = list(
                ProfissionalUsuario.objects.filter(loja_id=self.loja_id).select_related('user')
            )
            vend_links = list(
                VendedorUsuario.objects.filter(loja_id=self.loja_id).select_related('user')
            )
            user_ids = {link.user_id for link in prof_links + vend_links}

            ProfissionalUsuario.objects.filter(loja_id=self.loja_id).delete()
            VendedorUsuario.objects.filter(loja_id=self.loja_id).delete()

            for uid in user_ids:
                user = User.objects.filter(id=uid).first()
                if not user:
                    continue
                if user.is_superuser or user.is_staff:
                    pulados.append({'user_id': uid, 'motivo': 'superuser/staff'})
                    continue
                if Loja.objects.filter(owner_id=uid).exclude(id=self.loja_id).exists():
                    pulados.append({'user_id': uid, 'motivo': 'owner de outra loja'})
                    continue
                if ProfissionalUsuario.objects.filter(user_id=uid).exists():
                    pulados.append({'user_id': uid, 'motivo': 'profissional em outra loja'})
                    continue
                if VendedorUsuario.objects.filter(user_id=uid).exists():
                    pulados.append({'user_id': uid, 'motivo': 'vendedor em outra loja'})
                    continue
                username = user.username
                delete_user_raw(uid)
                removidos.append(username)
                logger.info(f"✅ Usuário staff removido: {username}")

            self.results['usuarios_staff'] = {
                'removidos': removidos,
                'pulados': pulados,
            }
        except Exception as e:
            logger.warning(f"⚠️ Erro ao limpar usuários staff: {e}")
            self.results['usuarios_staff'] = {'erro': str(e)}

    def cleanup_support_tickets(self):
        """Remove chamados de suporte da loja"""
        try:
            from django.db import connections

            db = 'suporte' if 'suporte' in connections.databases else 'default'
            chamados_count = 0
            respostas_count = 0

            with connections[db].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = 'suporte_chamado'
                      AND column_name = 'loja_slug'
                    LIMIT 1
                    """
                )
                if not cursor.fetchone():
                    logger.info('   ℹ️ suporte_chamado sem coluna loja_slug — pulando limpeza de chamados')
                    self.results['suporte'] = {'chamados_removidos': 0, 'pulado': 'coluna loja_slug ausente'}
                    return

            from suporte.models import Chamado

            with transaction.atomic(using=db):
                chamados = Chamado.objects.using(db).filter(loja_slug=self.loja_slug)
                chamados_count = chamados.count()
                if chamados_count:
                    respostas_count = sum(
                        c.respostas.using(db).count() for c in chamados.using(db).iterator()
                    )
                    chamados.delete()
                
                self.results['suporte'] = {
                    'chamados_removidos': chamados_count,
                    'respostas_removidas': respostas_count,
                }
                
                if chamados_count > 0:
                    logger.info(f"✅ Chamados removidos: {chamados_count}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover chamados: {e}")
            self.results['suporte'] = {'erro': str(e)}
    
    def cleanup_logs_and_alerts(self):
        """Remove logs de auditoria e alertas de segurança"""
        try:
            from superadmin.models import HistoricoAcessoGlobal, ViolacaoSeguranca
            from django.db.models import Q
            
            with transaction.atomic():
                # Logs de auditoria (ações dentro da loja + ações sobre a loja)
                logs = HistoricoAcessoGlobal.objects.filter(
                    Q(loja_slug=self.loja_slug) |
                    Q(loja_id=self.loja_id) |
                    Q(recurso='Loja', recurso_id=self.loja_id)
                )
                logs_count = logs.count()
                logs.delete()
                
                # Alertas de segurança
                alertas = ViolacaoSeguranca.objects.filter(loja__slug=self.loja_slug)
                alertas_count = alertas.count()
                alertas.delete()
                
                self.results['logs_auditoria'] = {
                    'logs_removidos': logs_count,
                    'alertas_removidos': alertas_count
                }
                
                if logs_count > 0 or alertas_count > 0:
                    logger.info(f"✅ Logs: {logs_count}, Alertas: {alertas_count}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover logs/alertas: {e}")
            self.results['logs_auditoria'] = {'erro': str(e)}
    
    def cleanup_payments(self):
        """Remove dados de pagamentos (Asaas)"""
        try:
            # Cancelar pagamentos Asaas
            asaas_cancelled = self._cleanup_asaas_payments()
            
            if asaas_cancelled > 0:
                logger.info(f"✅ Total de pagamentos cancelados: {asaas_cancelled}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover pagamentos: {e}")
            self.results['asaas'] = {'erro': str(e)}
    
    def _cleanup_asaas_payments(self):
        """Cancela TODOS os pagamentos pendentes no Asaas e remove dados locais"""
        try:
            from asaas_integration.models import LojaAssinatura, AsaasPayment, AsaasCustomer
            from asaas_integration.deletion_service import AsaasDeletionService
            
            cancelled_count = 0
            
            with transaction.atomic():
                # Buscar assinatura da loja
                assinatura = LojaAssinatura.objects.filter(loja_slug=self.loja_slug).first()
                
                if not assinatura:
                    # Fallback: tentar excluir customer via FinanceiroLoja.asaas_customer_id
                    try:
                        from superadmin.models import FinanceiroLoja, Loja
                        loja = Loja.objects.filter(slug=self.loja_slug).first()
                        if loja:
                            financeiro = FinanceiroLoja.objects.filter(loja=loja).first()
                            if financeiro and financeiro.asaas_customer_id:
                                deletion_service = AsaasDeletionService()
                                if deletion_service.available:
                                    deletion_service._delete_customer_payments(financeiro.asaas_customer_id)
                                    deletion_service._delete_customer_from_asaas(financeiro.asaas_customer_id)
                                    logger.info(f"✅ Asaas: cliente {financeiro.asaas_customer_id} excluído via fallback (FinanceiroLoja)")
                    except Exception as e:
                        logger.warning(f"⚠️ Fallback exclusão Asaas: {e}")
                    
                    self.results['asaas'] = {
                        'api': {'pagamentos_cancelados': 0},
                        'local': {'payments_removidos': 0, 'customers_removidos': 0, 'subscriptions_removidas': 0}
                    }
                    return 0
                
                # Usar o serviço de exclusão do Asaas para cancelar TODOS os pagamentos
                try:
                    deletion_service = AsaasDeletionService()
                    if deletion_service.available:
                        result = deletion_service.delete_loja_from_asaas(self.loja_slug)
                        
                        if result.get('success'):
                            cancelled_count = result.get('deleted_payments', 0)
                            logger.info(f"✅ Asaas: {cancelled_count} pagamentos cancelados via API")
                        else:
                            logger.warning(f"⚠️ Erro ao cancelar pagamentos Asaas: {result.get('error')}")
                    else:
                        logger.warning("⚠️ Serviço de exclusão Asaas não disponível")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao usar serviço de exclusão Asaas: {e}")
                
                # Remover dados locais
                payments = AsaasPayment.objects.filter(
                    external_reference__contains=f"loja_{self.loja_slug}"
                )
                payments_count = payments.count()
                payments.delete()
                
                customer = assinatura.asaas_customer
                customer_id = customer.asaas_id if customer else None
                
                assinatura.delete()
                
                if customer:
                    customer.delete()
                
                self.results['asaas'] = {
                    'api': {'pagamentos_cancelados': cancelled_count},
                    'local': {
                        'payments_removidos': payments_count,
                        'customers_removidos': 1 if customer else 0,
                        'subscriptions_removidas': 1,
                        'customer_id': customer_id
                    }
                }
                
                logger.info(f"✅ Asaas: {cancelled_count} cancelados na API, {payments_count} removidos localmente")
                
            return cancelled_count
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao limpar pagamentos Asaas: {e}")
            self.results['asaas'] = {'erro': str(e)}
            return 0
    
    def cleanup_fk_references(self):
        """
        Remove registros de tabelas com FK para superadmin_loja que podem bloquear
        a exclusão (quando CASCADE no banco não está aplicado corretamente ou
        a tabela está em schema diferente do search_path do ORM).
        """
        removed = {}

        # Fallback SQL direto: busca TODAS as FKs apontando para superadmin_loja
        # e remove os registros referenciando esta loja. Isso cobre qualquer tabela
        # independente do schema/search_path.
        try:
            from django.db import connection
            with connection.cursor() as cur:
                # Buscar todas as constraints FK que referenciam superadmin_loja
                cur.execute("""
                    SELECT
                        kcu.table_schema,
                        kcu.table_name,
                        kcu.column_name
                    FROM information_schema.referential_constraints rc
                    JOIN information_schema.key_column_usage kcu
                      ON kcu.constraint_name = rc.constraint_name
                      AND kcu.constraint_schema = rc.constraint_schema
                    JOIN information_schema.key_column_usage rcu
                      ON rcu.constraint_name = rc.unique_constraint_name
                      AND rcu.constraint_schema = rc.unique_constraint_schema
                    WHERE rcu.table_name = 'superadmin_loja'
                      AND rcu.column_name = 'id'
                """)
                fk_refs = cur.fetchall()

                for schema, table_name, col_name in fk_refs:
                    if table_name == 'superadmin_loja':
                        continue
                    try:
                        qualified_table = f'"{schema}"."{table_name}"' if schema != 'public' else f'"{table_name}"'
                        cur.execute(
                            f'DELETE FROM {qualified_table} WHERE "{col_name}" = %s',
                            [self.loja_id]
                        )
                        if cur.rowcount:
                            removed[f'{schema}.{table_name}'] = cur.rowcount
                            logger.info(f"  ✅ {schema}.{table_name}: {cur.rowcount} removidos")
                    except Exception as e:
                        logger.warning(f"  ⚠️ {schema}.{table_name}: {e}")
                        # Reconectar se a transação abortou
                        try:
                            connection.rollback() if not connection.get_autocommit() else None
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"  ⚠️ FK cleanup SQL: {e}")

        self.results['fk_references'] = removed
        if removed:
            logger.info(f"✅ FK references limpas: {removed}")

    def cleanup_lockout(self):
        """Remove registros de lockout de login do owner da loja."""
        try:
            from core.login_lockout import normalize_username
            from superadmin.models import LoginLockout

            username = normalize_username(self.owner.username)
            if username:
                deleted, _ = LoginLockout.objects.filter(username_key=username).delete()
                if deleted:
                    logger.info(f"  ✅ LoginLockout removido: {username} ({deleted})")
            # Também limpar por email
            email = normalize_username(self.owner.email)
            if email and email != username:
                deleted, _ = LoginLockout.objects.filter(username_key=email).delete()
                if deleted:
                    logger.info(f"  ✅ LoginLockout removido: {email} ({deleted})")
        except Exception as e:
            logger.warning(f"  ⚠️ Erro ao limpar lockout: {e}")

    def cleanup_database_file(self):
        """
        Remove schema PostgreSQL da loja E configuração do settings.DATABASES.

        Executa DROP SCHEMA CASCADE diretamente para garantir limpeza mesmo
        quando signals não são disparados (ex: DELETE SQL direto).
        """
        schema_name = self.database_name
        self.results['banco_dados'] = {'nome': schema_name}

        if not schema_name:
            self.results['banco_dados']['existia'] = False
            return

        # 1. DROP SCHEMA no PostgreSQL
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    [schema_name]
                )
                if cursor.fetchone():
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                    logger.info(f"✅ Schema PostgreSQL removido: {schema_name}")
                    self.results['banco_dados']['schema_removido'] = True
                else:
                    logger.info(f"  ℹ️ Schema {schema_name} não existe (já removido)")
                    self.results['banco_dados']['schema_removido'] = False
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover schema {schema_name}: {e}")
            self.results['banco_dados']['schema_erro'] = str(e)

        # 2. Remover configuração do settings.DATABASES
        try:
            if schema_name in settings.DATABASES:
                del settings.DATABASES[schema_name]
                self.results['banco_dados']['config_removida'] = True
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover config DATABASES: {e}")

    def cleanup_owner_user(self):
        """
        Remove o usuário proprietário SE ficar órfão (sem outras lojas).

        Executa a remoção diretamente em vez de depender do signal post_delete
        (que não dispara quando usamos DELETE SQL direto).
        """
        from superadmin.models import Loja

        try:
            outras_lojas = Loja.objects.filter(owner=self.owner).exclude(id=self.loja_id).count()

            if outras_lojas > 0:
                self.results['usuario_proprietario'] = {
                    'username': self.owner.username,
                    'removido': False,
                    'motivo_nao_removido': 'Possui outras lojas'
                }
                return

            if self.owner.is_superuser or self.owner.is_staff:
                self.results['usuario_proprietario'] = {
                    'username': self.owner.username,
                    'removido': False,
                    'motivo_nao_removido': 'Superuser/Staff'
                }
                return

            # Owner é órfão — remover user e dados relacionados
            from superadmin.utils import delete_user_raw
            username = self.owner.username
            owner_id = self.owner.id
            delete_user_raw(owner_id)
            logger.info(f"✅ Usuário órfão removido: {username}")
            self.results['usuario_proprietario'] = {
                'username': username,
                'removido': True,
            }
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover usuário órfão: {e}")
            self.results['usuario_proprietario'] = {
                'username': self.owner.username,
                'removido': False,
                'erro': str(e),
            }
