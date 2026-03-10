# ✅ CHECKLIST DE DEPLOY v895

**Correção:** Timeout de Conexão PostgreSQL  
**Data:** 10/03/2026  
**Prioridade:** 🔴 CRÍTICA

---

## 📋 PRÉ-DEPLOY

### Validação Local
- [x] Executar `python backend/test_timeout_fix_simple.py`
- [x] Verificar que todos os testes passaram (5/5)
- [x] Revisar código modificado
- [x] Verificar que não há erros de sintaxe

### Arquivos Modificados
- [x] `backend/config/settings.py` - Timeout configurável
- [x] `backend/superadmin/auth_views_secure.py` - Retry logic

### Arquivos Novos
- [x] `backend/diagnostico_db.py` - Script de diagnóstico
- [x] `backend/test_timeout_fix.py` - Teste completo
- [x] `backend/test_timeout_fix_simple.py` - Teste simples
- [x] `DIAGNOSTICO_TIMEOUT_POSTGRESQL.md` - Análise
- [x] `CORRECAO_TIMEOUT_POSTGRESQL.md` - Guia
- [x] `RESUMO_CORRECAO_TIMEOUT_v895.md` - Resumo
- [x] `DEPLOY_v895.sh` - Script de deploy
- [x] `CHECKLIST_DEPLOY_v895.md` - Este checklist

### Dependências
- [x] `dj-database-url==2.1.0` já está no requirements.txt
- [x] `psycopg2-binary==2.9.9` já está no requirements.txt

---

## 🚀 DEPLOY

### Git
```bash
# 1. Adicionar arquivos
git add backend/config/settings.py
git add backend/superadmin/auth_views_secure.py
git add backend/diagnostico_db.py
git add backend/test_timeout_fix.py
git add backend/test_timeout_fix_simple.py
git add DIAGNOSTICO_TIMEOUT_POSTGRESQL.md
git add CORRECAO_TIMEOUT_POSTGRESQL.md
git add RESUMO_CORRECAO_TIMEOUT_v895.md
git add DEPLOY_v895.sh
git add CHECKLIST_DEPLOY_v895.md

# 2. Commit
git commit -m "fix: adicionar timeout e retry para PostgreSQL (v895)"

# 3. Push para Heroku
git push heroku main
```

### Ou usar script automatizado
```bash
./DEPLOY_v895.sh
```

---

## 🔍 PÓS-DEPLOY

### Verificação Imediata (0-5 minutos)
- [ ] Deploy concluído sem erros
- [ ] Aplicação reiniciou corretamente
- [ ] Logs não mostram erros críticos

```bash
# Ver logs em tempo real
heroku logs --tail --app lwksistemas
```

### Diagnóstico (5-10 minutos)
- [ ] Executar script de diagnóstico
- [ ] Verificar conexão com PostgreSQL
- [ ] Verificar performance de queries

```bash
# Executar diagnóstico
heroku run python backend/diagnostico_db.py --app lwksistemas
```

### Teste Funcional (10-15 minutos)
- [ ] Testar login de superadmin
- [ ] Testar login de loja
- [ ] Verificar tempo de resposta (<10s)
- [ ] Verificar mensagens de erro (se houver)

```bash
# Testar login via curl
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha123"}' \
  -w "\nTempo: %{time_total}s\n"
```

### Métricas PostgreSQL (15-20 minutos)
- [ ] Verificar conexões ativas
- [ ] Verificar queries lentas
- [ ] Verificar uso de memória

```bash
# Informações do banco
heroku pg:info --app lwksistemas

# Conexões ativas
heroku pg:ps --app lwksistemas

# Queries lentas (se houver)
heroku pg:psql --app lwksistemas -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
  FROM pg_stat_activity 
  WHERE state = 'active' 
  ORDER BY duration DESC 
  LIMIT 10;
"
```

---

## 📊 CRITÉRIOS DE SUCESSO

### Obrigatórios (Deve passar TODOS)
- [ ] Deploy sem erros
- [ ] Aplicação acessível
- [ ] Login funciona (qualquer tipo de usuário)
- [ ] Tempo de resposta <30s (idealmente <10s)
- [ ] Sem erros H12 (Request Timeout)

