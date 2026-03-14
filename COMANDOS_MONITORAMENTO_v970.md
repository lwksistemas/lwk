# Comandos de Monitoramento - Deploy v970

## 🔍 HEROKU (Backend)

### Status e Informações
```bash
# Ver status dos dynos
heroku ps -a lwksistemas

# Ver informações do app
heroku apps:info -a lwksistemas

# Ver releases recentes
heroku releases -a lwksistemas

# Ver detalhes da release atual
heroku releases:info v965 -a lwksistemas
```

### Logs
```bash
# Ver logs em tempo real
heroku logs --tail -a lwksistemas

# Ver últimas 100 linhas
heroku logs -n 100 -a lwksistemas

# Filtrar logs por tipo
heroku logs --source app -a lwksistemas
heroku logs --source heroku -a lwksistemas

# Filtrar logs por erro
heroku logs --tail -a lwksistemas | grep ERROR
heroku logs --tail -a lwksistemas | grep CRITICAL
```

### Performance e Métricas
```bash
# Ver uso de recursos
heroku ps:scale -a lwksistemas

# Ver métricas (requer addon)
heroku metrics -a lwksistemas

# Ver uso de memória
heroku ps:exec -a lwksistemas
```

### Database
```bash
# Ver informações do banco
heroku pg:info -a lwksistemas

# Ver conexões ativas
heroku pg:ps -a lwksistemas

# Ver tamanho do banco
heroku pg:info -a lwksistemas | grep Size

# Backup do banco
heroku pg:backups:capture -a lwksistemas
heroku pg:backups -a lwksistemas
```

### Cache (Redis)
```bash
# Ver informações do Redis
heroku redis:info -a lwksistemas

# Ver estatísticas do Redis
heroku redis:stats -a lwksistemas

# Limpar cache (se necessário)
heroku redis:cli -a lwksistemas
# Dentro do CLI: FLUSHALL
```

### Comandos Django
```bash
# Executar comando Django
heroku run python backend/manage.py shell -a lwksistemas

# Verificar migrações
heroku run python backend/manage.py showmigrations -a lwksistemas

# Criar superuser (se necessário)
heroku run python backend/manage.py createsuperuser -a lwksistemas

# Collectstatic manual
heroku run python backend/manage.py collectstatic --noinput -a lwksistemas
```

### Restart e Manutenção
```bash
# Reiniciar dynos
heroku restart -a lwksistemas

# Reiniciar dyno específico
heroku restart web.1 -a lwksistemas

# Escalar dynos
heroku ps:scale web=1 -a lwksistemas

# Modo manutenção
heroku maintenance:on -a lwksistemas
heroku maintenance:off -a lwksistemas
```

---

## 🌐 VERCEL (Frontend)

### Status e Informações
```bash
# Ver lista de projetos
vercel list

# Ver informações do projeto
vercel inspect https://lwksistemas.com.br

# Ver deployments recentes
vercel ls

# Ver logs do último deploy
vercel logs https://lwksistemas.com.br
```

### Deploy e Rollback
```bash
# Deploy para produção
cd frontend && vercel --prod

# Deploy para preview
cd frontend && vercel

# Promover preview para produção
vercel promote [deployment-url]

# Rollback (promover deploy anterior)
vercel rollback
```

### Domínios e Aliases
```bash
# Ver domínios
vercel domains ls

# Ver aliases
vercel alias ls

# Adicionar alias
vercel alias set [deployment-url] lwksistemas.com.br
```

### Environment Variables
```bash
# Ver variáveis de ambiente
vercel env ls

# Adicionar variável
vercel env add [name]

# Remover variável
vercel env rm [name]
```

---

## 🧪 TESTES EM PRODUÇÃO

### Backend (API)

#### Health Check
```bash
curl https://lwksistemas-38ad47519238.herokuapp.com/health/
```

#### CRM Vendas - Endpoints com Cache
```bash
# Dashboard (cache 2min)
curl -H "Authorization: Bearer [token]" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/dashboard/

# Vendedores (decorator @require_admin_access)
curl -H "Authorization: Bearer [token]" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/vendedores/

# Contas (cache 5min)
curl -H "Authorization: Bearer [token]" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/contas/

# Leads (cache 5min - NOVO)
curl -H "Authorization: Bearer [token]" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/leads/

# Oportunidades (cache 5min - NOVO)
curl -H "Authorization: Bearer [token]" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/oportunidades/

# Atividades (cache 5min)
curl -H "Authorization: Bearer [token]" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/atividades/
```

