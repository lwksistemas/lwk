# 🚀 Criar Loja Completa do Zero

## Situação Atual
Todas as lojas foram excluídas e você precisa criar uma nova do zero.

## Passo 1: Limpar Tokens Antigos

### No Navegador (Console F12)
```javascript
localStorage.clear();
sessionStorage.clear();
location.reload();
```

### Ou usar Aba Anônima
- Chrome: Ctrl + Shift + N
- Firefox: Ctrl + Shift + P

## Passo 2: Criar Superadmin (se necessário)

```bash
heroku run python backend/manage.py shell
```

```python
from django.contrib.auth.models import User

# Verificar se já existe algum superadmin
admins = User.objects.filter(is_superuser=True)
print(f"Superadmins existentes: {admins.count()}")

if admins.count() == 0:
    # Criar novo superadmin
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@exemplo.com',
        password='Admin@123'  # TROCAR DEPOIS!
    )
    print(f"✅ Superadmin criado: {admin.username}")
else:
    print("✅ Já existe superadmin")
    for a in admins:
        print(f"  - {a.username} ({a.email})")
```

## Passo 3: Criar Tipo de Loja (se não existir)

```python
from superadmin.models import TipoLoja

# Verificar tipos existentes
tipos = TipoLoja.objects.all()
print(f"Tipos de loja: {tipos.count()}")

if tipos.count() == 0:
    # Criar tipo Clínica de Estética
    tipo = TipoLoja.objects.create(
        nome='Clínica de Estética',
        descricao='Sistema completo para clínicas de estética',
        cor_primaria='#EC4899',
        cor_secundaria='#F472B6'
    )
    print(f"✅ Tipo criado: {tipo.nome}")
else:
    print("✅ Tipos existentes:")
    for t in tipos:
        print(f"  - {t.nome}")
```

## Passo 4: Criar Plano (se não existir)

```python
from superadmin.models import Plano

# Verificar planos existentes
planos = Plano.objects.all()
print(f"Planos: {planos.count()}")

if planos.count() == 0:
    # Criar plano básico
    plano = Plano.objects.create(
        nome='Básico',
        descricao='Plano básico',
        preco_mensal=99.90,
        max_usuarios=5,
        max_produtos=100,
        is_active=True
    )
    print(f"✅ Plano criado: {plano.nome}")
else:
    print("✅ Planos existentes:")
    for p in planos:
        print(f"  - {p.nome} (R$ {p.preco_mensal})")
```

## Passo 5: Criar Usuário Proprietário da Loja

```python
from django.contrib.auth.models import User

# Criar usuário para ser dono da loja
owner = User.objects.create_user(
    username='felipe',
    email='financeiroluiz@hotmail.com',
    password='Senha@123',  # TROCAR DEPOIS!
    first_name='Felipe',
    last_name='Silva'
)
print(f"✅ Usuário criado: {owner.username}")
```

## Passo 6: Criar Loja (Signal vai criar funcionário automaticamente!)

```python
from superadmin.models import Loja, TipoLoja, Plano
from django.contrib.auth.models import User

# Buscar dados necessários
tipo = TipoLoja.objects.first()
plano = Plano.objects.first()
owner = User.objects.get(username='felipe')

# Criar loja
loja = Loja.objects.create(
    nome='Clínica Bella',
    slug='clinica-bella',  # Será usado na URL
    tipo_loja=tipo,
    plano=plano,
    owner=owner,
    is_active=True
)

print(f"✅ Loja criada: {loja.nome}")
print(f"   ID: {loja.id}")
print(f"   Slug: {loja.slug}")
print(f"   URL: https://lwksistemas.com.br/loja/{loja.slug}/dashboard")
```

## Passo 7: Verificar se Funcionário foi Criado

```python
from clinica_estetica.models import Funcionario

# Buscar funcionários da loja (bypass do manager)
funcionarios = Funcionario.objects.all_without_filter().filter(loja_id=loja.id)
print(f"\n📋 Funcionários da loja: {funcionarios.count()}")

for func in funcionarios:
    print(f"  ✅ {func.nome}")
    print(f"     Email: {func.email}")
    print(f"     Cargo: {func.cargo}")
    print(f"     Admin: {func.is_admin}")
    print(f"     Loja ID: {func.loja_id}")
```

