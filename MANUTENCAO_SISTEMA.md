# 🔧 Guia de Manutenção do Sistema

## 📋 Checklist de Manutenção Regular

### Diária
- [ ] Verificar logs do Heroku: `heroku logs --tail`
- [ ] Verificar status do sistema: https://lwksistemas.com.br
- [ ] Verificar dashboards funcionando sem loops

### Semanal
- [ ] Limpar cache Python: `find backend -type d -name "__pycache__" -exec rm -rf {} +`
- [ ] Verificar espaço em disco: `du -sh backend/ frontend/`
- [ ] Revisar logs de erro no Heroku

### Mensal
- [ ] Organizar documentação: `./limpar_codigo.sh`
- [ ] Atualizar dependências Python: `pip list --outdated`
- [ ] Atualizar dependências Node: `npm outdated` (no frontend/)
- [ ] Backup do banco de dados PostgreSQL

---

## 🧹 Comandos de Limpeza

### Backend

```bash
# Limpar cache Python
find backend -type d -name "__pycache__" -exec rm -rf {} +
find backend -type f -name "*.pyc" -delete

# Limpar bancos SQLite locais (se criados)
rm backend/*.sqlite3

# Verificar espaço
du -sh backend/
```

### Frontend

```bash
# Limpar build
rm -rf frontend/.next

# Limpar node_modules (se necessário reinstalar)
rm -rf frontend/node_modules
npm install

# Verificar espaço
du -sh frontend/.next frontend/node_modules
```

### Documentação

```bash
# Organizar arquivos antigos
./limpar_codigo.sh

# Verificar arquivos na raiz
ls -1 *.md

# Verificar docs_backup
ls -1 docs_backup/*.md | wc -l
```

---

## 📊 Monitoramento

### Heroku (Backend)

```bash
# Ver logs em tempo real
heroku logs --tail

# Ver últimas 200 linhas
heroku logs --num 200

# Ver apenas erros
heroku logs --tail | grep ERROR

# Ver status da aplicação
heroku ps

# Ver uso de recursos
heroku ps:scale
```

### Vercel (Frontend)

```bash
# Ver logs
vercel logs

# Ver status
vercel ls

# Ver domínios
vercel domains ls
```

---

## 🔄 Atualizações

### Backend (Python)

```bash
# Listar pacotes desatualizados
pip list --outdated

# Atualizar um pacote específico
pip install --upgrade nome-do-pacote

# Atualizar requirements.txt
pip freeze > requirements.txt

# Deploy
git add requirements.txt
git commit -m "chore: Atualizar dependências Python"
git push heroku master
```

### Frontend (Node)

```bash
# Listar pacotes desatualizados
cd frontend
npm outdated

# Atualizar um pacote específico
npm update nome-do-pacote

# Atualizar package.json
npm update

# Deploy
vercel --prod
```

---

## 🐛 Troubleshooting

### Dashboard com Loop Infinito

```bash
# 1. Verificar rate limiting
heroku logs --tail | grep "Rate limit"

# 2. Verificar versão do frontend
curl -I https://lwksistemas.com.br

# 3. Limpar cache do navegador
# Ctrl+Shift+Delete ou aba anônima

# 4. Verificar hook useDashboardData
cat frontend/hooks/useDashboardData.ts
```

### Erro 500 no Backend

```bash
# 1. Ver logs detalhados
heroku logs --tail | grep "500"

# 2. Verificar banco de dados
heroku pg:info

# 3. Verificar variáveis de ambiente
heroku config

# 4. Reiniciar dyno
heroku restart
```

### Frontend não atualiza

```bash
# 1. Verificar último deploy
vercel ls

# 2. Forçar novo deploy
vercel --prod --force

# 3. Limpar cache do Vercel
vercel --prod --no-cache

# 4. Verificar build
vercel logs
```

---

## 💾 Backup

### Banco de Dados PostgreSQL

```bash
# Criar backup
heroku pg:backups:capture

# Listar backups
heroku pg:backups

# Download backup
heroku pg:backups:download

# Restaurar backup
heroku pg:backups:restore b001 DATABASE_URL
```

### Código

```bash
# Criar tag de versão
git tag -a v351 -m "Versão 351 - Loop infinito corrigido"
git push --tags

# Criar branch de backup
git checkout -b backup-v351
git push origin backup-v351
```

---

## 📈 Performance

### Verificar Performance do Backend

```bash
# Ver tempo de resposta
heroku logs --tail | grep "service="

# Ver uso de memória
heroku ps:scale

# Ver métricas
heroku metrics
```

### Verificar Performance do Frontend

```bash
# Lighthouse (Chrome DevTools)
# 1. Abrir DevTools (F12)
# 2. Aba Lighthouse
# 3. Generate report

# Ou via CLI
npm install -g lighthouse
lighthouse https://lwksistemas.com.br
```

---

## 🔐 Segurança

### Verificar Vulnerabilidades

```bash
# Backend (Python)
pip install safety
safety check

# Frontend (Node)
cd frontend
npm audit

# Corrigir automaticamente
npm audit fix
```

### Atualizar Secrets

```bash
# Backend (Heroku)
heroku config:set SECRET_KEY=nova-chave-secreta

# Frontend (Vercel)
vercel env add SECRET_KEY
```

---

## 📞 Suporte

### Logs Úteis

```bash
# Backend: Últimos erros
heroku logs --tail | grep -E "(ERROR|CRITICAL)"

# Backend: Rate limiting
heroku logs --tail | grep "Rate limit"

# Backend: Autenticação
heroku logs --tail | grep "JWT"

# Backend: Dashboard
heroku logs --tail | grep "dashboard"
```

### Comandos Rápidos

```bash
# Status geral
heroku ps && vercel ls

# Reiniciar tudo
heroku restart && vercel --prod

# Ver configurações
heroku config && vercel env ls
```

---

## ✅ Checklist Pós-Deploy

Após cada deploy, verificar:

- [ ] Backend responde: `curl https://lwksistemas-38ad47519238.herokuapp.com/api/`
- [ ] Frontend responde: `curl https://lwksistemas.com.br`
- [ ] Login funciona
- [ ] Dashboards carregam (sem loops)
- [ ] Rate limiting ativo
- [ ] Sem erros nos logs

---

**Última atualização**: 03/02/2026  
**Versão**: v351  
**Mantido por**: Sistema LWK
