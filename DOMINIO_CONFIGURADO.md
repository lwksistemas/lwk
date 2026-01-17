# ✅ Domínio lwksistemas.com.br - Configuração

## 🎯 Status Atual

### ✅ Domínios Adicionados

**Vercel (Frontend)**:
- ✅ `lwksistemas.com.br` - Adicionado
- ✅ `www.lwksistemas.com.br` - Adicionado

**Heroku (Backend)**:
- ✅ `api.lwksistemas.com.br` - Adicionado

---

## 📋 Configuração DNS Necessária

### Acesse: https://registro.br/painel/dominios/?dominio=lwksistemas.com.br

### Adicione os seguintes registros:

#### 1. Domínio Raiz (Frontend)
```
Tipo: A
Nome: @
Valor: 76.76.21.21
TTL: 3600
```

#### 2. WWW (Frontend)
```
Tipo: A
Nome: www
Valor: 76.76.21.21
TTL: 3600
```

#### 3. API (Backend)
```
Tipo: CNAME
Nome: api
Valor: tropical-clam-2bwosmygf01khdf8s44ficex.herokudns.com
TTL: 3600
```

---

## ⏳ Próximos Passos

### 1. Configurar DNS no Registro.br ⏰ AGORA

Siga as instruções em: **`DNS_CONFIGURACAO_REGISTRO_BR.md`**

### 2. Aguardar Propagação DNS ⏰ 1-2 horas

Verificar propagação:
```bash
nslookup lwksistemas.com.br
nslookup www.lwksistemas.com.br
nslookup api.lwksistemas.com.br
```

Ou online: https://dnschecker.org/

### 3. Atualizar Variáveis de Ambiente ⏰ Após DNS propagar

Execute o script:
```bash
./atualizar_variaveis_dominio.sh
```

Ou manualmente:
```bash
# Backend
heroku config:set ALLOWED_HOSTS="lwksistemas-38ad47519238.herokuapp.com,api.lwksistemas.com.br" -a lwksistemas
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br" -a lwksistemas

# Frontend
cd frontend
vercel env add NEXT_PUBLIC_API_URL production
# Digite: https://api.lwksistemas.com.br
vercel --prod
```

### 4. Testar Sistema ⏰ Após deploy

Acesse:
- https://lwksistemas.com.br
- https://www.lwksistemas.com.br
- https://api.lwksistemas.com.br

---

## 🌐 URLs Finais

### Frontend (Vercel)
```
https://lwksistemas.com.br
https://www.lwksistemas.com.br
https://lwksistemas.com.br/superadmin/login
https://lwksistemas.com.br/suporte/login
https://lwksistemas.com.br/loja/harmonis/login
https://lwksistemas.com.br/loja/felix/login
```

### Backend (Heroku)
```
https://api.lwksistemas.com.br
https://api.lwksistemas.com.br/api/
https://api.lwksistemas.com.br/admin/
```

---

## 📊 Arquitetura Final

```
┌─────────────────────────────────────────┐
│  Registro.br (DNS)                      │
│  lwksistemas.com.br                     │
└─────────────┬───────────────────────────┘
              │
              ├─→ @ (raiz) → 76.76.21.21
              │   ↓
              │   lwksistemas.com.br
              │   ↓
              │   Vercel (Frontend)
              │
              ├─→ www → 76.76.21.21
              │   ↓
              │   www.lwksistemas.com.br
              │   ↓
              │   Vercel (Frontend)
              │
              └─→ api → tropical-clam-...herokudns.com
                  ↓
                  api.lwksistemas.com.br
                  ↓
                  Heroku (Backend)
                  ↓
                  PostgreSQL
```

---

## ✅ Checklist Completo

### Domínios
- [x] Domínio registrado (Registro.br)
- [x] Domínio adicionado na Vercel
- [x] Subdomínio www adicionado na Vercel
- [x] Subdomínio api adicionado no Heroku
- [ ] DNS configurado no Registro.br
- [ ] DNS propagado (aguardar 1-2 horas)

### Variáveis de Ambiente
- [ ] ALLOWED_HOSTS atualizado (Heroku)
- [ ] CORS_ORIGINS atualizado (Heroku)
- [ ] NEXT_PUBLIC_API_URL atualizado (Vercel)
- [ ] Deploy do frontend realizado

### Testes
- [ ] Frontend acessível via domínio
- [ ] WWW redireciona corretamente
- [ ] API acessível via subdomínio
- [ ] Login SuperAdmin funcionando
- [ ] Login Suporte funcionando
- [ ] Login Lojas funcionando
- [ ] HTTPS funcionando (automático)

---

## 💰 Custos

**Sem custo adicional!**

- Domínio: Já registrado
- Vercel: Grátis (Hobby)
- Heroku: $10/mês (já estava pagando)
- SSL: Grátis (automático)

**Total: $10/mês** (mesmo valor de antes)

---

## 🎉 Benefícios

✅ **Domínio profissional** próprio  
✅ **URLs amigáveis** e fáceis de lembrar  
✅ **HTTPS automático** (SSL grátis)  
✅ **Subdomínio API** separado  
✅ **Melhor SEO** e credibilidade  
✅ **Email profissional** (pode configurar depois)  

---

## 📝 Documentos de Referência

- **Configuração DNS**: `DNS_CONFIGURACAO_REGISTRO_BR.md`
- **Guia Completo**: `CONFIGURAR_DOMINIO.md`
- **Script de Atualização**: `atualizar_variaveis_dominio.sh`

---

## 🆘 Suporte

### Verificar Status dos Domínios

```bash
# Vercel
vercel domains ls

# Heroku
heroku domains -a lwksistemas
```

### Ver Logs

```bash
# Backend
heroku logs --tail -a lwksistemas

# Frontend
vercel logs
```

### Remover Domínio (se necessário)

```bash
# Vercel
vercel domains rm lwksistemas.com.br

# Heroku
heroku domains:remove api.lwksistemas.com.br -a lwksistemas
```

---

## 🎯 Ação Imediata

**Configure o DNS agora no Registro.br!**

1. Acesse: https://registro.br/painel/dominios/?dominio=lwksistemas.com.br
2. Adicione os 3 registros DNS (veja acima)
3. Aguarde 1-2 horas
4. Execute: `./atualizar_variaveis_dominio.sh`
5. Faça deploy do frontend
6. Teste o sistema!

---

**Domínio pronto para ser configurado!** 🚀

Siga o guia `DNS_CONFIGURACAO_REGISTRO_BR.md` para configurar o DNS.
