# Deploy: Correção Oportunidades Pipeline (v1150)

## Resumo
Correção implementada e deployada para resolver problema de oportunidades não aparecerem no pipeline após criação.

## Problema Corrigido
Após criar uma nova oportunidade, ela não aparecia no Pipeline de vendas devido à dessincronia entre `authService.getVendedorId()` (frontend) e `get_current_vendedor_id(request)` (backend).

## Solução Implementada

### 1. Backend (Heroku)
- Nenhuma alteração necessária no backend
- Backend já tinha lógica correta de filtro e criação

### 2. Frontend (Vercel)
- Adicionado método `setVendedorId()` ao `authService`
- Sincronização automática ao montar componente Pipeline
- Sincronização após criar oportunidade
- Aguarda sincronização antes de carregar lista

## Deploy Realizado

### Backend (Heroku)
```bash
git add -A
git commit -m "fix: sincronizar vendedor_id para oportunidades aparecerem no pipeline v1149"
git push heroku master
```

**Resultado:**
- ✅ Release v1150 deployado com sucesso
- ✅ Collectstatic: 160 arquivos copiados
- ✅ Migrations: Nenhuma pendente
- ⚠️ Warning: Models têm mudanças não refletidas em migration (esperado - mudanças anteriores)

### Frontend (Vercel)
```bash
cd frontend
vercel --prod --yes
```

**Resultado:**
- ✅ Deploy concluído em 58s
- ✅ URL: https://lwksistemas.com.br
- ✅ Inspect: https://vercel.com/lwks-projects-48afd555/frontend/DcPqYmGFzY61kCDSefjGbJAc2hiK

## Arquivos Modificados

### Frontend
1. `frontend/lib/auth.ts`
   - Adicionado método `setVendedorId(vendedorId: number)`

2. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx`
   - Adicionado estado `vendedorIdSynced`
   - Adicionado `useEffect` para sincronizar ao montar
   - Modificado `useEffect` de carregamento para aguardar sincronização
   - Adicionado sincronização após criar oportunidade

### Documentação
1. `ANALISE_OPORTUNIDADES_NAO_APARECEM_PIPELINE_v1149.md`
   - Análise completa do problema

2. `CORRECAO_OPORTUNIDADES_NAO_APARECEM_v1149.md`
   - Documentação da correção implementada

3. `DEPLOY_CORRECAO_PIPELINE_v1150.md`
   - Este documento

## Testes Recomendados

### Cenário 1: Owner sem VendedorUsuario
1. Login como owner (sem vendedor vinculado)
2. Acessar Pipeline de vendas
3. Criar nova oportunidade
4. ✅ Verificar se aparece na lista

### Cenário 2: Owner com VendedorUsuario
1. Login como owner (com vendedor vinculado)
2. Acessar Pipeline de vendas
3. Criar nova oportunidade
4. ✅ Verificar se aparece na lista

### Cenário 3: Vendedor comum
1. Login como vendedor (não-owner)
2. Acessar Pipeline de vendas
3. Criar nova oportunidade
4. ✅ Verificar se aparece na lista

### Cenário 4: Sessão antiga
1. Login antigo (sem vendedor_id no sessionStorage)
2. Acessar Pipeline de vendas
3. ✅ Verificar se sincroniza automaticamente
4. Criar nova oportunidade
5. ✅ Verificar se aparece na lista

## Monitoramento

### Logs Backend (Heroku)
```bash
heroku logs --tail --app lwksistemas
```

Procurar por:
- `Oportunidade criada SEM vendedor` (warning esperado para owner sem vendedor)
- `Oportunidade criada com vendedor herdado do lead` (info esperado)
- Erros 400/500 ao criar oportunidade

### Logs Frontend (Vercel)
Verificar no console do navegador:
- Chamadas para `/crm-vendas/crm-me/`
- Chamadas para `/crm-vendas/oportunidades/`
- Erros de sincronização

## Rollback (se necessário)

### Backend
```bash
heroku releases:rollback v1148 --app lwksistemas
```

### Frontend
```bash
cd frontend
vercel rollback https://frontend-au8172kt2-lwks-projects-48afd555.vercel.app
```

## Status

- ✅ Análise completa
- ✅ Correção implementada
- ✅ Deploy backend (Heroku v1150)
- ✅ Deploy frontend (Vercel)
- ⏳ Testes em produção
- ⏳ Validação com usuário

## Próximos Passos

1. Validar correção em produção
2. Monitorar logs por 24h
3. Coletar feedback do usuário
4. Marcar como resolvido se tudo OK

---

**Data:** 19/03/2026  
**Versão Backend:** v1150  
**Versão Frontend:** Última (Vercel)  
**Status:** Deploy concluído, aguardando validação
