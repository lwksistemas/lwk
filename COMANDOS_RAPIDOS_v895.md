# ⚡ COMANDOS RÁPIDOS - v895

Referência rápida de comandos para deploy e diagnóstico.

---

## 🚀 DEPLOY

```bash
# Deploy automatizado (RECOMENDADO)
./DEPLOY_v895.sh

# Deploy manual
git add backend/config/settings.py backend/superadmin/auth_views_secure.py backend/*.py *.md *.sh
git commit -m "fix: adicionar timeout e retry para PostgreSQL (v895)"
git push heroku main
```

---

## 🧪 TESTES

```bash
# Teste simples (sem Django)
python backend/test_timeout_fix_simple.py

# Teste completo (com Django)
python backend/test_timeout_fix.py

# Diagnóstico local
python backend/diagnostico_db.py
```

---

## 🔍 DIAGNÓSTICO HEROKU

```bash
# Logs em tempo real
heroku logs --tail --app lwksistemas

# Diagnóstico completo
heroku run python backend/diagnostico_db.py --app lwksistemas

# Informações do PostgreSQL
heroku pg:info --app lwksistemas

# Conexões ativas
heroku pg:ps --app lwksistemas

# Testar conexão
heroku pg:psql --app lwksistemas -c "SELECT 1;"

# Ver DATABASE_URL (sem senha)
heroku config:get DATABASE_URL --app lwksistemas | sed 's/:.*@/:***@/'
```

---

## 🧪 TESTAR LOGIN

```bash
# Testar login de superadmin
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha"}' \
  -w "\nTempo: %{time_total}s\nStatus: %{http_code}\n"

# Testar com timeout
curl --max-time 15 -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha"}'
```

---

## 📊 MONITORAMENTO

```bash
# Ver últimos 100 logs
heroku logs -n 100 --app lwksistemas

# Filtrar erros
heroku logs --tail --app lwksistemas | grep -E "(ERROR|CRITICAL|TIMEOUT)"

# Filtrar sucessos
heroku logs --tail --app lwksistemas | grep -E "(✅|SUCCESS)"

# Ver métricas
heroku ps --app lwksistemas
```

---

## 🔧 TROUBLESHOOTING

```bash
# Verificar queries lentas
heroku pg:psql --app lwksistemas -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
  FROM pg_stat_activity 
  WHERE state = 'active' 
  ORDER BY duration DESC 
  LIMIT 10;
"

# Verificar locks
heroku pg:psql --app lwksistemas -c "SELECT * FROM pg_locks WHERE NOT granted;"

# Matar conexões idle
heroku pg:psql --app lwksistemas -c "
  SELECT pg_terminate_backend(pid) 
  FROM pg_stat_activity 
  WHERE datname = current_database() 
  AND pid <> pg_backend_pid() 
  AND state = 'idle' 
  AND state_change < current_timestamp - INTERVAL '5 minutes';
"

# Verificar versão do PostgreSQL
heroku pg:psql --app lwksistemas -c "SELECT version();"
```

---

## 🚨 ROLLBACK

```bash
# Rollback para versão anterior
heroku rollback --app lwksistemas

# Ver releases
heroku releases --app lwksistemas

# Rollback para release específica
heroku rollback v894 --app lwksistemas
```

---

## 🔄 MIGRAÇÃO PARA HEROKU POSTGRES

```bash
# Criar addon
heroku addons:create heroku-postgresql:essential-0 --app lwksistemas

# Ver addons
heroku addons --app lwksistemas

# Promover novo banco
heroku pg:promote HEROKU_POSTGRESQL_COLOR --app lwksistemas

# Backup do banco antigo (antes de migrar)
heroku pg:backups:capture --app lwksistemas

# Ver backups
heroku pg:backups --app lwksistemas

# Restaurar backup
heroku pg:backups:restore b001 DATABASE_URL --app lwksistemas
```

---

## 🔌 PGBOUNCER

```bash
# Adicionar PgBouncer
heroku addons:create pgbouncer:mini --app lwksistemas

# Configurar DATABASE_URL para usar PgBouncer
heroku config:set DATABASE_URL=$(heroku config:get PGBOUNCER_URL) --app lwksistemas

# Ver informações do PgBouncer
heroku pg:info --app lwksistemas
```

---

## 📝 CONFIGURAÇÃO

```bash
# Ver todas as variáveis de ambiente
heroku config --app lwksistemas

# Ver variável específica
heroku config:get DATABASE_URL --app lwksistemas

# Definir variável
heroku config:set USE_REDIS=true --app lwksistemas

# Remover variável
heroku config:unset VARIAVEL --app lwksistemas
```

---

## 🐛 DEBUG

```bash
# Abrir console Python no Heroku
heroku run python backend/manage.py shell --app lwksistemas

# Executar comando Django
heroku run python backend/manage.py migrate --app lwksistemas

# Ver processos rodando
heroku ps --app lwksistemas

# Reiniciar aplicação
heroku restart --app lwksistemas

# Escalar dynos
heroku ps:scale web=1 --app lwksistemas
```

---

## 📦 DEPENDÊNCIAS

```bash
# Ver dependências instaladas
heroku run pip list --app lwksistemas

# Ver versão do Python
heroku run python --version --app lwksistemas

# Ver versão do Django
heroku run python -c "import django; print(django.get_version())" --app lwksistemas
```

---

## 🔐 SEGURANÇA

```bash
# Ver logs de autenticação
heroku logs --tail --app lwksistemas | grep -E "(login|LOGIN|auth)"

# Ver tentativas falhadas
heroku logs --tail --app lwksistemas | grep -E "(FALHOU|FAILED|401|403)"

# Ver acessos de superadmin
heroku logs --tail --app lwksistemas | grep "superadmin"
```

---

## 📈 PERFORMANCE

```bash
# Ver uso de memória
heroku ps:exec --app lwksistemas
> free -h

# Ver uso de CPU
heroku ps:exec --app lwksistemas
> top

# Ver uso de disco
heroku ps:exec --app lwksistemas
> df -h
```

---

## 🌐 REDE

```bash
# Testar conectividade com RDS
heroku run curl -v telnet://cet8r1hlj0mlnt.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432 --app lwksistemas

# Ver IP do dyno
heroku ps:exec --app lwksistemas
> curl ifconfig.me

# Testar DNS
heroku ps:exec --app lwksistemas
> nslookup cet8r1hlj0mlnt.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com
```

---

## 📚 DOCUMENTAÇÃO

```bash
# Ver documentação local
cat RESUMO_FINAL_v895.md
cat CORRECAO_TIMEOUT_POSTGRESQL.md
cat DIAGNOSTICO_TIMEOUT_POSTGRESQL.md

# Ver checklist
cat CHECKLIST_DEPLOY_v895.md
```

---

## ⚡ ATALHOS ÚTEIS

```bash
# Alias para comandos frequentes (adicionar ao ~/.bashrc ou ~/.zshrc)
alias hlogs='heroku logs --tail --app lwksistemas'
alias hps='heroku ps --app lwksistemas'
alias hpg='heroku pg:info --app lwksistemas'
alias hconfig='heroku config --app lwksistemas'
alias hrestart='heroku restart --app lwksistemas'
alias hdiag='heroku run python backend/diagnostico_db.py --app lwksistemas'
```

---

**Dica:** Salve este arquivo como favorito para acesso rápido aos comandos!
