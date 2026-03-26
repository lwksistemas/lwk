# Análise: Verificação de Órfãos no Frontend (Vercel)

**Data**: 25/03/2026  
**Status**: ✅ Nenhum dado órfão encontrado no código fonte

---

## RESUMO EXECUTIVO

O frontend não possui referências hardcoded às lojas excluídas. As únicas referências encontradas são exemplos em placeholders e comentários. O cache de build (.next) contém referências compiladas que serão removidas no próximo deploy.

---

## 1. VERIFICAÇÕES REALIZADAS

### 1.1. Busca por CNPJs/Slugs Específicos

**Busca**: `41449198000172|34787081845|clinica-da-beleza|loja-teste|tech-store`

**Resultado**: ✅ Nenhuma referência hardcoded encontrada

**Referências Encontradas** (apenas exemplos):
- `frontend/components/superadmin/lojas/ModalNovaLoja.tsx`
  - Linha 110: Comentário explicativo
  - Linha 446: Placeholder do input
  - Linha 450: Exemplo de URL

```typescript
// Comentário explicativo
/** Slug fixo: usa apenas os dígitos do CPF/CNPJ (URL: /loja/41449198000172/login). */

// Placeholder
placeholder="41449198000172 (CPF/CNPJ sem formatação)"

// Exemplo de URL
Ex.: CNPJ 41.449.198/0001-72 → /loja/41449198000172/login
```

### 1.2. Arquivos Estáticos (Public)

**Diretórios Verificados**:
- `frontend/public/`
- `frontend/public/icons/`

**Resultado**: ✅ Nenhum arquivo específico de loja encontrado

**Arquivos Presentes**:
- `clear-cache.html` - Página de limpeza de cache
- `limpar-cache.html` - Página de limpeza de cache (PT-BR)
- `manifest.json` - Manifest PWA genérico
- `sw.js` - Service Worker
- `workbox-f1770938.js` - Workbox
- `icons/icon.svg` - Ícone genérico
- `icons/README.md` - Documentação

### 1.3. Cache e Storage

**Busca**: `localStorage.setItem|sessionStorage.setItem|loja_|tenant_`

**Resultado**: ✅ Apenas uso dinâmico de storage (sem dados hardcoded)

**Padrões Identificados**:

1. **Cookies**:
   - `loja_slug` - Slug da loja atual (dinâmico)
   - `loja_usa_crm` - Flag se loja usa CRM (dinâmico)
   - `user_type` - Tipo de usuário (dinâmico)

2. **SessionStorage**:
   - `current_loja_id` - ID da loja atual (dinâmico)
   - `loja_slug` - Slug da loja atual (dinâmico)

3. **LocalStorage**:
   - `pwa_loja_slug` - Slug da loja para PWA (dinâmico)
   - `crm_loja_info` - Cache de informações da loja CRM (dinâmico, TTL 2min)

**Observação**: Todos os dados são armazenados dinamicamente baseados na loja acessada. Não há valores hardcoded.

---

## 2. CACHE DE BUILD (.next)

### 2.1. Tamanho do Cache

```bash
558MB - frontend/.next/
```

### 2.2. Conteúdo

O diretório `.next` contém:
- Código compilado (JavaScript minificado)
- Assets otimizados
- Manifests de rotas
- Cache de build

**Referências Encontradas**:
- Arquivos compilados contêm os exemplos de placeholder (41449198000172)
- Estas referências são apenas strings de exemplo no código compilado
- Serão removidas no próximo build/deploy

### 2.3. Limpeza Recomendada

O cache `.next` deve ser limpo antes do próximo deploy para:
1. Remover referências compiladas antigas
2. Reduzir tamanho do deploy
3. Garantir build limpo

---

## 3. ARQUITETURA DE DADOS NO FRONTEND

### 3.1. Dados Dinâmicos (API)

O frontend busca TODOS os dados de lojas via API:

**Endpoints Principais**:
- `GET /superadmin/lojas/` - Lista de lojas
- `GET /superadmin/lojas/info_publica/?slug={slug}` - Info pública da loja
- `GET /superadmin/lojas/{id}/` - Detalhes da loja

