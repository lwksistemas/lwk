import logging
import os
import shutil
from pathlib import Path

from core.logging_utils import mask_email

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
    - Arquivos em media/nfe_restaurante/ com prefixo loja_{id}_ (legado removido)
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

