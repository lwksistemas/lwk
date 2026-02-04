# 🧪 TESTE: Admin da loja aparecendo em Funcionários - v254

## ✅ STATUS

- ✅ Backend v254 deployado
- ✅ API `/superadmin/lojas/info_publica/` retorna ID da loja
- ✅ Vendedor admin existe no banco (ID: 35, nome: "vendas")

## 🧪 TESTE PASSO A PASSO

### 1. Limpar cache do navegador
```
Ctrl + Shift + Delete
ou
Ctrl + F5 (hard refresh)
```

### 2. Fazer logout e login novamente
1. Acesse: https://lwksistemas.com.br/loja/felix/login
2. Faça logout se estiver logado
3. Faça login com: `vendas` / senha

### 3. Verificar localStorage
Abra o console do navegador (F12 → Console) e digite:
```javascript
localStorage.getItem('current_loja_id')
```

**Resultado esperado:** `"73"` (não `undefined` ou `null`)

### 4. Clicar em "Funcionários" 💼
1. No dashboard, clique no botão "Funcionários" 💼
2. O modal deve abrir
3. ✅ Deve aparecer o vendedor "vendas" na lista com badge "👤 Administrador"

### 5. Verificar requisição no console
No console do navegador (F12 → Network), procure por:
```
GET /api/crm/vendedores/
```

**Headers esperados:**
```
X-Loja-ID: 73
Authorization: Bearer <token>
```

**Resposta esperada:**
```json
[
  {
    "id": 35,
    "nome": "vendas",
    "email": "...",
    "cargo": "Gerente de Vendas",
    "is_admin": true,
    "meta_mensal": "10000.00",
    ...
  }
]
```

## 🔍 TROUBLESHOOTING

### Se não aparecer o vendedor:

1. **Verificar se localStorage tem o ID:**
   ```javascript
   console.log('Loja ID:', localStorage.getItem('current_loja_id'));
   ```
   - Se for `undefined` ou `null`, recarregue a página (F5)

2. **Verificar se a requisição está enviando o header:**
   - Abra F12 → Network
   - Clique em "Funcionários"
   - Procure por `GET /api/crm/vendedores/`
   - Verifique se tem header `X-Loja-ID: 73`

3. **Verificar resposta da API:**
   - Se a resposta for `[]` (array vazio), o problema é no backend
   - Se a resposta tiver dados, o problema é no frontend

4. **Limpar cache mais agressivamente:**
   ```
   1. Fechar todas as abas do site
   2. Ctrl + Shift + Delete
   3. Marcar "Cookies" e "Cache"
   4. Limpar
   5. Abrir em aba anônima (Ctrl + Shift + N)
   ```

## 📊 VERIFICAÇÃO NO BACKEND

Para confirmar que o vendedor existe:

```bash
heroku run "python backend/manage.py shell -c \"from crm_vendas.models import Vendedor; vendedores = Vendedor.objects.all_without_filter().filter(loja_id=73); print(f'Total: {vendedores.count()}'); [print(f'  - {v.nome} (is_admin: {v.is_admin})') for v in vendedores]\"" --app lwksistemas
```

**Resultado esperado:**
```
Total: 1
  - vendas (is_admin: True)
```

## ✅ SUCESSO

Se tudo funcionar, você deve ver:
- ✅ Modal "Funcionários" abre
- ✅ Lista mostra "vendas" com badge "👤 Administrador"
- ✅ Botão "Editar" funciona
- ✅ Botão "Excluir" está desabilitado (admin não pode ser excluído)

## 🎯 PRÓXIMO PASSO

Após confirmar que funciona, testar a sessão única:
1. Fazer login no celular
2. Fazer login no computador
3. No celular, clicar em "Funcionários"
4. ❌ Deve receber erro: "Outra sessão foi iniciada em outro dispositivo"
