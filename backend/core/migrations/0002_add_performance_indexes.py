"""
🚀 MIGRAÇÃO: Adicionar índices de performance
Adiciona índices em campos frequentemente consultados
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adiciona índices compostos para melhorar performance de queries
    
    IMPORTANTE: Esta migração deve ser aplicada em TODOS os bancos:
    - default (superadmin)
    - suporte
    - loja_template
    - Todos os bancos de lojas existentes
    """
    
    dependencies = [
        ('core', '0001_initial'),
    ]
    
    operations = [
        # Nota: Índices específicos de cada app devem ser adicionados
        # nas migrações dos respectivos apps
        
        # Esta migração serve como exemplo e documentação
        # dos índices que devem ser criados
    ]


# ============================================
# ÍNDICES RECOMENDADOS POR APP
# ============================================

"""
CLINICA_ESTETICA:

class Agendamento(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'data'], name='clinica_agend_loja_data_idx'),
            models.Index(fields=['loja_id', 'status'], name='clinica_agend_loja_status_idx'),
            models.Index(fields=['cliente', 'data'], name='clinica_agend_cliente_data_idx'),
            models.Index(fields=['profissional', 'data'], name='clinica_agend_prof_data_idx'),
            models.Index(fields=['data', 'status'], name='clinica_agend_data_status_idx'),
        ]

class Cliente(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'is_active'], name='clinica_cli_loja_active_idx'),
            models.Index(fields=['email'], name='clinica_cli_email_idx'),
            models.Index(fields=['telefone'], name='clinica_cli_telefone_idx'),
        ]

class Profissional(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'is_active'], name='clinica_prof_loja_active_idx'),
        ]


RESTAURANTE:

class Pedido(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='rest_pedido_loja_status_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='rest_pedido_loja_created_idx'),
            models.Index(fields=['mesa', 'status'], name='rest_pedido_mesa_status_idx'),
            models.Index(fields=['status', 'created_at'], name='rest_pedido_status_created_idx'),
        ]

class Mesa(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='rest_mesa_loja_status_idx'),
            models.Index(fields=['numero'], name='rest_mesa_numero_idx'),
        ]

class ItemCardapio(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'is_disponivel'], name='rest_item_loja_disp_idx'),
            models.Index(fields=['categoria', 'is_disponivel'], name='rest_item_cat_disp_idx'),
        ]


CRM_VENDAS:

class Lead(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='crm_lead_loja_status_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_lead_loja_created_idx'),
            models.Index(fields=['status', 'created_at'], name='crm_lead_status_created_idx'),
            models.Index(fields=['email'], name='crm_lead_email_idx'),
        ]

class Venda(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='crm_venda_loja_status_idx'),
            models.Index(fields=['loja_id', 'data_venda'], name='crm_venda_loja_data_idx'),
            models.Index(fields=['cliente', 'data_venda'], name='crm_venda_cli_data_idx'),
        ]


ECOMMERCE:

class Produto(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'is_active'], name='ecom_prod_loja_active_idx'),
            models.Index(fields=['categoria', 'is_active'], name='ecom_prod_cat_active_idx'),
            models.Index(fields=['preco'], name='ecom_prod_preco_idx'),
        ]

class Pedido(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='ecom_pedido_loja_status_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='ecom_pedido_loja_created_idx'),
            models.Index(fields=['cliente', 'status'], name='ecom_pedido_cli_status_idx'),
        ]


SUPERADMIN:

class Loja(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['slug'], name='loja_slug_idx'),
            models.Index(fields=['owner'], name='loja_owner_idx'),
            models.Index(fields=['is_active'], name='loja_active_idx'),
            models.Index(fields=['tipo_loja'], name='loja_tipo_idx'),
        ]

class UserSession(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active'], name='session_user_active_idx'),
            models.Index(fields=['session_id'], name='session_id_idx'),
            models.Index(fields=['last_activity'], name='session_activity_idx'),
        ]

class FinanceiroLoja(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja'], name='fin_loja_idx'),
            models.Index(fields=['asaas_customer_id'], name='fin_asaas_customer_idx'),
            models.Index(fields=['asaas_subscription_id'], name='fin_asaas_sub_idx'),
        ]


SUPORTE:

class Chamado(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='sup_chamado_loja_status_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='sup_chamado_loja_created_idx'),
            models.Index(fields=['status', 'prioridade'], name='sup_chamado_status_prior_idx'),
        ]
"""
