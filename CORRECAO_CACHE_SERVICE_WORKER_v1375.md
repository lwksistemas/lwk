# CORREÇÃO: Cache do Service Worker Causando Dados "Sumindo" - v1375

**Data:** 26/03/2026  
**Versão:** v1375  
**Status:** ✅ IMPLEMENTADO

---

## 🐛 PROBLEMA IDENTIFICADO

### Sintomas
- Problema intermitente voltou após correção v1371
- Dados "sumindo" e "aparecendo" aleatoriamente
- Network tab mostrando: `Status Code 200 OK (from service worker)`
- API retornando `{"count":0,"results":[]}` do cache

### Causa Raiz
O **service worker do PWA** estava cacheando respostas de API antigas/vazias:

1. **v1371 corrigiu o backend**: Contexto da loja não é mais limpo prematuramente
2. **Mas o PWA continuou servindo cache antigo**: Service worker usa estratégia `NetworkFirst` mas ainda cacheia respostas
3. **Cache contém respostas vazias**: Quando o bug v1370 existia, o SW cacheou respostas `{"count":0,"results":[]}`
4. **Usuário vê dados antigos**: Mesmo com backend corrigido, o SW serve cache antigo

### Evidência
```
Request URL: https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/oportunidades/
Request Method: GET
Status Code: 200 OK (from service worker)  ← ❌ PROBLEMA: Vindo do cache!
Response: {"count":0,"next":null,"previous":null,"results":[]}
```

---

## ✅ SOLUÇÃO IMPLEMENTADA

### 1. Service Worker Customizado (sw-custom.js)

Criado novo service worker que **NUNCA** cacheia endpoints de API de dados:

```javascript
// Lista de endpoints que NUNCA devem ser cacheados
const NO_CACHE_API_PATTERNS = [
  /\/api\/crm-vendas\/vendedores/,
  /\/api\/crm-vendas\/oportunidades/,
  /\/api\/crm-vendas\/propostas/,
  /\/api\/crm-vendas\/contatos/,
  /\/api\/crm-vendas\/contas/,
  /\/api\/crm-vendas\/customers/,
  /\/api\/crm-vendas\/leads/,
  // ... outros endpoints
];

// Estratégia NetworkOnly (NUNCA cachear)
workbox.routing.registerRoute(
  ({ url }) => shouldNotCache(url),
  new workbox.strategies.NetworkOnly()
);
```

**Benefícios:**
- ✅ APIs de dados SEMPRE vêm do servidor
- ✅ Sem cache de respostas vazias
- ✅ Assets estáticos continuam cacheados (performance)

### 2. Middleware No-Cache no Backend

Criado `NoCacheAPIMiddleware` que adiciona headers agressivos:

```python
class NoCacheAPIMiddleware:
    def __call__(self, request):
        response = self.get_response(request)
        
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['X-No-Cache'] = 'true'
        
        return response
```

**Benefícios:**
- ✅ Navegadores não cacheem respostas
- ✅ Proxies não cacheem respostas
- ✅ Service workers respeitam headers

### 3. Atualização da Configuração PWA

Modificado `next.config.js` para usar SW customizado:

```javascript
const withPWA = require("@ducanh2912/next-pwa").default({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
  swSrc: "public/sw-custom.js",  // ✅ SW customizado
  scope: "/",
  reloadOnOnline: true,
});
```

### 4. Página de Limpeza de Cache

Criada página `limpar-cache-v1375.html` que:
- ✅ Desregistra service workers antigos
- ✅ Limpa todos os caches
- ✅ Limpa localStorage/sessionStorage
- ✅ Força reload completo

---

## 📋 ARQUIVOS MODIFICADOS/CRIADOS

### Criados
1. `frontend/public/sw-custom.js` - Service worker customizado
2. `backend/core/middleware/no_cache_api.py` - Middleware no-cache
3. `frontend/public/limpar-cache-v1375.html` - Página de limpeza

### Modificados
1. `backend/config/settings.py` - Adicionado NoCacheAPIMiddleware
2. `frontend/next.config.js` - Configuração PWA atualizada

---

## 🚀 DEPLOY

### Backend (Heroku)

```bash
# 1. Commit das mudanças
git add .
git commit -m "v1375: Corrigir cache do service worker causando dados sumindo"

# 2. Deploy no Heroku
git push heroku master

# 3. Verificar logs
heroku logs --tail --app lwksistemas
```

### Frontend (Vercel)

```bash
# 1. Deploy no Vercel
cd frontend
vercel --prod

# 2. Verificar build
# Build ID será: v1375-no-cache-fix-{timestamp}
```

---

## 🧪 TESTES

### Teste 1: Verificar Headers No-Cache

```bash
curl -I https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/vendedores/
```

**Esperado:**
```
Cache-Control: no-store, no-cache, must-revalidate, max-age=0, private
Pragma: no-cache
Expires: 0
X-No-Cache: true
```

