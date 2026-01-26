# 🔧 Correção: Senha Provisória não Solicita Troca

## 🐛 Problema Identificado

Ao fazer login com senha provisória, o sistema não estava solicitando a troca de senha, causando erro ao acessar o dashboard.

**Loja afetada:** Linda (felipefinanceiroluiz@hotmail.com)

## 🔍 Análise

### O que estava faltando:

1. ❌ Login não retornava flag `precisa_trocar_senha`
2. ✅ Endpoint de troca já existia: `/api/superadmin/lojas/{id}/alterar_senha_primeiro_acesso/`
3. ✅ Verificação já existia: `/api/superadmin/lojas/verificar_senha_provisoria/`

### Causa Raiz:

O endpoint de login (`SecureLoginView`) não estava incluindo a informação de senha provisória na resposta.

## ✅ Solução Implementada

### 1. Atualizado Login para Retornar Flag

**Arquivo:** `backend/superadmin/auth_views_secure.py`

**Antes:**
```python
response_data = {
    'access': access,
    'refresh': str(refresh),
    'user': {...}
}
# ❌ Não retornava precisa_trocar_senha
```

**Depois:**
```python
response_data = {
    'access': access,
    'refresh': str(refresh),
    'user': {...},
    'precisa_trocar_senha': True/False  # ✅ Agora retorna
}
```

### 2. Lógica de Verificação

**Para Lojas:**
```python
if real_user_type == 'loja':
    loja = Loja.objects.filter(owner=user, is_active=True).first()
    if loja:
        # Verificar se tem senha provisória e não foi alterada
        precisa_trocar_senha = not loja.senha_foi_alterada and bool(loja.senha_provisoria)
        response_data['precisa_trocar_senha'] = precisa_trocar_senha
```

**Para Suporte:**
```python
elif real_user_type == 'suporte':
    usuario_sistema = UsuarioSistema.objects.get(user=user, tipo='suporte')
    precisa_trocar_senha = not usuario_sistema.senha_foi_alterada and bool(usuario_sistema.senha_provisoria)
    response_data['precisa_trocar_senha'] = precisa_trocar_senha
```

## � Endpoints Existentes (Não Duplicados)

### 1. Verificar Senha Provisória
```
GET /api/superadmin/lojas/verificar_senha_provisoria/
```

**Resposta:**
```json
{
  "precisa_trocar_senha": true,
  "loja_id": 1,
  "loja_nome": "Linda"
}
```

### 2. Alterar Senha Primeiro Acesso
```
POST /api/superadmin/lojas/{id}/alterar_senha_primeiro_acesso/
```

**Body:**
```json
{
  "nova_senha": "novaSenha123",
  "confirmar_senha": "novaSenha123"
}
```

**Resposta:**
```json
{
  "message": "Senha alterada com sucesso!",
  "loja": "Linda"
}
```

### 3. Login (Atualizado)
```
POST /api/auth/loja/login/
```

**Body:**
```json
{
  "username": "felipefinanceiroluiz",
  "password": "senhaProvisoria123",
  "loja_slug": "linda"
}
```

**Resposta:**
```json
{
  "access": "token...",
  "refresh": "token...",
  "user": {...},
  "loja": {...},
  "precisa_trocar_senha": true  // ✅ NOVO
}
```

## 🔄 Fluxo Correto

```
1. Usuário faz login com senha provisória
   ↓
2. Backend retorna: precisa_trocar_senha = true
   ↓
3. Frontend detecta a flag
   ↓
4. Frontend redireciona para tela de troca de senha
   ↓
5. Usuário define nova senha
   ↓
6. Frontend chama: POST /api/superadmin/lojas/{id}/alterar_senha_primeiro_acesso/
   ↓
7. Backend atualiza senha e marca senha_foi_alterada = true
   ↓
8. Usuário é redirecionado para dashboard
```

## 🧪 Como Testar