### Desejáveis (Deve passar MAIORIA)
- [ ] Tempo de resposta <10s
- [ ] Taxa de sucesso >95%
- [ ] Retry funcionando (logs mostram tentativas)
- [ ] Mensagens de erro amigáveis
- [ ] Conexões PostgreSQL estáveis

---

## 🚨 PLANO DE ROLLBACK

### Se algo der errado:

```bash
# 1. Fazer rollback imediato
heroku rollback --app lwksistemas

# 2. Verificar logs
heroku logs --tail --app lwksistemas

# 3. Verificar se voltou ao normal
curl https://lwksistemas-38ad47519238.herokuapp.com/api/health/
```

### Quando fazer rollback:
- ❌ Aplicação não inicia
- ❌ Erros críticos nos logs
- ❌ Login completamente quebrado
- ❌ Timeout pior que antes (>30s)
- ❌ Erros 500 em massa

### Quando NÃO fazer rollback:
- ⚠️ Timeout ainda ocorre mas <30s (correção parcial)
- ⚠️ Alguns logins falham (problema de rede/RDS)
- ⚠️ Mensagens de erro diferentes (esperado)

---

## 🔧 TROUBLESHOOTING

### Problema: Timeout ainda ocorre

**Diagnóstico:**
```bash
heroku run python backend/diagnostico_db.py --app lwksistemas
```

**Possíveis causas:**
1. RDS inacessível (firewall/VPC)
2. Credenciais inválidas
3. PostgreSQL sobrecarregado
4. Rede lenta

**Soluções:**
1. Verificar DATABASE_URL: `heroku config:get DATABASE_URL --app lwksistemas`
2. Testar conexão: `heroku pg:psql --app lwksistemas -c "SELECT 1;"`
3. Migrar para Heroku Postgres (ver CORRECAO_TIMEOUT_POSTGRESQL.md)

### Problema: Erro de import

**Sintoma:** `ModuleNotFoundError: No module named 'dj_database_url'`

**Solução:**
```bash
# Verificar requirements.txt
heroku run pip list --app lwksistemas | grep dj-database-url

# Se não estiver instalado, adicionar e fazer redeploy
echo "dj-database-url==2.1.0" >> backend/requirements.txt
git add backend/requirements.txt
git commit -m "fix: adicionar dj-database-url ao requirements.txt"
git push heroku main
```

### Problema: Erro de sintaxe

**Sintoma:** `SyntaxError` ou `NameError` nos logs

**Solução:**
```bash
# Verificar sintaxe localmente
python -m py_compile backend/config/settings.py
python -m py_compile backend/superadmin/auth_views_secure.py

# Se houver erro, corrigir e fazer redeploy
```

---

## 📞 CONTATOS DE EMERGÊNCIA

### Logs e Monitoramento
- Heroku Dashboard: https://dashboard.heroku.com/apps/lwksistemas
- Logs: `heroku logs --tail --app lwksistemas`
- Status Heroku: https://status.heroku.com/

### Documentação
- Diagnóstico: `DIAGNOSTICO_TIMEOUT_POSTGRESQL.md`
- Correção: `CORRECAO_TIMEOUT_POSTGRESQL.md`
- Resumo: `RESUMO_CORRECAO_TIMEOUT_v895.md`

---

## 📈 MONITORAMENTO PÓS-DEPLOY

### Primeira Hora
- [ ] Verificar logs a cada 10 minutos
- [ ] Testar login 3x (superadmin, loja, suporte)
- [ ] Monitorar conexões PostgreSQL

### Primeiras 24 Horas
- [ ] Verificar logs 3x ao dia
- [ ] Monitorar métricas PostgreSQL
- [ ] Coletar feedback de usuários

### Primeira Semana
- [ ] Análise de logs diária
- [ ] Otimizar timeouts se necessário
- [ ] Considerar PgBouncer se houver problemas

---

## ✅ CONCLUSÃO

Após completar todos os itens deste checklist:

- [ ] Marcar deploy como concluído
- [ ] Atualizar documentação se necessário
- [ ] Comunicar equipe sobre mudanças
- [ ] Arquivar logs e métricas

---

**Data de Deploy:** ___/___/______  
**Responsável:** _________________  
**Status Final:** [ ] Sucesso [ ] Parcial [ ] Falhou  
**Observações:** _________________

---

**Desenvolvido com ❤️ para garantir deploys seguros e confiáveis**
