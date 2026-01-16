# 🚀 Deploy Rápido - LWK Sistemas no Heroku

## ⚡ Opção 1: Script Automatizado (RECOMENDADO)

### Passo 1: Fazer login no Heroku
```bash
heroku login
```
**Isso abrirá o navegador. Faça login e volte ao terminal.**

### Passo 2: Executar script de deploy
```bash
./deploy_heroku_completo.sh
```

**Pronto! O script fará tudo automaticamente.**

---

## 📝 Opção 2: Comandos Manuais

Se preferir executar passo a passo, siga os comandos abaixo:

### 1. Login
```bash
heroku login
```

### 2. Criar/Conectar App
```bash
heroku create lwksistemas
# OU se já existe:
heroku git:remote -a lwksistemas
```

### 3. Adicionar PostgreSQL
```bash
heroku addons:create heroku-postgresql:essential-0 -a lwksistemas
```

### 4. Configurar Variáveis
```bash
heroku config:set SECRET_KEY="django-insecure-$(openssl rand -base64 32)" -a lwksistemas
heroku config:set DJANGO_SETTINGS_MODULE=config.settings_production -a lwksistemas
heroku config:set DEBUG=False -a lwksistemas
heroku config:set ALLOWED_HOSTS=lwksistemas.herokuapp.com -a lwksistemas
heroku config:set EMAIL_HOST_USER=lwksistemas@gmail.com -a lwksistemas
heroku config:set EMAIL_HOST_PASSWORD="cabbshvjjbcjagzh" -a lwksistemas
```

### 5. Deploy
```bash
git add .
git commit -m "Deploy LWK Sistemas"
git push heroku master
```

### 6. Migrations
```bash
heroku run python manage.py migrate -a lwksistemas
```

### 7. Criar Superusuário
```bash
heroku run python manage.py createsuperuser -a lwksistemas
```

---

## 🎯 Após o Deploy

### Criar Dados Iniciais
```bash
heroku run python manage.py shell -a lwksistemas
```

Cole no shell:
```python
from superadmin.models import TipoLoja, PlanoAssinatura

# Tipos de Loja
tipos = [
    {'nome': 'E-commerce', 'descricao': 'Loja virtual'},
    {'nome': 'Serviços', 'descricao': 'Prestação de serviços'},
    {'nome': 'Restaurante', 'descricao': 'Delivery'},
    {'nome': 'Clínica de Estética', 'descricao': 'Agendamentos'},
    {'nome': 'CRM Vendas', 'descricao': 'Gestão de vendas'},
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

## 🔍 Comandos Úteis

```bash
# Ver logs
heroku logs --tail -a lwksistemas

# Abrir app
heroku open -a lwksistemas

# Status
heroku ps -a lwksistemas

# Info do banco
heroku pg:info -a lwksistemas

# Reiniciar
heroku restart -a lwksistemas

# Ver variáveis
heroku config -a lwksistemas
```

---

## 🌐 URLs do Sistema

- **Sistema**: https://lwksistemas.herokuapp.com
- **Admin**: https://lwksistemas.herokuapp.com/admin/
- **API**: https://lwksistemas.herokuapp.com/api/

---

## 💰 Custo

- Dyno Eco: $5/mês
- PostgreSQL Essential: $5/mês
- **Total: $10/mês**

---

## 🐛 Problemas?

### Erro no deploy
```bash
heroku logs --tail -a lwksistemas
```

### Resetar banco (CUIDADO!)
```bash
heroku pg:reset DATABASE_URL -a lwksistemas --confirm lwksistemas
heroku run python manage.py migrate -a lwksistemas
```

---

## ✅ Checklist

- [ ] Login no Heroku
- [ ] App criado/conectado
- [ ] PostgreSQL adicionado
- [ ] Variáveis configuradas
- [ ] Deploy realizado
- [ ] Migrations executadas
- [ ] Superusuário criado
- [ ] Dados iniciais criados
- [ ] Sistema testado

---

**🎉 Sistema no ar em: https://lwksistemas.herokuapp.com**
