"""
Signals para superadmin - Criação automática de funcionários
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='superadmin.Loja')
def create_funcionario_for_loja_owner(sender, instance, created, **kwargs):
    """
    Cria automaticamente um funcionário/vendedor para o administrador quando uma loja é criada
    """
    if not created:
        return
    
    try:
        tipo_loja_nome = instance.tipo_loja.nome
        owner = instance.owner
        
        # Dados básicos do funcionário (incluindo loja_id para o LojaIsolationMixin)
        funcionario_data = {
            'nome': owner.get_full_name() or owner.username,
            'email': owner.email,
            'telefone': '',  # Será preenchido posteriormente
            'cargo': 'Administrador',
            'is_admin': True,  # Marcar como administrador
            'loja_id': instance.id  # ✅ Adicionar loja_id para o LojaIsolationMixin
        }
        
        funcionario_criado = None
        
        # Criar funcionário baseado no tipo de loja
        if tipo_loja_nome == 'Clínica de Estética':
            from clinica_estetica.models import Funcionario
            
            # Verificar se já existe
            if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
                funcionario_criado = Funcionario.objects.create(**funcionario_data)
                
        elif tipo_loja_nome == 'Serviços':
            from servicos.models import Funcionario
            
            # Verificar se já existe
            if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
                funcionario_criado = Funcionario.objects.create(**funcionario_data)
                
        elif tipo_loja_nome == 'Restaurante':
            from restaurante.models import Funcionario
            
            # Verificar se já existe
            if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
                funcionario_data['cargo'] = 'Gerente'  # Cargo específico para restaurante
                funcionario_criado = Funcionario.objects.create(**funcionario_data)
                
        elif tipo_loja_nome == 'CRM Vendas':
            from crm_vendas.models import Vendedor
            
            # Verificar se já existe
            if not Vendedor.objects.filter(email=owner.email, loja_id=instance.id).exists():
                funcionario_data['cargo'] = 'Gerente de Vendas'
                funcionario_data['meta_mensal'] = 10000.00  # Meta padrão
                funcionario_criado = Vendedor.objects.create(**funcionario_data)
                
        elif tipo_loja_nome == 'E-commerce':
            # E-commerce não tem modelo de funcionário
            logger.info(f"E-commerce não possui modelo de funcionário. Loja: {instance.nome}")
            return
            
        else:
            logger.warning(f"Tipo de loja não reconhecido: {tipo_loja_nome}")
            return
        
        if funcionario_criado:
            logger.info(f"✅ Funcionário criado para administrador da loja {instance.nome}: {funcionario_criado.nome} ({tipo_loja_nome})")
        else:
            logger.info(f"ℹ️ Funcionário já existe para o usuário {owner.username} na loja {instance.nome}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar funcionário para loja {instance.nome}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Não interrompe a criação da loja, apenas loga o erro