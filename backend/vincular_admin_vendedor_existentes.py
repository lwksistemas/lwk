#!/usr/bin/env python
"""
Script para vincular administradores (owners) de lojas CRM existentes como vendedores.

Problema: Lojas CRM criadas antes da v1019 têm administradores que não são vendedores.
Solução: Criar registro Vendedor + VendedorUsuario para cada owner de loja CRM.

Uso:
    python backend/vincular_admin_vendedor_existentes.py
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja, VendedorUsuario
from crm_vendas.models import Vendedor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def vincular_admin_vendedor(loja):
    """
    Vincula o owner da loja como vendedor no CRM.
    
    Args:
        loja: Objeto Loja do tipo 'CRM Vendas'
    
    Returns:
        True se vinculado com sucesso, False caso contrário
    """
    owner = loja.owner
    
    # Verificar se já existe VendedorUsuario
    if VendedorUsuario.objects.using('default').filter(loja=loja, user=owner).exists():
        logger.info(f"✅ Loja {loja.slug}: Owner já tem vendedor vinculado")
        return True
    
    # Verificar se schema existe
    if not loja.database_name or not loja.database_created:
        logger.warning(f"⚠️ Loja {loja.slug}: Schema não criado, pulando")
        return False
    
    try:
        # Verificar se vendedor já existe (por email)
        email_owner = (owner.email or '').strip().lower()
        vendedor_existente = None
        
        if email_owner:
            vendedor_existente = Vendedor.objects.using(loja.database_name).filter(
                loja_id=loja.id,
                email__iexact=email_owner
            ).first()
        
        # Criar vendedor se não existir
        if not vendedor_existente:
            nome = owner.get_full_name() or owner.username or (owner.email or '').split('@')[0]
            vendedor_existente = Vendedor.objects.using(loja.database_name).create(
                nome=nome,
                email=owner.email or '',
                telefone=getattr(loja, 'owner_telefone', '') or '',
                cargo='Gerente de Vendas',
                is_admin=False,
                is_active=True,
                loja_id=loja.id,
            )
            logger.info(f"✅ Loja {loja.slug}: Vendedor criado para {nome}")
        else:
            logger.info(f"✅ Loja {loja.slug}: Vendedor já existe, apenas vinculando")
        
        # Criar VendedorUsuario
        VendedorUsuario.objects.create(
            user=owner,
            loja=loja,
            vendedor_id=vendedor_existente.id
        )
        
        logger.info(f"✅ Loja {loja.slug}: VendedorUsuario criado (vendedor_id={vendedor_existente.id})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Loja {loja.slug}: Erro ao vincular vendedor: {e}")
        return False


def main():
    """Processa todas as lojas CRM e vincula owners como vendedores."""
    logger.info("=" * 80)
    logger.info("INICIANDO VINCULAÇÃO DE ADMINISTRADORES COMO VENDEDORES")
    logger.info("=" * 80)
    
    # Buscar lojas CRM
    lojas_crm = Loja.objects.using('default').filter(
        tipo_loja__nome='CRM Vendas',
        database_created=True
    ).select_related('owner', 'tipo_loja')
    
    total = lojas_crm.count()
    logger.info(f"\n📊 Total de lojas CRM: {total}")
    
    if total == 0:
        logger.info("✅ Nenhuma loja CRM encontrada")
        return
    
    # Processar cada loja
    sucesso = 0
    ja_vinculado = 0
    erro = 0
    
    for loja in lojas_crm:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processando: {loja.nome} (ID: {loja.id}, Slug: {loja.slug})")
        logger.info(f"Owner: {loja.owner.email}")
        
        # Verificar se já tem vendedor vinculado
        if VendedorUsuario.objects.using('default').filter(loja=loja, user=loja.owner).exists():
            logger.info(f"✅ Owner já tem vendedor vinculado")
            ja_vinculado += 1
            continue
        
        # Vincular
        if vincular_admin_vendedor(loja):
            sucesso += 1
        else:
            erro += 1
    
    # Resumo
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DA MIGRAÇÃO")
    logger.info("=" * 80)
    logger.info(f"Total de lojas CRM: {total}")
    logger.info(f"✅ Já vinculados: {ja_vinculado}")
    logger.info(f"✅ Vinculados agora: {sucesso}")
    logger.info(f"❌ Erros: {erro}")
    logger.info("=" * 80)
    
    if erro > 0:
        logger.warning(f"\n⚠️ {erro} loja(s) com erro. Verifique os logs acima.")
    else:
        logger.info("\n🎉 Migração concluída com sucesso!")


if __name__ == '__main__':
    main()
