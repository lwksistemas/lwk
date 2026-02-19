"""
Configuração centralizada para prevenção e limpeza de dados órfãos (banco default).

- TABELAS_LOJA_ID: tabelas no default que têm coluna loja_id referenciando Loja.
  Usado pelo signal de exclusão de loja (limpeza) e pelo comando verificar_dados_orfaos.
- Ao adicionar novo app/tabela com loja_id no default, incluir aqui para:
  1) ser limpa automaticamente ao excluir a loja (signal)
  2) ser verificada/limpa pelo comando verificar_dados_orfaos
"""

# (nome da tabela no banco default, nome da coluna) para registros por loja_id
TABELAS_LOJA_ID = [
    ('superadmin_financeiroloja', 'loja_id'),
    ('superadmin_pagamentoloja', 'loja_id'),
    ('superadmin_profissionalusuario', 'loja_id'),
    # clinica_estetica (app clinica)
    ('clinica_funcionarios', 'loja_id'),
    ('clinica_clientes', 'loja_id'),
    ('clinica_agendamentos', 'loja_id'),
    ('clinica_profissionais', 'loja_id'),
    ('clinica_procedimentos', 'loja_id'),
    ('clinica_protocolos', 'loja_id'),
    ('clinica_consultas', 'loja_id'),
    ('clinica_evolucoes', 'loja_id'),
    ('clinica_anamneses_templates', 'loja_id'),
    ('clinica_anamneses', 'loja_id'),
    ('clinica_horarios_funcionamento', 'loja_id'),
    ('clinica_bloqueios_agenda', 'loja_id'),
    ('clinica_historico_login', 'loja_id'),
    ('clinica_categorias_financeiras', 'loja_id'),
    ('clinica_transacoes', 'loja_id'),
    # crm
    ('crm_vendedores', 'loja_id'),
    ('crm_clientes', 'loja_id'),
    ('crm_leads', 'loja_id'),
    ('crm_vendas', 'loja_id'),
    ('crm_pipeline', 'loja_id'),
    ('crm_produtos', 'loja_id'),
    # restaurante
    ('restaurante_categorias', 'loja_id'),
    ('restaurante_cardapio', 'loja_id'),
    ('restaurante_mesas', 'loja_id'),
    ('restaurante_clientes', 'loja_id'),
    ('restaurante_reservas', 'loja_id'),
    ('restaurante_pedidos', 'loja_id'),
    ('restaurante_fornecedores', 'loja_id'),
    ('restaurante_notas_fiscais_entrada', 'loja_id'),
    ('restaurante_estoque_itens', 'loja_id'),
    ('restaurante_funcionarios', 'loja_id'),
    # servicos
    ('servicos_funcionarios', 'loja_id'),
    ('servicos_servicos', 'loja_id'),
    ('servicos_profissionais', 'loja_id'),
    ('servicos_agendamentos', 'loja_id'),
    ('servicos_ordem_servico', 'loja_id'),
    ('servicos_orcamentos', 'loja_id'),
    ('servicos_clientes', 'loja_id'),
    ('servicos_categorias', 'loja_id'),
    # cabeleireiro
    ('cabeleireiro_clientes', 'loja_id'),
    ('cabeleireiro_profissionais', 'loja_id'),
    ('cabeleireiro_servicos', 'loja_id'),
    ('cabeleireiro_agendamentos', 'loja_id'),
    ('cabeleireiro_produtos', 'loja_id'),
    ('cabeleireiro_vendas', 'loja_id'),
    ('cabeleireiro_funcionarios', 'loja_id'),
    ('cabeleireiro_horariofuncionamento', 'loja_id'),
    ('cabeleireiro_bloqueioagenda', 'loja_id'),
]
