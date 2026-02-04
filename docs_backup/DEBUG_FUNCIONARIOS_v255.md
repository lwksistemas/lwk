# 🐛 DEBUG: Funcionários não aparecem no modal - v255

## 🔍 PROBLEMA

O modal de funcionários abre mas mostra apenas "Nenhum vendedor cadastrado" e o botão "+ Cadastrar Vendedor", mesmo com o vendedor existindo no banco.

## ✅ VERIFICAÇÕES FEITAS

1. ✅ Backend v254 deployado
2. ✅ API `/superadmin/lojas/info_publica/` retorna ID da loja (73)
3. ✅ Vendedor admin existe no banco (ID: 35, nome: "vendas")
4. ✅ Frontend v255 deployado com logs de debug

## 🧪 TESTE COM LOGS

### Passo 1: Limpar cache
```
Ctrl + Shift + Delete
ou
Ctrl + F5 (hard refresh)
```

### Passo 2: Abrir console do navegador
```
F12 → Console
```

### Passo 3: Fazer login
1. Acesse: https://lwksistemas.com.br/loja/felix/login
2. Faça login com: `vendas` / senha

### Passo 4: Verificar localStorage
No console, digite:
```javascript
localStorage.getItem('current_loja_id')
```

**Resultado esperado:** `"73"`

Se retornar `null` ou `undefined`:
1. Recarregue a página (F5)
2. Verifique novamente

### Passo 5: Clicar em "Funcionários" 💼

No console, você deve ver:
```
🔍 [loadFuncionarios] Loja ID: 73
✅ [loadFuncionarios] Resposta: [...]
📊 [loadFuncionarios] Total de vendedores: X
```

## 🔍 ANÁLISE DOS LOGS

### Cenário 1: Loja ID é null/undefined
```
🔍 [loadFuncionarios] Loja ID: null
```

**Problema:** localStorage não tem o ID da loja

**Solução:**
1. Recarregue a página (F5)
2. Verifique se a API `/superadmin/lojas/info_publica/` está retornando o ID
3. Verifique se o código está salvando no localStorage

### Cenário 2: Resposta é array vazio
```
🔍 [loadFuncionarios] Loja ID: 73
✅ [loadFuncionarios] Resposta: []
📊 [loadFuncionarios] Total de vendedores: 0
```

**Problema:** Backend não está retornando os vendedores

**Possíveis causas:**
1. Header `X-Loja-ID` não está sendo enviado
2. Middleware não está processando o header
3. Manager customizado está bloqueando a query

**Verificação:**
- Abra F12 → Network
- Procure por `GET /api/crm/vendedores/`
- Verifique se tem header `X-Loja-ID: 73`

### Cenário 3: Erro na requisição
```
❌ [loadFuncionarios] Erro ao carregar vendedores: ...
```

**Problema:** Erro na API

**Verificação:**
- Veja o erro completo no console
- Verifique se é erro 401 (não autenticado)
- Verifique se é erro 500 (erro no servidor)

## 🔧 COMANDOS DE VERIFICAÇÃO

### Verificar se vendedor existe no banco
```bash
heroku run "python backend/manage.py shell -c \"from crm_vendas.models import Vendedor; vendedores = Vendedor.objects.all_without_filter().filter(loja_id=73); print(f'Total: {vendedores.count()}'); [print(f'  - {v.nome} (is_admin: {v.is_admin})') for v in vendedores]\"" --app lwksistemas
```

### Testar API diretamente
```bash
# Obter token
TOKEN="seu_token_aqui"

# Testar API
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Loja-ID: 73" \
     "https://lwksistemas-38ad47519238.herokuapp.com/api/crm/vendedores/"
```

## 📊 PRÓXIMOS PASSOS

Após fazer o teste, me envie:
1. O que aparece no console quando clica em "Funcionários"
2. O valor de `localStorage.getItem('current_loja_id')`
3. Se há algum erro no console

Com essas informações, vou identificar exatamente onde está o problema!

## 🎯 POSSÍVEIS SOLUÇÕES

### Se localStorage está vazio:
- Problema no carregamento da página
- Solução: Forçar reload após login

### Se header não está sendo enviado:
- Problema no apiClient
- Solução: Verificar interceptor

### Se backend retorna vazio:
- Problema no middleware ou manager
- Solução: Adicionar logs no backend

### Se há erro 401:
- Problema de autenticação
- Solução: Verificar token JWT
