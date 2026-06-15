import logging
import os
import shutil
from pathlib import Path

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from core.logging_utils import mask_email

logger = logging.getLogger(__name__)

from .helpers import _criar_tabelas_crm

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
        from core.cloudinary_folders import ensure_loja_cloudinary_folders
        ensure_loja_cloudinary_folders(instance)
    except Exception as cloud_err:
        logger.warning(
            'Pastas Cloudinary não criadas para loja %s: %s',
            instance.slug,
            cloud_err,
        )
    
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
            # CRM Vendas: admin (owner) é criado como Vendedor com is_admin=True
            # Isso permite que o admin apareça na lista de funcionários e tenha acesso total
            from crm_vendas.models import Vendedor
            
            if not Vendedor.objects.filter(email=owner.email, loja_id=instance.id).exists():
                vendedor_data = {
                    'nome': owner.get_full_name() or owner.username,
                    'email': owner.email,
                    'telefone': '',
                    'cargo': 'Administrador',
                    'is_admin': True,
                    'is_active': True,
                    'loja_id': instance.id
                }
                funcionario_criado = Vendedor.objects.create(**vendedor_data)
                logger.info(f"✅ Vendedor Administrador criado para CRM Vendas: {funcionario_criado.nome}")
            
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

        elif tipo_loja_nome == 'Cabeleireiro':
            from cabeleireiro.models import Funcionario
            
            if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
                funcionario_criado = Funcionario.objects.create(**funcionario_data)

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
        # Ignorar erro de tabela inexistente (schema ainda não criado — vendedor será criado após migrations)
        err_str = str(e)
        if 'does not exist' in err_str or 'UndefinedTable' in err_str:
            logger.debug(
                f"ℹ️ Tabela ainda não existe para loja {instance.nome} — "
                f"vendedor/funcionário será criado após migrations do schema."
            )
        else:
            logger.error(f"❌ Erro ao criar funcionário para loja {instance.nome}: {e}")
            import traceback
            logger.error(traceback.format_exc())
        # Não interrompe a criação da loja

