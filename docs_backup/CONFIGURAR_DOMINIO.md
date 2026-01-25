# 🌐 Configurar Domínio lwksistemas.com.br

## 📋 Visão Geral

Vamos configurar o domínio `lwksistemas.com.br` para funcionar com:
- **Frontend (Vercel)**: `lwksistemas.com.br` e `www.lwksistemas.com.br`
- **Backend (Heroku)**: `api.lwksistemas.com.br`

---

## 🎯 Estrutura Final

```
lwksistemas.com.br              → Frontend (Vercel)
www.lwksistemas.com.br          → Frontend (Vercel)
api.lwksistemas.com.br          → Backend (Heroku)
```

---

## 1️⃣ Configurar Frontend na Vercel

### Passo 1: Adicionar Domínio na Vercel

```bash
cd frontend
vercel domains add lwksistemas.com.br
vercel domains add www.lwksistemas.com.br
```

Ou pelo Dashboard:
1. Acesse: https://vercel.com/lwks-projects-48afd555/frontend/settings/domains
2. Clique em "Add Domain"
3. Digite: `lwksistemas.com.br`
4. Clique em "Add"
5. Repita para: `www.lwksistemas.com.br`

### Passo 2: Obter Registros DNS da Vercel

A Vercel vai fornecer os registros DNS necessários. Geralmente são:

**Para lwksistemas.com.br:**
```
Tipo: A
Nome: @
Valor: 76.76.21.21
```

**Para www.lwksistemas.com.br:**
```
Tipo: CNAME
Nome: www
Valor: cname.vercel-dns.com
```

---

## 2️⃣ Configurar Backend no Heroku

### Passo 1: Adicionar Domínio no Heroku

```bash
heroku domains:add api.lwksistemas.com.br -a lwksistemas
```

### Passo 2: Obter DNS Target do Heroku

```bash
heroku domains -a lwksistemas
```

Você verá algo como:
```
=== lwksistemas Heroku Domain
lwksistemas-38ad47519238.herokuapp.com

=== lwksistemas Custom Domains
Domain Name              DNS Target
───────────────────────  ──────────────────────────────────────
api.lwksistemas.com.br   xxx-xxx-xxx.herokudns.com
```

Copie o valor do **DNS Target** (exemplo: `xxx-xxx-xxx.herokudns.com`)

---

## 3️⃣ Configurar DNS no Registro.br

Acesse: https://registro.br/painel/dominios/?dominio=lwksistemas.com.br

### Configurações DNS:

#### Registro 1: Frontend (Raiz)
```
Tipo: A
Nome: @
Valor: 76.76.21.21
TTL: 3600
```

#### Registro 2: Frontend (WWW)
```
Tipo: CNAME
Nome: www
Valor: cname.vercel-dns.com
TTL: 3600
```

#### Registro 3: Backend (API)
```
Tipo: CNAME
Nome: api
Valor: [DNS Target do Heroku - obtido no passo 2]
TTL: 3600
```

**Exemplo do DNS Target do Heroku:**
```
Tipo: CNAME
Nome: api
Valor: xxx-xxx-xxx.herokudns.com
TTL: 3600
```

---

## 4️⃣ Atualizar Variáveis de Ambiente

### Backend (Heroku)

```bash
# Atualizar ALLOWED_HOSTS
heroku config:set ALLOWED_HOSTS="lwksistemas-38ad47519238.herokuapp.com,api.lwksistemas.com.br" -a lwksistemas

# Atualizar CORS_ORIGINS
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br,https://frontend-weld-sigma-25.vercel.app" -a lwksistemas
```

### Frontend (Vercel)

Pelo Dashboard:
1. Acesse: https://vercel.com/lwks-projects-48afd555/frontend/settings/environment-variables
2. Edite `NEXT_PUBLIC_API_URL`
3. Altere para: `https://api.lwksistemas.com.br`
4. Clique em "Save"

Ou pelo CLI:
```bash
cd frontend
vercel env add NEXT_PUBLIC_API_URL production
# Digite: https://api.lwksistemas.com.br
```

Depois faça novo deploy:
```bash
vercel --prod
```

---

## 5️⃣ Aguardar Propagação DNS

⏳ **Tempo de propagação**: 5 minutos a 48 horas (geralmente 1-2 horas)

### Verificar Propagação

```bash
# Verificar domínio raiz
nslookup lwksistemas.com.br

# Verificar www
nslookup www.lwksistemas.com.br

# Verificar api
nslookup api.lwksistemas.com.br
```

Ou use: https://dnschecker.org/

---

## 6️⃣ Testar o Sistema

Após a propagação DNS, teste:

