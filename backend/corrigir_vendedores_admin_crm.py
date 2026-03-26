#!/usr/bin/env python
"""
Script para corrigir lojas CRM Vendas que não têm o administrador vinculado como Vendedor.

PROBLEMA:
- Signal antigo tentava criar Funcionario (que não existe no CRM Vendas)
- Administrador não aparecia na lista de vendedores/funcionários
- Causava problemas de permissões e filtros

SOLUÇÃO:
- Busca todas as lojas CRM Vendas
- Para cada loja, verifica se owner existe como Vendedor
- Se não existir, cria Vendedor com is_admin=True

USO:
    python manage.py shell < corrigir_vendedores_admin_crm.py
    OU
    python manage.py runscript corrigir_vendedores_admin_crm
"""
from superadmin.models import Loja, TipoLoja
from crm_vendas.models import Vendedor
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def run():
    """
    Função principal para uso com django-extensions runscript.
    """
    corrigir_vendedores_admin()


def corrigir_vendedores_admin():
    """
    Corrige todas as lojas CRM Vendas criando Vendedor admin quando necessário.
    """
    try:
        # Buscar tipo de loja CRM Vendas
        tipo_crm = TipoLoja.objects.filter(nome='CRM Vendas').first()
        if not tipo_crm:
            logger.error("❌ Tipo de loja 'CRM Vendas' não encontrado")
            return
        
        # Buscar todas as lojas CRM Vendas
        lojas_crm = Loja.objects.filter(tipo_loja=tipo_crm, is_active=True)
        total_lojas = lojas_crm.count()
        
        logger.info(f"🔍 Encontradas {total_lojas} lojas CRM Vendas ativas")
        
        if total_lojas == 0:
            logger.info("✅ Nenhuma loja CRM Vendas para corrigir")
            return
        
        corrigidas = 0
        ja_corretas = 0
        erros = 0
        
        for loja in lojas_crm:
            try:
                owner = loja.owner
                logger.info(f"\n📋 Processando loja: {loja.nome} (ID: {loja.id}, Slug: {loja.slug})")
                logger.info(f"   Owner: {owner.username} ({owner.email})")
                
                # Verificar se owner já existe como Vendedor
                vendedor_existente = Vendedor.objects.filter(
                    loja_id=loja.id,
                    email=owner.email
                ).first()
                
                if vendedor_existente:
                    logger.info(f"   ✅ Vendedor já existe: {vendedor_existente.nome} (ID: {vendedor_existente.id})")
                    
                    # Verificar se está marcado como admin
                    if not vendedor_existente.is_admin:
                        logger.info(f"   ⚠️  Vendedor não está marcado como admin. Corrigindo...")
                        vendedor_existente.is_admin = True
                        vendedor_existente.cargo = 'Administrador'
                        vendedor_existente.save()
                        logger.info(f"   ✅ Vendedor atualizado para admin")
                        corrigidas += 1
                    else:
                        ja_corretas += 1
                    continue
                
                # Criar Vendedor admin
                logger.info(f"   🔧 Criando Vendedor admin...")
                
                vendedor_data = {
                    'nome': owner.get_full_name() or owner.username,
                    'email': owner.email,
                    'telefone': '',
                    'cargo': 'Administrador',
                    'is_admin': True,
                    'is_active': True,
                    'loja_id': loja.id
                }
                
                vendedor = Vendedor.objects.create(**vendedor_data)
                logger.info(f"   ✅ Vendedor admin criado: {vendedor.nome} (ID: {vendedor.id})")
                corrigidas += 1
                
            except Exception as e:
                logger.error(f"   ❌ Erro ao processar loja {loja.nome}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                erros += 1
        
        # Resumo
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RESUMO DA CORREÇÃO")
        logger.info(f"{'='*60}")
        logger.info(f"Total de lojas processadas: {total_lojas}")
        logger.info(f"Lojas corrigidas: {corrigidas}")
        logger.info(f"Lojas já corretas: {ja_corretas}")
        logger.info(f"Erros: {erros}")
        logger.info(f"{'='*60}")
        
        if erros == 0:
            logger.info("✅ Correção concluída com sucesso!")
        else:
            logger.warning(f"⚠️  Correção concluída com {erros} erro(s)")
        
    except Exception as e:
        logger.error(f"❌ Erro fatal ao executar correção: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    logger.info("🚀 Iniciando correção de vendedores admin em lojas CRM Vendas...")
    run()
