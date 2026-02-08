# Processo de Deploy - Dashboard Clínica v481

## 🚀 Guia Completo de Deploy

Este documento detalha o processo completo de deploy do dashboard da clínica de estética, incluindo comandos, validações e troubleshooting.

---

## 📋 Pré-requisitos

### Backend (Heroku)
- ✅ Conta Heroku ativa
- ✅ Heroku CLI instalado
- ✅ Git configurado
- ✅ Acesso ao repositório
- ✅ Variáveis de ambiente configuradas

### Frontend (Vercel)
- ✅ Conta Vercel ativa
- ✅ Vercel CLI instalado (`npm i -g vercel`)
- ✅ Projeto linkado ao Vercel
- ✅ Variáveis de ambiente configuradas

---

## 🔧 Deploy Backend (Heroku)

### 1. Preparação

```bash
# Navegar para o diretório backend
cd backend

# Verificar status do git
git status

# Verificar branch atual
git branch
```

---

### 2. Commit das Alterações

```bash
# Adicionar todos os arquivos modificados
git add -A

# Criar commit com mensagem descritiva
git commit -m "feat: adiciona funcionalidades de agendamento v481"

# Exemplos de mensagens de commit:
# git commit -m "fix: corrige dark mode no calendário v479"
# git commit -m "refactor: remove código duplicado v478"
# git commit -m "style: ajusta z-index dos modais v478"
```

---

### 3. Deploy para Heroku

```bash
# Push para o Heroku (branch master)
git push heroku master

# OU se estiver em outra branch:
git push heroku sua-branch:master
```

**Saída Esperada:**
```
Enumerating objects: 15, done.
Counting objects: 100% (15/15), done.
Delta compression using up to 8 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (8/8), 2.45 KiB | 2.45 MiB/s, done.
Total 8 (delta 6), reused 0 (delta 0), pack-reused 0
remote: Compressing source files... done.
remote: Building source:
remote: 
remote: -----> Building on the Heroku-22 stack
remote: -----> Using buildpack: heroku/python
remote: -----> Python app detected
remote: -----> Installing python-3.11.7
remote: -----> Installing pip 23.3.2, setuptools 69.0.3 and wheel 0.42.0
remote: -----> Installing SQLite3
remote: -----> Installing requirements with pip
remote:        Collecting Django==4.2.7
remote:        ...
remote: -----> Discovering process types
remote:        Procfile declares types -> web
remote: 
remote: -----> Compressing...
remote:        Done: 85.2M
remote: -----> Launching...
remote:        Released v180
remote:        https://lwksistemas-38ad47519238.herokuapp.com/ deployed to Heroku
remote: 
remote: Verifying deploy... done.
To https://git.heroku.com/lwksistemas-38ad47519238.git
   abc1234..def5678  master -> master
```

---

### 4. Verificar Deploy

```bash
# Ver logs em tempo real
heroku logs --tail

# Ver últimas 100 linhas de log
heroku logs -n 100

# Ver status da aplicação
heroku ps

# Abrir aplicação no navegador
heroku open
```

---

### 5. Executar Migrações (se necessário)

```bash
# Executar migrações
heroku run python manage.py migrate

# Criar superusuário (se necessário)
heroku run python manage.py createsuperuser

# Coletar arquivos estáticos
heroku run python manage.py collectstatic --noinput
```

---

## 🌐 Deploy Frontend (Vercel)

### 1. Preparação

```bash
# Navegar para o diretório frontend
cd frontend

# Verificar se está logado no Vercel
vercel whoami

# Se não estiver logado:
vercel login
```

---

### 2. Build Local (Opcional)

```bash
# Testar build localmente antes do deploy
npm run build

# Verificar se não há erros de TypeScript
npm run type-check

# Verificar se não há erros de lint
npm run lint
```

---

### 3. Deploy para Produção

```bash
# Deploy direto para produção
vercel --prod --yes

# OU deploy em duas etapas:
# 1. Deploy para preview
vercel

# 2. Promover para produção
vercel --prod
```

**Saída Esperada:**
```
Vercel CLI 33.0.1
🔍  Inspect: https://vercel.com/seu-usuario/lwk-sistemas/abc123 [2s]
✅  Production: https://lwksistemas.com.br [2m 15s]
```

