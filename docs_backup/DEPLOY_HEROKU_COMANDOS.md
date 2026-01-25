# 🚀 Deploy LWK Sistemas no Heroku - Guia Passo a Passo

## ⚠️ IMPORTANTE: Execute estes comandos no seu terminal

Este documento contém todos os comandos necessários para fazer o deploy.
Copie e cole cada comando no terminal, um por vez.

---

## 📋 Passo 1: Login no Heroku

**IMPORTANTE: Execute este comando no seu terminal (não aqui no chat)**

```bash
heroku login
```

**O que vai acontecer:**
1. O comando vai gerar um link único (válido por alguns minutos)
2. Seu navegador vai abrir automaticamente
3. Faça login na página do Heroku
4. Após o login, volte ao terminal
5. Você verá a mensagem: "Logged in as seu-email@exemplo.com"

**Se o navegador não abrir automaticamente:**
- Copie o link que aparece no terminal
- Cole no navegador
- Faça login
- Volte ao terminal

**Após fazer login com sucesso, continue para o Passo 2.**

---

## 📋 Passo 2: Verificar/Criar App no Heroku

### Opção A: Se o app já existe
```bash
heroku git:remote -a lwksistemas
```

### Opção B: Se precisa criar o app
```bash
heroku create lwksistemas
```

---

## 📋 Passo 3: Adicionar PostgreSQL

```bash
heroku addons:create heroku-postgresql:essential-0 -a lwksistemas
```

**Custo**: $5/mês (plano Essential)

**Aguarde ~2 minutos para o banco ser provisionado**

---

## 📋 Passo 4: Configurar Variáveis de Ambiente

### 4.1 - Secret Key (Gerar nova)
```bash
heroku config:set SECRET_KEY="django-insecure-$(openssl rand -base64 32)" -a lwksistemas
```

### 4.2 - Django Settings
```bash
heroku config:set DJANGO_SETTINGS_MODULE=config.settings_production -a lwksistemas
```

### 4.3 - Debug (Produção)
```bash
heroku config:set DEBUG=False -a lwksistemas
```

### 4.4 - Allowed Hosts
```bash
heroku config:set ALLOWED_HOSTS=lwksistemas.herokuapp.com -a lwksistemas
```

### 4.5 - Email (Gmail)
```bash
heroku config:set EMAIL_HOST_USER=lwksistemas@gmail.com -a lwksistemas
heroku config:set EMAIL_HOST_PASSWORD="cabbshvjjbcjagzh" -a lwksistemas
```

### 4.6 - CORS (se frontend separado)
```bash
heroku config:set CORS_ORIGINS=https://lwksistemas.vercel.app -a lwksistemas
```

### 4.7 - Verificar todas as variáveis
```bash
heroku config -a lwksistemas
```

---

## 📋 Passo 5: Preparar Arquivos para Deploy

### 5.1 - Adicionar novos arquivos ao Git
```bash
git add .
git commit -m "Preparando deploy para Heroku - LWK Sistemas"
```

### 5.2 - Verificar branch
```bash
git branch
```

Se estiver em `master`, está correto. Se estiver em `main`, use `main` nos comandos.

---

## 📋 Passo 6: Deploy!

```bash
git push heroku master
```

**OU se sua branch é main:**
```bash
git push heroku main
```

**Aguarde o build (~3-5 minutos)**

Você verá mensagens como:
- "Building source"
- "Installing dependencies"
- "Collecting static files"
- "Launching..."

---

## 📋 Passo 7: Executar Migrations

```bash
heroku run python manage.py migrate -a lwksistemas
```

---

## 📋 Passo 8: Criar Superusuário

```bash
heroku run python manage.py createsuperuser -a lwksistemas
```

**Dados sugeridos:**
- Username: `superadmin`
- Email: `admin@lwksistemas.com`
- Password: (escolha uma senha forte)

---

## 📋 Passo 9: Coletar Arquivos Estáticos

```bash
heroku run python manage.py collectstatic --noinput -a lwksistemas
```

---

## 📋 Passo 10: Verificar Deploy

### Ver logs em tempo real:
```bash
heroku logs --tail -a lwksistemas
```

### Abrir aplicação:
```bash
heroku open -a lwksistemas
```

### Verificar status:
```bash
heroku ps -a lwksistemas
```

### Verificar banco de dados:
```bash
heroku pg:info -a lwksistemas
```

---

## 📋 Passo 11: Criar Dados Iniciais

```bash
heroku run python manage.py shell -a lwksistemas
```

**Cole este código no shell Python:**

