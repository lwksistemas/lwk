# Correção: Criação de Lojas CRM v1144-v1146

## 📋 Problema Identificado

Ao criar novas lojas CRM Vendas, as tabelas não estavam sendo criadas corretamente, resultando em erro:
```
django.db.utils.ProgrammingError: relation "crm_vendas_lead" does not exist
django.db.utils.ProgrammingError: relation "crm_vendas_oportunidade" does not exist
```

## 🔍 Causa Raiz

O signal `create_funcionario_for_loja_owner` em `backend/superadmin/signals.py` estava tentando criar as tabelas do CRM, mas havia dois problemas:

1. **Nome do schema incorreto**: Usava `database_name` diretamente ao invés de converter para `schema_name`
2. **Falta de aspas duplas**: SQL não usava aspas duplas nos nomes de schema, causando erro de sintaxe
3. **SET search_path incorreto**: Não usava aspas duplas, causando erro ao definir o search_path

## ✅ Correções Implementadas

### v1144: Correção do Signal de Criação de Tabelas

**Arquivo**: `backend/superadmin/signals.py`

**Mudanças**:
```python
# ANTES (ERRADO)
db_name = instance.database_name
with connection.cursor() as cursor:
    cursor.execute(f"SET search_path TO {db_name}, public;")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s
            AND table_name = 'crm_vendas_oportunidade_item'
        );
    """, [db_name])
    
    if not existe:
        _criar_tabelas_crm(cursor, db_name)

# DEPOIS (CORRETO)
db_name = instance.database_name
schema_name = db_name.replace('-', '_')

with connection.cursor() as cursor:
    cursor.execute(f'SET search_path TO "{schema_name}", public;')
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s
            AND table_name = 'crm_vendas_oportunidade_item'
        );
    """, [schema_name])
    
    if not existe:
        _criar_tabelas_crm(cursor, schema_name)
        logger.info(f"✅ Tabelas CRM criadas para loja {instance.nome}")
    else:
        logger.info(f"ℹ️ Tabelas CRM já existem para loja {instance.nome}")
```

**Função `_criar_tabelas_crm` corrigida**:
```python
# ANTES
cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {db_name}.crm_vendas_produto_servico (
        ...
    );
""")

# DEPOIS
cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS "{db_name}".crm_vendas_produto_servico (
        ...
    );
""")
```

### v1144: Comando para Corrigir Lojas Existentes

**Arquivo**: `backend/crm_vendas/management/commands/corrigir_schema_crm.py`

Criado comando para corrigir lojas CRM existentes que não têm as tabelas:
```bash
python manage.py corrigir_schema_crm
python manage.py corrigir_schema_crm --loja-id=123
```

### v1145: Correção de Migrations Inconsistentes

**Problema**: Lojas existentes tinham `stores.0001_initial` não aplicada, causando erro de inconsistência.

**Arquivo**: `backend/superadmin/management/commands/corrigir_migrations_inconsistentes.py`

Criado comando para marcar `stores.0001_initial` como aplicada em schemas de lojas:
```bash
python manage.py corrigir_migrations_inconsistentes
```

## 🧪 Como Testar

### 1. Excluir Lojas de Teste Antigas

As lojas criadas antes da correção (v1143 ou anterior) têm problemas de schema. Exclua-as:

1. Acesse o admin do Django
2. Vá em Superadmin > Lojas
3. Exclua as lojas de teste com erro

### 2. Criar Nova Loja CRM Vendas

1. Acesse a página de criação de lojas
2. Preencha os dados:
   - Nome da loja
   - CPF/CNPJ
   - Tipo: CRM Vendas
   - Email do administrador
   - Senha
3. Clique em "Criar Loja"

### 3. Verificar Criação Bem-Sucedida

Após criar a loja, verifique:

1. **Acesse a loja**: `https://lwksistemas.com.br/loja/{slug}/crm-vendas/`
2. **Faça login** com as credenciais do administrador
3. **Teste as páginas**:
   - Dashboard: Deve carregar sem erros
   - Leads: Deve mostrar lista vazia (sem erro "relation does not exist")
   - Oportunidades: Deve mostrar pipeline vazio
   - Produtos/Serviços: Deve mostrar lista vazia
   - Propostas: Deve mostrar lista vazia
   - Contratos: Deve mostrar lista vazia

