"""
Configuração de tabelas para verificação de dados órfãos.

Lista de tabelas que possuem coluna loja_id e devem ser verificadas
para garantir que não existam registros com loja_id inválido (órfãos).
"""

# Tabelas no banco DEFAULT (public) que têm loja_id
# Formato: (nome_tabela, nome_coluna_loja_id)
# NOTA: LojaAssinatura usa loja_slug (não loja_id) - tratada no signal e verificar_dados_orfaos
# NOTA: CRM Vendas, Rules etc podem estar em schemas tenant - não incluir se não existirem em public
TABELAS_LOJA_ID_DEFAULT = [
    # Superadmin
    # NOTA: superadmin_loja é deletada automaticamente pelo Django, não incluir aqui
    ('superadmin_historico_backup', 'loja_id'),
    ('superadmin_configuracao_backup', 'loja_id'),

    # WhatsApp (modelos reais: WhatsAppConfig, WhatsAppLog)
    ('whatsapp_whatsappconfig', 'loja_id'),
    ('whatsapp_whatsapplog', 'loja_id'),

    # CRM Vendas: tabelas ficam APENAS no schema da loja (nunca em public).
    # Não incluir aqui - são limpas no signal via .using(db_alias) antes de dropar o schema.
]

# Tabelas em schemas de loja (tenant) - verificadas via ORM com .using(db_alias)
# Estas são limpas automaticamente pelos signals quando a loja é excluída
TABELAS_TENANT_LOJA_ID = {
    'clinica_estetica': [
        'clinica_estetica_funcionario',
        'clinica_estetica_cliente',
        'clinica_estetica_agendamento',
        'clinica_estetica_profissional',
        'clinica_estetica_procedimento',
        'clinica_bloqueios_agenda',
        'clinica_horarios_funcionamento',
    ],
    'restaurante': [
        'restaurante_funcionario',
        'restaurante_reserva',
        'restaurante_pedido',
        'restaurante_itemcardapio',
        'restaurante_categoria',
        'restaurante_mesa',
        'restaurante_cliente',
        'restaurante_fornecedor',
        'restaurante_notafiscalentrada',
        'restaurante_estoqueitem',
        'restaurante_movimentoestoque',
        'restaurante_registropesobalanca',
    ],
    'servicos': [
        'servicos_funcionario',
        'servicos_servico',
        'servicos_profissional',
        'servicos_agendamento',
        'servicos_ordemservico',
        'servicos_orcamento',
        'servicos_cliente',
        'servicos_categoria',
    ],
    'clinica_beleza': [
        'clinica_beleza_patient',
        'clinica_beleza_professional',
        'clinica_beleza_procedure',
        'clinica_beleza_appointment',
        'clinica_beleza_bloqueiohorario',
        'clinica_beleza_horariotrabalhoprofissional',
        'clinica_beleza_payment',
        'clinica_beleza_campanhapromocao',
    ],
    'cabeleireiro': [
        'cabeleireiro_cliente',
        'cabeleireiro_profissional',
        'cabeleireiro_servico',
        'cabeleireiro_agendamento',
        'cabeleireiro_produto',
        'cabeleireiro_venda',
        'cabeleireiro_funcionario',
        'cabeleireiro_horariofuncionamento',
        'cabeleireiro_bloqueioagenda',
    ],
}

# Alias para compatibilidade com comandos verificar_dados_orfaos e validar_config_orfaos
TABELAS_LOJA_ID = TABELAS_LOJA_ID_DEFAULT

# Ordem de limpeza de FKs antes de deletar tabela pai (evita violação de FK)
LIMPAR_REFERENCIAS_ANTES = {}
