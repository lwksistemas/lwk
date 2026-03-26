"""
Signals para superadmin - Criação e exclusão automática

IMPORTANTE: 
1. Quando uma loja é CRIADA, cria automaticamente um funcionário para o admin
2. Quando uma loja é EXCLUÍDA, deleta TODOS os dados relacionados (cascata)
3. Arquivos (backups, media) são removidos para evitar órfãos
"""
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def _criar_tabelas_crm(cursor, db_name):
    """
    Cria tabelas de ProdutoServico, OportunidadeItem, Proposta e Contrato no schema do CRM.
    Usado no signal de criação de lojas CRM Vendas.
    """
    # Criar tabela ProdutoServico
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS "{db_name}".crm_vendas_produto_servico (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            tipo VARCHAR(20) NOT NULL DEFAULT 'produto',
            nome VARCHAR(255) NOT NULL,
            descricao TEXT,
            preco DECIMAL(12, 2) NOT NULL DEFAULT 0,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """)
    
    # Criar índices para ProdutoServico
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS crm_ps_loja_tipo_idx 
        ON "{db_name}".crm_vendas_produto_servico (loja_id, tipo);
    """)
    
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS crm_ps_loja_ativo_idx 
        ON "{db_name}".crm_vendas_produto_servico (loja_id, ativo);
    """)
    
    # Criar tabela OportunidadeItem
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS "{db_name}".crm_vendas_oportunidade_item (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            oportunidade_id BIGINT NOT NULL REFERENCES "{db_name}".crm_vendas_oportunidade(id) ON DELETE CASCADE,
            produto_servico_id BIGINT NOT NULL REFERENCES "{db_name}".crm_vendas_produto_servico(id) ON DELETE CASCADE,
            quantidade DECIMAL(10, 2) NOT NULL DEFAULT 1,
            preco_unitario DECIMAL(12, 2) NOT NULL,
            observacao VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """)
    
    # Criar índice para OportunidadeItem
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS crm_oi_loja_opor_idx 
        ON "{db_name}".crm_vendas_oportunidade_item (loja_id, oportunidade_id);
    """)
    
    # Criar tabela Proposta
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS "{db_name}".crm_vendas_proposta (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            oportunidade_id BIGINT NOT NULL REFERENCES "{db_name}".crm_vendas_oportunidade(id) ON DELETE CASCADE,
            titulo VARCHAR(255) NOT NULL,
            conteudo TEXT,
            valor_total DECIMAL(12, 2),
            status VARCHAR(20) NOT NULL DEFAULT 'rascunho',
            data_envio TIMESTAMP WITH TIME ZONE,
            data_resposta TIMESTAMP WITH TIME ZONE,
            observacoes TEXT,
            nome_vendedor_assinatura VARCHAR(255),
            nome_cliente_assinatura VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """)
    
    # Criar índices para Proposta
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS crm_prop_loja_opor_idx 
        ON "{db_name}".crm_vendas_proposta (loja_id, oportunidade_id);
    """)
    
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS crm_prop_loja_status_idx 
        ON "{db_name}".crm_vendas_proposta (loja_id, status);
    """)
    
    # Criar tabela Contrato
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS "{db_name}".crm_vendas_contrato (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            oportunidade_id BIGINT NOT NULL UNIQUE REFERENCES "{db_name}".crm_vendas_oportunidade(id) ON DELETE CASCADE,
            numero VARCHAR(50),
            titulo VARCHAR(255) NOT NULL,
            conteudo TEXT,
            valor_total DECIMAL(12, 2),
            status VARCHAR(20) NOT NULL DEFAULT 'rascunho',
            data_envio TIMESTAMP WITH TIME ZONE,
            data_assinatura TIMESTAMP WITH TIME ZONE,
            observacoes TEXT,
            nome_vendedor_assinatura VARCHAR(255),
            nome_cliente_assinatura VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """)
    
    # Criar índices para Contrato
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS crm_cont_loja_opor_idx 
        ON "{db_name}".crm_vendas_contrato (loja_id, oportunidade_id);
    """)
    
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS crm_cont_loja_status_idx 
        ON "{db_name}".crm_vendas_contrato (loja_id, status);
    """)


def _limpar_arquivos_orfaos_loja(loja):
    """
    Remove arquivos órfãos ao excluir loja:
    - Diretório backups/{slug}/ (arquivos de backup)
    - Arquivos em media/nfe_restaurante/ com prefixo loja_{id}_
    """
    from django.conf import settings
    base_dir = Path(settings.BASE_DIR)

    # Diretório de backups da loja
    backups_dir = base_dir / 'backups' / loja.slug
    if backups_dir.exists():
        try:
            shutil.rmtree(backups_dir)
            logger.info(f"   ✅ Diretório backups removido: {backups_dir}")
        except OSError as e:
            logger.warning(f"   ⚠️ Erro ao remover backups/{loja.slug}: {e}")

    # Arquivos NF-e em media/nfe_restaurante/ com prefixo loja_{id}_
    media_root = getattr(settings, 'MEDIA_ROOT', base_dir / 'media')
    nfe_base = Path(media_root) / 'nfe_restaurante'
    if nfe_base.exists():
        prefix = f'loja_{loja.id}_'
        removidos = 0
        for subdir in nfe_base.rglob('*'):
            if subdir.is_file() and prefix in subdir.name:
                try:
                    subdir.unlink()
                    removidos += 1
                except OSError as e:
                    logger.warning(f"   ⚠️ Erro ao remover NF-e {subdir}: {e}")
        if removidos:
            logger.info(f"   ✅ {removidos} arquivo(s) NF-e órfão(s) removido(s)")


@receiver(pre_delete, sender='superadmin.HistoricoBackup')
def remover_arquivo_backup_ao_deletar(sender, instance, **kwargs):
    """
    Remove o arquivo de backup do disco quando HistoricoBackup é excluído.
    Evita arquivos órfãos em backups/{slug}/.
    """
    if instance.arquivo_path:
        try:
            if os.path.exists(instance.arquivo_path):
                os.remove(instance.arquivo_path)
                logger.debug(f"🗑️ Arquivo backup removido: {instance.arquivo_nome}")
        except (ValueError, OSError) as e:
            logger.warning(f"⚠️ Erro ao remover arquivo backup: {e}")


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
        
        # Criar funcionário baseado no tipo de app
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
            # CRM Vendas: admin (owner) NÃO é vendedor - aparece em funcionários como
            # "Administrador" (Loja.owner). Admin cadastra gerentes e vendedores pela página.
            # As tabelas do CRM são criadas pelas migrations (0015_add_produto_servico_proposta_contrato)
            logger.info(
                f"CRM Vendas: admin aparece como Administrador em funcionários (não é Vendedor). "
                f"Tabelas serão criadas pelas migrations."
            )
            
            # Criar categorias padrão de produtos/serviços
            try:
                from crm_vendas.models import CategoriaProdutoServico
                
                categorias_padrao = [
                    {'nome': 'Hardware', 'cor': '#3B82F6', 'ordem': 1},
                    {'nome': 'Software', 'cor': '#8B5CF6', 'ordem': 2},
                    {'nome': 'Consultoria', 'cor': '#10B981', 'ordem': 3},
                    {'nome': 'Suporte Técnico', 'cor': '#F59E0B', 'ordem': 4},
                    {'nome': 'Treinamento', 'cor': '#EF4444', 'ordem': 5},
                ]
                
                for cat_data in categorias_padrao:
                    CategoriaProdutoServico.objects.get_or_create(
                        loja_id=instance.id,
                        nome=cat_data['nome'],
                        defaults={
                            'cor': cat_data['cor'],
                            'ordem': cat_data['ordem'],
                            'ativo': True,
                        }
                    )
                
                logger.info(f"✅ Categorias padrão criadas para loja CRM Vendas: {instance.nome}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar categorias padrão para loja {instance.nome}: {e}")
            
            return

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
            logger.warning(f"Tipo de app não reconhecido: {tipo_loja_nome}")
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
    
    IMPORTANTE (v993): NÃO usar transaction.atomic() neste signal. O pre_delete
    já roda dentro da transação do loja.delete(). Transações aninhadas criam
    savepoints e podem causar rollback silencioso, impedindo a exclusão da loja.
    
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
        logger.warning(f"⚠️ Tipo de app não disponível para {loja_nome}, pulando exclusão de dados relacionados")
        return
    
    try:
        # Alias do banco da loja: usar schema isolado (evita deletar no default e criar órfãos)
        from django.conf import settings
        db_alias = None
        db_name = getattr(instance, 'database_name', None)
        if db_name:
            import os
            DATABASE_URL = os.environ.get('DATABASE_URL', '')
            if 'postgres' in DATABASE_URL.lower() and db_name not in settings.DATABASES:
                try:
                    from core.db_config import ensure_loja_database_config
                    ensure_loja_database_config(db_name, conn_max_age=0)
                except Exception as e:
                    logger.warning(f"   ⚠️ Não foi possível configurar banco da loja {db_name}: {e}")
            if db_name in settings.DATABASES:
                db_alias = db_name

        # 0. Remover LojaAssinatura por slug (evita órfãos se loja for excluída fora da API)
        try:
            from asaas_integration.models import LojaAssinatura
            n = LojaAssinatura.objects.filter(loja_slug=instance.slug).count()
            LojaAssinatura.objects.filter(loja_slug=instance.slug).delete()
            if n:
                logger.info(f"   ✅ {n} assinatura(s) Asaas (loja_slug) removida(s)")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao remover LojaAssinatura por slug: {e}")
        
        # 1. Deletar funcionários/vendedores baseado no tipo de app (no schema da loja quando db_alias definido)
        if tipo_loja_nome == 'Clínica de Estética':
            from clinica_estetica.models import Funcionario, Cliente, Agendamento, Profissional, Procedimento
            _db = db_alias

            # Funcionários
            qs = Funcionario.objects.all_without_filter().filter(loja_id=loja_id)
            if _db:
                qs = qs.using(_db)
            func_count = qs.count()
            qs.delete()
            logger.info(f"   ✅ {func_count} funcionários deletados")

            qs = Cliente.objects.all_without_filter().filter(loja_id=loja_id)
            if _db:
                qs = qs.using(_db)
            cli_count = qs.count()
            qs.delete()
            logger.info(f"   ✅ {cli_count} clientes deletados")

            qs = Agendamento.objects.all_without_filter().filter(loja_id=loja_id)
            if _db:
                qs = qs.using(_db)
            agend_count = qs.count()
            qs.delete()
            logger.info(f"   ✅ {agend_count} agendamentos deletados")

            qs = Profissional.objects.all_without_filter().filter(loja_id=loja_id)
            if _db:
                qs = qs.using(_db)
            prof_count = qs.count()
            qs.delete()
            logger.info(f"   ✅ {prof_count} profissionais deletados")

            qs = Procedimento.objects.all_without_filter().filter(loja_id=loja_id)
            if _db:
                qs = qs.using(_db)
            proc_count = qs.count()
            qs.delete()
            logger.info(f"   ✅ {proc_count} procedimentos deletados")
            
        elif tipo_loja_nome == 'CRM Vendas':
            from crm_vendas.models import Atividade, Oportunidade, Lead, Contato, Conta, Vendedor
            _db = db_alias

            def _delete_crm(model, nome):
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    if _db:
                        qs = qs.using(_db)
                    count = qs.count()
                    qs.delete()
                    logger.info(f"   ✅ {count} {nome} (CRM Vendas) deletados")
                except Exception as e:
                    # Schema vazio (tabelas nunca criadas): esperado, não é erro
                    if 'does not exist' in str(e).lower():
                        logger.debug(f"   ℹ️ Schema vazio: {nome} não existem (ok)")
                    else:
                        logger.warning(f"   ⚠️ Erro ao deletar {nome} CRM Vendas: {e}")

            _delete_crm(Atividade, 'atividades')
            _delete_crm(Oportunidade, 'oportunidades')
            _delete_crm(Lead, 'leads')
            _delete_crm(Contato, 'contatos')
            _delete_crm(Conta, 'contas')
            _delete_crm(Vendedor, 'vendedores')

        elif tipo_loja_nome == 'Restaurante':
            from restaurante.models import (
                Funcionario, Reserva, Pedido, ItemCardapio, Categoria, Mesa, Cliente,
                Fornecedor, NotaFiscalEntrada, EstoqueItem, MovimentoEstoque, RegistroPesoBalança
            )
            _db = db_alias

            def _delete_restaurante(model, nome):
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    if _db:
                        qs = qs.using(_db)
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
                qs = MovimentoEstoque.objects.filter(estoque_item__loja_id=loja_id)
                if _db:
                    qs = qs.using(_db)
                mov_count = qs.count()
                qs.delete()
                logger.info(f"   ✅ {mov_count} movimentos de estoque deletados")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar movimentos estoque: {e}")
            try:
                qs = RegistroPesoBalança.objects.filter(estoque_item__loja_id=loja_id)
                if _db:
                    qs = qs.using(_db)
                reg_count = qs.count()
                qs.delete()
                logger.info(f"   ✅ {reg_count} registros peso deletados")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao deletar registros peso: {e}")
            _delete_restaurante(EstoqueItem, 'itens estoque')
            
        elif tipo_loja_nome == 'Serviços':
            from servicos.models import Funcionario, Servico, Profissional, Agendamento, OrdemServico, Orcamento, Cliente, Categoria
            _db = db_alias

            def _delete_servicos(model, nome):
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    if _db:
                        qs = qs.using(_db)
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
            from clinica_beleza.models import (
                Patient, Professional, Procedure, Appointment, BloqueioHorario,
                HorarioTrabalhoProfissional, Payment, CampanhaPromocao
            )
            _db = db_alias

            def _delete_clinica_beleza(model, nome):
                """Sem transaction.atomic() - signal já está na transação do loja.delete()"""
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    if _db:
                        qs = qs.using(_db)
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
            from cabeleireiro.models import (
                Cliente, Profissional, Servico, Agendamento, Produto, Venda,
                Funcionario, HorarioFuncionamento, BloqueioAgenda
            )
            _db = db_alias

            def _delete_cabeleireiro(model, nome):
                try:
                    if hasattr(model.objects, 'all_without_filter'):
                        qs = model.objects.all_without_filter().filter(loja_id=loja_id)
                    else:
                        qs = model.objects.filter(loja_id=loja_id)
                    if _db:
                        qs = qs.using(_db)
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
        
        # 5. Rede de segurança: limpar só tabelas do default (public) com loja_id.
        # Dados operacionais da loja estão no schema da loja (já limpos acima com .using());
        # no default ficam só superadmin/asaas (TABELAS_LOJA_ID_DEFAULT).
        # Cada tabela usa transaction.atomic() (savepoint) para que falha em uma (ex: tabela
        # inexistente) não aborte a transação principal do loja.delete()
        try:
            from django.db import connection, transaction
            from superadmin.orfaos_config import TABELAS_LOJA_ID_DEFAULT
            for tabela, coluna in TABELAS_LOJA_ID_DEFAULT:
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
            logger.warning(f"   ⚠️ Erro na rede de segurança TABELAS_LOJA_ID_DEFAULT: {e}")
        
        # 6. Remover config do banco de settings.DATABASES (evitar nome órfão no default)
        db_name = getattr(instance, 'database_name', None)
        if db_name and db_name in settings.DATABASES:
            try:
                del settings.DATABASES[db_name]
                logger.info(f"   ✅ Config do banco removida do settings: {db_name}")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao remover config do banco: {e}")

        # 7. Remover arquivos órfãos: diretório de backups e media da loja
        _limpar_arquivos_orfaos_loja(instance)
        
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

    IMPORTANTE: Usa transaction.on_commit() para executar APÓS o commit do delete.
    Caso contrário, se user.delete() falhar (ex: tabela stores_store inexistente),
    a transação do PostgreSQL seria abortada e o delete da loja seria revertido.
    """
    from django.db import transaction

    owner_id = getattr(instance, 'owner_id', None)
    loja_slug = getattr(instance, 'slug', 'unknown')
    loja_nome = getattr(instance, 'nome', 'unknown')
    
    logger.info(f"🔍 Signal remove_owner_if_orphan: Loja excluída: {loja_nome} (slug: {loja_slug}, owner_id: {owner_id})")
    
    if not owner_id:
        logger.warning(f"   ⚠️ owner_id não encontrado para loja {loja_slug}")
        return

    def _remover_owner_apos_commit():
        from django.contrib.auth.models import User
        from superadmin.models import Loja
        from superadmin.utils import delete_user_raw

        logger.info(f"   🔍 Verificando se owner {owner_id} ficou órfão após exclusão da loja {loja_slug}...")
        
        # Verificar se owner possui outras lojas
        outras_lojas = Loja.objects.filter(owner_id=owner_id).count()
        if outras_lojas > 0:
            logger.info(f"   ℹ️  Owner {owner_id} possui {outras_lojas} loja(s) ativa(s). Não será removido.")
            return
        
        logger.info(f"   🔍 Owner {owner_id} não possui outras lojas. Verificando se pode ser removido...")
        
        try:
            user = User.objects.filter(id=owner_id).first()
            if not user:
                logger.warning(f"   ⚠️ Usuário {owner_id} não encontrado no banco de dados")
                return
            
            if user.is_superuser:
                logger.info(f"   ℹ️  Usuário {user.username} é superuser. Não será removido.")
                return
            
            logger.info(f"   🗑️  Removendo usuário órfão: {user.username} (ID: {owner_id}, email: {user.email})")
            delete_user_raw(owner_id)
            logger.info(f"   ✅ Usuário órfão removido com sucesso: {user.username}")
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao remover owner órfão {owner_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())

    logger.info(f"   📝 Agendando remoção de owner órfão para após commit da transação...")
    transaction.on_commit(_remover_owner_apos_commit)



