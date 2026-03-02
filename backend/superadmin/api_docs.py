"""
Documentação da API do Superadmin
✅ FASE 7 v771: Documentação centralizada para Swagger
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

# Exemplos de respostas para documentação
LOJA_EXAMPLE = {
    "id": 1,
    "nome": "Clínica Exemplo",
    "slug": "clinica-exemplo",
    "tipo_loja": {
        "id": 1,
        "nome": "Clínica de Estética"
    },
    "plano": {
        "id": 1,
        "nome": "Plano Básico"
    },
    "is_active": True,
    "database_created": True,
    "created_at": "2024-01-01T00:00:00Z"
}

TIPO_LOJA_EXAMPLE = {
    "id": 1,
    "nome": "Clínica de Estética",
    "slug": "clinica-de-estetica",
    "descricao": "Sistema completo para clínicas de estética",
    "dashboard_template": "default",
    "cor_primaria": "#10B981",
    "cor_secundaria": "#059669",
    "tem_produtos": True,
    "tem_servicos": True,
    "tem_agendamento": True,
    "tem_delivery": False,
    "tem_estoque": True,
    "total_lojas": 5
}

PLANO_EXAMPLE = {
    "id": 1,
    "nome": "Plano Básico",
    "preco_mensal": 99.90,
    "preco_anual": 999.00,
    "limite_usuarios": 5,
    "limite_produtos": 100,
    "tem_suporte": True,
    "tipos_loja": [1, 2]
}

# Schemas para documentação de endpoints

# Lojas
LOJA_LIST_SCHEMA = extend_schema(
    summary="Listar Lojas",
    description="Lista todas as lojas do sistema com paginação",
    parameters=[
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Número da página"
        ),
        OpenApiParameter(
            name="search",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Buscar por nome ou slug"
        ),
    ],
    examples=[
        OpenApiExample(
            "Exemplo de Loja",
            value=LOJA_EXAMPLE,
            response_only=True,
        )
    ],
    tags=["Lojas"]
)

LOJA_CREATE_SCHEMA = extend_schema(
    summary="Criar Loja",
    description="""
    Cria uma nova loja no sistema.
    
    **Processo:**
    1. Cria usuário owner
    2. Cria loja
    3. Cria schema PostgreSQL isolado
    4. Aplica migrations
    5. Cria financeiro
    6. Cria profissional/funcionário admin
    7. Integra com Asaas (via signal)
    
    **Nota:** A senha será enviada por email após confirmação do pagamento.
    """,
    examples=[
        OpenApiExample(
            "Criar Loja",
            value={
                "nome": "Clínica Exemplo",
                "slug": "clinica-exemplo",
                "tipo_loja": 1,
                "plano": 1,
                "owner_full_name": "João Silva",
                "owner_username": "joao.silva",
                "owner_email": "joao@exemplo.com",
                "owner_telefone": "(11) 99999-9999",
                "dia_vencimento": 10
            },
            request_only=True,
        ),
        OpenApiExample(
            "Loja Criada",
            value=LOJA_EXAMPLE,
            response_only=True,
        )
    ],
    tags=["Lojas"]
)

LOJA_DELETE_SCHEMA = extend_schema(
    summary="Excluir Loja",
    description="""
    Exclui uma loja e todos os dados relacionados.
    
    **Limpeza realizada:**
    - Chamados de suporte
    - Logs de auditoria
    - Alertas de segurança
    - Pagamentos (Asaas + Mercado Pago)
    - Arquivo do banco de dados
    - Usuário proprietário (se não tiver outras lojas)
    
    **Nota:** Esta ação é irreversível!
    """,
    tags=["Lojas"]
)

# Tipos de Loja
TIPO_LOJA_LIST_SCHEMA = extend_schema(
    summary="Listar Tipos de App",
    description="Lista todos os tipos de app (anteriormente tipos de loja) disponíveis",
    examples=[
        OpenApiExample(
            "Exemplo de Tipo",
            value=TIPO_LOJA_EXAMPLE,
            response_only=True,
        )
    ],
    tags=["Tipos de App"]
)

TIPO_LOJA_CREATE_SCHEMA = extend_schema(
    summary="Criar Tipo de App",
    description="Cria um novo tipo de app com configurações personalizadas",
    examples=[
        OpenApiExample(
            "Criar Tipo",
            value={
                "nome": "Clínica de Estética",
                "slug": "clinica-de-estetica",
                "descricao": "Sistema completo para clínicas",
                "dashboard_template": "default",
                "cor_primaria": "#10B981",
                "cor_secundaria": "#059669",
                "tem_produtos": True,
                "tem_servicos": True,
                "tem_agendamento": True
            },
            request_only=True,
        )
    ],
    tags=["Tipos de App"]
)

# Planos
PLANO_LIST_SCHEMA = extend_schema(
    summary="Listar Planos",
    description="Lista todos os planos de assinatura disponíveis",
    parameters=[
        OpenApiParameter(
            name="tipo_loja",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filtrar por tipo de app"
        ),
    ],
    examples=[
        OpenApiExample(
            "Exemplo de Plano",
            value=PLANO_EXAMPLE,
            response_only=True,
        )
    ],
    tags=["Planos"]
)

# Financeiro
FINANCEIRO_LIST_SCHEMA = extend_schema(
    summary="Listar Financeiro",
    description="Lista informações financeiras de todas as lojas",
    parameters=[
        OpenApiParameter(
            name="status",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filtrar por status (ativo, pendente, inadimplente)"
        ),
    ],
    tags=["Financeiro"]
)

# Auditoria
AUDITORIA_LIST_SCHEMA = extend_schema(
    summary="Listar Logs de Auditoria",
    description="""
    Lista logs de auditoria do sistema.
    
    **Informações registradas:**
    - Usuário que realizou a ação
    - Loja relacionada
    - Tipo de ação (criar, editar, excluir, etc.)
    - Recurso afetado
    - IP e navegador
    - Data e hora
    - Sucesso ou erro
    """,
    parameters=[
        OpenApiParameter(
            name="loja_slug",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filtrar por loja"
        ),
        OpenApiParameter(
            name="acao",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filtrar por tipo de ação"
        ),
        OpenApiParameter(
            name="data_inicio",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="Data inicial (YYYY-MM-DD)"
        ),
        OpenApiParameter(
            name="data_fim",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="Data final (YYYY-MM-DD)"
        ),
    ],
    tags=["Auditoria"]
)