#### Testar Invalidação de Cache
```bash
# 1. Fazer GET (deve cachear)
curl -H "Authorization: Bearer [token]" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/contas/

# 2. Criar nova conta (deve invalidar cache)
curl -X POST -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Teste Cache","email":"teste@cache.com"}' \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/contas/

# 3. Fazer GET novamente (deve buscar do banco, não do cache)
curl -H "Authorization: Bearer [token]" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/contas/
```

### Frontend

#### Páginas Principais
```bash
# Home
curl -I https://lwksistemas.com.br

# Login
curl -I https://lwksistemas.com.br/login

# CRM Vendas (requer autenticação)
curl -I https://lwksistemas.com.br/loja/felix-5889/crm-vendas/
```

---

## 📊 MONITORAMENTO DE PERFORMANCE

### Métricas para Acompanhar

#### Backend (Heroku)
- ✅ Tempo de resposta dos endpoints
- ✅ Taxa de hit do cache (Redis)
- ✅ Uso de memória dos dynos
- ✅ Número de queries ao banco
- ✅ Erros 500 (Internal Server Error)
- ✅ Tempo de build e deploy

#### Frontend (Vercel)
- ✅ Tempo de carregamento das páginas
- ✅ Core Web Vitals (LCP, FID, CLS)
- ✅ Taxa de erro de build
- ✅ Tempo de deploy

### Ferramentas de Monitoramento

#### Heroku Dashboard
- https://dashboard.heroku.com/apps/lwksistemas
- Metrics → Ver gráficos de performance
- Activity → Ver histórico de deploys
- Resources → Ver addons e uso

#### Vercel Dashboard
- https://vercel.com/lwks-projects-48afd555/frontend
- Analytics → Ver métricas de uso
- Deployments → Ver histórico
- Logs → Ver logs em tempo real

---

## 🚨 TROUBLESHOOTING

### Problema: Cache não está funcionando
```bash
# Verificar Redis
heroku redis:info -a lwksistemas

# Ver logs de cache
heroku logs --tail -a lwksistemas | grep cache

# Limpar cache manualmente
heroku redis:cli -a lwksistemas
> FLUSHALL
```

### Problema: Endpoint lento
```bash
# Ver logs com tempo de resposta
heroku logs --tail -a lwksistemas | grep "GET /api/crm-vendas"

# Verificar queries N+1
heroku run python backend/manage.py shell -a lwksistemas
# No shell: from django.db import connection; connection.queries
```

### Problema: Erro 500
```bash
# Ver logs de erro
heroku logs --tail -a lwksistemas | grep ERROR

# Ver traceback completo
heroku logs -n 500 -a lwksistemas | grep -A 20 "Traceback"

# Verificar variáveis de ambiente
heroku config -a lwksistemas
```

### Problema: Deploy falhou
```bash
# Ver logs do build
heroku builds -a lwksistemas
heroku builds:info [build-id] -a lwksistemas

# Rollback para versão anterior
heroku rollback -a lwksistemas

# Verificar Procfile
cat backend/Procfile
```

---

## 📝 CHECKLIST PÓS-DEPLOY

### Imediato (0-1h)
- [ ] Verificar status dos dynos: `heroku ps`
- [ ] Verificar logs por erros: `heroku logs --tail | grep ERROR`
- [ ] Testar endpoints principais com curl
- [ ] Verificar cache funcionando (Redis stats)
- [ ] Testar login no frontend

### Curto Prazo (1-24h)
- [ ] Monitorar logs por 24h
- [ ] Verificar métricas de performance
- [ ] Testar invalidação de cache
- [ ] Coletar feedback dos usuários
- [ ] Verificar uso de memória

### Médio Prazo (1-7 dias)
- [ ] Analisar métricas de cache hit rate
- [ ] Verificar tempo de resposta médio
- [ ] Identificar endpoints mais lentos
- [ ] Otimizar queries se necessário
- [ ] Ajustar TTL do cache se necessário

---

## 🎯 MÉTRICAS DE SUCESSO

### Performance
- ✅ Tempo de resposta < 500ms (endpoints com cache)
- ✅ Cache hit rate > 70%
- ✅ Queries por request < 10
- ✅ Uso de memória < 80%

### Qualidade
- ✅ Zero erros 500 em produção
- ✅ Zero regressões funcionais
- ✅ Código duplicado < 5%
- ✅ Cobertura de cache 100%

### Usuário
- ✅ Tempo de carregamento < 2s
- ✅ Zero reclamações de lentidão
- ✅ Funcionalidades operando normalmente
- ✅ Feedback positivo

---

**Última atualização**: 2026-03-12 13:54 BRT
**Versão**: v970 (Heroku v965)
