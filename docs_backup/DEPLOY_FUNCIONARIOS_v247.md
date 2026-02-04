# 🚀 Deploy e Teste de Funcionários - v247

## 📦 Deploy Atual

**Backend**: v247 (Heroku)
**Frontend**: v245 (Vercel)

## 🔧 Comandos para Heroku

### 1. Verificar Loja "vida"
```bash
heroku run python manage.py shell -c "
from superadmin.models import Loja, User

# Verificar loja vida
try:
    loja = Loja.objects.get(slug='vida')
    print(f'✅ Loja: {loja.nome} (ID: {loja.id})')
    print(f'   Owner: {loja.owner.username} (ID: {loja.owner.id})')
    print(f'   Email: {loja.owner.email}')
    print(f'   Tipo: {loja.tipo_loja.nome}')
except Loja.DoesNotExist:
    print('❌ Loja vida não encontrada')
" --app lwksistemas
```

### 2. Redefinir Senha do Owner
```bash
heroku run python manage.py shell -c "
from superadmin.models import Loja

loja = Loja.objects.get(slug='vida')
user = loja.owner

print(f'🔑 Redefinindo senha para: {user.username}')
user.set_password('123456')
user.senha_foi_alterada = False
user.save()
print('✅ Senha: 123456 (trocar obrigatória)')
" --app lwksistemas
```

### 3. Verificar Funcionários da Loja
```bash
heroku run python manage.py shell -c "
from superadmin.models import Loja
from clinica_estetica.models import Funcionario

loja = Loja.objects.get(slug='vida')
funcionarios = Funcionario.objects.all_without_filter().filter(loja_id=loja.id)

print(f'👥 Funcionários da loja {loja.nome}:')
print(f'   Total: {funcionarios.count()}')
for func in funcionarios:
    admin = '👤 ADMIN' if func.is_admin else ''
    print(f'   - {func.nome} ({func.email}) {admin}')
" --app lwksistemas
```

### 4. Criar Funcionário Admin (se não existir)
```bash
heroku run python manage.py shell -c "
from superadmin.models import Loja
from clinica_estetica.models import Funcionario

loja = Loja.objects.get(slug='vida')
owner = loja.owner

# Verificar se já existe
if Funcionario.objects.all_without_filter().filter(loja_id=loja.id, email=owner.email).exists():
    print('ℹ️ Funcionário já existe')
    func = Funcionario.objects.all_without_filter().get(loja_id=loja.id, email=owner.email)
    func.is_admin = True
    func.save()
    print('✅ Atualizado para admin')
else:
    func = Funcionario.objects.create(
        nome=owner.get_full_name() or owner.username,
        email=owner.email,
        telefone='',
        cargo='Administrador',
        is_admin=True,
        loja_id=loja.id
    )
    print(f'✅ Funcionário criado: {func.nome}')
" --app lwksistemas
```

### 5. Limpar Sessões Antigas
```bash
heroku run python manage.py shell -c "
from superadmin.models import UserSession, Loja

loja = Loja.objects.get(slug='vida')
user = loja.owner

sessoes = UserSession.objects.filter(user=user)
count = sessoes.count()
sessoes.delete()
print(f'🗑️ {count} sessões deletadas')
" --app lwksistemas
```

### 6. Ver Logs em Tempo Real
```bash
heroku logs --tail --app lwksistemas
```

## 🧪 Passo a Passo para Testar

### Preparação (Executar UMA VEZ)
```bash
# 1. Verificar loja
heroku run python manage.py shell -c "
from superadmin.models import Loja
loja = Loja.objects.get(slug='vida')
print(f'Loja: {loja.nome} (ID: {loja.id})')
print(f'Owner: {loja.owner.username}')
print(f'Email: {loja.owner.email}')
" --app lwksistemas

# 2. Redefinir senha
heroku run python manage.py shell -c "
from superadmin.models import Loja
loja = Loja.objects.get(slug='vida')
loja.owner.set_password('123456')
loja.owner.senha_foi_alterada = False
loja.owner.save()
print('Senha: 123456')
" --app lwksistemas

# 3. Verificar/criar funcionário
heroku run python manage.py shell -c "
from superadmin.models import Loja
from clinica_estetica.models import Funcionario

loja = Loja.objects.get(slug='vida')
funcionarios = Funcionario.objects.all_without_filter().filter(loja_id=loja.id)
print(f'Funcionários: {funcionarios.count()}')
for f in funcionarios:
    print(f'  {f.nome} - Admin: {f.is_admin}')
" --app lwksistemas

# 4. Limpar sessões
heroku run python manage.py shell -c "
from superadmin.models import UserSession, Loja
loja = Loja.objects.get(slug='vida')
UserSession.objects.filter(user=loja.owner).delete()
print('Sessões limpas')
" --app lwksistemas
```