## Passo 8: Acessar a Loja

1. **Fazer logout do superadmin** (se estiver logado)

2. **Acessar URL da loja**:
```
https://lwksistemas.com.br/loja/clinica-bella/login
```

3. **Fazer login**:
- Email: financeiroluiz@hotmail.com
- Senha: Senha@123

4. **Clicar em "Funcionários"** (botão rosa 👥)

5. **Verificar**:
- Funcionário "Felipe Silva" aparece
- Badge "👤 Administrador" visível
- Botão "Excluir" não aparece

## Script Completo (Copiar e Colar)

```python
from django.contrib.auth.models import User
from superadmin.models import TipoLoja, Plano, Loja
from clinica_estetica.models import Funcionario

# 1. Criar superadmin (se necessário)
if not User.objects.filter(is_superuser=True).exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@exemplo.com',
        password='Admin@123'
    )
    print(f"✅ Superadmin: {admin.username}")

# 2. Criar tipo de loja (se necessário)
tipo, created = TipoLoja.objects.get_or_create(
    nome='Clínica de Estética',
    defaults={
        'descricao': 'Sistema completo para clínicas de estética',
        'cor_primaria': '#EC4899',
        'cor_secundaria': '#F472B6'
    }
)
print(f"✅ Tipo: {tipo.nome}")

# 3. Criar plano (se necessário)
plano, created = Plano.objects.get_or_create(
    nome='Básico',
    defaults={
        'descricao': 'Plano básico',
        'preco_mensal': 99.90,
        'max_usuarios': 5,
        'max_produtos': 100,
        'is_active': True
    }
)
print(f"✅ Plano: {plano.nome}")

# 4. Criar usuário proprietário
owner, created = User.objects.get_or_create(
    username='felipe',
    defaults={
        'email': 'financeiroluiz@hotmail.com',
        'first_name': 'Felipe',
        'last_name': 'Silva'
    }
)
if created:
    owner.set_password('Senha@123')
    owner.save()
print(f"✅ Owner: {owner.username}")

# 5. Criar loja (signal cria funcionário automaticamente!)
loja, created = Loja.objects.get_or_create(
    slug='clinica-bella',
    defaults={
        'nome': 'Clínica Bella',
        'tipo_loja': tipo,
        'plano': plano,
        'owner': owner,
        'is_active': True
    }
)
print(f"✅ Loja: {loja.nome} (ID: {loja.id})")

# 6. Verificar funcionário
funcionarios = Funcionario.objects.all_without_filter().filter(loja_id=loja.id)
print(f"\n📋 Funcionários: {funcionarios.count()}")
for func in funcionarios:
    print(f"  ✅ {func.nome} - Admin: {func.is_admin}")

print(f"\n🌐 URL: https://lwksistemas.com.br/loja/{loja.slug}/dashboard")
print(f"🔑 Login: {owner.email} / Senha@123")
```

## Resultado Esperado

```
✅ Superadmin: admin
✅ Tipo: Clínica de Estética
✅ Plano: Básico
✅ Owner: felipe
✅ Loja: Clínica Bella (ID: 1)

📋 Funcionários: 1
  ✅ Felipe Silva - Admin: True

🌐 URL: https://lwksistemas.com.br/loja/clinica-bella/dashboard
🔑 Login: financeiroluiz@hotmail.com / Senha@123
```

## Troubleshooting

### Erro: "Usuário 68 não encontrado"
- **Causa**: Tokens antigos no navegador
- **Solução**: Limpar localStorage ou usar aba anônima

### Erro: "Loja não encontrada"
- **Causa**: Slug incorreto ou loja não existe
- **Solução**: Verificar slug no banco de dados

### Funcionário não foi criado
- **Causa**: Signal não executou
- **Solução**: Verificar logs do Heroku ou criar manualmente

### Não consigo fazer login
- **Causa**: Senha incorreta ou usuário não existe
- **Solução**: Resetar senha via shell
