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

    # WhatsApp: tabelas ficam APENAS no schema da loja (tenant), nunca em public.
    # Ver TABELAS_TENANT_LOJA_ID e core/tests_tenant_tables.py.
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
        'whatsapp_whatsappconfig',
        'whatsapp_whatsapplog',
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


def tabela_existe_em_public(cursor, table_name: str) -> bool:
    """Evita SQL em tabelas tenant-only (ex.: whatsapp_*) que geram ERROR no log do Postgres."""
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
        LIMIT 1
        """,
        [table_name],
    )
    return cursor.fetchone() is not None


def get_usuarios_orfaos_queryset():
    """
    Usuários sem vínculo válido: não são owner, profissional nem vendedor de loja.
    """
    from django.contrib.auth import get_user_model

    from superadmin.models import Loja, ProfissionalUsuario, VendedorUsuario

    User = get_user_model()
    usuarios_validos = set(Loja.objects.values_list('owner_id', flat=True))
    usuarios_validos |= set(ProfissionalUsuario.objects.values_list('user_id', flat=True))
    usuarios_validos |= set(VendedorUsuario.objects.values_list('user_id', flat=True))
    return (
        User.objects.exclude(id__in=usuarios_validos)
        .exclude(is_superuser=True)
        .exclude(is_staff=True)
    )
