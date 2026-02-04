"""
Utilitários compartilhados entre apps
"""
import logging

logger = logging.getLogger(__name__)


def ensure_owner_as_funcionario(funcionario_model, cargo_padrao='Administrador'):
    """
    Garante que o administrador da loja exista como funcionário.
    Cria automaticamente se não existir.
    
    Args:
        funcionario_model: Modelo de Funcionario do app (ex: servicos.models.Funcionario)
        cargo_padrao: Cargo padrão para o admin (ex: 'Administrador', 'gerente')
    
    Returns:
        bool: True se admin existe ou foi criado, False se houve erro
    """
    from tenants.middleware import get_current_loja_id
    from superadmin.models import Loja
    from django.db import connection
    from datetime import date
    
    loja_id = get_current_loja_id()
    
    if not loja_id:
        logger.warning("⚠️ [ensure_owner_as_funcionario] Nenhuma loja_id no contexto")
        return False
    
    try:
        loja = Loja.objects.get(id=loja_id)
        owner = loja.owner
        
        # Usar SQL direto para garantir que estamos no schema correto
        table_name = funcionario_model._meta.db_table
        
        with connection.cursor() as cursor:
            # Verificar se já existe
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE loja_id = %s AND email = %s
            """, [loja_id, owner.email])
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info(f"✅ [ensure_owner_as_funcionario] Criando funcionário admin para loja {loja_id}")
                
                nome = owner.get_full_name() or owner.username or owner.email.split('@')[0]
                telefone = getattr(owner, 'telefone', '') or ''
                data_admissao = date.today()
                
                # Inserir diretamente
                cursor.execute(f"""
                    INSERT INTO {table_name} 
                    (loja_id, nome, email, telefone, cargo, data_admissao, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())
                """, [loja_id, nome, owner.email, telefone, cargo_padrao, data_admissao])
                
                logger.info(f"✅ [ensure_owner_as_funcionario] Funcionário admin criado com sucesso")
                return True
            else:
                logger.debug(f"ℹ️ [ensure_owner_as_funcionario] Funcionário admin já existe para loja {loja_id}")
                return True
            
    except Loja.DoesNotExist:
        logger.error(f"❌ [ensure_owner_as_funcionario] Loja {loja_id} não encontrada")
        return False
    except Exception as e:
        logger.error(f"❌ [ensure_owner_as_funcionario] Erro ao criar funcionário admin: {e}", exc_info=True)
        return False
