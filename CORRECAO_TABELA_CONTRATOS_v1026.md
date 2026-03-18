# Correção: Tabela de Templates de Contratos Não Existia (v1026)

**Data**: 18/03/2026  
**Versão Backend**: v1131 (Heroku)  

---

## 🔴 PROBLEMA

Ao acessar a página de templates de contratos, o frontend retornava erro 500:

```
psycopg2.errors.UndefinedTable: relation "crm_vendas_contrato_template" does not exist
```

**Causa**: Mesmo problema das propostas - a migration foi marcada como aplicada, mas a tabela não foi criada no banco de dados PostgreSQL.

---

## ✅ SOLUÇÃO APLICADA

### Criação Manual da Tabela via Django Shell

Executado no Heroku:

```python
from django.db import connection

sql = """
CREATE TABLE IF NOT EXISTS crm_vendas_contrato_template (
    id BIGSERIAL PRIMARY KEY,
    loja_id INTEGER NOT NULL,
    nome VARCHAR(255) NOT NULL,
    conteudo TEXT NOT NULL,
    is_padrao BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS crm_ct_loja_ativo_idx 
    ON crm_vendas_contrato_template (loja_id, ativo);
    
CREATE INDEX IF NOT EXISTS crm_ct_loja_padrao_idx 
    ON crm_vendas_contrato_template (loja_id, is_padrao);
    
CREATE INDEX IF NOT EXISTS crm_vendas_contrato_template_loja_id_idx 
    ON crm_vendas_contrato_template (loja_id);
"""

with connection.cursor() as cursor:
    cursor.execute(sql)
```

**Resultado**: ✅ Tabela criada com sucesso!

---

## 📊 ESTRUTURA DA TABELA CRIADA

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | BIGSERIAL | Chave primária |
| loja_id | INTEGER | ID da loja (tenant) |
| nome | VARCHAR(255) | Nome do template |
| conteudo | TEXT | Conteúdo do template |
| is_padrao | BOOLEAN | Se é o template padrão |
| ativo | BOOLEAN | Se está ativo |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Data de atualização |

### Índices Criados

1. `crm_ct_loja_ativo_idx` - (loja_id, ativo)
2. `crm_ct_loja_padrao_idx` - (loja_id, is_padrao)
3. `crm_vendas_contrato_template_loja_id_idx` - (loja_id)

---

## 🤔 POR QUE ISSO ACONTECEU?

Mesmo problema das propostas:
- Migration marcada como aplicada sem executar o SQL
- Django retornou "no-op" ao gerar o SQL da migration
- Possível conflito ou erro silencioso durante o deploy

---

## 📝 LIÇÃO APRENDIDA

**Sempre criar tabelas manualmente após deploy de migrations que criam novos modelos.**

### Processo Recomendado:

1. Fazer deploy do código
2. Verificar se a migration foi aplicada: `heroku run "cd backend && python manage.py showmigrations"`
3. Verificar se a tabela existe: Testar o endpoint da API
4. Se erro 500, criar tabela manualmente via Django shell
5. Confirmar que funciona

---

## ✅ STATUS FINAL

- [x] Tabela `crm_vendas_contrato_template` criada
- [x] Índices criados
- [x] Migration marcada como aplicada
- [x] Endpoint `/api/crm-vendas/contrato-templates/` funcional
- [x] Frontend pode acessar a página de templates

---

## 🔗 REFERÊNCIAS

- Correção similar: `CORRECAO_TABELA_TEMPLATES_v1025.md` (propostas)
- Feature completa: `FEATURE_TEMPLATES_CONTRATOS_v1026.md`

---

**Status**: ✅ RESOLVIDO  
**Método**: Criação manual via Django shell  
**Tempo de resolução**: ~5 minutos
