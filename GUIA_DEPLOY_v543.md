# Guia de Deploy - v543

**Correção:** Exclusão Automática de Schema PostgreSQL  
**Data:** 09/02/2026  
**Prioridade:** CRÍTICA

---

## 🚀 Comandos de Deploy

### 1. Verificar Alterações

```bash
# Ver arquivos modificados
git status

# Ver diferenças
git diff backend/superadmin/signals.py
```

### 2. Commit

```bash
# Adicionar arquivos
git add backend/superadmin/signals.py
git add backend/superadmin/management/commands/test_schema_deletion.py
git add CORRECAO_EXCLUSAO_SCHEMA_v543.md
git add RESUMO_IMPLEMENTACAO_v543.md
git add RELATORIO_SEGURANCA_SISTEMA_v542.md
git add GUIA_DEPLOY_v543.md

# Commit
git commit -m "fix(v543): adicionar exclusão automática de schema PostgreSQL ao deletar loja

- Adicionada lógica de exclusão de schema no signal pre_delete
- Previne criação de schemas órfãos no PostgreSQL
- Validações de segurança implementadas
- Comando de teste criado
- Documentação completa

Fixes: Sistema criava schemas órfãos ao excluir lojas"
```

### 3. Deploy no Heroku

```bash
# Deploy
git push heroku master

# Acompanhar logs
heroku logs --tail --app lwksistemas
```

---

## ✅ Verificação Pós-Deploy

### 1. Verificar Aplicação

```bash
# Status da aplicação
heroku ps --app lwksistemas

# Logs recentes
heroku logs --tail --app lwksistemas | grep -i error
```

### 2. Executar Teste Automatizado

```bash
# Executar comando de teste
heroku run python manage.py test_schema_deletion --app lwksistemas
```

**Resultado Esperado:**
```
================================================================================
TESTE: Exclusão Automática de Schema PostgreSQL
================================================================================

✅ Ambiente: PostgreSQL (produção)

ETAPA 1: Criando loja de teste...
   ✅ Usuário criado: test_schema_deletion_xxxxx
   ✅ Loja criada: Loja Teste Schema Deletion
   ✅ Schema: loja_test_schema_xxxxx

ETAPA 2: Criando schema PostgreSQL...
   ✅ Schema criado: loja_test_schema_xxxxx
   ✅ Tabela de teste criada
   ✅ Dados de teste inseridos
   ✅ Schema confirmado no PostgreSQL

ETAPA 3: Excluindo loja...
   ✅ Loja excluída: Loja Teste Schema Deletion (ID: xxx)

ETAPA 4: Verificando remoção do schema...
   ✅ SUCESSO: Schema foi removido automaticamente
   ✅ Signal pre_delete funcionou corretamente

ETAPA 5: Limpando dados de teste...
   ✅ Usuário de teste removido

================================================================================
✅ TESTE CONCLUÍDO COM SUCESSO
================================================================================

Resultado:
  ✅ Loja criada
  ✅ Schema PostgreSQL criado
  ✅ Loja excluída
  ✅ Schema PostgreSQL removido automaticamente

Conclusão: Signal pre_delete está funcionando corretamente!
```

### 3. Teste Manual (Opcional)

```bash
# 1. Acessar painel superadmin
# URL: https://lwksistemas.com.br/superadmin

# 2. Criar loja de teste
# - Nome: Teste Schema Deletion
# - Tipo: Clínica de Estética
# - Plano: Básico

# 3. Verificar schema criado
heroku pg:psql --app lwksistemas
SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'loja_%' ORDER BY schema_name;
\q

# 4. Excluir loja pelo painel

# 5. Verificar que schema foi removido
heroku pg:psql --app lwksistemas
SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'loja_%' ORDER BY schema_name;
\q

# 6. Verificar logs
heroku logs --tail --app lwksistemas | grep "Schema PostgreSQL"
```

---

## 📊 Monitoramento

### Logs a Observar

```bash
# Logs de exclusão de loja
heroku logs --tail --app lwksistemas | grep "Iniciando exclusão em cascata"

# Logs de exclusão de schema
heroku logs --tail --app lwksistemas | grep "Schema PostgreSQL removido"

# Logs de erro
heroku logs --tail --app lwksistemas | grep -i "erro.*schema"
```

### Mensagens Esperadas

**Sucesso:**
```
🗑️ Iniciando exclusão em cascata para loja: [Nome] (ID: [ID])
   ✅ X funcionários deletados
   ✅ X clientes deletados
   ✅ X agendamentos deletados
   ✅ Schema PostgreSQL removido: loja_xxxxx
✅ Exclusão em cascata concluída para loja: [Nome]
```

**Erro (não deve acontecer):**
```
❌ Erro ao remover schema PostgreSQL: [mensagem]
```

---

## 🔍 Verificação de Schemas

### Listar Schemas Ativos

```bash
heroku pg:psql --app lwksistemas

-- Listar todos os schemas
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name LIKE 'loja_%' 
ORDER BY schema_name;

-- Contar schemas
SELECT COUNT(*) as total_schemas 
FROM information_schema.schemata 
WHERE schema_name LIKE 'loja_%';

-- Sair
\q
```

### Verificar Lojas Ativas

```bash
heroku run python manage.py shell --app lwksistemas

# No shell Python:
from superadmin.models import Loja
lojas = Loja.objects.all()
print(f"Total de lojas: {lojas.count()}")
for loja in lojas:
    print(f"  - {loja.slug} ({loja.database_name})")
exit()
```

---

## 🚨 Rollback (Se Necessário)

### Se algo der errado:

```bash
# 1. Reverter commit
git revert HEAD

# 2. Deploy da reversão
git push heroku master

# 3. Verificar aplicação
heroku logs --tail --app lwksistemas
```

### Restaurar manualmente:

```bash
# 1. Editar signals.py
# 2. Remover seção de exclusão de schema
# 3. Commit e deploy

git add backend/superadmin/signals.py
git commit -m "revert: remover exclusão automática de schema"
git push heroku master
```

---

## ✅ Checklist de Deploy

- [ ] Código revisado
- [ ] Commit realizado
- [ ] Deploy no Heroku concluído
- [ ] Aplicação rodando sem erros
- [ ] Teste automatizado executado com sucesso
- [ ] Logs verificados
- [ ] Schemas verificados
- [ ] Teste manual realizado (opcional)
- [ ] Monitoramento ativo por 24h
- [ ] Equipe notificada

---

## 📞 Contatos de Emergência

Em caso de problemas críticos:

1. Verificar logs do Heroku
2. Executar rollback se necessário
3. Contatar desenvolvedor responsável
4. Documentar o problema

---

## 🎉 Conclusão

Após o deploy e verificação, o sistema estará protegido contra criação de schemas órfãos. Todas as exclusões de lojas removerão automaticamente os schemas PostgreSQL correspondentes.

**Status:** ✅ PRONTO PARA DEPLOY

---

**Última Atualização:** 09/02/2026
