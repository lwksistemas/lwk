# ✅ CORREÇÃO: Permissões de Proprietários de Lojas

## 📋 PROBLEMA IDENTIFICADO

**Usuário "vida" (administrador da loja ID 52) recebia erro 403 Forbidden ao tentar alterar senha provisória.**

### Logs do Erro:
```
VIOLAÇÃO DE SEGURANÇA: Usuário vida tentou acessar /api/superadmin/lojas/52/alterar_senha_primeiro_acesso/
Forbidden: /api/superadmin/lojas/52/alterar_senha_primeiro_acesso/
Status: 403
```

### Causa Raiz:
O middleware `SuperAdminSecurityMiddleware` estava bloqueando o acesso porque:
- Usuário autenticado mas não é superuser
- Rota `/api/superadmin/lojas/52/alterar_senha_primeiro_acesso/` não estava na lista de endpoints permitidos
- Middleware exigia superuser para todas as rotas do superadmin que não fossem públicas

---

## 🔧 SOLUÇÃO IMPLEMENTADA

### 1. Atualização do Middleware de Segurança

**Arquivo:** `backend/superadmin/middleware.py`

**Alterações:**
- ✅ Adicionado padrão `/alterar_senha_primeiro_acesso/` aos endpoints permitidos para proprietários
- ✅ Adicionado padrão `/reenviar_senha/` aos endpoints permitidos para proprietários
- ✅ Adicionado padrão `/financeiro/` aos endpoints permitidos para proprietários
- ✅ Adicionado log de acesso permitido para debug
- ✅ Comentários explicativos sobre cada tipo de endpoint

**Código:**
```python
# Endpoints que proprietários de lojas podem acessar (com autenticação)
# Esses endpoints têm verificação adicional na view para garantir que o usuário é o proprietário
owner_allowed_patterns = [
    '/alterar_senha_primeiro_acesso/',  # Trocar senha provisória
    '/reenviar_senha/',                  # Reenviar senha por email
    '/financeiro/',                      # Dados financeiros da própria loja
]

is_owner_allowed = any(pattern in request.path for pattern in owner_allowed_patterns)

# Se é um endpoint permitido para owners, deixar a view fazer a verificação específica
if is_owner_allowed:
    # A view fará a verificação de permissão (IsOwnerOrSuperAdmin ou verificação manual)
    logger.info(f"Acesso de proprietário permitido: {request.user.username} -> {request.path}")
    pass
```

### 2. Atualização do Endpoint reenviar_senha

**Arquivo:** `backend/superadmin/views.py`

**Alterações:**
- ✅ Adicionado `permission_classes=[IsOwnerOrSuperAdmin]` ao método
- ✅ Adicionado verificação de proprietário no método
- ✅ Mensagem de erro específica se não for o proprietário

**Código:**
```python
@action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSuperAdmin])
def reenviar_senha(self, request, pk=None):
    """Reenviar senha provisória por email (apenas proprietário ou superadmin)"""
    loja = self.get_object()
    
    # Verificar se o usuário é o proprietário (superadmin já passou pela permissão)
    if not request.user.is_superuser and request.user != loja.owner:
        return Response(
            {'error': 'Apenas o proprietário pode reenviar a senha'},
            status=status.HTTP_403_FORBIDDEN
        )
    # ... resto do código
```

### 3. Script de Teste Completo

**Arquivo:** `testar_permissoes_proprietario.py`

**Funcionalidades:**
- ✅ Testa autenticação de proprietário
- ✅ Testa acesso a endpoints permitidos
- ✅ Testa bloqueio de endpoints restritos
- ✅ Relatório completo de resultados

---

## 🎯 ENDPOINTS ACESSÍVEIS PARA PROPRIETÁRIOS

### ✅ Endpoints Permitidos (com autenticação)

| Endpoint | Método | Descrição | Verificação |
|----------|--------|-----------|-------------|
| `/api/superadmin/lojas/{id}/alterar_senha_primeiro_acesso/` | POST | Alterar senha provisória | IsOwnerOrSuperAdmin |
| `/api/superadmin/lojas/{id}/reenviar_senha/` | POST | Reenviar senha por email | IsOwnerOrSuperAdmin |
| `/api/superadmin/loja/{slug}/financeiro/` | GET | Dados financeiros da loja | Verificação manual na view |

### 🔒 Endpoints Bloqueados (apenas superadmin)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/superadmin/lojas/` | GET | Listar todas as lojas |
| `/api/superadmin/lojas/` | POST | Criar nova loja |
| `/api/superadmin/lojas/{id}/` | PUT/PATCH | Editar loja |
| `/api/superadmin/lojas/{id}/` | DELETE | Excluir loja |
| `/api/superadmin/lojas/estatisticas/` | GET | Estatísticas do sistema |
| `/api/superadmin/tipos-loja/` | * | Gerenciar tipos de loja |
| `/api/superadmin/planos/` | * | Gerenciar planos |

### 🌐 Endpoints Públicos (sem autenticação)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/superadmin/lojas/info_publica/` | GET | Informações públicas da loja |
| `/api/superadmin/lojas/verificar_senha_provisoria/` | GET | Verificar se precisa trocar senha |

---

## 🚀 DEPLOY