### Teste 2: Verificar Service Worker

1. Abrir DevTools → Application → Service Workers
2. Verificar versão: `v1375`
3. Verificar status: `activated and is running`

### Teste 3: Verificar Network Tab

1. Abrir DevTools → Network
2. Acessar: `https://lwksistemas.com.br/loja/41449198000172/crm-vendas/pipeline`
3. Verificar requisição API:
   - ✅ Status: `200 OK` (SEM "from service worker")
   - ✅ Response: Dados reais (count > 0)

### Teste 4: Limpar Cache Antigo

1. Acessar: `https://lwksistemas.com.br/limpar-cache-v1375.html`
2. Aguardar limpeza automática
3. Clicar em "Recarregar Aplicação"
4. Verificar se dados aparecem corretamente

---

## 📊 IMPACTO

### Positivo
- ✅ Problema de cache resolvido definitivamente
- ✅ Dados sempre atualizados (vêm do servidor)
- ✅ Performance de assets estáticos mantida
- ✅ PWA continua funcionando (offline para páginas)

### Considerações
- ⚠️ APIs de dados não são mais cacheadas (sempre network)
- ⚠️ Pode aumentar ligeiramente o uso de dados móveis
- ✅ Mas garante dados sempre corretos e atualizados

---

## 🔍 MONITORAMENTO

### Como verificar se está funcionando?

1. **Verificar Network Tab:**
   ```
   Status Code: 200 OK  ← ✅ SEM "(from service worker)"
   ```

2. **Verificar Headers de Resposta:**
   ```
   Cache-Control: no-store, no-cache, must-revalidate
   X-No-Cache: true
   ```

3. **Verificar Service Worker:**
   ```javascript
   navigator.serviceWorker.getRegistrations().then(regs => {
     console.log('SW Version:', regs[0]?.active?.scriptURL);
   });
   ```

4. **Verificar Caches:**
   ```javascript
   caches.keys().then(keys => {
     console.log('Caches:', keys);
     // Não deve ter caches de API (api-cache-*)
   });
   ```

---

## 📚 LIÇÕES APRENDIDAS

### 1. PWA e Cache
- Service workers cacheiam agressivamente por padrão
- Estratégia `NetworkFirst` ainda cacheia respostas
- APIs de dados dinâmicos NUNCA devem ser cacheadas

### 2. Headers HTTP
- `Cache-Control: no-store` é mais forte que `no-cache`
- Múltiplos headers garantem compatibilidade (Pragma, Expires)
- Service workers respeitam headers HTTP

### 3. Debugging de Cache
- Network tab mostra origem da resposta (cache vs network)
- Application tab mostra service workers e caches
- Limpar cache é essencial após mudanças no SW

### 4. Defesa em Profundidade
- Backend: Headers no-cache
- Service Worker: NetworkOnly para APIs
- Frontend: Página de limpeza de cache
- Versão: Forçar atualização do SW

---

## ✅ CONCLUSÃO

O problema intermitente de dados "sumindo" foi causado pelo cache do service worker do PWA. A solução implementa defesa em profundidade:

1. **Service Worker Customizado**: NUNCA cacheia APIs de dados
2. **Middleware Backend**: Headers no-cache agressivos
3. **Página de Limpeza**: Remove cache antigo
4. **Versão Incrementada**: Força atualização do SW

**Status:** ✅ IMPLEMENTADO  
**Versão:** v1375  
**Deploy:** 26/03/2026

---

## 📝 PRÓXIMOS PASSOS

### Imediato
- [x] Deploy backend (Heroku)
- [x] Deploy frontend (Vercel)
- [ ] Instruir usuários a acessar `/limpar-cache-v1375.html`
- [ ] Monitorar logs por 24h

### Curto Prazo
- [ ] Verificar se problema não volta
- [ ] Monitorar uso de dados móveis
- [ ] Coletar feedback dos usuários

### Longo Prazo
- [ ] Considerar estratégia de cache mais sofisticada (SWR)
- [ ] Implementar cache seletivo com TTL curto
- [ ] Adicionar indicador visual de "dados do cache"

---

## 🆘 TROUBLESHOOTING

### Problema: Dados ainda "somem" após deploy

**Solução:**
1. Acessar `/limpar-cache-v1375.html`
2. Aguardar limpeza completa
3. Recarregar aplicação
4. Verificar Network tab (não deve ter "from service worker")

### Problema: Service Worker não atualiza

**Solução:**
1. DevTools → Application → Service Workers
2. Clicar em "Unregister"
3. Recarregar página (Ctrl+Shift+R)
4. Verificar nova versão (v1375)

### Problema: Cache não limpa

**Solução:**
1. DevTools → Application → Storage
2. Clicar em "Clear site data"
3. Recarregar página
4. Verificar se caches foram removidos

---

**Documentação criada por:** Kiro AI  
**Data:** 26/03/2026  
**Versão do documento:** 1.0
