# 🔍 ANÁLISE: Admin da loja não aparece na lista - v257

## 📊 STATUS ATUAL

- ✅ Backend v257 deployado com logs detalhados
- ✅ Frontend v256 deployado com modal correto
- ✅ Vendedor admin existe no banco (ID: 35, nome: "vendas", loja_id: 73)
- ❌ Lista de vendedores aparece vazia no frontend

## 🧪 TESTE COM LOGS

### Passo 1: Limpar cache e fazer login
```
1. Ctrl + Shift + Delete (limpar cache)
2. Acesse: https://lwksistemas.com.br/loja/felix/login
3. Faça login com: vendas / senha
```

### Passo 2: Abrir console do navegador
```
F12 → Console
```

### Passo 3: Verificar localStorage
No console, digite:
```javascript
localStorage.getItem('current_loja_id')
```

**Resultado esperado:** `"73"`

### Passo 4: Clicar em "Funcionários" 💼

**Logs esperados no CONSOLE DO NAVEGADOR:**
```
🔍 [loadFuncionarios] Loja ID: 73
✅ [loadFuncionarios] Resposta: [...]
📊 [loadFuncionarios] Total de vendedores: X
```

### Passo 5: Verificar logs do Heroku

Abra outro terminal e rode:
```bash
heroku logs --tail --app lwksistemas
```

**Logs esperados no HEROKU:**
```
🔍 [_get_tenant_slug] X-Loja-ID header: 73
✅ [TenantMiddleware] Contexto setado: loja_id=73, db=...
🔍 [VendedorViewSet] Loja ID do contexto: 73
📊 [VendedorViewSet] Queryset count: 1
```

## 🔍 ANÁLISE DOS CENÁRIOS

### Cenário 1: localStorage está vazio
```javascript
localStorage.getItem('current_loja_id')  // null ou undefined
```

**Problema:** Frontend não salvou o ID da loja

**Solução:**
1. Recarregue a página (F5)
2. Verifique se a API `/superadmin/lojas/info_publica/` retorna o ID

### Cenário 2: Header não está sendo enviado
**Logs do Heroku:**
```
🔍 [_get_tenant_slug] X-Loja-ID header: None
```

**Problema:** Frontend não está enviando o header

**Solução:**
- Verificar se `apiClient` está configurado corretamente
- Verificar se o interceptor está funcionando

### Cenário 3: Middleware não está setando o contexto
**Logs do Heroku:**
```
🔍 [_get_tenant_slug] X-Loja-ID header: 73
⚠️ [TenantMiddleware] Loja não encontrada: slug=...
```

**Problema:** Middleware não conseguiu encontrar a loja

**Solução:**
- Verificar se a loja ID 73 existe no banco
- Verificar se o middleware está convertendo ID para slug corretamente

### Cenário 4: Manager retorna queryset vazio
**Logs do Heroku:**
```
✅ [TenantMiddleware] Contexto setado: loja_id=73
🔍 [VendedorViewSet] Loja ID do contexto: None
📊 [VendedorViewSet] Queryset count: 0
```

**Problema:** Contexto não está sendo mantido entre middleware e view

**Solução:**
- Verificar se `_thread_locals` está funcionando
- Verificar se há algum problema com threading

### Cenário 5: Vendedor não existe
**Logs do Heroku:**
```
✅ [TenantMiddleware] Contexto setado: loja_id=73
🔍 [VendedorViewSet] Loja ID do contexto: 73
📊 [VendedorViewSet] Queryset count: 0
```

**Problema:** Vendedor não existe no banco

**Solução:**
- Rodar comando para criar vendedor manualmente

## 📋 COMANDOS DE VERIFICAÇÃO

### Verificar se vendedor existe
```bash
heroku run "python backend/manage.py shell -c \"from crm_vendas.models import Vendedor; vendedores = Vendedor.objects.all_without_filter().filter(loja_id=73); print(f'Total: {vendedores.count()}'); [print(f'  - {v.nome} (is_admin: {v.is_admin})') for v in vendedores]\"" --app lwksistemas
```

### Verificar se loja existe
```bash
heroku run "python backend/manage.py shell -c \"from superadmin.models import Loja; loja = Loja.objects.get(id=73); print(f'Loja: {loja.nome} (slug: {loja.slug})')\"" --app lwksistemas
```

## 🎯 PRÓXIMOS PASSOS

1. Faça o teste completo (Passos 1-5)
2. Me envie:
   - O que aparece no console do navegador
   - O valor de `localStorage.getItem('current_loja_id')`
   - Os logs do Heroku quando clica em "Funcionários"

Com essas informações vou identificar exatamente onde está o problema!

## 💡 DICA

Se quiser ver os logs do Heroku em tempo real, rode em outro terminal:
```bash
heroku logs --tail --app lwksistemas | grep -E "(loadFuncionarios|VendedorViewSet|TenantMiddleware|_get_tenant_slug)"
```

Isso vai filtrar apenas os logs relevantes.
