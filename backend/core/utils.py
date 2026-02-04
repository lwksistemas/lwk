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
    from datetime import date
    
    loja_id = get_current_loja_id()
    
    if not loja_id:
        logger.warning("⚠️ [ensure_owner_as_funcionario] Nenhuma loja_id no contexto")
        return False
    
    try:
        loja = Loja.objects.get(id=loja_id)
        owner = loja.owner
        
        # Verificar se o manager tem all_without_filter (LojaIsolationManager)
        # Se não tiver, usar filter direto (bypass do isolamento não é necessário)
        manager = funcionario_model.objects
        if hasattr(manager, 'all_without_filter'):
            # Manager customizado com bypass de isolamento
            base_queryset = manager.all_without_filter()
        else:
            # Manager padrão do Django - usar filter direto
            base_queryset = manager.all()
        
        # Verificar se já existe
        exists = base_queryset.filter(
            loja_id=loja_id, 
            email=owner.email
        ).exists()
        
        if not exists:
            logger.info(f"✅ [ensure_owner_as_funcionario] Criando funcionário admin para loja {loja_id}")
            
            # Preparar dados do funcionário
            funcionario_data = {
                'nome': owner.get_full_name() or owner.username or owner.email.split('@')[0],
                'email': owner.email,
                'telefone': getattr(owner, 'telefone', '') or '',
                'cargo': cargo_padrao,
                'loja_id': loja_id,
            }
            
            # Adicionar is_admin apenas se o modelo tiver esse campo
            if hasattr(funcionario_model, 'is_admin'):
                funcionario_data['is_admin'] = True
            
            # Adicionar data_admissao se o modelo tiver esse campo e for obrigatório
            model_fields = {f.name: f for f in funcionario_model._meta.get_fields()}
            if 'data_admissao' in model_fields:
                field = model_fields['data_admissao']
                if not field.null and not field.blank:
                    funcionario_data['data_admissao'] = date.today()
            
            base_queryset.create(**funcionario_data)
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