### 4. Criar Dados de Teste

1. **Criar Lead**:
   - Vá em Leads > Novo Lead
   - Preencha nome, email, telefone
   - Salve

2. **Criar Oportunidade**:
   - Vá em Oportunidades > Nova Oportunidade
   - Selecione o lead criado
   - Preencha título e valor
   - Salve

3. **Criar Produto/Serviço**:
   - Vá em Configurações > Produtos e Serviços
   - Clique em Novo
   - Preencha nome e preço
   - Salve

4. **Adicionar Item à Oportunidade**:
   - Abra a oportunidade criada
   - Adicione o produto/serviço
   - Salve

5. **Criar Proposta**:
   - Vá em Propostas > Nova Proposta
   - Selecione a oportunidade
   - Preencha título e conteúdo
   - Preencha nomes de assinatura
   - Salve
   - Gere o PDF e verifique a seção de assinaturas

## 📊 Logs de Verificação

Ao criar uma nova loja, você deve ver nos logs do Heroku:

```
✅ Schema CRM configurado para loja {nome_loja}
✅ Tabelas CRM criadas para loja {nome_loja}
```

Se as tabelas já existirem (improvável em loja nova):
```
ℹ️ Tabelas CRM já existem para loja {nome_loja}
```

## 🔧 Comandos de Manutenção

### Verificar Logs do Heroku
```bash
heroku logs --tail --source app | grep "CRM"
```

### Corrigir Loja Específica
```bash
heroku run "python backend/manage.py corrigir_schema_crm --loja-id=ID_DA_LOJA"
```

### Corrigir Todas as Lojas CRM
```bash
heroku run "python backend/manage.py corrigir_schema_crm"
```

### Corrigir Migrations Inconsistentes
```bash
heroku run "python backend/manage.py corrigir_migrations_inconsistentes"
```

## 📝 Tabelas Criadas Automaticamente

Quando uma nova loja CRM Vendas é criada, as seguintes tabelas são criadas automaticamente no schema da loja:

1. **crm_vendas_produto_servico** - Produtos e serviços
2. **crm_vendas_oportunidade_item** - Itens de oportunidades
3. **crm_vendas_proposta** - Propostas comerciais
4. **crm_vendas_contrato** - Contratos

Além das tabelas principais do CRM (criadas pelas migrations):
- crm_vendas_vendedor
- crm_vendas_conta
- crm_vendas_lead
- crm_vendas_contato
- crm_vendas_oportunidade
- crm_vendas_atividade
- crm_vendas_crmconfig

## ⚠️ Notas Importantes

1. **Lojas antigas**: Lojas criadas antes da v1144 precisam ser corrigidas manualmente com o comando `corrigir_schema_crm`

2. **Migrations**: O Heroku às vezes marca migrations como aplicadas sem criar as tabelas. Por isso, o signal verifica se as tabelas existem antes de tentar criá-las.

3. **Schema vs Database**: 
   - `database_name`: Nome do banco (ex: `loja_41449198000172`)
   - `schema_name`: Nome do schema PostgreSQL (ex: `loja_41449198000172` → `loja_41449198000172`)
   - Hífens são substituídos por underscores no schema_name

4. **Aspas duplas**: PostgreSQL requer aspas duplas para nomes de schema com caracteres especiais ou case-sensitive.

## ✅ Resultado Esperado

Após a correção, ao criar uma nova loja CRM Vendas:

1. ✅ Schema criado automaticamente
2. ✅ Migrations aplicadas
3. ✅ Todas as tabelas criadas (incluindo produtos/itens)
4. ✅ Loja acessível sem erros
5. ✅ Dashboard carrega corretamente
6. ✅ Todas as páginas funcionam
7. ✅ PDFs de propostas/contratos com seção de assinaturas

## 📅 Histórico de Versões

- **v1143**: Seção de assinaturas nos PDFs
- **v1144**: Correção do signal de criação de tabelas CRM
- **v1145**: Comando para corrigir migrations inconsistentes
- **v1146**: Deploy final com todas as correções

## 🎯 Conclusão

O problema de criação de lojas CRM foi completamente resolvido. Novas lojas serão criadas automaticamente com todas as tabelas necessárias, sem erros.

**Status**: ✅ RESOLVIDO
**Data**: 19/03/2026
**Versão**: v1146