@receiver(post_save, sender='superadmin.FinanceiroLoja')
def on_payment_confirmed(sender, instance, created, **kwargs):
    """
    Dispara envio de senha provisória quando pagamento é confirmado.
    
    ✅ NOVO v719: Signal para enviar senha após confirmação de pagamento
    
    Trigger: status_pagamento muda para 'ativo' E senha ainda não foi enviada
    
    Fluxo:
    1. Webhook recebe confirmação de pagamento (Asaas ou Mercado Pago)
    2. Webhook atualiza status_pagamento para 'ativo'
    3. Este signal é disparado automaticamente
    4. EmailService envia senha provisória para o administrador
    5. FinanceiroLoja é atualizado (senha_enviada=True, data_envio_senha=now)
    
    Args:
        sender: Modelo FinanceiroLoja
        instance: Instância do FinanceiroLoja atualizado
        created: False (signal só dispara em updates)
        **kwargs: Argumentos adicionais do signal
    """
    # Não processar em criação (apenas em updates)
    if created:
        return
    
    # Verificar se status mudou para 'ativo' e senha ainda não foi enviada
    if instance.status_pagamento == 'ativo' and not instance.senha_enviada:
        from superadmin.email_service import EmailService
        
        try:
            loja = instance.loja
            owner = loja.owner
            
            logger.info(f"💰 Pagamento confirmado para loja {loja.nome}. Enviando senha provisória...")
            
            # Enviar senha provisória
            service = EmailService()
            success = service.enviar_senha_provisoria(loja, owner)
            
            if success:
                logger.info(f"✅ Senha provisória enviada para {owner.email} (loja {loja.slug})")
            else:
                logger.warning(
                    f"⚠️ Falha ao enviar senha para {owner.email} (loja {loja.slug}). "
                    "Email registrado para retry automático."
                )
        
        except Exception as e:
            logger.error(
                f"❌ Erro ao processar envio de senha para loja {instance.loja.slug}: {e}",
                exc_info=True
            )
