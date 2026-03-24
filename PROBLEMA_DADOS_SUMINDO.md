# Problema: Dados Sumindo das Páginas

## Sintomas
- Páginas do CRM aparecem vazias (sem dados)
- Ao fazer logout e login novamente, os dados voltam a aparecer
- Afeta todas as páginas: Pipeline, Customers, Contatos, Propostas

## URLs Afetadas
- https://lwksistemas.com.br/loja/41449198000172/crm-vendas/pipeline
- https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers
- https://lwksistemas.com.br/loja/41449198000172/crm-vendas/contatos
- https://lwksistemas.com.br/loja/41449198000172/crm-vendas/propostas

## Possíveis Causas

### 1. Sessão/Token Expirado
O token JWT pode estar expirando e não sendo renovado automaticamente.

### 2. Cache do Navegador
O navegador pode estar usando dados em cache desatualizados.

### 3. Problema com CORS
Headers CORS podem estar bloqueando requisições.

## Soluções Imediatas

### Para o Usuário (Temporário)

1. **Limpar Cache do Navegador**
   - Chrome/Edge: `Ctrl + Shift + Delete`
   - Selecionar "Imagens e arquivos em cache"
   - Limpar dados

2. **Forçar Atualização**
   - `Ctrl + Shift + R` (Windows/Linux)
   - `Cmd + Shift + R` (Mac)

3. **Fazer Logout e Login Novamente**
   - Isso renova o token JWT

4. **Usar Modo Anônimo**
   - Testar se o problema persiste em modo anônimo
   - Se funcionar, é problema de cache/cookies

### Para o Desenvolvedor (Permanente)

#### Verificar Token JWT

1. Abrir DevTools (F12)
2. Ir em Application > Local Storage
3. Verificar se há token válido
4. Verificar data de expiração do token

#### Verificar Requisições da API

1. Abrir DevTools (F12)
2. Ir em Network
3. Filtrar por "XHR" ou "Fetch"
4. Verificar se as requisições estão retornando:
   - Status 200 (sucesso)
   - Status 401 (não autorizado - token expirado)
   - Status 403 (proibido - sem permissão)
   - Status 500 (erro no servidor)

#### Verificar Console

1. Abrir DevTools (F12)
2. Ir em Console
3. Procurar por erros em vermelho
4. Erros comuns:
   - "Network Error"
   - "401 Unauthorized"
   - "CORS policy"
   - "Failed to fetch"

## Investigação Técnica

### Verificar Logs do Backend (Heroku)

```bash
heroku logs --tail --app lwksistemas
```

Procurar por:
- Erros 401 (autenticação)
- Erros 403 (permissão)
- Erros 500 (servidor)
- Timeout de requisições

### Verificar Logs do Frontend (Vercel)

1. Acessar: https://vercel.com/lwk-sistemas/dashboard
2. Ir em Logs
3. Filtrar por erros

### Verificar Headers da Requisição

Headers esperados:
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

### Verificar Response Headers

Headers recebidos (do seu exemplo):
```
cache-control: private, no-cache, no-store, max-age=0, must-revalidate
content-encoding: br
content-type: text/x-component
x-vercel-cache: MISS
```

O header `cache-control: no-cache, no-store` indica que o cache está desabilitado.

## Possível Solução: Renovação Automática de Token

O sistema pode precisar de um mecanismo de renovação automática de token JWT.

### Implementar Refresh Token

1. Quando o token expirar (401), tentar renovar automaticamente
2. Se a renovação falhar, redirecionar para login
3. Manter o usuário logado sem interrupção

### Código Sugerido (api-client.ts)

```typescript
// Interceptor para renovar token automaticamente
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Se erro 401 e não é retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Tentar renovar token
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/token/refresh/', {
          refresh: refreshToken
        });
        
        // Salvar novo token
        const newToken = response.data.access;
        localStorage.setItem('token', newToken);
        
        // Repetir requisição original com novo token
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Se falhar, fazer logout
        authService.logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

## Ações Recomendadas

### Curto Prazo (Agora)
1. ✅ Limpar cache do navegador
2. ✅ Fazer logout e login novamente
3. ✅ Verificar console do navegador (F12) para erros

### Médio Prazo (Próximos Dias)
1. Implementar renovação automática de token
2. Adicionar logs detalhados de autenticação
3. Melhorar tratamento de erros 401

### Longo Prazo (Próximas Semanas)
1. Implementar sistema de refresh token
2. Adicionar monitoramento de sessões
3. Implementar heartbeat para manter sessão ativa

## Teste Rápido

Para identificar a causa, faça o seguinte:

1. **Abrir DevTools (F12)**
2. **Ir em Network**
3. **Acessar uma página vazia (ex: Pipeline)**
4. **Verificar requisições**:
   - Se não houver requisições: problema no frontend
   - Se houver requisições com erro 401: token expirado
   - Se houver requisições com erro 500: problema no backend
   - Se houver requisições com status 200 mas sem dados: problema na API

5. **Ir em Console**
6. **Procurar erros em vermelho**
7. **Copiar e enviar os erros**

## Contato

Se o problema persistir após limpar cache e fazer login novamente, envie:
1. Screenshot do console (F12 > Console)
2. Screenshot do network (F12 > Network)
3. Descrição detalhada do que acontece