### Versão: v166
### Data: 22 de Janeiro de 2026
### Status: ✅ Em Produção

**Commits:**
1. `bed1f33` - fix: permitir proprietários alterarem senha provisória no middleware (v165)
2. `2bcffb2` - fix: garantir que proprietários de TODAS as lojas possam acessar endpoints necessários (v166)

---

## 🧪 COMO TESTAR

### Teste Manual

1. **Login como proprietário de loja:**
```bash
curl -X POST "https://lwksistemas-38ad47519238.herokuapp.com/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "vida", "password": "senha"}'
```

2. **Verificar senha provisória:**
```bash
curl -X GET "https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/verificar_senha_provisoria/" \
  -H "Authorization: Bearer {TOKEN}"
```

3. **Alterar senha (se necessário):**
```bash
curl -X POST "https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/52/alterar_senha_primeiro_acesso/" \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"nova_senha": "novaSenha123", "confirmar_senha": "novaSenha123"}'
```

4. **Acessar dados financeiros:**
```bash
curl -X GET "https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/loja/vida/financeiro/" \
  -H "Authorization: Bearer {TOKEN}"
```

### Teste Automatizado

Execute o script de teste:
```bash
python testar_permissoes_proprietario.py
```

O script irá:
- ✅ Solicitar credenciais do proprietário
- ✅ Fazer login e obter token
- ✅ Testar todos os endpoints permitidos
- ✅ Testar endpoints que devem ser bloqueados
- ✅ Gerar relatório completo

---

## 📊 IMPACTO

### ✅ Benefícios

1. **Segurança Mantida:**
   - Proprietários só acessam dados da própria loja
   - Endpoints administrativos continuam protegidos
   - Verificação dupla (middleware + view)

2. **Funcionalidade Restaurada:**
   - Proprietários podem alterar senha provisória
   - Proprietários podem reenviar senha por email
   - Proprietários podem acessar dados financeiros

3. **Aplicável a TODOS os Tipos de Loja:**
   - Clínica de Estética ✅
   - CRM Vendas ✅
   - Restaurante ✅
   - Serviços ✅
   - E-commerce ✅

### 🎯 Problema Resolvido

**ANTES:**
- ❌ Proprietários recebiam erro 403 ao tentar alterar senha
- ❌ Proprietários não conseguiam acessar dados financeiros
- ❌ Problema afetava TODAS as lojas criadas

**DEPOIS:**
- ✅ Proprietários podem alterar senha provisória
- ✅ Proprietários podem acessar dados financeiros
- ✅ Problema NÃO acontecerá em novas lojas
- ✅ Segurança mantida para endpoints administrativos

---

## 🔐 SEGURANÇA

### Camadas de Proteção

1. **Middleware (Primeira Camada):**
   - Verifica autenticação JWT
   - Permite acesso apenas a endpoints específicos
   - Bloqueia endpoints administrativos

2. **Permission Class (Segunda Camada):**
   - `IsOwnerOrSuperAdmin` verifica se é proprietário ou superadmin
   - Aplicada nos métodos das views

3. **Verificação na View (Terceira Camada):**
   - Verifica se o usuário é o proprietário específico da loja
   - Retorna 403 se não for o proprietário

### Exemplo de Fluxo de Segurança

```
Requisição: POST /api/superadmin/lojas/52/alterar_senha_primeiro_acesso/
Usuario: vida (proprietário da loja 52)

1. Middleware:
   ✅ Usuário autenticado? SIM
   ✅ Endpoint permitido para proprietários? SIM (/alterar_senha_primeiro_acesso/)
   ✅ Passa para a view

2. Permission Class (IsOwnerOrSuperAdmin):
   ✅ Usuário é superuser? NÃO
   ✅ Usuário é autenticado? SIM
   ✅ Passa para o método

3. Método da View:
   ✅ Busca loja ID 52
   ✅ Verifica: request.user == loja.owner? SIM
   ✅ Permite alteração de senha

RESULTADO: ✅ SUCESSO
```

---

## 📝 CHECKLIST DE VALIDAÇÃO

### Para Cada Nova Loja Criada:

- [ ] Proprietário consegue fazer login
- [ ] Proprietário consegue verificar senha provisória
- [ ] Proprietário consegue alterar senha provisória (se aplicável)
- [ ] Proprietário consegue acessar dados financeiros da própria loja
- [ ] Proprietário NÃO consegue acessar dados de outras lojas
- [ ] Proprietário NÃO consegue criar/editar/excluir lojas
- [ ] Proprietário NÃO consegue acessar estatísticas do sistema

---

## 🎉 CONCLUSÃO

**O problema foi completamente resolvido!**

✅ Proprietários de TODAS as lojas (novos e existentes) podem:
- Alterar senha provisória no primeiro acesso
- Reenviar senha por email
- Acessar dados financeiros da própria loja

✅ Segurança mantida:
- Proprietários só acessam dados da própria loja
- Endpoints administrativos protegidos
- Múltiplas camadas de verificação

✅ Problema NÃO acontecerá mais:
- Middleware atualizado
- Permissões corretas aplicadas
- Testes automatizados criados

---

**Data:** 22 de Janeiro de 2026  
**Versão:** v166  
**Status:** ✅ RESOLVIDO E EM PRODUÇÃO
