# Correção: Erro de Conexão com Banco de Dados no Render

## 🐛 Erro Identificado

```
psycopg2.OperationalError: falha na conexão com o servidor em 
"cet8r1hlj0mlnt.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com"
FATAL: falha na autenticação por senha para o usuário "uav89ndofshapp"
FATAL: nenhuma entrada pg_hba.conf para o host "74.220.48.4", 
usuário "uav89ndofshapp", banco de dados "d6rgsibf3ofk9d", sem criptografia
```

## 🔍 Análise do Problema

### Problema 1: DATABASE_URL Incorreta
O Render está tentando conectar a um banco **diferente** do Heroku:

**Banco Correto (Heroku):**
- Host: `chepvbj2ergru.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com`
- User: `ufqqlop2dk1g7n`

**Banco Errado (Render está usando):**
- Host: `cet8r1hlj0mlnt.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com` ❌
- User: `uav89ndofshapp` ❌

### Problema 2: Falta SSL
A mensagem "sem criptografia" indica que a conexão precisa de SSL.

### Problema 3: Restrição de IP
O erro `nenhuma entrada pg_hba.conf para o host "74.220.48.4"` indica que o IP do Render (`74.220.48.4`) não tem permissão para acessar o banco.

## ✅ Solução

### Opção 1: Usar o Banco de Dados do Heroku (Recomendado)

O banco do Heroku Essential-0 **não permite conexões externas** por padrão. Você precisa:

1. **Atualizar para Heroku Postgres Standard ou superior** (permite conexões externas)
2. **Ou criar um banco de dados separado no Render**

### Opção 2: Criar Banco de Dados no Render (Mais Simples)

Esta é a solução mais prática e recomendada.

## 🚀 Implementação: Banco Separado no Render

### Passo 1: Criar PostgreSQL no Render

1. Acesse: https://dashboard.render.com/
2. Clique em **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `lwksistemas-db`
   - **Database:** `lwksistemas`
   - **User:** (gerado automaticamente)
   - **Region:** `Oregon` (mesma do servidor)
   - **Plan:** `Free` (para testes) ou `Starter` (produção)

4. Clique em **"Create Database"**

### Passo 2: Copiar Dados do Heroku para Render

Após criar o banco no Render, você precisa copiar os dados:

```bash
# 1. Fazer backup do banco Heroku
heroku pg:backups:capture --app lwksistemas
heroku pg:backups:download --app lwksistemas

# 2. Obter URL do banco Render
# Dashboard Render → lwksistemas-db → Connection String (Internal)

# 3. Restaurar backup no Render
pg_restore --verbose --clean --no-acl --no-owner \
  -d <RENDER_DATABASE_URL> \
  latest.dump
```

### Passo 3: Configurar DATABASE_URL no Render

1. Dashboard Render → `lwksistemas-backup` → Environment
2. Adicionar/Atualizar variável:

```
DATABASE_URL=<URL_DO_BANCO_RENDER>
```

A URL será algo como:
```
postgres://lwksistemas_user:senha@dpg-xxxxx-a.oregon-postgres.render.com/lwksistemas
```

### Passo 4: Adicionar SSL à URL

O Render requer SSL. Adicione `?sslmode=require` no final da URL:

```
DATABASE_URL=postgres://user:senha@host/db?sslmode=require
```

## 🔧 Alternativa: Permitir Conexões Externas no Heroku

Se você quiser usar o mesmo banco do Heroku:

### Passo 1: Verificar Plano do Postgres

```bash
heroku pg:info --app lwksistemas
```

Se for **Essential-0**, você precisa fazer upgrade:

```bash
# Upgrade para Standard-0 (permite conexões externas)
heroku addons:upgrade postgresql-metric-94135:standard-0 --app lwksistemas
```

**Custo:** ~$50/mês (Standard-0)

### Passo 2: Habilitar Conexões Externas

```bash
# Obter credenciais
heroku pg:credentials:url --app lwksistemas
```

### Passo 3: Adicionar SSL à URL

Adicione `?sslmode=require` no final da DATABASE_URL no Render:

```
DATABASE_URL=postgres://ufqqlop2dk1g7n:senha@chepvbj2ergru.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dbt72goeeek1up?sslmode=require
```

## 📊 Comparação das Opções

| Opção | Vantagens | Desvantagens | Custo |
|-------|-----------|--------------|-------|
| **Banco Separado Render** | ✅ Simples<br>✅ Independente<br>✅ Sem upgrade | ❌ Dados separados<br>❌ Precisa sincronizar | $7/mês (Starter) |
| **Mesmo Banco Heroku** | ✅ Mesmos dados<br>✅ Sincronização automática | ❌ Precisa upgrade<br>❌ Mais caro | $50/mês (Standard-0) |

## 🎯 Recomendação

### Para Backup Real (Failover)
Use **banco separado no Render** com sincronização periódica:

1. Criar banco no Render
2. Configurar job de sincronização diária
3. Em caso de falha do Heroku, o Render tem dados recentes

### Para Desenvolvimento/Testes
Use **banco separado no Render** (plano Free):

1. Criar banco no Render (Free)
2. Popular com dados de teste
3. Usar para testes sem afetar produção

## 🔄 Script de Sincronização (Opcional)

Se optar por banco separado, crie um job para sincronizar:

```bash
#!/bin/bash
# sync_databases.sh

# Fazer backup do Heroku
heroku pg:backups:capture --app lwksistemas

# Download do backup
heroku pg:backups:download --app lwksistemas -o /tmp/heroku_backup.dump

# Restaurar no Render
pg_restore --verbose --clean --no-acl --no-owner \
  -d $RENDER_DATABASE_URL \
  /tmp/heroku_backup.dump

# Limpar
rm /tmp/heroku_backup.dump
```

Agendar no Heroku Scheduler (diariamente):
```bash
heroku addons:create scheduler:standard --app lwksistemas
heroku addons:open scheduler --app lwksistemas
```

## 📝 Próximos Passos

### Opção A: Banco Separado (Recomendado)

1. ✅ Criar PostgreSQL no Render
2. ✅ Copiar dados do Heroku
3. ✅ Configurar DATABASE_URL no Render (com `?sslmode=require`)
4. ✅ Fazer deploy
5. ✅ Testar: `curl https://lwksistemas-backup.onrender.com/api/superadmin/health/`

### Opção B: Mesmo Banco (Mais Caro)

1. ✅ Fazer upgrade do Heroku Postgres para Standard-0
2. ✅ Adicionar `?sslmode=require` na DATABASE_URL
3. ✅ Configurar no Render
4. ✅ Fazer deploy
5. ✅ Testar

## ⚠️ Importante

Se você escolher **banco separado**, lembre-se:

- Os dados **não serão sincronizados automaticamente**
- Você precisa configurar sincronização periódica
- Em caso de failover, pode haver perda de dados recentes
- Considere usar o Render apenas para **leitura** ou **testes**

## 🎉 Conclusão

O erro ocorre porque:
1. A DATABASE_URL no Render está incorreta
2. Falta SSL na conexão
3. O plano Essential-0 do Heroku não permite conexões externas

**Solução mais simples:** Criar banco separado no Render com sincronização periódica.