### Frontend
- ✅ https://lwksistemas.com.br
- ✅ https://www.lwksistemas.com.br
- ✅ https://lwksistemas.com.br/superadmin/login
- ✅ https://lwksistemas.com.br/suporte/login
- ✅ https://lwksistemas.com.br/loja/harmonis/login

### Backend
- ✅ https://api.lwksistemas.com.br
- ✅ https://api.lwksistemas.com.br/api/
- ✅ https://api.lwksistemas.com.br/admin/

---

## 📊 Resumo das URLs

### Antes (Temporárias)
```
Frontend: https://frontend-weld-sigma-25.vercel.app
Backend:  https://lwksistemas-38ad47519238.herokuapp.com
```

### Depois (Domínio Próprio)
```
Frontend: https://lwksistemas.com.br
Backend:  https://api.lwksistemas.com.br
```

---

## 🔧 Comandos Rápidos

### Adicionar domínios
```bash
# Frontend (Vercel)
cd frontend
vercel domains add lwksistemas.com.br
vercel domains add www.lwksistemas.com.br

# Backend (Heroku)
heroku domains:add api.lwksistemas.com.br -a lwksistemas
```

### Ver domínios configurados
```bash
# Vercel
vercel domains ls

# Heroku
heroku domains -a lwksistemas
```

### Atualizar variáveis
```bash
# Backend
heroku config:set ALLOWED_HOSTS="lwksistemas-38ad47519238.herokuapp.com,api.lwksistemas.com.br" -a lwksistemas
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br" -a lwksistemas

# Frontend (depois fazer deploy)
vercel env add NEXT_PUBLIC_API_URL production
# Digite: https://api.lwksistemas.com.br
vercel --prod
```

---

## ✅ Checklist

### Vercel (Frontend)
- [ ] Domínio `lwksistemas.com.br` adicionado
- [ ] Domínio `www.lwksistemas.com.br` adicionado
- [ ] Registros DNS obtidos

### Heroku (Backend)
- [ ] Domínio `api.lwksistemas.com.br` adicionado
- [ ] DNS Target obtido
- [ ] ALLOWED_HOSTS atualizado
- [ ] CORS_ORIGINS atualizado

### Registro.br (DNS)
- [ ] Registro A para @ (raiz)
- [ ] Registro CNAME para www
- [ ] Registro CNAME para api
- [ ] Aguardar propagação (1-2 horas)

### Variáveis de Ambiente
- [ ] Backend: ALLOWED_HOSTS atualizado
- [ ] Backend: CORS_ORIGINS atualizado
- [ ] Frontend: NEXT_PUBLIC_API_URL atualizado
- [ ] Frontend: Deploy realizado

### Testes
- [ ] Frontend acessível via domínio
- [ ] Backend acessível via api.domínio
- [ ] Login SuperAdmin funcionando
- [ ] Login Suporte funcionando
- [ ] Login Lojas funcionando
- [ ] HTTPS funcionando (automático)

---

## 🎯 Próximos Passos

1. **Adicionar domínios** na Vercel e Heroku
2. **Obter registros DNS** de ambos
3. **Configurar DNS** no Registro.br
4. **Aguardar propagação** (1-2 horas)
5. **Atualizar variáveis** de ambiente
6. **Fazer deploy** do frontend
7. **Testar** o sistema completo

---

## 💡 Dicas

### SSL/HTTPS
- ✅ Vercel: SSL automático (Let's Encrypt)
- ✅ Heroku: SSL automático (ACM)
- ✅ Não precisa configurar nada!

### Redirecionamento WWW
A Vercel automaticamente redireciona:
- `www.lwksistemas.com.br` → `lwksistemas.com.br`

### Cache DNS
Se não funcionar imediatamente:
- Limpe cache DNS: `sudo systemd-resolve --flush-caches`
- Teste em modo anônimo do navegador
- Aguarde mais tempo (até 48h)

---

## 🆘 Troubleshooting

### Domínio não resolve
```bash
# Verificar DNS
nslookup lwksistemas.com.br
dig lwksistemas.com.br

# Verificar propagação
# Acesse: https://dnschecker.org/
```

### Erro de CORS
```bash
# Verificar CORS no backend
heroku config:get CORS_ORIGINS -a lwksistemas

# Atualizar se necessário
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br" -a lwksistemas
```

### Erro 404 no backend
```bash
# Verificar ALLOWED_HOSTS
heroku config:get ALLOWED_HOSTS -a lwksistemas

# Atualizar se necessário
heroku config:set ALLOWED_HOSTS="api.lwksistemas.com.br" -a lwksistemas
```

---

**Pronto para configurar o domínio!** 🚀

Comece adicionando os domínios na Vercel e Heroku, depois configure o DNS no Registro.br.
