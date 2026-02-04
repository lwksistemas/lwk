# 🧪 Teste de Funcionários - Loja "vida"

## ✅ Verificação no Banco (Heroku)

**Loja:**
- Nome: vida
- ID: 72
- Owner: felipe
- Email: financeiroluiz@hotmail.com

**Funcionário:**
- Nome: felipe
- Email: financeiroluiz@hotmail.com
- Cargo: Administrador
- is_admin: **True** ✅
- ID: 37

## ❌ Problema Identificado

O funcionário **EXISTE** no banco e está marcado como admin, mas o **frontend não está recebendo os dados**.

## 🔍 Possíveis Causas

1. **Header X-Loja-ID não está sendo enviado**
   - Frontend não está salvando `current_loja_id` no localStorage
   - Frontend não está adicionando o header na requisição

2. **Middleware não está processando o header**
   - Backend não está recebendo o header
   - Middleware não está setando o contexto da loja

3. **API está retornando vazio por causa do filtro**
   - LojaIsolationManager está filtrando mas não encontra a loja no contexto

## 🧪 Como Testar

### 1. Verificar se localStorage tem loja_id

Abra o DevTools (F12) no navegador e execute:

```javascript
console.log('current_loja_id:', localStorage.getItem('current_loja_id'));
```

**Esperado:** `72`

Se não aparecer, o problema está no frontend não salvando o ID.

### 2. Verificar se header está sendo enviado

1. Abra DevTools (F12)
2. Vá na aba **Network**
3. Clique em "Funcionários" no dashboard
4. Procure a requisição para `/api/clinica/funcionarios/`
5. Clique na requisição
6. Vá em **Headers** → **Request Headers**
7. Procure por `X-Loja-ID`

**Esperado:** `X-Loja-ID: 72`

Se não aparecer, o problema está no `clinicaApiClient` não adicionando o header.

### 3. Verificar logs do Heroku

Execute no terminal:

```bash
heroku logs --tail --app lwksistemas
```

Depois clique em "Funcionários" no dashboard e veja os logs.

**Esperado:**
```
🔍 [TenantMiddleware] URL: /api/clinica/funcionarios/ | Slug detectado: vida
✅ [TenantMiddleware] Contexto setado: loja_id=72, db=loja_vida
```

Se aparecer:
```
⚠️ [LojaIsolationManager] Nenhuma loja no contexto - retornando queryset vazio
```

Significa que o middleware não está setando o contexto corretamente.

## 🔧 Soluções

### Solução 1: Forçar salvamento do loja_id

Abra o DevTools (F12) e execute:

```javascript
localStorage.setItem('current_loja_id', '72');
location.reload();
```

Depois clique em "Funcionários" novamente.

### Solução 2: Verificar se frontend está atualizado

O frontend precisa estar na versão v245 ou superior com as seguintes mudanças:

**Arquivo:** `frontend/app/(dashboard)/loja/[slug]/dashboard/page.tsx`
```typescript
// Salvar loja_id no localStorage
if (lojaResponse.data.id) {
  localStorage.setItem('current_loja_id', lojaResponse.data.id.toString());
}
```

**Arquivo:** `frontend/lib/api-client.ts`
```typescript
// Interceptor do clinicaApiClient
clinicaApiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const lojaId = localStorage.getItem('current_loja_id');
      if (lojaId) {
        config.headers['X-Loja-ID'] = lojaId;
      }
    }
    return config;
  }
);
```

### Solução 3: Redeploy do frontend

Se o código está correto mas não funciona, pode ser cache do Vercel:

```bash
# No diretório frontend
git add .
git commit -m "Force redeploy"
git push
```

Ou no Vercel Dashboard:
1. Ir em Deployments
2. Clicar nos 3 pontinhos do último deploy
3. Clicar em "Redeploy"
4. Marcar "Use existing Build Cache" como **OFF**

## 📊 Checklist de Debug

- [ ] localStorage tem `current_loja_id = 72`
- [ ] Request Headers tem `X-Loja-ID: 72`
- [ ] Logs do Heroku mostram contexto setado
- [ ] API retorna o funcionário
- [ ] Frontend exibe o funcionário

## 🎯 Teste Rápido

Execute este comando para testar a API diretamente:

```bash
# Obter token de autenticação
TOKEN="seu_token_aqui"

# Testar API com X-Loja-ID
curl -X GET "https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/funcionarios/" \
  -H "X-Loja-ID: 72" \
  -H "Content-Type: application/json"
```

**Esperado:**
```json
[
  {
    "id": 37,
    "nome": "felipe",
    "email": "financeiroluiz@hotmail.com",
    "cargo": "Administrador",
    "is_admin": true
  }
]
```

Se retornar vazio `[]`, o problema está no backend (middleware ou manager).

Se retornar o funcionário, o problema está no frontend (não está enviando o header).

## 🚀 Próximo Passo

**AGORA:** Abra o DevTools (F12) no navegador em https://lwksistemas.com.br/loja/vida/dashboard e execute:

```javascript
// 1. Verificar localStorage
console.log('loja_id:', localStorage.getItem('current_loja_id'));

// 2. Forçar salvamento
localStorage.setItem('current_loja_id', '72');

// 3. Recarregar
location.reload();
```

Depois clique em "Funcionários" e veja se aparece.
