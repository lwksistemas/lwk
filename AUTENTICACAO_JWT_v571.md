# 🔐 SISTEMA DE AUTENTICAÇÃO JWT - CLÍNICA DA BELEZA

**Data:** 11/02/2026  
**Versão Backend:** v571 (aguardando deploy)  
**Base URL:** `https://lwksistemas.com.br/api/clinica-beleza/auth/`

---

## 🎯 SISTEMA IMPLEMENTADO

### ✅ Autenticação JWT
- Login com username/password
- Token JWT com informações do cargo
- Refresh token
- Logout com blacklist

### ✅ 3 Perfis/Cargos
1. **Admin** - Acesso total
2. **Recepção** - Gerenciar agenda e pacientes
3. **Profissional** - Ver apenas seus agendamentos

### ✅ Permissões no Backend
- Decoradores de permissão por cargo
- Validação em cada endpoint
- Proteção de rotas sensíveis

---

## 👥 CARGOS E PERMISSÕES

### 🔑 Administrador (admin)
**Pode:**
- ✅ Gerenciar todos os agendamentos
- ✅ Ver informações financeiras
- ✅ Gerenciar usuários
- ✅ Gerenciar pacientes
- ✅ Gerenciar profissionais
- ✅ Gerenciar procedimentos
- ✅ Acessar todas as funcionalidades

**Credenciais de Teste:**
- Usuário: `admin`
- Senha: `admin123`

---

### 📋 Recepção (recepcao)
**Pode:**
- ✅ Gerenciar agendamentos (criar, editar, deletar)
- ✅ Gerenciar pacientes
- ✅ Ver profissionais
- ✅ Ver procedimentos
- ❌ Ver informações financeiras
- ❌ Gerenciar usuários

**Credenciais de Teste:**
- Usuário: `recepcao`
- Senha: `recepcao123`

---

### 👩‍⚕️ Profissional (profissional)
**Pode:**
- ✅ Ver apenas SEUS agendamentos
- ✅ Atualizar status dos seus agendamentos
- ❌ Ver agendamentos de outros profissionais
- ❌ Criar/deletar agendamentos
- ❌ Ver informações financeiras
- ❌ Gerenciar pacientes

**Credenciais de Teste:**
- Usuário: `dra.ana` / `dra.julia` / `dra.fernanda`
- Senha: `prof123`

---

## 📡 ENDPOINTS DA API

### 1. Login
**POST** `/api/clinica-beleza/auth/login/`

**Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@clinica.com",
    "first_name": "Admin",
    "last_name": "Sistema",
    "cargo": "admin",
    "cargo_display": "Administrador",
    "is_admin": true,
    "is_recepcao": true,
    "is_profissional": false
  }
}
```

---

### 2. Refresh Token
**POST** `/api/clinica-beleza/auth/refresh/`

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 3. Informações do Usuário
**GET** `/api/clinica-beleza/auth/me/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@clinica.com",
  "first_name": "Admin",
  "last_name": "Sistema",
  "cargo": "admin",
  "cargo_display": "Administrador",
  "is_admin": true,
  "is_recepcao": true,
  "is_profissional": false,
  "professional_info": null
}
```

---

### 4. Verificar Permissões
**GET** `/api/clinica-beleza/auth/permissions/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "is_admin": true,
  "is_recepcao": true,
  "is_profissional": false,
  "cargo": "admin",
  "can_manage_appointments": true,
  "can_view_financial": true,
  "can_manage_users": true
}
```

---

### 5. Logout
**POST** `/api/clinica-beleza/auth/logout/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "message": "Logout realizado com sucesso"
}
```

---

### 6. Listar Usuários (Admin)
**GET** `/api/clinica-beleza/auth/users/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Permissão:** Apenas Admin

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@clinica.com",
    "first_name": "Admin",
    "last_name": "Sistema",
    "cargo": "admin",
    "cargo_display": "Administrador",
    "is_admin": true,
    "is_recepcao": true,
    "is_profissional": false,
    "professional_info": null
  }
]
```

---

### 7. Criar Usuário (Admin)
**POST** `/api/clinica-beleza/auth/users/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Permissão:** Apenas Admin

**Body:**
```json
{
  "username": "novo_usuario",
  "email": "usuario@clinica.com",
  "password": "senha123",
  "first_name": "Nome",
  "last_name": "Sobrenome",
  "cargo": "recepcao",
  "professional_id": null
}
```

---

## 🔒 PERMISSÕES CUSTOMIZADAS

### Classes de Permissão

```python
from clinica_beleza.permissions import (
    IsAdmin,
    IsRecepcao,
    IsProfissional,
    IsAdminOrRecepcao,
    CanManageAppointments,
    CanViewFinancial,
    CanManageUsers,
)
```

### Uso nas Views

```python
from rest_framework.views import APIView
from clinica_beleza.permissions import IsAdmin

class MinhaView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        # Apenas admin pode acessar
        pass
```

---

## 🔑 TOKEN JWT

### Informações no Token

O token JWT contém:
- `user_id` - ID do usuário
- `username` - Nome de usuário
- `email` - E-mail
- `cargo` - Cargo (admin/recepcao/profissional)
- `first_name` - Primeiro nome
- `last_name` - Sobrenome
- `is_admin` - É admin?
- `is_recepcao` - É recepção?
- `is_profissional` - É profissional?
- `professional_id` - ID do profissional (se aplicável)
- `professional_name` - Nome do profissional (se aplicável)

### Tempo de Expiração
- **Access Token:** 8 horas
- **Refresh Token:** 7 dias

---

## 📝 MODELO DE USUÁRIO

```python
class ClinicaUser(AbstractUser):
    CARGO_CHOICES = [
        ('admin', 'Administrador'),
        ('recepcao', 'Recepção'),
        ('profissional', 'Profissional'),
    ]
    
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES)
    professional = models.OneToOneField(
        'Professional',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
```

---

## 🚀 CRIAR USUÁRIOS DE TESTE

Execute o script no Heroku:

```bash
heroku run python backend/criar_usuarios_clinica_beleza.py --app lwksistemas
```

**Usuários criados:**
- `admin` / `admin123` - Administrador
- `recepcao` / `recepcao123` - Recepção
- `dra.ana` / `prof123` - Profissional
- `dra.julia` / `prof123` - Profissional
- `dra.fernanda` / `prof123` - Profissional

---

## 🎯 PRÓXIMOS PASSOS (Frontend)

Aguardando códigos do frontend para implementar:

1. **Página de Login**
   - Formulário de login
   - Validação
   - Armazenar token no localStorage
   - Redirecionar após login

2. **Proteção de Rotas**
   - Middleware de autenticação
   - Verificar token em cada requisição
   - Redirecionar para login se não autenticado

3. **Controle de Permissões**
   - Mostrar/ocultar funcionalidades por cargo
   - Desabilitar botões sem permissão
   - Mensagens de erro amigáveis

4. **Componentes**
   - Header com informações do usuário
   - Menu adaptado por cargo
   - Botão de logout

---

## ✅ STATUS

- ✅ Modelo de usuário customizado
- ✅ Serializers JWT customizados
- ✅ Permissões por cargo
- ✅ Endpoints de autenticação
- ✅ Script de criação de usuários
- ⏳ Aguardando deploy (v571)
- ⏳ Aguardando códigos do frontend

**Pronto para receber os códigos do frontend!** 🚀
