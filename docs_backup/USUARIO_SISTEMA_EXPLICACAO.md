# Explicação: Usuários do Sistema

## Problema Identificado

O usuário "luiz" foi criado via `python manage.py createsuperuser`, mas não aparecia na página de usuários do sistema (`/superadmin/usuarios`).

## Causa

O sistema tem dois tipos de usuários:

1. **User (Django)** - Tabela padrão do Django para autenticação
2. **UsuarioSistema** - Tabela customizada com informações adicionais (tipo, permissões, etc)

Quando você cria um usuário via `createsuperuser`, ele cria apenas o **User**, mas não o **UsuarioSistema**.

A página `/superadmin/usuarios` busca dados da tabela **UsuarioSistema**, por isso o usuário "luiz" não aparecia.

## Solução Aplicada

Foi criado um registro `UsuarioSistema` para o usuário "luiz" via shell do Django:

```python
from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema

user = User.objects.get(username='luiz')

usuario_sistema = UsuarioSistema.objects.create(
    user=user,
    tipo='superadmin',
    pode_criar_lojas=True,
    pode_gerenciar_financeiro=True,
    pode_acessar_todas_lojas=True,
    is_active=True
)
```

## Como Evitar no Futuro

### Opção 1: Usar a Interface Web (Recomendado)

Sempre criar usuários através da interface web em `/superadmin/usuarios`:
- Acesse https://lwksistemas.com.br/superadmin/usuarios
- Clique em "+ Novo Usuário"
- Preencha os dados
- O sistema cria automaticamente tanto o User quanto o UsuarioSistema

### Opção 2: Usar o Script Criado

Se você criar um usuário via `createsuperuser`, use o script para criar o UsuarioSistema:

```bash
# Local
cd backend
source venv/bin/activate
python criar_usuario_sistema.py <username> superadmin

# Heroku
heroku run "cd backend && python criar_usuario_sistema.py <username> superadmin" -a lwksistemas
```

**Exemplo:**
```bash
python criar_usuario_sistema.py luiz superadmin
```

### Opção 3: Via Shell do Django

```bash
# Local
cd backend
source venv/bin/activate
python manage.py shell

# Heroku
heroku run "cd backend && python manage.py shell" -a lwksistemas
```

Depois execute:
```python
from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema

user = User.objects.get(username='SEU_USERNAME')

UsuarioSistema.objects.create(
    user=user,
    tipo='superadmin',  # ou 'suporte'
    pode_criar_lojas=True,
    pode_gerenciar_financeiro=True,
    pode_acessar_todas_lojas=True,
    is_active=True
)
```

## Estrutura do UsuarioSistema

```python
class UsuarioSistema(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Tipo
    tipo = models.CharField(max_length=20, choices=[
        ('superadmin', 'Super Admin'),
        ('suporte', 'Suporte'),
    ])
    
    # Informações adicionais
    telefone = models.CharField(max_length=20, blank=True)
    foto = models.URLField(blank=True)
    
    # Permissões específicas
    pode_criar_lojas = models.BooleanField(default=False)
    pode_gerenciar_financeiro = models.BooleanField(default=False)
    pode_acessar_todas_lojas = models.BooleanField(default=False)
    
    # Lojas que pode acessar (para suporte)
    lojas_acesso = models.ManyToManyField(Loja, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Tipos de Usuário

### Super Admin
- Acesso total ao sistema
- Pode criar/editar/excluir lojas
- Pode gerenciar financeiro
- Pode acessar todas as lojas
- Pode criar outros usuários

### Suporte
- Acesso limitado
- Pode atender chamados
- Pode acessar apenas lojas específicas (configurável)
- Não pode criar lojas ou gerenciar financeiro (por padrão)

## Verificar Usuários Existentes

### Via Interface Web
Acesse: https://lwksistemas.com.br/superadmin/usuarios

### Via Shell
```python
from superadmin.models import UsuarioSistema

# Listar todos
for u in UsuarioSistema.objects.all():
    print(f"{u.user.username} - {u.get_tipo_display()} - Ativo: {u.is_active}")

# Contar por tipo
print(f"Super Admins: {UsuarioSistema.objects.filter(tipo='superadmin').count()}")
print(f"Suporte: {UsuarioSistema.objects.filter(tipo='suporte').count()}")
```

## Status Atual

✅ Usuário "luiz" agora tem UsuarioSistema criado
✅ Aparece na página /superadmin/usuarios
✅ Tipo: Super Admin
✅ Permissões: Todas (criar lojas, gerenciar financeiro, acessar todas lojas)

---

**Data:** 16/01/2026
**Sistema:** https://lwksistemas.com.br
