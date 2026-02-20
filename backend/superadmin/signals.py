"""
Signals para superadmin - Criação e exclusão automática

IMPORTANTE: 
1. Quando uma loja é CRIADA, cria automaticamente um funcionário para o admin
2. Quando uma loja é EXCLUÍDA, deleta TODOS os dados relacionados (cascata)
"""
from django.db.models.signals import post_save, pre_delete, post_delete
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

        elif tipo_loja_nome == 'Clínica da Beleza':
            # Owner é vinculado como Professional + ProfissionalUsuario (recepção) no serializer,
            # após a criação do schema e das tabelas clinica_beleza.
            logger.info(
                f"Clínica da Beleza: owner {owner.username} será vinculado como administrador no cadastro de profissionais (serializer)"
            )
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
        logger.warning(f"⚠️ Tipo de loja não disponível para {loja_nome}, pulando exclusão de dados relacionados")
        return
    
    try:
        # 0. Remover LojaAssinatura por slug (evita órfãos se loja for excluída fora da API)
        try:
            from asaas_integration.models import LojaAssinatura
            n = LojaAssinatura.objects.filter(loja_slug=instance.slug).count()
            LojaAssinatura.objects.filter(loja_slug=instance.slug).delete()
            if n:
                logger.info(f"   ✅ {n} assinatura(s) Asaas (loja_slug) removida(s)")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao remover LojaAssinatura por slug: {e}")
        
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
            from crm_vendas.models import Vendedor, Cliente, Lead, Venda, Pipeline, Produto
            
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
            
            # Vendas, Pipeline e Produtos (evitar órfãos)
            try:
                venda_count = Venda.objects.all_without_filter().filter(loja_id=loja_id).count()
                Venda.objects.all_without_filter().filter(loja_id=loja_id).delete()
                logger.info(f"   ✅ {venda_count} vendas deletadas")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar vendas CRM: {e}")
            try:
                pipe_count = Pipeline.objects.all_without_filter().filter(loja_id=loja_id).count()
                Pipeline.objects.all_without_filter().filter(loja_id=loja_id).delete()
                logger.info(f"   ✅ {pipe_count} etapas pipeline deletadas")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar pipeline: {e}")
            try:
                prod_count = Produto.objects.all_without_filter().filter(loja_id=loja_id).count()
                Produto.objects.all_without_filter().filter(loja_id=loja_id).delete()
                logger.info(f"   ✅ {prod_count} produtos CRM deletados")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar produtos CRM: {e}")
            
        elif tipo_loja_nome == 'Restaurante':
            from restaurante.models import (
                Funcionario, Reserva, Pedido, ItemCardapio, Categoria, Mesa, Cliente,
                Fornecedor, NotaFiscalEntrada, EstoqueItem, MovimentoEstoque, RegistroPesoBalança
            )
            
            def _delete_restaurante(model, nome):
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    count = qs.count()
                    qs.delete()
                    logger.info(f"   ✅ {count} {nome} deletados")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao deletar {nome}: {e}")
            
            # Ordem: dependentes primeiro. MovimentoEstoque/RegistroPesoBalança referenciam EstoqueItem (PROTECT)
            _delete_restaurante(Reserva, 'reservas')
            _delete_restaurante(Pedido, 'pedidos')
            _delete_restaurante(ItemCardapio, 'itens cardápio')
            _delete_restaurante(Categoria, 'categorias')
            _delete_restaurante(Mesa, 'mesas')
            _delete_restaurante(Cliente, 'clientes')
            _delete_restaurante(Funcionario, 'funcionários')
            _delete_restaurante(Fornecedor, 'fornecedores')
            _delete_restaurante(NotaFiscalEntrada, 'notas fiscais')
            # Movimentos e registros de peso antes de EstoqueItem (FK PROTECT)
            try:
                mov_count = MovimentoEstoque.objects.filter(estoque_item__loja_id=loja_id).count()
                MovimentoEstoque.objects.filter(estoque_item__loja_id=loja_id).delete()
                logger.info(f"   ✅ {mov_count} movimentos de estoque deletados")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar movimentos estoque: {e}")
            try:
                reg_count = RegistroPesoBalança.objects.filter(estoque_item__loja_id=loja_id).count()
                RegistroPesoBalança.objects.filter(estoque_item__loja_id=loja_id).delete()
                logger.info(f"   ✅ {reg_count} registros peso deletados")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar registros peso: {e}")
            _delete_restaurante(EstoqueItem, 'itens estoque')
            
        elif tipo_loja_nome == 'Serviços':
            from servicos.models import Funcionario, Servico, Profissional, Agendamento, OrdemServico, Orcamento, Cliente, Categoria
            
            def _delete_servicos(model, nome):
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    count = qs.count()
                    qs.delete()
                    logger.info(f"   ✅ {count} {nome} deletados")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao deletar {nome} (Serviços): {e}")
            
            _delete_servicos(Agendamento, 'agendamentos')
            _delete_servicos(OrdemServico, 'ordens de serviço')
            _delete_servicos(Orcamento, 'orçamentos')
            _delete_servicos(Servico, 'serviços')  # antes de Categoria (FK)
            _delete_servicos(Profissional, 'profissionais')
            _delete_servicos(Cliente, 'clientes')
            _delete_servicos(Categoria, 'categorias')
            _delete_servicos(Funcionario, 'funcionários')
            
        elif tipo_loja_nome == 'Clínica da Beleza':
            from django.db import transaction as tx
            from clinica_beleza.models import (
                Patient, Professional, Procedure, Appointment, BloqueioHorario,
                HorarioTrabalhoProfissional, Payment, CampanhaPromocao
            )
            def _delete_clinica_beleza(model, nome):
                try:
                    with tx.atomic():
                        if hasattr(model.objects, 'all_without_filter'):
                            qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                        else:
                            qs = model.objects.filter(loja_id=loja_id)
                        count = qs.count()
                        qs.delete()
                        logger.info(f"   ✅ {count} {nome} (Clínica da Beleza) deletados")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao deletar {nome} Clínica da Beleza: {e}")
            # Ordem: dependentes primeiro (Payment -> Appointment; BloqueioHorario, HorarioTrabalhoProfissional)
            _delete_clinica_beleza(Payment, 'pagamentos')
            _delete_clinica_beleza(Appointment, 'agendamentos')
            _delete_clinica_beleza(BloqueioHorario, 'bloqueios horário')
            _delete_clinica_beleza(HorarioTrabalhoProfissional, 'horários trabalho profissional')
            _delete_clinica_beleza(CampanhaPromocao, 'campanhas promoção')
            _delete_clinica_beleza(Procedure, 'procedimentos')
            _delete_clinica_beleza(Professional, 'profissionais')
            _delete_clinica_beleza(Patient, 'pacientes')
            
        elif tipo_loja_nome == 'Cabeleireiro':
            # Dados do Cabeleireiro podem estar no schema (DROP abaixo) ou no default
            from cabeleireiro.models import (
                Cliente, Profissional, Servico, Agendamento, Produto, Venda,
                Funcionario, HorarioFuncionamento, BloqueioAgenda
            )
            
            def _delete_cabeleireiro(model, nome):
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    count = qs.count()
                    qs.delete()
                    logger.info(f"   ✅ {count} {nome} (Cabeleireiro) deletados")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao deletar {nome} Cabeleireiro: {e}")
            
            _delete_cabeleireiro(BloqueioAgenda, 'bloqueios agenda')
            _delete_cabeleireiro(Agendamento, 'agendamentos')
            _delete_cabeleireiro(Venda, 'vendas')
            _delete_cabeleireiro(Funcionario, 'funcionários')
            _delete_cabeleireiro(HorarioFuncionamento, 'horários')
            _delete_cabeleireiro(Produto, 'produtos')
            _delete_cabeleireiro(Servico, 'serviços')
            _delete_cabeleireiro(Profissional, 'profissionais')
            _delete_cabeleireiro(Cliente, 'clientes')
        
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
        
        # 5. Rede de segurança: limpar qualquer tabela do default com loja_id (evita órfãos)
        # Cada DELETE em um savepoint para que falha em uma tabela (ex.: não existe em public)
        # não aborte a transação inteira (evita "current transaction is aborted")
        try:
            from django.db import connection, transaction
            from superadmin.orfaos_config import TABELAS_LOJA_ID
            for tabela, coluna in TABELAS_LOJA_ID:
                try:
                    with transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute(
                                f'DELETE FROM {tabela} WHERE {coluna} = %s',
                                [loja_id]
                            )
                            if cursor.rowcount:
                                logger.info(f"   ✅ Safety net: {cursor.rowcount} linha(s) em {tabela} removida(s)")
                except Exception as e:
                    logger.warning(f"   ⚠️ Safety net {tabela}: {e}")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro na rede de segurança TABELAS_LOJA_ID: {e}")
        
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
    """
    from django.contrib.auth.models import User
    from superadmin.models import UserSession, ProfissionalUsuario

    owner_id = getattr(instance, 'owner_id', None)
    if not owner_id:
        return
    # Após o delete da loja, contar se o owner ainda tem outras lojas
    from superadmin.models import Loja
    if Loja.objects.filter(owner_id=owner_id).exists():
        return
    try:
        user = User.objects.filter(id=owner_id).first()
        if not user or user.is_superuser:
            return
        UserSession.objects.filter(user=user).delete()
        ProfissionalUsuario.objects.filter(user=user).delete()
        user.groups.clear()
        user.user_permissions.clear()
        user.delete()
        logger.info(f"   ✅ Usuário órfão removido (owner da loja excluída): {user.username}")
    except Exception as e:
        logger.warning(f"   ⚠️ Erro ao remover owner órfão: {e}")
