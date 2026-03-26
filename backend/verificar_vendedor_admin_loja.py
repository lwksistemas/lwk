#!/usr/bin/env python
"""
Script para verificar o estado do vendedor admin em uma loja CRM Vendas.

USO:
    python manage.py shell -c "from verificar_vendedor_admin_loja import verificar; verificar('41449198000172')"
"""
from django.db import connections
from superadmin.models import Loja
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def verificar(slug):
    """Verifica o estado do vendedor admin em uma loja."""
    try:
        loja = Loja.objects.get(slug=slug)
        owner = loja.owner
        schema_name = f'loja_{loja.slug.replace("-", "_")}'
        
        logger.info(f"{'='*60}")
        logger.info(f"VERIFICAÇÃO: {loja.nome}")
        logger.info(f"{'='*60}")
        logger.info(f"Loja ID: {loja.id}")
        logger.info(f"Slug: {loja.slug}")
        logger.info(f"Schema: {schema_name}")
        logger.info(f"Owner: {owner.username} ({owner.email})")
        logger.info(f"Owner ID: {owner.id}")
        logger.info("")
        
        # Verificar VendedorUsuario
        from superadmin.models import VendedorUsuario
        vu = VendedorUsuario.objects.filter(user=owner, loja=loja).first()
        
        if vu:
            logger.info(f"✅ VendedorUsuario encontrado:")
            logger.info(f"   ID: {vu.id}")
            logger.info(f"   Vendedor ID: {vu.vendedor_id}")
            logger.info(f"   Precisa trocar senha: {vu.precisa_trocar_senha}")
        else:
            logger.warning(f"⚠️  VendedorUsuario NÃO encontrado")
        
        logger.info("")
        
        # Verificar Vendedor no schema da loja
        with connections['default'].cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema_name}", public')
            
            cursor.execute(f"""
                SELECT id, nome, email, cargo, is_admin, is_active, comissao_padrao
                FROM "{schema_name}".crm_vendas_vendedor
                WHERE loja_id = %s AND email = %s
            """, [loja.id, owner.email])
            
            vendedor = cursor.fetchone()
            
            if vendedor:
                v_id, v_nome, v_email, v_cargo, v_is_admin, v_is_active, v_comissao = vendedor
                logger.info(f"✅ Vendedor encontrado no schema:")
                logger.info(f"   ID: {v_id}")
                logger.info(f"   Nome: {v_nome}")
                logger.info(f"   Email: {v_email}")
                logger.info(f"   Cargo: {v_cargo}")
                logger.info(f"   Is Admin: {v_is_admin} {'✅' if v_is_admin else '❌'}")
                logger.info(f"   Is Active: {v_is_active}")
                logger.info(f"   Comissão: {v_comissao}%")
                
                if vu and vu.vendedor_id != v_id:
                    logger.warning(f"⚠️  INCONSISTÊNCIA: VendedorUsuario.vendedor_id ({vu.vendedor_id}) != Vendedor.id ({v_id})")
                
                if not v_is_admin:
                    logger.error(f"❌ PROBLEMA: Vendedor NÃO está marcado como admin!")
                    logger.info(f"   Solução: Executar script de correção")
            else:
                logger.error(f"❌ Vendedor NÃO encontrado no schema da loja")
                logger.info(f"   Solução: Executar script criar_vendedor_admin_direto.py")
        
        logger.info("")
        logger.info(f"{'='*60}")
        
    except Loja.DoesNotExist:
        logger.error(f"❌ Loja com slug '{slug}' não encontrada")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        verificar(sys.argv[1])
    else:
        logger.error("Uso: python verificar_vendedor_admin_loja.py <slug_loja>")
