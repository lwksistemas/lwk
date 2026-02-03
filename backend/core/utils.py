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
    
    loja_id = get_current_loja_id()
    
    if not loja_id:
        logger.warning("⚠️ [ensure_owner_as_funcionario] Nenhuma loja_id no contexto")
        return False
    
    try:
        loja = Loja.objects.get(id=loja_id)
        owner = loja.owner
        
        # Verificar se já existe usando all_without_filter para bypass do isolamento
        exists = funcionario_model.objects.all_without_filter().filter(
            loja_id=loja_id, 
            email=owner.email
        ).exists()
        
        if not exists:
            logger.info(f"✅ [ensure_owner_as_funcionario] Criando funcionário admin para loja {loja_id}")
            funcionario_model.objects.all_without_filter().create(
                nome=owner.get_full_name() or owner.username or owner.email.split('@')[0],
                email=owner.email,
                telefone=getattr(owner, 'telefone', '') or '',
                cargo=cargo_padrao,
                is_admin=True,
                loja_id=loja_id,
            )
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
