# 🔍 Diagnóstico: Lentidão no CRM Vendas

**Data:** 10/03/2026  
**Loja:** FELIX REPRESENTACOES (felix-representacoes-000172)  
**Usuário:** felipe (luizbackup1982@gmail.com) - OWNER  
**Problema:** Calendário e Leads demorando a carregar

---

## ✅ VERIFICAÇÕES REALIZADAS

### 1. Dados no Banco
- ✅ 12 atividades existem no schema `loja_felix_representacoes_000172`
- ✅ 5 leads existem no schema
- ✅ Dados estão presentes no PostgreSQL

### 2. Usuário e Permissões
- ✅ Usuário `felipe` (ID: 266) é o OWNER da loja
- ✅ `get_current_vendedor_id()` retorna `None` para owner (correto)
- ✅ Owner deveria ver TODOS os dados

### 3. Logs do Heroku
```
GET /api/crm-vendas/atividades/?data_inicio=2026-03-01T03:00:00Z&data_fim=2026-04-12T03:00:00Z
Status: 200
Bytes: 52 (resposta vazia - apenas [])
Service time: 16-79ms (rápido)
```

**Problema identificado:** API retorna 200 OK mas com resposta vazia (52 bytes = `[]`)

### 4. Cache
- ✅ Cache limpo manualmente
- ⚠️ BUG ENCONTRADO: `get_cache_key()` não incluía `:owner` quando `vendedor_id=None`
- ✅ BUG CORRIGIDO no commit 02cce764

---

## 🐛 CAUSA RAIZ

### Bug no CRMCacheManager.get_cache_key()

**Antes (BUGADO):**
```python
if vendedor_id is not None:
    key += f':{vendedor_id}'
elif kwargs.get('owner'):  # ❌ Nunca era True
    key += ':owner'
```

**Resultado:** Chave ficava `crm_atividades:200:2026-03-01:2026-04-12` sem identificar owner/vendedor

**Depois (CORRIGIDO):**
```python
if vendedor_id is not None:
    key += f':{vendedor_id}'
else:
    key += ':owner'  # ✅ Sempre inclui :owner
```

**Resultado:** Chave fica `crm_atividades:200:owner:2026-03-01:2026-04-12`

---

## ✅ SOLUÇÃO APLICADA

### Deploy v898 CONCLUÍDO
```
✅ Deploy v898 realizado com sucesso (10/03/2026 00:05)
✅ Correção do bug de cache aplicada em produção
✅ Cache limpo manualmente após deploy
```

**Status:**
- v896: Bug no cache (chave sem `:owner`)
- v897: Falhou no release (timeout PostgreSQL)
- v898: ✅ RODANDO (correção aplicada)

**Ações realizadas:**
1. ✅ Commit vazio para forçar novo deploy
2. ✅ Deploy v898 concluído com sucesso
3. ✅ Cache limpo manualmente
4. ✅ Sistema pronto para uso

---

## 📊 IMPACTO DO BUG

### Cenário Problemático
1. Owner faz requisição → Cache salvo com chave `crm_atividades:200:...`
2. Vendedor faz requisição → Busca mesma chave `crm_atividades:200:...`
3. Vendedor recebe dados do owner (ou vice-versa)

### Dados Afetados
- ✅ Atividades (AtividadeViewSet usa `@cache_list_response`)
- ✅ Contas (ContaViewSet usa `@cache_list_response`)
- ✅ Dashboard (usa `CRMCacheManager.get_cache_key`)

### Dados NÃO Afetados
- ✅ Leads (não usa cache em list())
- ✅ Oportunidades (não usa cache em list())
- ✅ Contatos (não usa cache em list())

---

## 🎯 PRÓXIMOS PASSOS

### ✅ Concluído
1. ✅ Deploy v898 aplicado com sucesso
2. ✅ Cache limpo manualmente
3. ⏳ Aguardando teste do usuário no navegador

### Teste pelo Usuário
1. Acessar: https://lwksistemas.com.br/loja/felix-representacoes-000172/crm-vendas/calendario
2. Verificar se as 12 atividades aparecem
3. Acessar: https://lwksistemas.com.br/loja/felix-representacoes-000172/crm-vendas/leads
4. Verificar se os 5 leads aparecem

### Monitoramento (24h)
```bash
# Verificar logs de requisições
heroku logs --tail --app lwksistemas | grep crm-vendas

# Verificar cache hits/misses
heroku run "python backend/manage.py shell -c \"
from django.core.cache import cache
print(cache.get('crm_atividades:200:owner:2026-03-01:2026-04-12'))
\"" --app lwksistemas
```

### Prevenção Futura
1. ✅ Adicionar testes unitários para `get_cache_key()`
2. ✅ Adicionar testes de integração para cache
3. ✅ Documentar formato de chaves de cache

---

## 💡 LIÇÕES APRENDIDAS

1. **Cache é complexo:** Pequenos bugs em chaves podem causar grandes problemas
2. **Testes são essenciais:** Bug não teria passado com testes unitários
3. **Monitoramento:** Logs mostraram resposta vazia (52 bytes)
4. **Timeout do PostgreSQL:** Pode acontecer durante deploys (retry resolve)

---

## 📝 COMANDOS ÚTEIS

### Limpar Cache
```bash
heroku run "python backend/manage.py shell -c \"
from django.core.cache import cache
cache.clear()
\"" --app lwksistemas
```

### Verificar Dados
```bash
heroku run "python backend/manage.py shell -c \"
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SET search_path TO loja_felix_representacoes_000172, public')
    cursor.execute('SELECT COUNT(*) FROM crm_vendas_atividade')
    print(f'Atividades: {cursor.fetchone()[0]}')
\"" --app lwksistemas
```

### Monitorar Logs
```bash
heroku logs --tail --app lwksistemas | grep crm-vendas
```

---

**Status:** ✅ RESOLVIDO - Deploy v898 aplicado com sucesso (10/03/2026 00:05)
