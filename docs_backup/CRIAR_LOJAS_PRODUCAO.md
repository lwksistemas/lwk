# 🏪 Criar Lojas em Produção

## ⚠️ IMPORTANTE

As lojas **Harmonis** e **Felix** só existem no banco de dados LOCAL.

Em **PRODUÇÃO**, você precisa criar as lojas através do SuperAdmin.

---

## 📋 Situação Atual

### ✅ O que existe em PRODUÇÃO:
- Sistema deployado
- Banco PostgreSQL vazio (sem lojas)
- SuperAdmin (precisa criar usuário)
- Tipos de loja (precisam ser criados)
- Planos (precisam ser criados)

### ❌ O que NÃO existe em PRODUÇÃO:
- Loja Harmonis
- Loja Felix
- Nenhuma loja criada ainda

---

## 🎯 Como Criar Lojas em Produção

### Passo 1: Criar Superusuário

```bash
heroku run python manage.py createsuperuser -a lwksistemas
```

Preencha:
- Username: `superadmin`
- Email: `admin@lwksistemas.com`
- Password: (escolha uma senha forte)

---

### Passo 2: Criar Tipos de Loja e Planos

```bash
heroku run python manage.py shell -a lwksistemas
```

Cole este código:

```python
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
    tipo, created = TipoLoja.objects.get_or_create(
        nome=tipo_data['nome'],
        defaults={'descricao': tipo_data['descricao']}
    )
    if created:
        print(f"✅ Tipo criado: {tipo.nome}")
    else:
        print(f"ℹ️  Tipo já existe: {tipo.nome}")

# Criar planos
planos = [
    {'nome': 'Básico', 'preco': 49.90, 'max_usuarios': 3},
    {'nome': 'Profissional', 'preco': 99.90, 'max_usuarios': 10},
    {'nome': 'Enterprise', 'preco': 199.90, 'max_usuarios': 50},
]

for plano_data in planos:
    plano, created = PlanoAssinatura.objects.get_or_create(
        nome=plano_data['nome'],
        defaults={
            'preco_mensal': plano_data['preco'],
            'max_usuarios': plano_data['max_usuarios']
        }
    )
    if created:
        print(f"✅ Plano criado: {plano.nome}")
    else:
        print(f"ℹ️  Plano já existe: {plano.nome}")

print("\n✅ Dados iniciais criados!")
exit()
```

---

### Passo 3: Acessar SuperAdmin

1. Acesse: https://lwksistemas.com.br/superadmin/login
2. Faça login com o superusuário criado
3. Você verá o dashboard do SuperAdmin

---

### Passo 4: Criar Primeira Loja (Exemplo: Harmonis)

No dashboard do SuperAdmin:

1. Clique em **"Lojas"** no menu
2. Clique em **"Nova Loja"**
3. Preencha o formulário:

```
Nome da Loja: Harmonis
Slug: harmonis
Email do Proprietário: harmonis@example.com
Tipo de Loja: Clínica de Estética
Plano: Profissional
CPF/CNPJ: 12345678901
```

4. A senha provisória será gerada automaticamente
5. Clique em **"Criar Loja"**
6. A senha será exibida e enviada por email

---

### Passo 5: Criar Segunda Loja (Exemplo: Felix)

Repita o processo:

```
Nome da Loja: FELIX
Slug: felix
Email do Proprietário: felix@example.com
Tipo de Loja: CRM Vendas
Plano: Enterprise
CPF/CNPJ: 98765432100
```

---

### Passo 6: Testar Acesso das Lojas

Após criar as lojas, você pode acessar:

**Loja Harmonis**:
- URL: https://lwksistemas.com.br/loja/harmonis/login
- Email: harmonis@example.com
- Senha: (senha provisória gerada)

**Loja Felix**:
- URL: https://lwksistemas.com.br/loja/felix/login
- Email: felix@example.com
- Senha: (senha provisória gerada)

---

## 🔍 Como Funciona a Rota Dinâmica

### Rota: `/loja/[slug]/login`

A rota existe para **qualquer slug**, mas:

✅ **Se a loja existe**: Mostra o formulário de login  
❌ **Se a loja NÃO existe**: Mostra erro "Loja não encontrada"

### Exemplos:

```
https://lwksistemas.com.br/loja/harmonis/login
→ Se loja "harmonis" existe: ✅ Mostra login
→ Se loja "harmonis" NÃO existe: ❌ Erro 404

https://lwksistemas.com.br/loja/qualquer-coisa/login
→ Sempre mostra a página, mas valida se loja existe
```

---

## 📊 Fluxo Completo

```
1. Criar Superusuário
   ↓
2. Criar Tipos de Loja e Planos
   ↓
3. Acessar SuperAdmin
   ↓
4. Criar Nova Loja
   ↓
   - Sistema gera senha provisória
   - Sistema cria banco da loja
   - Sistema envia email
   ↓
5. Loja pode fazer login
   ↓
6. Primeiro acesso: Trocar senha
   ↓
7. Dashboard personalizado da loja
```

---

## ✅ Checklist de Produção

### Dados Iniciais
- [ ] Superusuário criado
- [ ] Tipos de loja criados (5 tipos)
- [ ] Planos criados (3 planos)

### Lojas de Teste
- [ ] Loja Harmonis criada
- [ ] Loja Felix criada
- [ ] Senhas provisórias anotadas
- [ ] Emails enviados

### Testes
- [ ] Login Harmonis funcionando
- [ ] Login Felix funcionando
- [ ] Dashboard Harmonis (Clínica)
- [ ] Dashboard Felix (CRM)
- [ ] Troca de senha funcionando

---

## 🎯 URLs Corretas

### Antes de Criar Lojas:
```
❌ https://lwksistemas.com.br/loja/harmonis/login
   → Erro: "Loja não encontrada"

❌ https://lwksistemas.com.br/loja/felix/login
   → Erro: "Loja não encontrada"
```

### Depois de Criar Lojas:
```
✅ https://lwksistemas.com.br/loja/harmonis/login
   → Formulário de login da Harmonis

✅ https://lwksistemas.com.br/loja/felix/login
   → Formulário de login da Felix
```

---

## 💡 Importante

1. **Lojas são criadas pelo SuperAdmin**, não existem por padrão
2. **Cada loja tem seu próprio banco de dados** isolado
3. **Slug deve ser único** (não pode ter duas lojas com mesmo slug)
4. **Senha provisória** é gerada automaticamente
5. **Email é enviado** automaticamente com as credenciais
6. **Primeiro acesso** obriga troca de senha

---

## 🚀 Comandos Rápidos

### Criar tudo de uma vez:

```bash
# 1. Criar superusuário
heroku run python manage.py createsuperuser -a lwksistemas

# 2. Criar dados iniciais
heroku run python manage.py shell -a lwksistemas
# Cole o código Python acima

# 3. Acessar SuperAdmin e criar lojas manualmente
# https://lwksistemas.com.br/superadmin/login
```

---

## 📝 Resumo

**Situação Atual**:
- ✅ Sistema deployado
- ✅ Domínio funcionando
- ❌ Nenhuma loja criada ainda

**Próximos Passos**:
1. Criar superusuário
2. Criar tipos e planos
3. Criar lojas via SuperAdmin
4. Testar acesso das lojas

**Tempo estimado**: 15 minutos

---

**Comece agora criando o superusuário!** 🚀

```bash
heroku run python manage.py createsuperuser -a lwksistemas
```