**Fluxo**:
1. Usuário acessa `/loja/{slug}/login`
2. Frontend busca info da loja via API
3. Se loja não existe, API retorna 404
4. Frontend redireciona para página de erro

### 3.2. Roteamento Dinâmico

**Padrão**: `/loja/[slug]/*`

O Next.js usa rotas dinâmicas:
- `[slug]` é um parâmetro dinâmico
- Não há rotas hardcoded para lojas específicas
- Todas as rotas são geradas em runtime

**Exemplos**:
- `/loja/41449198000172/login` ✅ Dinâmico
- `/loja/34787081845/dashboard` ✅ Dinâmico
- `/loja/qualquer-slug/crm-vendas` ✅ Dinâmico

### 3.3. Middleware de Tenant

**Arquivo**: `frontend/middleware.ts`

O middleware verifica:
1. Cookie `loja_slug` - Slug da loja atual
2. Cookie `user_type` - Tipo de usuário
3. Cookie `loja_usa_crm` - Se loja usa CRM

**Comportamento**:
- Se loja não existe, redireciona para home
- Se usuário tenta acessar outra loja, redireciona para sua loja
- Todos os dados são dinâmicos (cookies)

---

## 4. LIMPEZA DE CACHE DO USUÁRIO

### 4.1. Service Worker

**Arquivo**: `frontend/public/sw.js`

O Service Worker faz cache de:
- Assets estáticos (CSS, JS, imagens)
- Páginas visitadas
- Respostas de API (estratégia cache-first)

**Limpeza Automática**:
- Cache expira após período configurado
- Novo deploy invalida cache antigo (versão do SW muda)

### 4.2. Páginas de Limpeza Manual

**Arquivos**:
- `frontend/public/clear-cache.html`
- `frontend/public/limpar-cache.html`

**Funcionalidade**:
- Limpa localStorage
- Limpa sessionStorage
- Desregistra Service Worker
- Limpa cache do navegador

**Acesso**:
- `https://lwksistemas.com.br/clear-cache.html`
- `https://lwksistemas.com.br/limpar-cache.html`

---

## 5. DEPLOY NO VERCEL

### 5.1. Processo de Build

**Comando**: `npm run build`

**Etapas**:
1. Limpa diretório `.next`
2. Compila TypeScript
3. Otimiza assets
4. Gera rotas estáticas
5. Cria manifests

### 5.2. Cache do Vercel

O Vercel faz cache de:
- `node_modules/` (dependências)
- `.next/cache/` (cache de build)

**Limpeza**:
```bash
# Via CLI
vercel --force

# Via Dashboard
Settings > General > Clear Build Cache
```

### 5.3. Variáveis de Ambiente

**Arquivo**: `frontend/.env.production`

Verificar se há referências a lojas específicas:

```bash
# Buscar por slugs ou IDs de lojas
grep -i "loja\|slug\|41449198000172\|34787081845" frontend/.env.production
```

---

## 6. CONCLUSÕES

### 6.1. Pontos Fortes

✅ **Arquitetura Dinâmica**
- Nenhum dado hardcoded de lojas
- Todas as rotas são dinâmicas
- Dados buscados via API

✅ **Roteamento Flexível**
- Next.js com rotas dinâmicas `[slug]`
- Middleware de tenant robusto
- Redirecionamentos automáticos

✅ **Cache Gerenciado**
- Service Worker com estratégia adequada
- Páginas de limpeza manual disponíveis
- Cache expira automaticamente

### 6.2. Ações Necessárias

⚠️ **Limpeza de Cache de Build**
- Remover diretório `.next` antes do próximo deploy
- Garantir build limpo sem referências antigas

⚠️ **Verificar Variáveis de Ambiente**
- Confirmar que não há referências hardcoded em `.env.production`

✅ **Nenhuma Ação no Código Fonte**
- Código está limpo
- Apenas exemplos em placeholders (aceitável)

### 6.3. Recomendações

1. **Limpar Cache de Build**
   ```bash
   cd frontend
   rm -rf .next
   npm run build
   ```

