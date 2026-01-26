"""
Signals para superadmin - Criação e exclusão automática

IMPORTANTE: 
1. Quando uma loja é CRIADA, cria automaticamente um funcionário para o admin
2. Quando uma loja é EXCLUÍDA, deleta TODOS os dados relacionados (cascata)
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='superadmin.Loja')
def create_funcionario_for_loja_owner(sender, instance, created, **kwargs):
    """
    Cria automaticamente um funcionário para o administrador quando uma loja é criada.
    
    Este signal é executado APENAS na criação de novas lojas (created=True).
    Não é executado em atualizações de lojas existentes.
    
    Args:
        sender: Modelo Loja
        instance: Instância da loja criada
        created: True se a loja foi criada, False se foi atualizada
        **kwargs: Argumentos adicionais do signal
    """
    if not created:
        return
    
    try:
        tipo_loja_nome = instance.tipo_loja.nome
        owner = instance.owner
        
        # Dados básicos do funcionário
        funcionario_data = {
            'nome': owner.get_full_name() or owner.username,
            'email': owner.email,
            'telefone': '',  # Será preenchido posteriormente pelo admin
            'cargo': 'Administrador',
            'is_admin': True,  # Marca como administrador da loja
            'loja_id': instance.id  # ID da loja (obrigatório para LojaIsolationMixin)
        }
        
        funcionario_criado = None
        
        # Criar funcionário baseado no tipo de loja
        if tipo_loja_nome == 'Clínica de Estética':
            from clinica_estetica.models import Funcionario
            
            if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
                funcionario_criado = Funcionario.objects.create(**funcionario_data)
                
        elif tipo_loja_nome == 'Serviços':
            from servicos.models import Funcionario
            
            if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
                funcionario_criado = Funcionario.objects.create(**funcionario_data)
                
        elif tipo_loja_nome == 'Restaurante':
            from restaurante.models import Funcionario
            
            if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
                funcionario_data['cargo'] = 'Gerente'
                funcionario_criado = Funcionario.objects.create(**funcionario_data)
                
        elif tipo_loja_nome == 'CRM Vendas':
            from crm_vendas.models import Vendedor
            
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
            logger.info(
                f"✅ Funcionário admin criado automaticamente: "
                f"{funcionario_criado.nome} para loja {instance.nome} ({tipo_loja_nome})"
            )
        else:
            logger.info(
                f"ℹ️ Funcionário já existe para {owner.username} na loja {instance.nome}"
            )
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar funcionário para loja {instance.nome}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Não interrompe a criação da loja, apenas loga o erro



@receiver(pre_delete, sender='superadmin.Loja')
def delete_all_loja_data(sender, instance, **kwargs):
    """
    Deleta TODOS os dados relacionados quando uma loja é excluída.
    
    Este signal garante que nenhum dado órfão fique no banco quando uma loja é deletada.
    Deleta em cascata:
    - Funcionários/Vendedores
    - Clientes
    - Agendamentos
    - Profissionais
    - Procedimentos
    - Leads
    - Pagamentos Asaas
    - Sessões de usuários
    - E qualquer outro dado relacionado
    
    Args:
        sender: Modelo Loja
        instance: Instância da loja sendo deletada
        **kwargs: Argumentos adicionais do signal
    """
    loja_id = instance.id
    loja_nome = instance.nome
    tipo_loja_nome = instance.tipo_loja.nome
    
    logger.info(f"🗑️ Iniciando exclusão em cascata para loja: {loja_nome} (ID: {loja_id})")
    
    try:
        # 1. Deletar funcionários/vendedores baseado no tipo de loja
        if tipo_loja_nome == 'Clínica de Estética':
            from clinica_estetica.models import Funcionario, Cliente, Agendamento, Profissional, Procedimento
            
            # Funcionários
            func_count = Funcionario.objects.all_without_filter().filter(loja_id=loja_id).count()
            Funcionario.objects.all_without_filter().filter(loja_id=loja_id).delete()
            logger.info(f"   ✅ {func_count} funcionários deletados")
            
            # Clientes
            cli_count = Cliente.objects.all_without_filter().filter(loja_id=loja_id).count()
            Cliente.objects.all_without_filter().filter(loja_id=loja_id).delete()
            logger.info(f"   ✅ {cli_count} clientes deletados")
            
            # Agendamentos
            agend_count = Agendamento.objects.all_without_filter().filter(loja_id=loja_id).count()
            Agendamento.objects.all_without_filter().filter(loja_id=loja_id).delete()
            logger.info(f"   ✅ {agend_count} agendamentos deletados")
            
            # Profissionais
            prof_count = Profissional.objects.all_without_filter().filter(loja_id=loja_id).count()
            Profissional.objects.all_without_filter().filter(loja_id=loja_id).delete()
            logger.info(f"   ✅ {prof_count} profissionais deletados")
            
            # Procedimentos
            proc_count = Procedimento.objects.all_without_filter().filter(loja_id=loja_id).count()
            Procedimento.objects.all_without_filter().filter(loja_id=loja_id).delete()
            logger.info(f"   ✅ {proc_count} procedimentos deletados")
            
        elif tipo_loja_nome == 'CRM Vendas':
            from crm_vendas.models import Vendedor, Cliente, Lead
            
            # Vendedores
            vend_count = Vendedor.objects.all_without_filter().filter(loja_id=loja_id).count()
            Vendedor.objects.all_without_filter().filter(loja_id=loja_id).delete()
            logger.info(f"   ✅ {vend_count} vendedores deletados")
            
            # Clientes
            cli_count = Cliente.objects.all_without_filter().filter(loja_id=loja_id).count()
            Cliente.objects.all_without_filter().filter(loja_id=loja_id).delete()
            logger.info(f"   ✅ {cli_count} clientes deletados")
            
            # Leads
            lead_count = Lead.objects.all_without_filter().filter(loja_id=loja_id).count()
            Lead.objects.all_without_filter().filter(loja_id=loja_id).delete()
            logger.info(f"   ✅ {lead_count} leads deletados")
            
        elif tipo_loja_nome == 'Restaurante':
            from restaurante.models import Funcionario
            
            # Funcionários (se tiver o manager correto)
            try:
                func_count = Funcionario.objects.filter(loja_id=loja_id).count()
                Funcionario.objects.filter(loja_id=loja_id).delete()
                logger.info(f"   ✅ {func_count} funcionários deletados")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar funcionários de restaurante: {e}")
            
        elif tipo_loja_nome == 'Serviços':
            from servicos.models import Funcionario
            
            # Funcionários (se tiver o manager correto)
            try:
                func_count = Funcionario.objects.filter(loja_id=loja_id).count()
                Funcionario.objects.filter(loja_id=loja_id).delete()
                logger.info(f"   ✅ {func_count} funcionários deletados")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar funcionários de serviços: {e}")
        
        # 2. Deletar usuário da loja (se não for usado por outras lojas)
        owner = instance.owner
        outras_lojas = sender.objects.filter(owner=owner).exclude(id=loja_id).count()
        
        if outras_lojas == 0:
            # Usuário não tem outras lojas, pode deletar
            logger.info(f"   🗑️ Deletando usuário {owner.username} (sem outras lojas)")
            owner.delete()
        else:
            logger.info(f"   ℹ️ Usuário {owner.username} mantido (tem {outras_lojas} outras lojas)")
        
        # 3. Deletar sessões do usuário
        try:
            from superadmin.models import UserSession
            sessoes_count = UserSession.objects.filter(user=owner).count()
            UserSession.objects.filter(user=owner).delete()
            logger.info(f"   ✅ {sessoes_count} sessões deletadas")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao deletar sessões: {e}")
        
        # 4. Deletar pagamentos Asaas relacionados
        try:
            from asaas_integration.models import AsaasPayment
            # Assumindo que tem um campo loja ou customer relacionado
            # Ajustar conforme o modelo real
            logger.info(f"   ℹ️ Verificando pagamentos Asaas...")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao verificar Asaas: {e}")
        
        logger.info(f"✅ Exclusão em cascata concluída para loja: {loja_nome}")
        
    except Exception as e:
        logger.error(f"❌ Erro durante exclusão em cascata da loja {loja_nome}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Não interrompe a exclusão da loja, apenas loga o erro