---

### 4. Verificar Deploy

```bash
# Abrir URL de produção
open https://lwksistemas.com.br

# Ver logs do deploy
vercel logs https://lwksistemas.com.br

# Ver informações do projeto
vercel inspect
```

---

## ✅ Checklist de Validação Pós-Deploy

### Backend

- [ ] Aplicação está rodando (status: up)
- [ ] Logs não mostram erros críticos
- [ ] Endpoint de health check responde: `https://lwksistemas-38ad47519238.herokuapp.com/health/`
- [ ] API de agendamentos responde: `GET /clinica/agendamentos/dashboard/`
- [ ] Autenticação funciona corretamente
- [ ] CORS configurado para frontend
- [ ] Variáveis de ambiente corretas

**Comandos de Verificação:**
```bash
# Health check
curl https://lwksistemas-38ad47519238.herokuapp.com/health/

# Ver variáveis de ambiente
heroku config

# Ver status
heroku ps
```

---

### Frontend

- [ ] Site carrega sem erros
- [ ] Console do navegador sem erros (F12)
- [ ] Dark mode funciona
- [ ] Modais abrem corretamente
- [ ] Calendário carrega
- [ ] Próximos agendamentos aparecem
- [ ] Botões de ação funcionam
- [ ] Responsividade mobile OK
- [ ] Todas as páginas acessíveis

**Teste Manual:**
1. Acessar: https://lwksistemas.com.br/loja/clinica-harmonis-5898/dashboard
2. Fazer login
3. Verificar dashboard carrega
4. Testar cada ação rápida
5. Alternar dark mode
6. Testar em mobile (DevTools)

---

## 🐛 Troubleshooting

### Problema: Deploy do Backend Falha

**Sintomas:**
```
remote: !     Push rejected, failed to compile Python app.
```

**Soluções:**
```bash
# 1. Verificar requirements.txt
cat requirements.txt

# 2. Verificar runtime.txt
cat runtime.txt

# 3. Ver logs detalhados
heroku logs --tail

# 4. Verificar buildpacks
heroku buildpacks

# 5. Limpar cache do Heroku
heroku repo:purge_cache -a lwksistemas-38ad47519238
git commit --allow-empty -m "Purge cache"
git push heroku master
```

---

### Problema: Frontend Não Conecta com Backend

**Sintomas:**
- Erros de CORS no console
- Requisições falhando com 401 ou 403
- "Network Error" nas chamadas de API

**Soluções:**
```bash
# 1. Verificar variáveis de ambiente no Vercel
vercel env ls

# 2. Verificar NEXT_PUBLIC_API_URL
# Deve ser: https://lwksistemas-38ad47519238.herokuapp.com

# 3. Verificar CORS no backend
heroku config:get ALLOWED_ORIGINS

# 4. Adicionar origem se necessário
heroku config:set ALLOWED_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br"
```

---

### Problema: Modais Não Carregam

**Sintomas:**
- Loading infinito ao abrir modal
- Erro "Failed to load module"

**Soluções:**
```bash
# 1. Limpar cache do Next.js
rm -rf .next
npm run build

# 2. Verificar imports dinâmicos
# Garantir que lazy imports estão corretos

# 3. Rebuild e redeploy
vercel --prod --yes
```

---

### Problema: Dark Mode Não Funciona

**Sintomas:**
- Botão de tema não alterna
- Classes dark: não aplicadas

**Soluções:**
```typescript
// 1. Verificar se Tailwind está configurado para dark mode
// tailwind.config.js
module.exports = {
  darkMode: 'class', // ✅ Deve estar como 'class'
  // ...
}

// 2. Verificar se o script de tema está no _document.tsx
// Deve carregar tema do localStorage antes do render

// 3. Limpar localStorage e testar
localStorage.clear();
location.reload();
```

---

### Problema: Agendamentos Não Aparecem

**Sintomas:**
- Seção "Próximos Agendamentos" vazia
- Mas existem agendamentos no banco

