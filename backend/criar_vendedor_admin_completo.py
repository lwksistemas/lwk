#!/usr/bin/env python
"""
Script para criar vendedor admin COMPLETO (Vendedor + VendedorUsuario) nas lojas CRM Vendas.
Versão: v1354

USO:
    heroku run "python backend/criar_vendedor_admin_completo.py" --app lwksistemas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lwksistemas.settings')
django.setup()

from django.db import connections, transaction
from superadmin.models import Loja, VendedorUsuario
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def criar_vendedor_admin_completo():
    """Cria vendedor admin + VendedorUsuario para todas as lojas CRM Vendas."""
    try:
        # Buscar lojas CRM Vendas
        lojas_crm = Loja.objects.filter(tipo_loja__nome='CRM Vendas', is_active=True)
        total = lojas_crm.count()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"CRIAÇÃO DE VENDEDORES ADMIN COMPLETO - CRM VENDAS")
        logger.info(f"{'='*80}\n")
        logger.info(f"Total de lojas CRM Vendas: {total}\n")
        
        if total == 0:
            logger.info("✅ Nenhuma loja para processar")
            return
        
        corrigidas = 0
        ja_corretas = 0
        erros = 0
        
        for loja in lojas_crm:
            try:
                owner = loja.owner
                schema_name = loja.database_name
                
                logger.info(f"{'='*80}")
                logger.info(f"Loja: {loja.nome}")
                logger.info(f"CPF/CNPJ: {loja.cpf_cnpj}")
                logger.info(f"Schema: {schema_name}")
                logger.info(f"Owner: {owner.username} ({owner.email})")
                
                with transaction.atomic():
                    with connections['default'].cursor() as cursor:
                        # 1. Verificar/Criar Vendedor no schema da loja
                        cursor.execute(f"""
                            SET search_path TO {schema_name}, public;
                            SELECT id, nome, is_admin FROM crm_vendas_vendedor
                            WHERE loja_id = %s AND email = %s;
                        """, [loja.id, owner.email])
                        
                        vendedor_existente = cursor.fetchone()
                        
                        if vendedor_existente:
                            vendedor_id, vendedor_nome, is_admin = vendedor_existente
                            logger.info(f"✅ Vendedor já existe: {vendedor_nome} (ID: {vendedor_id})")
                            
                            if not is_admin:
                                logger.info(f"🔧 Atualizando para admin...")
                                cursor.execute(f"""
                                    SET search_path TO {schema_name}, public;
                                    UPDATE crm_vendas_vendedor
                                    SET is_admin = TRUE, cargo = 'Administrador', updated_at = NOW()
                                    WHERE id = %s;
                                """, [vendedor_id])
                                logger.info(f"✅ Atualizado para admin")
                        else:
                            # Criar vendedor admin
                            logger.info(f"🔧 Criando vendedor admin...")
                            nome = owner.get_full_name() or owner.username
                            
                            cursor.execute(f"""
                                SET search_path TO {schema_name}, public;
                                INSERT INTO crm_vendas_vendedor
                                (loja_id, nome, email, telefone, cargo, is_admin, is_active, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                                RETURNING id;
                            """, [loja.id, nome, owner.email, '', 'Administrador', True, True])
                            
                            vendedor_id = cursor.fetchone()[0]
                            logger.info(f"✅ Vendedor admin criado (ID: {vendedor_id})")
                        
                        # 2. Verificar/Criar VendedorUsuario (tabela pública)
                        vendedor_usuario_existe = VendedorUsuario.objects.filter(
                            user=owner,
                            loja=loja
                        ).exists()
                        
                        if vendedor_usuario_existe:
                            logger.info(f"✅ VendedorUsuario já existe")
                            ja_corretas += 1
                        else:
                            logger.info(f"🔧 Criando VendedorUsuario...")
                            VendedorUsuario.objects.create(
                                user=owner,
                                loja=loja,
                                vendedor_id=vendedor_id,
                                precisa_trocar_senha=False  # Owner não precisa trocar senha
                            )
                            logger.info(f"✅ VendedorUsuario criado")
                            corrigidas += 1
                
                logger.info(f"✅ CONFIGURAÇÃO CORRETA - Owner é admin!")
                logger.info("")
                
            except Exception as e:
                logger.error(f"❌ ERRO: {e}")
                import traceback
                logger.error(traceback.format_exc())
                erros += 1
                logger.info("")
        
        # Resumo
        logger.info(f"{'='*80}")
        logger.info(f"RESUMO DA CORREÇÃO")
        logger.info(f"{'='*80}")
        logger.info(f"Total de lojas: {total}")
        logger.info(f"✅ Lojas corrigidas: {corrigidas}")
        logger.info(f"✅ Lojas já corretas: {ja_corretas}")
        logger.info(f"❌ Lojas com erros: {erros}")
        logger.info(f"{'='*80}\n")
        
        if erros == 0:
            logger.info("✅ Correção concluída com sucesso!")
        else:
            logger.warning(f"⚠️  Correção concluída com {erros} erro(s)")
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info("🚀 Iniciando criação de vendedores admin completo...")
    criar_vendedor_admin_completo()
