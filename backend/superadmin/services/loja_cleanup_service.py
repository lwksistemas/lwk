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
            'limpeza_completa': False
        }
    
    def cleanup_all(self):
        """
        Executa toda a limpeza de dados da loja
        Retorna dicionário com detalhes da operação
        """
        try:
            self.cleanup_support_tickets()
            self.cleanup_logs_and_alerts()
            self.cleanup_payments()
            self.cleanup_fk_references()
            self.cleanup_database_file()
            self.cleanup_owner_user()
            
            self.results['loja_removida'] = True
            self.results['limpeza_completa'] = True
            
            return self.results
            
        except Exception as e:
            logger.error(f"Erro na limpeza da loja {self.loja_slug}: {e}")
            raise
    
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
        a exclusão (quando CASCADE no banco não está aplicado corretamente).
        """
        removed = {}
        tables_to_clean = [
            ('whatsapp', 'WhatsAppConfig', 'loja_id'),
            ('whatsapp', 'WhatsAppInstance', 'loja_id'),
            ('superadmin', 'GoogleCalendarConnection', 'loja_id'),
            ('superadmin', 'EmailRetry', 'loja_id'),
            ('superadmin', 'BackupConfig', 'loja_id'),
            ('superadmin', 'BackupHistorico', 'loja_id'),
        ]

        for app_label, model_name, fk_field in tables_to_clean:
            try:
                from django.apps import apps
                model = apps.get_model(app_label, model_name)
                qs = model.objects.filter(**{fk_field: self.loja_id})
                count = qs.count()
                if count:
                    qs.delete()
                    removed[f'{app_label}.{model_name}'] = count
                    logger.info(f"  ✅ {app_label}.{model_name}: {count} removidos")
            except LookupError:
                pass  # Model não existe nesta instalação
            except Exception as e:
                logger.warning(f"  ⚠️ {app_label}.{model_name}: {e}")
                removed[f'{app_label}.{model_name}'] = f'erro: {e}'

        # Fallback SQL: limpar qualquer FK restante via query direta
        try:
            from django.db import connection
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT table_name, column_name
                    FROM information_schema.key_column_usage kcu
                    JOIN information_schema.table_constraints tc
                      ON kcu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND kcu.column_name = 'loja_id'
                      AND tc.table_name != 'superadmin_loja'
                      AND kcu.table_schema = current_schema()
                """)
                fk_tables = cur.fetchall()

                for table_name, col_name in fk_tables:
                    try:
                        cur.execute(
                            f'DELETE FROM "{table_name}" WHERE "{col_name}" = %s',
                            [self.loja_id]
                        )
                        if cur.rowcount:
                            removed[table_name] = cur.rowcount
                            logger.info(f"  ✅ SQL {table_name}: {cur.rowcount} removidos")
                    except Exception as e:
                        logger.warning(f"  ⚠️ SQL {table_name}: {e}")
        except Exception as e:
            logger.warning(f"  ⚠️ Fallback SQL FK cleanup: {e}")

        self.results['fk_references'] = removed
        if removed:
            logger.info(f"✅ FK references limpas: {removed}")

    def cleanup_database_file(self):
        """
        Remove configuração do banco de dados da loja.
        
        NOTA: Sistema usa PostgreSQL com schemas isolados.
        A remoção do schema é feita pelo signal pre_delete.
        Este método apenas remove a configuração do settings.DATABASES.
        """
        if not self.database_created:
            self.results['banco_dados'] = {
                'existia': False,
                'nome': self.database_name
            }
            return
        
        try:
            # Remover configuração do settings.DATABASES
            if self.database_name in settings.DATABASES:
                del settings.DATABASES[self.database_name]
                logger.info(f"✅ Configuração do banco removida: {self.database_name}")
                
                self.results['banco_dados'] = {
                    'existia': True,
                    'nome': self.database_name,
                    'config_removida': True
                }
            else:
                self.results['banco_dados'] = {
                    'existia': True,
                    'nome': self.database_name,
                    'config_removida': False,
                    'motivo': 'Configuração não encontrada'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover configuração do banco: {e}")
            self.results['banco_dados'] = {
                'existia': True,
                'nome': self.database_name,
                'erro': str(e)
            }
    
    def cleanup_owner_user(self):
        """
        Registra se o usuário proprietário será removido pelo signal post_delete.
        NÃO remove o usuário aqui: a loja ainda existe (owner_id referencia o user).
        O signal remove_owner_if_orphan remove o owner órfão após loja.delete().
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

            self.results['usuario_proprietario'] = {
                'username': self.owner.username,
                'removido': False,
                'motivo_nao_removido': 'Será removido pelo signal após exclusão da loja'
            }
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar usuário: {e}")
            self.results['usuario_proprietario'] = {
                'username': self.owner.username,
                'erro': str(e)
            }