### 1. Criar Loja com Senha Provisória

```bash
# Via interface do superadmin
# Criar loja → Sistema gera senha provisória automaticamente
```

### 2. Fazer Login

```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/loja/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario",
    "password": "senhaProvisoria",
    "loja_slug": "loja-slug"
  }'
```

**Verificar resposta:**
```json
{
  "precisa_trocar_senha": true  // ✅ Deve estar presente
}
```

### 3. Trocar Senha

```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/1/alterar_senha_primeiro_acesso/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "nova_senha": "novaSenha123",
    "confirmar_senha": "novaSenha123"
  }'
```

### 4. Fazer Login Novamente

```bash
# Usar nova senha
# Verificar que precisa_trocar_senha = false
```

## 📝 Campos do Modelo

### Loja
```python
senha_provisoria = models.CharField(max_length=50, blank=True)
senha_foi_alterada = models.BooleanField(default=False)
```

### UsuarioSistema (Suporte)
```python
senha_provisoria = models.CharField(max_length=50, blank=True)
senha_foi_alterada = models.BooleanField(default=False)
```

## ⚠️ Importante

### Quando `precisa_trocar_senha = True`:
- ✅ Usuário consegue fazer login
- ✅ Recebe token de acesso
- ⚠️ Frontend deve redirecionar para tela de troca de senha
- ❌ Não deve permitir acesso ao dashboard até trocar senha

### Quando `precisa_trocar_senha = False`:
- ✅ Usuário pode acessar dashboard normalmente
- ✅ Senha já foi alterada anteriormente

## 🎯 Solução para Loja "Linda"

1. **Verificar senha provisória atual:**
```bash
heroku run "python backend/manage.py shell -c \"from superadmin.models import Loja; l = Loja.objects.get(slug='linda'); print(f'Senha provisória: {l.senha_provisoria}'); print(f'Foi alterada: {l.senha_foi_alterada}')\"" -a lwksistemas
```

2. **Fazer login com senha provisória**
3. **Sistema agora retorna `precisa_trocar_senha: true`**
4. **Frontend redireciona para troca de senha**
5. **Usuário define nova senha**
6. **Acessa dashboard normalmente**

## 🎊 Resultado Final

**Antes:**
- ❌ Login não informava sobre senha provisória
- ❌ Frontend não sabia que precisava trocar senha
- ❌ Erro ao acessar dashboard

**Depois:**
- ✅ Login retorna flag `precisa_trocar_senha`
- ✅ Frontend pode detectar e redirecionar
- ✅ Fluxo de troca de senha funciona
- ✅ Acesso ao dashboard após troca

## 🧪 Teste Realizado

### Login com Senha Provisória - Loja "Linda"

**Dados de teste:**
```bash
Username: felipe
Email: financeiroluiz@hotmail.com
Senha provisória: a@N5TA*i
Loja: linda
```

**Comando:**
```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/loja/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "felipe", "password": "a@N5TA*i", "loja_slug": "linda"}'
```

**Resposta:**
```json
{
  "access": "token...",
  "refresh": "token...",
  "session_id": "573bcd863de69eeeaa6d0c8b4dbe19a3e6c485532902e08eda78dd05f461bc14",
  "session_timeout_minutes": 30,
  "user": {
    "id": 68,
    "username": "felipe",
    "email": "financeiroluiz@hotmail.com",
    "is_superuser": false,
    "user_type": "loja"
  },
  "loja": {
    "id": 67,
    "slug": "linda",
    "nome": "Linda",
    "tipo_loja": "Clínica de Estética"
  },
  "precisa_trocar_senha": true  // ✅ FLAG PRESENTE!
}
```

**Resultado:** ✅ **SUCESSO!** A flag `precisa_trocar_senha: true` está sendo retornada corretamente!

---

**Status:** ✅ Correção implementada e testada
**Versão:** v234 (deploy realizado)
**Data:** 25/01/2026
