# 🚀 Deploy Frontend (Next.js) na Vercel

## ⚡ Opção 1: Deploy via CLI (Rápido)

### 1. Instalar Vercel CLI
```bash
npm install -g vercel
```

### 2. Fazer Login
```bash
vercel login
```

### 3. Configurar Variável de Ambiente
```bash
cd frontend
```

Criar arquivo `.env.production`:
```bash
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://lwksistemas-38ad47519238.herokuapp.com
EOF
```

### 4. Deploy
```bash
vercel
```

Responda as perguntas:
- Set up and deploy? **Y**
- Which scope? (escolha sua conta)
- Link to existing project? **N**
- What's your project's name? **lwksistemas-frontend**
- In which directory is your code located? **./frontend** (ou apenas Enter se já estiver na pasta)

### 5. Deploy para Produção
```bash
vercel --prod
```

**Pronto! Seu frontend estará no ar em:** `https://lwksistemas-frontend.vercel.app`

---

## 🌐 Opção 2: Deploy via Dashboard (Visual)

### 1. Acesse
https://vercel.com/new

### 2. Conecte o GitHub
- Clique em "Import Git Repository"
- Conecte sua conta GitHub
- Selecione o repositório `lwksistemas`

### 3. Configure o Projeto
- **Framework Preset**: Next.js
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (automático)
- **Output Directory**: `.next` (automático)

### 4. Adicione Variável de Ambiente
Clique em "Environment Variables" e adicione:

```
Name: NEXT_PUBLIC_API_URL
Value: https://lwksistemas-38ad47519238.herokuapp.com
```

### 5. Deploy
Clique em "Deploy"

Aguarde ~2 minutos e seu frontend estará no ar!

---

## 🔗 Após o Deploy

### URLs do Frontend (Vercel):
- **Home**: https://lwksistemas-frontend.vercel.app
- **SuperAdmin Login**: https://lwksistemas-frontend.vercel.app/superadmin/login
- **Suporte Login**: https://lwksistemas-frontend.vercel.app/suporte/login
- **Loja Login**: https://lwksistemas-frontend.vercel.app/loja/[slug]/login

### Atualizar CORS no Backend

Após o deploy, você precisa adicionar a URL do frontend no CORS do backend:

```bash
heroku config:set CORS_ORIGINS=https://lwksistemas-frontend.vercel.app -a lwksistemas
```

---

## 🔧 Configuração Completa

### Arquivo `.env.production` (frontend)
```env
NEXT_PUBLIC_API_URL=https://lwksistemas-38ad47519238.herokuapp.com
```

### Variáveis no Backend (Heroku)
```bash
heroku config:set CORS_ORIGINS=https://lwksistemas-frontend.vercel.app -a lwksistemas
heroku config:set ALLOWED_HOSTS=lwksistemas-38ad47519238.herokuapp.com -a lwksistemas
```

---

## 📊 Custos

**Vercel Hobby (Grátis):**
- ✅ Deploy ilimitado
- ✅ HTTPS automático
- ✅ CDN global
- ✅ Domínio .vercel.app

**Total: R$ 0,00/mês** 🎉

---

## 🐛 Troubleshooting

### Erro: "API request failed"
Verifique se a variável `NEXT_PUBLIC_API_URL` está configurada corretamente.

### Erro: "CORS policy"
Adicione a URL do frontend no CORS do backend:
```bash
heroku config:set CORS_ORIGINS=https://seu-frontend.vercel.app -a lwksistemas
```

### Erro: "Build failed"
Verifique se o diretório raiz está configurado como `frontend`.

---

## ✅ Checklist

- [ ] Vercel CLI instalado (ou usar dashboard)
- [ ] Login na Vercel realizado
- [ ] Variável `NEXT_PUBLIC_API_URL` configurada
- [ ] Deploy realizado
- [ ] CORS atualizado no backend
- [ ] Frontend testado e funcionando

---

## 🎉 Pronto!

Seu sistema completo estará no ar:
- **Backend**: https://lwksistemas-38ad47519238.herokuapp.com
- **Frontend**: https://lwksistemas-frontend.vercel.app

**Sistema Multi-Tenant completo funcionando! 🚀**
