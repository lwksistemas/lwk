# 🌐 Configuração DNS - Registro.br

## 📋 Instruções para Configurar DNS

Acesse: https://registro.br/painel/dominios/?dominio=lwksistemas.com.br

---

## ⚙️ Registros DNS a Adicionar

### 1️⃣ Frontend - Domínio Raiz (lwksistemas.com.br)

```
Tipo: A
Nome: @
Valor: 76.76.21.21
TTL: 3600
```

**Explicação**: Aponta o domínio raiz para o servidor da Vercel

---

### 2️⃣ Frontend - WWW (www.lwksistemas.com.br)

```
Tipo: A
Nome: www
Valor: 76.76.21.21
TTL: 3600
```

**Explicação**: Aponta o subdomínio www para o servidor da Vercel

---

### 3️⃣ Backend - API (api.lwksistemas.com.br)

```
Tipo: CNAME
Nome: api
Valor: tropical-clam-2bwosmygf01khdf8s44ficex.herokudns.com
TTL: 3600
```

**Explicação**: Aponta o subdomínio api para o servidor do Heroku

---

## 📝 Passo a Passo no Registro.br

### 1. Acessar Painel
- Acesse: https://registro.br/painel/
- Faça login com suas credenciais
- Clique em "Domínios"
- Selecione: `lwksistemas.com.br`

### 2. Editar DNS
- Clique em "Editar Zona"
- Ou "Gerenciar DNS"
- Ou "Configurar DNS"

### 3. Adicionar Registros

#### Registro 1: @ (Raiz)
1. Clique em "Adicionar Registro" ou "+"
2. Tipo: **A**
3. Nome: **@** (ou deixe em branco)
4. Valor: **76.76.21.21**
5. TTL: **3600**
6. Salvar

#### Registro 2: www
1. Clique em "Adicionar Registro" ou "+"
2. Tipo: **A**
3. Nome: **www**
4. Valor: **76.76.21.21**
5. TTL: **3600**
6. Salvar

#### Registro 3: api
1. Clique em "Adicionar Registro" ou "+"
2. Tipo: **CNAME**
3. Nome: **api**
4. Valor: **tropical-clam-2bwosmygf01khdf8s44ficex.herokudns.com**
5. TTL: **3600**
6. Salvar

### 4. Salvar Alterações
- Clique em "Salvar" ou "Aplicar"
- Confirme as alterações

---

## ⏳ Tempo de Propagação

- **Mínimo**: 5 minutos
- **Médio**: 1-2 horas
- **Máximo**: 48 horas

**Geralmente funciona em 30 minutos a 2 horas**

---

## ✅ Verificar Configuração

### Verificar DNS (Terminal)

```bash
# Verificar domínio raiz
nslookup lwksistemas.com.br

# Verificar www
nslookup www.lwksistemas.com.br

# Verificar api
nslookup api.lwksistemas.com.br
```

### Verificar DNS (Online)

Acesse: https://dnschecker.org/

Digite cada domínio:
- `lwksistemas.com.br`
- `www.lwksistemas.com.br`
- `api.lwksistemas.com.br`

---

## 📊 Resumo Visual

```
┌─────────────────────────────────────────────────┐
│ Registro.br (DNS)                               │
├─────────────────────────────────────────────────┤
│                                                 │
│ @ (raiz)                                        │
│ Tipo: A                                         │
│ Valor: 76.76.21.21                              │
│ ↓                                               │
│ lwksistemas.com.br → Vercel (Frontend)          │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│ www                                             │
│ Tipo: A                                         │
│ Valor: 76.76.21.21                              │
│ ↓                                               │
│ www.lwksistemas.com.br → Vercel (Frontend)      │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│ api                                             │
│ Tipo: CNAME                                     │
│ Valor: tropical-clam-...herokudns.com           │
│ ↓                                               │
│ api.lwksistemas.com.br → Heroku (Backend)       │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🎯 Após Configurar DNS

Aguarde a propagação (1-2 horas) e então execute:

### 1. Atualizar Variáveis de Ambiente

```bash
# Backend (Heroku)
heroku config:set ALLOWED_HOSTS="lwksistemas-38ad47519238.herokuapp.com,api.lwksistemas.com.br" -a lwksistemas

heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br,https://frontend-weld-sigma-25.vercel.app" -a lwksistemas
```

### 2. Atualizar Frontend

```bash
cd frontend

# Adicionar variável de ambiente
vercel env add NEXT_PUBLIC_API_URL production
# Digite quando solicitado: https://api.lwksistemas.com.br

# Fazer novo deploy
vercel --prod
```

---

## ✅ Checklist

- [ ] Acessar painel Registro.br
- [ ] Adicionar registro A para @ (76.76.21.21)
- [ ] Adicionar registro A para www (76.76.21.21)
- [ ] Adicionar registro CNAME para api (tropical-clam-...herokudns.com)
- [ ] Salvar alterações
- [ ] Aguardar propagação (1-2 horas)
- [ ] Verificar DNS com nslookup ou dnschecker.org
- [ ] Atualizar variáveis de ambiente no Heroku
- [ ] Atualizar variável de ambiente na Vercel
- [ ] Fazer deploy do frontend
- [ ] Testar sistema completo

---

## 🎉 URLs Finais

Após tudo configurado:

**Frontend**:
- https://lwksistemas.com.br
- https://www.lwksistemas.com.br
- https://lwksistemas.com.br/superadmin/login
- https://lwksistemas.com.br/suporte/login
- https://lwksistemas.com.br/loja/harmonis/login

**Backend**:
- https://api.lwksistemas.com.br
- https://api.lwksistemas.com.br/api/
- https://api.lwksistemas.com.br/admin/

---

## 💡 Dicas Importantes

1. **Não remova os registros antigos** até confirmar que os novos funcionam
2. **TTL de 3600** = 1 hora de cache
3. **HTTPS é automático** (Vercel e Heroku)
4. **Aguarde pacientemente** a propagação DNS
5. **Teste em modo anônimo** do navegador

---

## 🆘 Problemas Comuns

### DNS não propaga
- Aguarde mais tempo (até 48h)
- Limpe cache DNS: `sudo systemd-resolve --flush-caches`
- Teste em outro dispositivo/rede

### Erro de certificado SSL
- Aguarde alguns minutos após DNS propagar
- Vercel e Heroku geram SSL automaticamente
- Pode levar até 1 hora após DNS propagar

### Site não carrega
- Verifique se DNS está correto
- Verifique se propagou: https://dnschecker.org/
- Verifique variáveis de ambiente

---

**Pronto para configurar!** 🚀

Configure os 3 registros DNS no Registro.br e aguarde a propagação.
