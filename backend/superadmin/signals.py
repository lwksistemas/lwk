"""
Signals para o app superadmin
Garante limpeza completa quando lojas são excluídas
"""
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender='superadmin.Loja')
def cleanup_before_loja_deletion(sender, instance, **kwargs):
    """
    Executa limpeza ANTES da exclusão da loja
    Coleta informações necessárias antes que sejam perdidas
    """
    try:
        # Coletar informações antes da exclusão
        loja_nome = instance.nome
        loja_slug = instance.slug
        loja_id = instance.id
        database_name = instance.database_name
        database_created = instance.database_created
        owner = instance.owner
        owner_username = owner.username
        owner_email = owner.email
        
        # Verificar se o owner tem outras lojas
        outras_lojas_count = sender.objects.filter(owner=owner).exclude(id=instance.id).count()
        
        # Salvar informações no contexto da instância para usar no post_delete
        instance._cleanup_info = {
            'loja_nome': loja_nome,
            'loja_slug': loja_slug,
            'loja_id': loja_id,
            'database_name': database_name,
            'database_created': database_created,
            'owner': owner,
            'owner_username': owner_username,
            'owner_email': owner_email,
            'outras_lojas_count': outras_lojas_count,
            'deve_remover_owner': outras_lojas_count == 0
        }
        
        logger.info(f"🗑️  Preparando exclusão da loja: {loja_nome}")
        logger.info(f"   Owner: {owner_username} ({owner_email})")
        logger.info(f"   Outras lojas do owner: {outras_lojas_count}")
        logger.info(f"   Deve remover owner: {outras_lojas_count == 0}")
        
    except Exception as e:
        logger.error(f"❌ Erro no pre_delete da loja: {e}")

@receiver(post_delete, sender='superadmin.Loja')
def cleanup_after_loja_deletion(sender, instance, **kwargs):
    """
    Executa limpeza APÓS a exclusão da loja
    Remove dados relacionados e usuário órfão se necessário
    """
    try:
        # Recuperar informações salvas no pre_delete
        cleanup_info = getattr(instance, '_cleanup_info', {})
        
        if not cleanup_info:
            logger.warning("⚠️ Informações de limpeza não encontradas")
            return
        
        loja_nome = cleanup_info['loja_nome']
        loja_slug = cleanup_info['loja_slug']
        database_name = cleanup_info['database_name']
        database_created = cleanup_info['database_created']
        owner = cleanup_info['owner']
        owner_username = cleanup_info['owner_username']
        deve_remover_owner = cleanup_info['deve_remover_owner']
        
        logger.info(f"🧹 Iniciando limpeza pós-exclusão da loja: {loja_nome}")
        
        # 1. Remover chamados de suporte da loja
        chamados_removidos = 0
        respostas_removidas = 0
        try:
            from suporte.models import Chamado, RespostaChamado
            
            # Buscar chamados da loja
            chamados = Chamado.objects.filter(loja_slug=loja_slug)
            chamados_removidos = chamados.count()
            
            # Contar respostas antes de deletar
            for chamado in chamados:
                respostas_removidas += chamado.respostas.count()
            
            # Deletar chamados (respostas são deletadas em cascade)
            chamados.delete()
            logger.info(f"✅ Chamados de suporte removidos: {chamados_removidos}")
            logger.info(f"✅ Respostas de suporte removidas: {respostas_removidas}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover chamados de suporte: {e}")
        
        # 2. Remover assinaturas Asaas se existirem
        try:
            from asaas_integration.models import LojaAssinatura, AsaasPayment, AsaasCustomer
            
            # Buscar assinatura da loja
            assinaturas = LojaAssinatura.objects.filter(loja_slug=loja_slug)
            assinaturas_removidas = assinaturas.count()
            
            for assinatura in assinaturas:
                # Remover pagamentos relacionados
                AsaasPayment.objects.filter(customer=assinatura.asaas_customer).delete()
                # Remover cliente
                assinatura.asaas_customer.delete()
            
            # Remover assinaturas
            assinaturas.delete()
            
            if assinaturas_removidas > 0:
                logger.info(f"✅ Assinaturas Asaas removidas: {assinaturas_removidas}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover assinaturas Asaas: {e}")
        
        # 3. Remover banco de dados físico se existir
        banco_removido = False
        if database_created and database_name:
            try:
                # Remover das configurações do Django
                if database_name in settings.DATABASES:
                    del settings.DATABASES[database_name]
                    logger.info(f"✅ Configuração do banco removida: {database_name}")
                
                # Para PostgreSQL, remover schema
                try:
                    from django.db import connection
                    schema_name = database_name.replace('-', '_')
                    
                    with connection.cursor() as cursor:
                        cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
                        banco_removido = True
                        logger.info(f"✅ Schema PostgreSQL removido: {schema_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao remover schema PostgreSQL: {e}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro ao remover banco de dados: {e}")
        
        # 4. Remover usuário proprietário se não for usado por outras lojas
        usuario_removido = False
        if deve_remover_owner:
            try:
                # Verificar novamente se o usuário não tem outras lojas (double-check)
                outras_lojas_atual = sender.objects.filter(owner=owner).count()
                
                if outras_lojas_atual == 0:
                    # Verificar se o usuário não é superuser ou staff importante
                    if not owner.is_superuser and not owner.is_staff:
                        owner.delete()
                        usuario_removido = True
                        logger.info(f"✅ Usuário proprietário removido: {owner_username}")
                    else:
                        logger.info(f"⚠️ Usuário {owner_username} mantido (superuser/staff)")
                else:
                    logger.info(f"⚠️ Usuário {owner_username} mantido (possui {outras_lojas_atual} outras lojas)")
            except Exception as e:
                logger.error(f"❌ Erro ao remover usuário proprietário: {e}")
        
        # 5. Log final da limpeza
        logger.info(f"🎯 Limpeza concluída para loja: {loja_nome}")
        logger.info(f"   ✅ Loja removida: {loja_nome}")
        logger.info(f"   ✅ Chamados removidos: {chamados_removidos}")
        logger.info(f"   ✅ Respostas removidas: {respostas_removidas}")
        logger.info(f"   ✅ Banco removido: {banco_removido}")
        logger.info(f"   ✅ Usuário removido: {usuario_removido}")
        
    except Exception as e:
        logger.error(f"❌ Erro na limpeza pós-exclusão: {e}")
        import traceback
        logger.error(traceback.format_exc())