**Soluções:**
```bash
# 1. Verificar logs do backend
heroku logs --tail | grep agendamentos

# 2. Testar endpoint diretamente
curl -H "Authorization: Bearer TOKEN" \
     -H "X-Loja-ID: 5898" \
     https://lwksistemas-38ad47519238.herokuapp.com/clinica/agendamentos/dashboard/

# 3. Verificar filtro de status no backend
# Deve incluir: agendado, confirmado, em_atendimento

# 4. Verificar console do navegador
# F12 → Console → Ver resposta da API
```

---

## 📊 Histórico de Deploys (v478-v481)

### v478 - Correções de Interface
```bash
cd backend
git add -A
git commit -m "fix: corrige z-index modais e adiciona funcionalidades agendamentos v478"
git push heroku master

cd ../frontend
vercel --prod --yes
```

**Alterações:**
- Modal.tsx (z-index z-40)
- GerenciadorConsultas.tsx (remove duplicação)
- clinica-estetica.tsx (adiciona handlers delete e status)

---

### v479 - Correção Dark Mode Principal
```bash
cd frontend
git add -A
git commit -m "fix: corrige dark mode calendário e modais principais v479"
vercel --prod --yes
```

**Alterações:**
- CalendarioAgendamentos.tsx (dark mode completo)
- ModalProtocolos.tsx (dark mode)
- ModalConfiguracoes.tsx (já estava correto)

---

### v480 - Correção Modais FullScreen
```bash
cd frontend
git add -A
git commit -m "fix: remove fullScreen de todos os modais v480"
vercel --prod --yes
```

**Alterações:**
- ModalClientes.tsx (remove fullScreen)
- ModalProfissionais.tsx (remove fullScreen)
- ModalProcedimentos.tsx (remove fullScreen)
- ModalProtocolos.tsx (remove fullScreen)
- ModalAnamnese.tsx (remove fullScreen)
- ConfiguracoesModal.tsx (remove fullScreen)

---

### v481 - Correção Dark Mode Adicional + Investigação
```bash
# Backend
cd backend
git add -A
git commit -m "fix: adiciona status em_atendimento no filtro dashboard v467"
git push heroku master

# Frontend
cd ../frontend
git add -A
git commit -m "fix: corrige dark mode modais adicionais e adiciona logs debug v481"
vercel --prod --yes
```

**Alterações Backend:**
- clinica_estetica/views.py (filtro de status)

**Alterações Frontend:**
- ModalClientes.tsx (dark mode cards)
- ModalProcedimentos.tsx (dark mode cards)
- GerenciadorConsultas.tsx (dark mode cards)
- clinica-estetica.tsx (logs de debug)

---

## 🔐 Variáveis de Ambiente

### Backend (Heroku)

```bash
# Ver todas as variáveis
heroku config

# Variáveis necessárias:
DJANGO_SECRET_KEY=...
DATABASE_URL=...
ALLOWED_HOSTS=lwksistemas-38ad47519238.herokuapp.com
ALLOWED_ORIGINS=https://lwksistemas.com.br,https://www.lwksistemas.com.br
DEBUG=False
ASAAS_API_KEY=...
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

---

### Frontend (Vercel)

```bash
# Ver variáveis
vercel env ls

# Variáveis necessárias:
NEXT_PUBLIC_API_URL=https://lwksistemas-38ad47519238.herokuapp.com
NEXT_PUBLIC_SITE_URL=https://lwksistemas.com.br
```

---

## 📝 Comandos Úteis

### Backend

```bash
# Restart da aplicação
heroku restart

# Escalar dynos
heroku ps:scale web=1

# Acessar console Python
heroku run python manage.py shell

# Backup do banco
heroku pg:backups:capture
heroku pg:backups:download

# Ver uso de recursos
heroku ps
heroku logs --tail
```

---

### Frontend

```bash
# Ver deployments
vercel ls

# Rollback para versão anterior
vercel rollback

# Ver domínios
vercel domains ls

# Adicionar domínio
vercel domains add lwksistemas.com.br

# Ver analytics
vercel analytics
```

---

## 🎉 Conclusão

Este documento fornece um guia completo para deploy do dashboard da clínica de estética, incluindo:
- ✅ Processo passo a passo
- ✅ Comandos de verificação
- ✅ Checklist de validação
- ✅ Troubleshooting comum
- ✅ Histórico de deploys
- ✅ Variáveis de ambiente

Seguindo este guia, qualquer desenvolvedor pode fazer deploy com segurança! 🚀
