# Correção: Selects Vazios no Mobile Android (v979)

## Problema Identificado

Vendedor Daniel Souza Felix (danielsouzafelix30@gmail.com) reportou que ao criar:
- **Novo Lead**: Campo "Origem" aparecia vazio (sem opções)
- **Nova Oportunidade**: Campo "Etapa inicial" aparecia vazio (sem opções)

Problema ocorria especificamente no celular Android.

### Causa Raiz

O `CRMConfigContext` tinha fallback para quando o config não carregava, mas não tratava o caso onde:
1. Config carrega com sucesso
2. Mas os arrays `origens_leads` ou `etapas_pipeline` estão vazios
3. Ou após filtrar por `ativo`, o array resultante fica vazio

Isso causava selects vazios no mobile.

## Solução Implementada

### Fallback Duplo

Adicionado verificação em dois níveis:

```typescript
// ANTES: Só verificava se config existe
if (!config || !config.origens_leads) {
  return VALORES_PADRAO;
}
return config.origens_leads.filter(o => o.ativo);

// DEPOIS: Verifica se existe E se não está vazio
if (!config || !config.origens_leads || config.origens_leads.length === 0) {
  return VALORES_PADRAO;
}

const ativas = config.origens_leads.filter(o => o.ativo);

// Se filtro resultar em array vazio, retornar padrão
if (ativas.length === 0) {
  return VALORES_PADRAO;
}

return ativas;
```

### Valores Padrão Garantidos

**Origens (6 opções):**
- WhatsApp
- Facebook
- Instagram
- Site
- Indicação
- Outro

**Etapas (6 opções):**
- Prospecção
- Qualificação
- Proposta
- Negociação
- Fechado (ganho)
- Fechado (perdido)

### Logs de Debug

Adicionados logs para investigar problemas:
```
✅ CRM Config carregado: {...}
❌ Erro ao carregar config CRM: {...}
```

## Arquivos Modificados

```
frontend/contexts/CRMConfigContext.tsx
```

## Impacto

### Antes
- ❌ Selects vazios no mobile Android
- ❌ Impossível criar leads (sem origem)
- ❌ Impossível criar oportunidades (sem etapa)
- 😤 Vendedores não conseguiam usar o sistema

### Depois
- ✅ Selects sempre têm opções (mínimo 6)
- ✅ Possível criar leads normalmente
- ✅ Possível criar oportunidades normalmente
- ✅ Sistema funcional em todos os dispositivos

## Teste

### Desktop
1. Acesse https://lwksistemas.com.br/loja/felix-5889/crm-vendas/leads
2. Clique em "Novo Lead"
3. ✅ Campo "Origem" deve ter opções

### Mobile Android
1. Acesse pelo celular Android
2. Faça login como vendedor (danielsouzafelix30@gmail.com)
3. Vá em CRM Vendas > Leads
4. Clique em "Novo Lead"
5. ✅ Campo "Origem" deve ter 6+ opções
6. Vá em CRM Vendas > Pipeline
7. Clique em "Nova Oportunidade"
8. ✅ Campo "Etapa inicial" deve ter 6 opções

## Deploy

### Frontend
```bash
git add frontend/contexts/CRMConfigContext.tsx
git commit -m "fix(crm): Garante valores padrão para origens e etapas (v979)"
git push origin master
vercel --prod --yes
```

**Status**: ✅ Deploy realizado com sucesso  
**Vercel**: Production

## Observações

- Correção é defensiva: sempre garante valores mínimos
- Não afeta usuários que têm config personalizado
- Se config personalizado estiver vazio, usa padrão
- Logs ajudam a identificar problemas de carregamento

---

**Versão**: v979  
**Data**: 2026-03-12  
**Commit**: 639a0433
