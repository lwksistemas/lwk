# Teste da Correção v1002 - search_path em conn_params

**Data**: 18/03/2026  
**Versão Heroku**: v1098-v1099  
**Status**: ✅ PRONTO PARA TESTE

---

## 📋 RESUMO DA CORREÇÃO

### Problema Original (v1001)
- Tentava definir `search_path` DEPOIS de criar conexão usando `cursor.execute()`
- Erro: "set_session cannot be used inside a transaction"
- Schema ficava vazio, tabelas criadas em `public`

### Solução v1002
- Define `search_path` ANTES de criar conexão
- Adiciona aos `conn_params['options']` no formato PostgreSQL
- Formato: `-c search_path="schema_name",public`
- Evita problemas com transações e connection pooling

---

## 🧪 COMO TESTAR

### 1. Criar Nova Loja CRM
1. Acesse: https://lwksistemas.com.br/
2. Faça login como superadmin
3. Vá em "Lojas" > "Criar Nova Loja"
4. Preencha os dados:
   - Nome: "Teste v1002"
   - CNPJ: qualquer válido
   - Tipo: "CRM Vendas"
   - Plano: qualquer
5. Clique em "Criar"

### 2. Verificar Criação
Após criar a loja, anote o ID ou CNPJ e execute:

```bash
heroku run "python backend/verificar_loja_criada.py <id_ou_cnpj>" --app lwksistemas
```

### 3. Resultado Esperado

#### ✅ SUCESSO (v1002 funcionando)
```
================================================================================
VERIFICAÇÃO DE LOJA CRIADA
================================================================================

✅ Loja encontrada:
   - ID: XXX
   - Slug: CNPJ
   - Nome: Teste v1002
   - Tipo: CRM Vendas
   - Database: loja_CNPJ
   - Database Created: True

================================================================================
1. VERIFICANDO SCHEMA NO POSTGRESQL
================================================================================
✅ Schema 'loja_CNPJ' existe no PostgreSQL

================================================================================
2. TABELAS NO SCHEMA DA LOJA
================================================================================

✅ Schema 'loja_CNPJ' tem 25+ tabela(s):

📊 CRM Vendas (XX tabelas):
   ✓ crm_vendas_vendedor
   ✓ crm_vendas_conta
   ✓ crm_vendas_contato
   ✓ crm_vendas_lead
   ✓ crm_vendas_oportunidade
   ✓ crm_vendas_atividade
   ... (outras tabelas)

🏪 Stores (X tabelas):
   ✓ stores_loja
   ... (outras tabelas)

📦 Products (X tabelas):
   ✓ products_produto
   ... (outras tabelas)

================================================================================
3. VERIFICANDO TABELAS ESSENCIAIS DO CRM
================================================================================
   ✅ crm_vendas_vendedor
   ✅ crm_vendas_conta
   ✅ crm_vendas_contato
   ✅ crm_vendas_lead
   ✅ crm_vendas_oportunidade
   ✅ crm_vendas_atividade

✅ TODAS as tabelas essenciais do CRM estão presentes!

================================================================================
4. VERIFICANDO VAZAMENTO PARA SCHEMA PUBLIC
================================================================================
✅ Nenhuma tabela de apps encontrada em 'public' (sem vazamento)

================================================================================
5. TESTANDO CONEXÃO COM BANCO DA LOJA
================================================================================
✅ Configuração do banco 'loja_CNPJ' adicionada
✅ Search path: "loja_CNPJ",public
✅ Schema 'loja_CNPJ' está no search_path

================================================================================
RESUMO FINAL
================================================================================
Loja: Teste v1002 (ID: XXX)
Schema: loja_CNPJ
Tabelas: 25+
Vazamento para public: NÃO ✅

🎉 SUCESSO! Loja criada corretamente com isolamento de dados!
```

#### ❌ FALHA (v1002 não funcionou)
```
❌ ERRO CRÍTICO: Schema 'loja_CNPJ' está VAZIO após migrations!
⚠️  Nenhuma tabela encontrada em 'public' para mover para 'loja_CNPJ'
```

---

## 🔍 LOGS ESPERADOS NO HEROKU

### Durante Criação da Loja
```bash
heroku logs --tail --app lwksistemas
```

#### ✅ Logs de Sucesso (v1002)
```
✅ search_path 'loja_CNPJ' adicionado aos parâmetros de conexão
✅ search_path confirmado: "loja_CNPJ",public
Migrations aplicadas: stores
Migrations aplicadas: products
Migrations aplicadas: crm_vendas
✅ Schema 'loja_CNPJ' criado com sucesso: 25 tabela(s)
```

#### ❌ Logs de Falha
```
✅ search_path 'loja_CNPJ' adicionado aos parâmetros de conexão
⚠️  Verificação search_path: [erro]
❌ ERRO CRÍTICO: Schema 'loja_CNPJ' está VAZIO após migrations!
```

---

## 🧹 LIMPEZA APÓS TESTE

### Se Teste Passou
```bash
# Verificar órfãos
heroku run "python backend/analisar_orfaos_completo.py" --app lwksistemas

# Se houver loja de teste, excluir
heroku run "python backend/excluir_loja_<ID>.py" --app lwksistemas
```

### Se Teste Falhou
1. Anotar logs completos do erro
2. Verificar se tabelas foram criadas em `public`:
```bash
heroku run "python -c \"
import sys; sys.path.insert(0, 'backend');
import django; django.setup();
from django.db import connection;
with connection.cursor() as c:
    c.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name LIKE %s', ['public', 'crm_vendas_%']);
    print('Tabelas CRM em public:', [r[0] for r in c.fetchall()])
\"" --app lwksistemas
```
3. Limpar loja órfã
4. Reportar erro com logs

---

## 📊 CHECKLIST DE VERIFICAÇÃO

- [ ] Loja criada sem erro
- [ ] Schema existe no PostgreSQL
- [ ] Schema contém 25+ tabelas
- [ ] Tabelas essenciais do CRM presentes
- [ ] Nenhuma tabela em `public`
- [ ] `search_path` correto na conexão
- [ ] Logs mostram "search_path adicionado aos parâmetros"
- [ ] Logs mostram "Schema criado com sucesso: X tabela(s)"

---

## 🎯 PRÓXIMOS PASSOS

### Se Teste Passar ✅
1. Documentar sucesso
2. Limpar loja de teste
3. Atualizar documentação final
4. Marcar v1002 como CONCLUÍDO

### Se Teste Falhar ❌
1. Analisar logs detalhados
2. Verificar se `conn_params['options']` está sendo respeitado
3. Considerar abordagem alternativa (ex: usar `PGOPTIONS` env var)
4. Investigar se PgBouncer está ignorando options

---

**Aguardando teste do usuário para confirmar correção v1002.**
