-- Script SQL para criar o tipo de loja Cabeleireiro
-- Execute no banco de dados superadmin

-- Verificar se já existe
SELECT * FROM superadmin_tipoloja WHERE slug = 'cabeleireiro';

-- Se não existir, inserir
INSERT INTO superadmin_tipoloja (
    nome,
    slug,
    descricao,
    dashboard_template,
    cor_primaria,
    cor_secundaria,
    tem_produtos,
    tem_servicos,
    tem_agendamento,
    tem_delivery,
    tem_estoque,
    created_at,
    updated_at
) VALUES (
    'Cabeleireiro',
    'cabeleireiro',
    'Salão de beleza, barbearia e cabeleireiro com gestão completa de agendamentos, serviços, produtos e vendas',
    'cabeleireiro',
    '#EC4899',
    '#DB2777',
    1,  -- tem_produtos
    1,  -- tem_servicos
    1,  -- tem_agendamento
    0,  -- tem_delivery
    1,  -- tem_estoque
    datetime('now'),
    datetime('now')
)
ON CONFLICT(slug) DO NOTHING;

-- Verificar se foi criado
SELECT 
    id,
    nome,
    slug,
    dashboard_template,
    cor_primaria,
    tem_produtos,
    tem_servicos,
    tem_agendamento,
    tem_estoque
FROM superadmin_tipoloja 
WHERE slug = 'cabeleireiro';
