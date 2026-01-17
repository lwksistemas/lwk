# ✅ Troca de Senha Obrigatória - SuperAdmin e Suporte

## 📋 Implementação Completa

Sistema de troca de senha obrigatória após recuperação de senha para usuários SuperAdmin e Suporte, similar ao sistema já existente para lojas.

## 🔧 Alterações no Backend

### 1. Modelo UsuarioSistema Atualizado

**Arquivo**: `backend/superadmin/models.py`

Adicionados campos:
```python
# Senha provisória (para recuperação de senha)
senha_provisoria = models.CharField(max_length=50, blank=True, help_text='Senha provisória gerada automaticamente')
senha_foi_alterada = models.BooleanField(default=False, help_text='Indica se o usuário já alterou a senha provisória')
```

### 2. Migration Criada

**Arquivo**: `backend/superadmin/migrations/0006_add_senha_provisoria_usuario_sistema.py`

Adiciona os campos `senha_provisoria` e `senha_foi_alterada` ao modelo `UsuarioSistema`.

### 3. Endpoints Criados/Atualizados

#### A. Recuperação de Senha (Atualizado)
**Endpoint**: `POST /api/superadmin/usuarios/recuperar_senha/`

**Alterações**:
- Agora salva `senha_provisoria` no `UsuarioSistema`
- Define `senha_foi_alterada = False`

```python
# Atualizar senha provisória no UsuarioSistema
usuario_sistema.senha_provisoria = nova_senha
usuario_sistema.senha_foi_alterada = False
usuario_sistema.save()
```

#### B. Verificar Senha Provisória (Novo)
**Endpoint**: `GET /api/superadmin/usuarios/verificar_senha_provisoria/`

**Permissão**: Público (mas requer autenticação JWT)

**Resposta**:
```json
{
  "precisa_trocar_senha": true,
  "usuario_id": 1,
  "usuario_nome": "luiz",
  "tipo": "superadmin"
}
```

**Lógica**:
```python
precisa_trocar_senha = not usuario_sistema.senha_foi_alterada and bool(usuario_sistema.senha_provisoria)
```

#### C. Alterar Senha Primeiro Acesso (Novo)
**Endpoint**: `POST /api/superadmin/usuarios/alterar_senha_primeiro_acesso/`

**Permissão**: Público (mas requer autenticação JWT)

**Payload**:
```json
{
  "nova_senha": "minhaNovaSenh@123",
  "confirmar_senha": "minhaNovaSenh@123"
}
```

**Validações**:
- ✅ Usuário autenticado
- ✅ Possui `UsuarioSistema`
- ✅ Senha ainda não foi alterada (`senha_foi_alterada = False`)
- ✅ Senhas coincidem
- ✅ Mínimo 6 caracteres

**Processo**:
1. Atualiza senha do usuário
2. Marca `senha_foi_alterada = True`
3. Retorna sucesso

## 🎨 Alterações no Frontend

### 1. Login SuperAdmin Atualizado

**Arquivo**: `frontend/app/(auth)/superadmin/login/page.tsx`

**Alterações**:
```typescript
// Após login bem-sucedido
await new Promise(resolve => setTimeout(resolve, 100));

const checkResponse = await apiClient.get('/superadmin/usuarios/verificar_senha_provisoria/');

if (checkResponse.data.precisa_trocar_senha) {
  router.push('/superadmin/trocar-senha');
  return;
}
```

### 2. Login Suporte Atualizado

**Arquivo**: `frontend/app/(auth)/suporte/login/page.tsx`

Mesma lógica do SuperAdmin, mas redireciona para `/suporte/trocar-senha`.

### 3. Página Trocar Senha - SuperAdmin (Nova)

**Arquivo**: `frontend/app/(dashboard)/superadmin/trocar-senha/page.tsx`

**Características**:
- Design roxo (tema SuperAdmin)
- Formulário com nova senha e confirmação
- Validação no frontend
- Chamada ao endpoint de alteração
- Redirecionamento automático após sucesso

### 4. Página Trocar Senha - Suporte (Nova)

**Arquivo**: `frontend/app/(dashboard)/suporte/trocar-senha/page.tsx`

**Características**:
- Design azul (tema Suporte)
- Mesma funcionalidade do SuperAdmin
- Redirecionamento para `/suporte/dashboard`

## 🎯 Fluxo Completo

### 1. Recuperação de Senha
```
Usuário → Clica "Esqueceu sua senha?"
       → Digita email
       → Sistema:
          - Gera senha provisória
          - Atualiza user.password
          - Salva usuario_sistema.senha_provisoria
          - Define usuario_sistema.senha_foi_alterada = False
          - Envia email
```

### 2. Login com Senha Provisória
```
Usuário → Faz login com senha provisória
       → authService.login() salva token JWT
       → Aguarda 100ms
       → Verifica se precisa trocar senha
       → Se precisa_trocar_senha = True:
          → Redireciona para /[tipo]/trocar-senha
       → Senão:
          → Redireciona para dashboard
```

