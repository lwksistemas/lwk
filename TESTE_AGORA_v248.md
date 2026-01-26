# ⚡ TESTE AGORA - Funcionários não aparecem

## 🎯 Ação Imediata

O funcionário **EXISTE** no banco (felipe, ID: 37, is_admin: True), mas não aparece no frontend.

### Passo 1: Abrir DevTools

1. Acesse: https://lwksistemas.com.br/loja/vida/dashboard
2. Pressione **F12** para abrir DevTools
3. Vá na aba **Console**

### Passo 2: Executar no Console

Cole e execute este código:

```javascript
// Verificar se loja_id está salvo
console.log('🔍 current_loja_id:', localStorage.getItem('current_loja_id'));

// Forçar salvamento do ID correto
localStorage.setItem('current_loja_id', '72');
console.log('✅ loja_id setado para 72');

// Recarregar página
location.reload();
```

### Passo 3: Clicar em Funcionários

Após a página recarregar, clique no botão **"Funcionários"** nas Ações Rápidas.

### Passo 4: Verificar Network

1. Mantenha DevTools aberto (F12)
2. Vá na aba **Network**
3. Clique em "Funcionários" novamente
4. Procure a requisição `/api/clinica/funcionarios/`
5. Clique nela
6. Vá em **Headers**
7. Procure por `X-Loja-ID` nos **Request Headers**

**Deve aparecer:** `X-Loja-ID: 72`

## 🔍 Diagnóstico

### Se aparecer o funcionário:
✅ **RESOLVIDO!** O problema era o localStorage não ter o loja_id.

### Se NÃO aparecer o funcionário:

#### Cenário A: X-Loja-ID está nos headers
**Problema:** Backend não está processando o header corretamente.

**Solução:** Ver logs do Heroku:
```bash
heroku logs --tail --app lwksistemas
```

Procure por:
- `⚠️ [LojaIsolationManager] Nenhuma loja no contexto`
- `🔍 [TenantMiddleware] URL: /api/clinica/funcionarios/`

#### Cenário B: X-Loja-ID NÃO está nos headers
**Problema:** Frontend não está enviando o header.

**Solução:** Frontend precisa ser atualizado/redeployado.

Verifique se o arquivo `frontend/lib/api-client.ts` tem este código:

```typescript
clinicaApiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const lojaId = localStorage.getItem('current_loja_id');
      if (lojaId) {
        config.headers['X-Loja-ID'] = lojaId;
        logger.log('🏪 [clinicaApiClient] Adicionando X-Loja-ID:', lojaId);
      }
    }
    return config;
  }
);
```

## 🚨 Teste Alternativo (API Direta)

Se quiser testar a API diretamente sem o frontend:

```bash
# Testar API com curl
curl -X GET "https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/funcionarios/" \
  -H "X-Loja-ID: 72" \
  -H "Content-Type: application/json"
```

**Deve retornar:**
```json
[
  {
    "id": 37,
    "nome": "felipe",
    "email": "financeiroluiz@hotmail.com",
    "telefone": "",
    "cargo": "Administrador",
    "is_admin": true,
    "loja_id": 72
  }
]
```

Se retornar vazio `[]`, o problema é no backend.
Se retornar o funcionário, o problema é no frontend.

## 📝 Resumo

1. ✅ Funcionário existe no banco (felipe, ID: 37)
2. ✅ Funcionário está marcado como admin (is_admin: True)
3. ❌ Frontend não está recebendo os dados

**Causa mais provável:** localStorage não tem `current_loja_id` salvo.

**Solução:** Executar o código JavaScript acima no console do navegador.

## 🎬 Depois de Resolver

Quando funcionar, você deve ver:

```
Gerenciar Funcionários

👤 felipe (Administrador)
   📧 financeiroluiz@hotmail.com
   🏷️ Administrador
   [Badge: 👤 Administrador]
   [Botões: Editar | Excluir (desabilitado)]
```

O botão "Excluir" estará desabilitado porque é o administrador da loja.
