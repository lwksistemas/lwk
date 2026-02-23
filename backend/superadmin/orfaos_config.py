"""
Configuração centralizada para prevenção e limpeza de dados órfãos (banco default).

- TABELAS_LOJA_ID: tabelas que existem NO BANCO DEFAULT (schema public) e têm coluna loja_id.
  Usado pelo signal (rede de segurança) e pelo comando verificar_dados_orfaos.
  Inclui APENAS: superadmin (FinanceiroLoja, PagamentoLoja, ProfissionalUsuario), etc.
  NÃO inclui tabelas de apps de loja (clinica_*, cabeleireiro_*, crm_*, etc.): essas
  existem só nos schemas isolados por loja e são apagadas com o DROP SCHEMA.

- ProfissionalUsuario (superadmin_profissionalusuario): tabela GLOBAL no default que
  vincula User a Loja (perfil profissional/recepção). Não é dado “da loja” no schema
  isolado; por isso fica no default e entra nesta lista.

- LIMPAR_REFERENCIAS_ANTES: para tabelas que são referenciadas por outras (FK).
  Usado pelo comando verificar_dados_orfaos --remover. No default não há dependências
  entre as tabelas listadas; mantido para eventual uso em bases legado.
"""

# Tabelas que existem no banco default (public) e têm loja_id.
# Signal (rede de segurança) e verificar_dados_orfaos usam esta lista.
# Dados operacionais das lojas (clinica_*, cabeleireiro_*, etc.) ficam no schema da loja.
TABELAS_LOJA_ID = [
    ('superadmin_financeiroloja', 'loja_id'),
    ('superadmin_pagamentoloja', 'loja_id'),
    ('superadmin_profissionalusuario', 'loja_id'),
]

# Alias para compatibilidade (signal usa esta nomeação no comentário; mesmo conteúdo).
TABELAS_LOJA_ID_DEFAULT = TABELAS_LOJA_ID

# Tabelas filhas que referenciam tabelas pai por FK (verificar_dados_orfaos --remover).
# No default atual não há essas tabelas; útil para bases legado com clinica_* no public.
LIMPAR_REFERENCIAS_ANTES = {
    'clinica_procedimentos': [
        ('clinica_anamneses_templates', 'procedimento_id'),
        ('clinica_protocolos', 'procedimento_id'),
        ('clinica_consultas', 'procedimento_id'),
        ('clinica_agendamentos', 'procedimento_id'),
    ],
}