### Teste no Navegador

1. **Limpar cache do navegador:**
   - Pressionar `Ctrl+Shift+Delete`
   - Selecionar "Cookies e dados de sites"
   - Limpar

2. **Limpar localStorage:**
   - Abrir DevTools (F12)
   - Console: `localStorage.clear()`
   - Recarregar página

3. **Fazer login:**
   - URL: https://lwksistemas.com.br/loja/vida/login
   - Email: (verificar no comando 1)
   - Senha: 123456

4. **Trocar senha:**
   - Sistema vai pedir para trocar senha
   - Definir nova senha

5. **Acessar dashboard:**
   - Clicar em "Funcionários" nas Ações Rápidas
   - Verificar se aparece o funcionário admin

6. **Verificar Network:**
   - Abrir DevTools (F12)
   - Aba Network
   - Clicar em "Funcionários"
   - Ver request para `/api/clinica/funcionarios/`
   - Verificar Headers: `X-Loja-ID: 72`

## 🔍 Troubleshooting

### Erro: "Usuário não encontrado"
**Causa**: Token antigo de usuário deletado
**Solução**:
```bash
# Limpar localStorage
localStorage.clear()

# Limpar sessões no Heroku
heroku run python manage.py shell -c "
from superadmin.models import UserSession
UserSession.objects.all().delete()
print('Todas as sessões limpas')
" --app lwksistemas
```

### Erro: "Nenhum funcionário cadastrado"
**Causa**: X-Loja-ID não está sendo enviado ou funcionário não foi criado
**Solução**:
```bash
# Verificar funcionários
heroku run python manage.py shell -c "
from clinica_estetica.models import Funcionario
funcionarios = Funcionario.objects.all_without_filter().filter(loja_id=72)
print(f'Total: {funcionarios.count()}')
for f in funcionarios:
    print(f'{f.nome} - {f.email} - Admin: {f.is_admin}')
" --app lwksistemas

# Se não houver funcionários, criar:
heroku run python manage.py shell -c "
from superadmin.models import Loja
from clinica_estetica.models import Funcionario

loja = Loja.objects.get(id=72)
owner = loja.owner

Funcionario.objects.create(
    nome=owner.get_full_name() or owner.username,
    email=owner.email,
    telefone='',
    cargo='Administrador',
    is_admin=True,
    loja_id=loja.id
)
print('Funcionário criado')
" --app lwksistemas
```

### Erro: "Loja não encontrada"
**Causa**: Slug incorreto ou loja não existe
**Solução**:
```bash
# Listar todas as lojas
heroku run python manage.py shell -c "
from superadmin.models import Loja
lojas = Loja.objects.all()
print('Lojas no sistema:')
for loja in lojas:
    print(f'  {loja.nome} - Slug: {loja.slug} - ID: {loja.id}')
" --app lwksistemas
```

## 📊 Verificação Final

Após executar os comandos e fazer login, você deve ver:

1. ✅ Login bem-sucedido
2. ✅ Redirecionamento para trocar senha
3. ✅ Dashboard carregado
4. ✅ Botão "Funcionários" visível
5. ✅ Modal com lista de funcionários
6. ✅ Funcionário admin com badge "👤 Administrador"
7. ✅ Logs do Heroku mostrando `X-Loja-ID: 72`

## 🎯 Comandos Rápidos

```bash
# Ver informações da loja
heroku run python manage.py shell -c "from superadmin.models import Loja; l=Loja.objects.get(slug='vida'); print(f'{l.nome} - ID:{l.id} - Owner:{l.owner.username}')" --app lwksistemas

# Redefinir senha
heroku run python manage.py shell -c "from superadmin.models import Loja; l=Loja.objects.get(slug='vida'); l.owner.set_password('123456'); l.owner.save(); print('OK')" --app lwksistemas

# Ver funcionários
heroku run python manage.py shell -c "from clinica_estetica.models import Funcionario; [print(f'{f.nome} - Admin:{f.is_admin}') for f in Funcionario.objects.all_without_filter().filter(loja_id=72)]" --app lwksistemas

# Limpar sessões
heroku run python manage.py shell -c "from superadmin.models import UserSession; UserSession.objects.all().delete(); print('OK')" --app lwksistemas
```
