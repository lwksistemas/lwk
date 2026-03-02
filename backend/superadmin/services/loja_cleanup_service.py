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
            'mercadopago': {},
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
            from suporte.models import Chamado
            
            with transaction.atomic():
                chamados = Chamado.objects.filter(loja_slug=self.loja_slug)
                chamados_count = chamados.count()
                respostas_count = sum(c.respostas.count() for c in chamados)
                chamados.delete()
                
                self.results['suporte'] = {
                    'chamados_removidos': chamados_count,
                    'respostas_removidas': respostas_count
                }
                
                if chamados_count > 0:
                    logger.info(f"✅ Chamados removidos: {chamados_count}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover chamados: {e}")
            self.results['suporte'] = {'erro': str(e)}
    
    def cleanup_logs_and_alerts(self):
        """Remove logs de auditoria e alertas de segurança"""
        try:
            from .models import HistoricoAcessoGlobal, ViolacaoSeguranca
            from django.db.models import Q
            
            with transaction.atomic():
                # Logs de auditoria (ações dentro da loja + ações sobre a loja)
                logs = HistoricoAcessoGlobal.objects.filter(
                    Q(loja_slug=self.loja_slug) |
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
        """Remove dados de pagamentos (Asaas + Mercado Pago)"""
        try:
            from .payment_deletion_service import UnifiedPaymentDeletionService
            
            payment_service = UnifiedPaymentDeletionService()
            payment_results = payment_service.delete_all_payments_for_loja(self.loja_slug)
            
            # Asaas
            asaas_result = payment_results['providers'].get('Asaas', {})
            self.results['asaas'] = {
                'api': {
                    'pagamentos_cancelados': asaas_result.get('api_cancelled', 0),
                    'cliente_removido': asaas_result.get('local_deleted_customers', 0) > 0
                },
                'local': {
                    'payments_removidos': asaas_result.get('local_deleted_payments', 0),
                    'customers_removidos': asaas_result.get('local_deleted_customers', 0),
                    'subscriptions_removidas': asaas_result.get('local_deleted_subscriptions', 0)
                }
            }
            
            # Mercado Pago
            mercadopago_result = payment_results['providers'].get('Mercado Pago', {})
            self.results['mercadopago'] = {
                'boletos_pendentes_cancelados': mercadopago_result.get('api_cancelled', 0)
            }
            
            if payment_results['total_cancelled'] > 0:
                logger.info(f"✅ Pagamentos cancelados: {payment_results['total_cancelled']}")
                
            if payment_results['errors']:
                for error in payment_results['errors']:
                    logger.warning(f"⚠️ {error}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover pagamentos: {e}")
            self.results['asaas'] = {'erro': str(e)}
            self.results['mercadopago'] = {'erro': str(e)}
    
    def cleanup_database_file(self):
        """Remove arquivo SQLite do banco de dados isolado"""
        if not self.database_created:
            self.results['banco_dados'] = {
                'existia': False,
                'nome': self.database_name
            }
            return
        
        try:
            import os
            db_path = settings.BASE_DIR / f'db_{self.database_name}.sqlite3'
            
            if db_path.exists():
                os.remove(db_path)
                logger.info(f"✅ Arquivo do banco removido: {db_path}")
                
                self.results['banco_dados'] = {
                    'existia': True,
                    'nome': self.database_name,
                    'arquivo_removido': True,
                    'config_removida': True
                }
            else:
                self.results['banco_dados'] = {
                    'existia': True,
                    'nome': self.database_name,
                    'arquivo_removido': False,
                    'motivo': 'Arquivo não encontrado'
                }
                
            # Remover configuração do settings.DATABASES
            if self.database_name in settings.DATABASES:
                del settings.DATABASES[self.database_name]
                logger.info(f"✅ Configuração do banco removida: {self.database_name}")
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover banco: {e}")
            self.results['banco_dados'] = {
                'existia': True,
                'nome': self.database_name,
                'erro': str(e)
            }
    
    def cleanup_owner_user(self):
        """Remove usuário proprietário se não tiver outras lojas"""
        from django.contrib.auth.models import User
        from .models import Loja
        
        try:
            # Verificar se o usuário tem outras lojas
            outras_lojas = Loja.objects.filter(owner=self.owner).exclude(id=self.loja_id).count()
            
            if outras_lojas > 0:
                self.results['usuario_proprietario'] = {
                    'username': self.owner.username,
                    'removido': False,
                    'motivo_nao_removido': 'Possui outras lojas'
                }
                return
            
            # Verificar se é superuser/staff
            if self.owner.is_superuser or self.owner.is_staff:
                self.results['usuario_proprietario'] = {
                    'username': self.owner.username,
                    'removido': False,
                    'motivo_nao_removido': 'Superuser/Staff'
                }
                return
            
            # Remover usuário
            with transaction.atomic():
                user_to_delete = User.objects.filter(id=self.owner_id).first()
                if user_to_delete:
                    user_to_delete.groups.clear()
                    user_to_delete.user_permissions.clear()
                    user_to_delete.delete()
                    
                    self.results['usuario_proprietario'] = {
                        'username': self.owner.username,
                        'removido': True
                    }
                    
                    logger.info(f"✅ Usuário removido: {self.owner.username}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover usuário: {e}")
            self.results['usuario_proprietario'] = {
                'username': self.owner.username,
                'erro': str(e)
            }
