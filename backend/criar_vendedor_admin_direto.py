#!/usr/bin/env python
"""
Script para criar vendedor admin diretamente via SQL nas lojas CRM Vendas.
Evita problemas com migrations e schemas.

USO:
    python manage.py shell -c "from criar_vendedor_admin_direto import run; run()"
"""
from django.db import connections
from superadmin.models import Loja, TipoLoja
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def run():
    """Função principal."""
    criar_vendedores_admin_direto()


def criar_vendedores_admin_direto():
    """Cria vendedores admin diretamente via SQL."""
    try:
        # Buscar tipo CRM Vendas
        tipo_crm = TipoLoja.objects.filter(nome='CRM Vendas').first()
        if not tipo_crm:
            logger.error("❌ Tipo 'CRM Vendas' não encontrado")
            return
        
        # Buscar lojas CRM Vendas
        lojas_crm = Loja.objects.filter(tipo_loja=tipo_crm, is_active=True)
        total = lojas_crm.count()
        
        logger.info(f"🔍 Encontradas {total} lojas CRM Vendas ativas\n")
        
        if total == 0:
            logger.info("✅ Nenhuma loja para processar")
            return
        
        corrigidas = 0
        ja_corretas = 0
        erros = 0
        
        for loja in lojas_crm:
            try:
                owner = loja.owner
                schema_name = f'loja_{loja.slug.replace("-", "_")}'
                
                logger.info(f"📋 Loja: {loja.nome} (ID: {loja.id})")
                logger.info(f"   Schema: {schema_name}")
                logger.info(f"   Owner: {owner.username} ({owner.email})")
                
                # Conectar ao banco default (onde estão os schemas)
                with connections['default'].cursor() as cursor:
                    # Verificar se schema existe
                    cursor.execute(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        [schema_name]
                    )
                    if not cursor.fetchone():
                        logger.warning(f"   ⚠️  Schema {schema_name} não existe")
                        erros += 1
                        continue
                    
                    # Setar search_path para o schema da loja
                    cursor.execute(f'SET search_path TO "{schema_name}", public')
                    
                    # Verificar se tabela crm_vendas_vendedor existe
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = %s 
                            AND table_name = 'crm_vendas_vendedor'
                        )
                    """, [schema_name])
                    
                    tabela_existe = cursor.fetchone()[0]
                    
                    if not tabela_existe:
                        logger.info(f"   🔧 Criando tabela crm_vendas_vendedor...")
                        cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS "{schema_name}".crm_vendas_vendedor (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(200) NOT NULL,
                                email VARCHAR(254),
                                telefone VARCHAR(20),
                                cargo VARCHAR(100) DEFAULT 'Vendedor',
                                comissao_padrao DECIMAL(5, 2) DEFAULT 0,
                                is_admin BOOLEAN DEFAULT FALSE,
                                is_active BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            )
                        """)
                        
                        # Criar índices
                        cursor.execute(f"""
                            CREATE INDEX IF NOT EXISTS crm_vend_loja_active_idx 
                            ON "{schema_name}".crm_vendas_vendedor (loja_id, is_active)
                        """)
                        cursor.execute(f"""
                            CREATE INDEX IF NOT EXISTS crm_vend_loja_email_idx 
                            ON "{schema_name}".crm_vendas_vendedor (loja_id, email)
                        """)
                        logger.info(f"   ✅ Tabela criada")
                    
                    # Verificar se vendedor admin já existe
                    cursor.execute(f"""
                        SELECT id, nome, is_admin FROM "{schema_name}".crm_vendas_vendedor
                        WHERE loja_id = %s AND email = %s
                    """, [loja.id, owner.email])
                    
                    vendedor_existente = cursor.fetchone()
                    
                    if vendedor_existente:
                        vendedor_id, vendedor_nome, is_admin = vendedor_existente
                        logger.info(f"   ✅ Vendedor já existe: {vendedor_nome} (ID: {vendedor_id})")
                        
                        if not is_admin:
                            logger.info(f"   🔧 Atualizando para admin...")
                            cursor.execute(f"""
                                UPDATE "{schema_name}".crm_vendas_vendedor
                                SET is_admin = TRUE, cargo = 'Administrador', updated_at = NOW()
                                WHERE id = %s
                            """, [vendedor_id])
                            logger.info(f"   ✅ Atualizado para admin")
                            corrigidas += 1
                        else:
                            ja_corretas += 1
                    else:
                        # Criar vendedor admin
                        logger.info(f"   🔧 Criando vendedor admin...")
                        nome = owner.get_full_name() or owner.username
                        
                        cursor.execute(f"""
                            INSERT INTO "{schema_name}".crm_vendas_vendedor
                            (loja_id, nome, email, telefone, cargo, is_admin, is_active, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            RETURNING id
                        """, [loja.id, nome, owner.email, '', 'Administrador', True, True])
                        
                        vendedor_id = cursor.fetchone()[0]
                        logger.info(f"   ✅ Vendedor admin criado (ID: {vendedor_id})")
                        corrigidas += 1
                
                logger.info("")  # Linha em branco
                
            except Exception as e:
                logger.error(f"   ❌ Erro: {e}")
                import traceback
                logger.error(traceback.format_exc())
                erros += 1
                logger.info("")
        
        # Resumo
        logger.info(f"{'='*60}")
        logger.info(f"📊 RESUMO")
        logger.info(f"{'='*60}")
        logger.info(f"Total processadas: {total}")
        logger.info(f"Corrigidas: {corrigidas}")
        logger.info(f"Já corretas: {ja_corretas}")
        logger.info(f"Erros: {erros}")
        logger.info(f"{'='*60}")
        
        if erros == 0:
            logger.info("✅ Correção concluída com sucesso!")
        else:
            logger.warning(f"⚠️  Correção concluída com {erros} erro(s)")
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info("🚀 Iniciando criação de vendedores admin...")
    run()