```python
from django.contrib.auth.models import User, Group
from superadmin.models import TipoLoja, PlanoAssinatura

# Criar tipos de loja
tipos = [
    {'nome': 'E-commerce', 'descricao': 'Loja virtual de produtos'},
    {'nome': 'Serviços', 'descricao': 'Prestação de serviços'},
    {'nome': 'Restaurante', 'descricao': 'Delivery e gestão de pedidos'},
    {'nome': 'Clínica de Estética', 'descricao': 'Agendamentos e procedimentos'},
    {'nome': 'CRM Vendas', 'descricao': 'Gestão de leads e vendas'},
]

for tipo_data in tipos:
    TipoLoja.objects.get_or_create(
        nome=tipo_data['nome'],
        defaults={'descricao': tipo_data['descricao']}
    )

# Criar planos
planos = [
    {'nome': 'Básico', 'preco': 49.90, 'max_usuarios': 3},
    {'nome': 'Profissional', 'preco': 99.90, 'max_usuarios': 10},
    {'nome': 'Enterprise', 'preco': 199.90, 'max_usuarios': 50},
]

for plano_data in planos:
    PlanoAssinatura.objects.get_or_create(
        nome=plano_data['nome'],
        defaults={
            'preco_mensal': plano_data['preco'],
            'max_usuarios': plano_data['max_usuarios']
        }
    )

print("✅ Dados iniciais criados!")
exit()
```

---

## 🔍 Comandos Úteis

### Ver todas as variáveis de ambiente:
```bash
heroku config
```

### Editar variável:
```bash
heroku config:set NOME_VARIAVEL=valor
```

### Remover variável:
```bash
heroku config:unset NOME_VARIAVEL
```

### Reiniciar aplicação:
```bash
heroku restart
```

### Acessar console Python:
```bash
heroku run python backend/manage.py shell
```

### Acessar banco de dados:
```bash
heroku pg:psql
```

### Ver informações do dyno:
```bash
heroku ps:scale
```

### Escalar dynos (se necessário):
```bash
heroku ps:scale web=1
```

---

## 🌐 URLs do Sistema

Após o deploy, seu sistema estará disponível em:

- **Backend API**: https://lwksistemas.herokuapp.com/api/
- **Admin Django**: https://lwksistemas.herokuapp.com/admin/
- **SuperAdmin Login**: https://lwksistemas.herokuapp.com/api/superadmin/login/
- **Suporte Login**: https://lwksistemas.herokuapp.com/api/suporte/login/
- **Loja Login**: https://lwksistemas.herokuapp.com/api/lojas/{slug}/login/

---

## 🐛 Troubleshooting

### Erro: "Application Error"
```bash
heroku logs --tail
```
Verifique os logs para identificar o erro.

### Erro: "Database connection failed"
```bash
heroku pg:info
heroku config:get DATABASE_URL
```

### Erro: "Module not found"
```bash
heroku run pip list
```
Verifique se todas as dependências estão instaladas.

### Erro: "Static files not found"
```bash
heroku run python backend/manage.py collectstatic --noinput
```

### Resetar banco de dados (CUIDADO!)
```bash
heroku pg:reset DATABASE_URL
heroku run python backend/manage.py migrate
```

---

## 💰 Custos Mensais

- **Dyno Eco**: $5/mês
- **PostgreSQL Essential**: $5/mês
- **Total**: **$10/mês**

---

## 📊 Monitoramento

### Dashboard Heroku:
https://dashboard.heroku.com/apps/lwksistemas

### Métricas:
```bash
heroku ps
heroku pg:info
heroku logs --tail
```

---

## 🔐 Segurança

✅ SECRET_KEY único gerado
✅ DEBUG=False em produção
✅ HTTPS automático (Heroku)
✅ PostgreSQL com SSL
✅ CORS configurado
✅ Senhas fortes obrigatórias

---

## ✅ Checklist Final

- [ ] Login no Heroku realizado
- [ ] App conectado
- [ ] PostgreSQL adicionado
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy realizado
- [ ] Migrations executadas
- [ ] Superusuário criado
- [ ] Arquivos estáticos coletados
- [ ] Dados iniciais criados
- [ ] Sistema testado e funcionando

---

## 🎉 Sistema Pronto!

Seu sistema **LWK Sistemas** está no ar em:
**https://lwksistemas.herokuapp.com**

Para acessar o admin:
**https://lwksistemas.herokuapp.com/admin**

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs: `heroku logs --tail`
2. Verifique o status: `heroku ps`
3. Verifique o banco: `heroku pg:info`

**Boa sorte com o deploy! 🚀**
