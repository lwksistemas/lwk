# 📋 Próximos Passos - LWK Sistemas

## ✅ O que já está pronto:

- ✅ **Backend deployado no Heroku**: https://lwksistemas-38ad47519238.herokuapp.com
- ✅ **Frontend deployado na Vercel**: https://frontend-weld-sigma-25.vercel.app
- ✅ **API funcionando**
- ✅ **PostgreSQL configurado**
- ✅ **Migrations executadas**
- ✅ **CORS configurado**

---

## 🚀 O que falta fazer:

### 1️⃣ Criar Superusuário (IMPORTANTE) ⚠️ NECESSÁRIO

```bash
heroku run python manage.py createsuperuser -a lwksistemas
```

**Dados sugeridos:**
- Username: `superadmin`
- Email: `admin@lwksistemas.com`
- Password: (escolha uma senha forte)

---

### 2️⃣ Criar Dados Iniciais ⚠️ NECESSÁRIO

```bash
heroku run python manage.py shell -a lwksistemas
```

Cole este código:
```python
from superadmin.models import TipoLoja, PlanoAssinatura

# Tipos de Loja
tipos = [
    {'nome': 'E-commerce', 'descricao': 'Loja virtual de produtos'},
    {'nome': 'Serviços', 'descricao': 'Prestação de serviços'},
    {'nome': 'Restaurante', 'descricao': 'Delivery e gestão de pedidos'},
    {'nome': 'Clínica de Estética', 'descricao': 'Agendamentos e procedimentos'},
    {'nome': 'CRM Vendas', 'descricao': 'Gestão de leads e vendas'},
]
for t in tipos:
    TipoLoja.objects.get_or_create(nome=t['nome'], defaults={'descricao': t['descricao']})

# Planos
planos = [
    {'nome': 'Básico', 'preco': 49.90, 'max': 3},
    {'nome': 'Profissional', 'preco': 99.90, 'max': 10},
    {'nome': 'Enterprise', 'preco': 199.90, 'max': 50},
]
for p in planos:
    PlanoAssinatura.objects.get_or_create(nome=p['nome'], defaults={'preco_mensal': p['preco'], 'max_usuarios': p['max']})

print("✅ Dados criados!")
exit()
```

---

### 3️⃣ Criar Lojas ⚠️ NECESSÁRIO

Acesse: https://lwksistemas.com.br/superadmin/login

1. Faça login com o superusuário criado
2. Crie lojas através do dashboard
3. Teste o acesso das lojas

**Guia completo**: `CRIAR_LOJAS_PRODUCAO.md`

**Nota**: As lojas Harmonis e Felix não existem em produção. Elas precisam ser criadas manualmente.

---

### 4️⃣ Configurar Domínio Personalizado (Opcional)

**Frontend (Vercel):**
```bash
vercel domains add seudominio.com.br
```

**Backend (Heroku):**
```bash
heroku domains:add api.seudominio.com.br -a lwksistemas
```

---

## 🌐 URLs Atuais

### Backend (Heroku) - ✅ FUNCIONANDO
- **API**: https://lwksistemas-38ad47519238.herokuapp.com/
- **Admin**: https://lwksistemas-38ad47519238.herokuapp.com/admin/

### Frontend (Vercel) - ✅ FUNCIONANDO
- **Home**: https://frontend-weld-sigma-25.vercel.app
- **SuperAdmin**: https://frontend-weld-sigma-25.vercel.app/superadmin/login
- **Suporte**: https://frontend-weld-sigma-25.vercel.app/suporte/login
- **Loja**: https://frontend-weld-sigma-25.vercel.app/loja/[slug]/login

---

## 📊 Arquitetura Atual

```
┌─────────────────────────────────────────┐
│  Frontend (Next.js)                     │
│  ✅ Vercel                              │
│  https://frontend-weld-sigma-25.vercel  │
│      .app                               │
└─────────────────┬───────────────────────┘
                  │
                  │ API Calls (HTTPS + CORS)
                  ▼
┌─────────────────────────────────────────┐
│  Backend (Django)                       │
│  ✅ Heroku                              │
│  https://lwksistemas-38ad47519238       │
│      .herokuapp.com                     │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  PostgreSQL Essential                   │
│  ✅ Heroku                              │
└─────────────────────────────────────────┘
```

---

## 💰 Custos

### Atual:
- Heroku Dyno: $5/mês
- PostgreSQL: $5/mês
- Vercel: **Grátis**
- **Total: $10/mês** 🎉

---

## ✅ Checklist Completo

### Backend
- [x] Deploy no Heroku
- [x] PostgreSQL configurado
- [x] Migrations executadas
- [x] API funcionando
- [ ] Superusuário criado
- [ ] Dados iniciais criados

### Frontend
- [x] Deploy na Vercel
- [x] Variável NEXT_PUBLIC_API_URL configurada
- [x] CORS configurado no backend
- [ ] Testado em produção

---

## 🎯 Ordem Recomendada

1. ✅ **Criar superusuário** (5 minutos)
2. ✅ **Criar dados iniciais** (5 minutos)
3. ✅ **Testar sistema completo** (10 minutos)

**Tempo total estimado: ~20 minutos**

---

## 📞 Precisa de Ajuda?

### Ver logs do backend:
```bash
heroku logs --tail -a lwksistemas
```

### Reiniciar backend:
```bash
heroku restart -a lwksistemas
```

### Ver status:
```bash
heroku ps -a lwksistemas
```

---

## 🎉 Quando Tudo Estiver Pronto

Você terá um sistema completo funcionando:

✅ Backend API no Heroku  
✅ Frontend Next.js na Vercel  
✅ PostgreSQL configurado  
✅ HTTPS automático  
✅ Sistema Multi-Tenant completo  
✅ CORS configurado

**Sistema profissional por apenas $10/mês!** 🚀

---

**Próximo passo recomendado:** Criar o superusuário! 👆

**Acesse o sistema:** https://frontend-weld-sigma-25.vercel.app