### 3. Troca de Senha
```
Usuário → Digita nova senha
       → Confirma nova senha
       → Sistema:
          - Valida senhas
          - Atualiza user.password
          - Define usuario_sistema.senha_foi_alterada = True
          - Redireciona para dashboard
```

### 4. Próximo Login
```
Usuário → Faz login com nova senha
       → Verificação retorna precisa_trocar_senha = False
       → Vai direto para dashboard
```

## 📁 Arquivos Criados/Modificados

### Backend
- ✅ `backend/superadmin/models.py` - Adicionados campos
- ✅ `backend/superadmin/migrations/0006_add_senha_provisoria_usuario_sistema.py` - Nova migration
- ✅ `backend/superadmin/views.py` - 2 novos endpoints + 1 atualizado

### Frontend
- ✅ `frontend/app/(auth)/superadmin/login/page.tsx` - Verificação adicionada
- ✅ `frontend/app/(auth)/suporte/login/page.tsx` - Verificação adicionada
- ✅ `frontend/app/(dashboard)/superadmin/trocar-senha/page.tsx` - Nova página
- ✅ `frontend/app/(dashboard)/suporte/trocar-senha/page.tsx` - Nova página

## ✅ Como Testar

### SuperAdmin

1. **Recuperar Senha**:
   - Acesse: https://lwksistemas.com.br/superadmin/login
   - Clique em "Esqueceu sua senha?"
   - Digite: `consultorluizfelix@hotmail.com`
   - Verifique o email recebido

2. **Login com Senha Provisória**:
   - Faça login com usuário `luiz` e senha provisória do email
   - **Resultado Esperado**: Redireciona para `/superadmin/trocar-senha`

3. **Trocar Senha**:
   - Digite nova senha (mínimo 6 caracteres)
   - Confirme a senha
   - **Resultado Esperado**: Redireciona para `/superadmin/dashboard`

4. **Verificar que Não Pede Mais**:
   - Faça logout
   - Faça login com a nova senha
   - **Resultado Esperado**: Vai direto para dashboard

### Suporte

Mesmo processo, mas usando:
- URL: https://lwksistemas.com.br/suporte/login
- Email de um usuário de suporte
- Redirecionamentos para `/suporte/*`

## 🔍 Debug

### Console do Navegador

Após login, verifique:
```javascript
Verificação senha SuperAdmin: {
  precisa_trocar_senha: true,
  usuario_id: 1,
  usuario_nome: "luiz",
  tipo: "superadmin"
}
```

### Verificar no Heroku

```bash
heroku run "cd backend && python manage.py shell -c \"
from superadmin.models import UsuarioSistema;
from django.contrib.auth.models import User;
user = User.objects.get(username='luiz');
us = UsuarioSistema.objects.get(user=user);
print(f'Senha provisória: {us.senha_provisoria}');
print(f'Senha foi alterada: {us.senha_foi_alterada}')
\""
```

**Após Recuperação**:
```
Senha provisória: zvE9IU9Rqk
Senha foi alterada: False
```

**Após Trocar Senha**:
```
Senha provisória: zvE9IU9Rqk
Senha foi alterada: True
```

## 🚀 Deploy

- **Backend**: ✅ Heroku (v27)
  - Migration aplicada automaticamente
- **Frontend**: ✅ Vercel
  - 2 novas rotas criadas
- **Status**: Em produção

## 📊 Comparação com Sistema de Lojas

| Recurso | Lojas | SuperAdmin/Suporte |
|---------|-------|-------------------|
| Modelo | `Loja` | `UsuarioSistema` |
| Campo senha provisória | ✅ | ✅ |
| Campo senha alterada | ✅ | ✅ |
| Endpoint verificação | ✅ | ✅ |
| Endpoint alteração | ✅ | ✅ |
| Página troca senha | ✅ | ✅ |
| Verificação no login | ✅ | ✅ |

## 📝 Observações

### Segurança
- Senha provisória tem 10 caracteres (letras, números, símbolos)
- Troca de senha é obrigatória (não pode pular)
- Senha nova deve ter mínimo 6 caracteres
- Token JWT necessário para alterar senha

### UX
- Delay de 100ms garante que token esteja disponível
- Logs no console para debug
- Mensagens de erro claras
- Redirecionamento automático após sucesso

### Melhorias Futuras
- [ ] Adicionar força da senha (fraca/média/forte)
- [ ] Implementar histórico de senhas
- [ ] Adicionar expiração de senha provisória (24h)
- [ ] Implementar 2FA opcional

---

**Data**: 17/01/2026
**Sistema**: https://lwksistemas.com.br
**API**: https://api.lwksistemas.com.br
**Status**: ✅ Implementado e em Produção