2. **Deploy Limpo no Vercel**
   ```bash
   vercel --force
   ```

3. **Monitorar Logs**
   - Verificar se há erros 404 para lojas excluídas
   - Confirmar que usuários não estão tentando acessar lojas antigas

4. **Documentação**
   - Manter exemplos em placeholders atualizados
   - Usar CNPJs fictícios em vez de reais

---

## 7. SCRIPT DE LIMPEZA

### 7.1. Limpeza Local

```bash
#!/bin/bash
# limpar-cache-frontend.sh

echo "🧹 Limpando cache do frontend..."

cd frontend

# Remover .next
if [ -d ".next" ]; then
  echo "  ✅ Removendo .next (558MB)..."
  rm -rf .next
fi

# Remover node_modules/.cache
if [ -d "node_modules/.cache" ]; then
  echo "  ✅ Removendo node_modules/.cache..."
  rm -rf node_modules/.cache
fi

# Remover .vercel
if [ -d ".vercel" ]; then
  echo "  ✅ Removendo .vercel..."
  rm -rf .vercel
fi

echo "✅ Cache limpo com sucesso!"
echo ""
echo "📦 Próximos passos:"
echo "  1. npm run build"
echo "  2. vercel --force"
```

### 7.2. Limpeza no Vercel

```bash
#!/bin/bash
# deploy-limpo-vercel.sh

echo "🚀 Deploy limpo no Vercel..."

cd frontend

# Limpar cache local
rm -rf .next node_modules/.cache .vercel

# Build limpo
echo "📦 Executando build..."
npm run build

# Deploy forçado (ignora cache do Vercel)
echo "🚀 Fazendo deploy..."
vercel --force

echo "✅ Deploy concluído!"
```

---

## 8. VERIFICAÇÃO PÓS-DEPLOY

### 8.1. Checklist

- [ ] Build executado sem erros
- [ ] Deploy concluído no Vercel
- [ ] Páginas de lojas ativas carregam corretamente
- [ ] Páginas de lojas excluídas retornam 404
- [ ] Cache do navegador limpo (testar em modo anônimo)
- [ ] Service Worker atualizado (verificar versão)
- [ ] Logs do Vercel sem erros 404 excessivos

### 8.2. Testes Manuais

1. **Acessar loja ativa**:
   ```
   https://lwksistemas.com.br/loja/{slug_ativo}/login
   ```
   Resultado esperado: ✅ Página de login carrega

2. **Acessar loja excluída**:
   ```
   https://lwksistemas.com.br/loja/41449198000172/login
   ```
   Resultado esperado: ❌ Erro 404 ou redirecionamento

3. **Limpar cache do navegador**:
   ```
   https://lwksistemas.com.br/limpar-cache.html
   ```
   Resultado esperado: ✅ Cache limpo, página recarrega

---

## 9. ARQUIVOS RELACIONADOS

### 9.1. Frontend

- `frontend/middleware.ts` - Middleware de tenant
- `frontend/components/superadmin/lojas/ModalNovaLoja.tsx` - Modal de criação (exemplos)
- `frontend/public/sw.js` - Service Worker
- `frontend/public/limpar-cache.html` - Página de limpeza
- `frontend/.env.production` - Variáveis de ambiente

### 9.2. Scripts

- `limpar-cache-frontend.sh` - Script de limpeza local
- `deploy-limpo-vercel.sh` - Script de deploy limpo

### 9.3. Documentação

- `ANALISE_FRONTEND_ORFAOS.md` (este arquivo)
- `ANALISE_EXCLUSAO_LOJAS_ORFAOS.md` - Análise do backend

---

## 10. PRÓXIMOS PASSOS

1. ✅ **Verificação Concluída**: Nenhum órfão no código fonte
2. ⏳ **Limpar cache de build**: Remover `.next` antes do próximo deploy
3. ⏳ **Deploy limpo no Vercel**: Usar `vercel --force`
4. ⏳ **Testar páginas**: Confirmar que lojas excluídas retornam 404
5. 📝 **Documentar processo**: Adicionar ao README

---

**Última Atualização**: 25/03/2026  
**Autor**: Kiro AI Assistant
