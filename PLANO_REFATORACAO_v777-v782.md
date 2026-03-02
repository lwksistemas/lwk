# Plano de Refatoração - Páginas de Configuração e Monitoramento (v777-v782)

## 📋 Resumo

Refatoração de 6 páginas do superadmin seguindo o padrão estabelecido em v770-v775: separação de lógica em hooks, componentes reutilizáveis e redução de código.

**Data**: 02/03/2026  
**Padrão**: Hooks + Componentes + Página Orquestradora  
**Objetivo**: Reduzir ~2.610 linhas em ~50-60%

---

## 📊 Análise Atual

### Páginas Identificadas

| Página | Linhas | Complexidade | Prioridade |
|--------|--------|--------------|------------|
| `/superadmin/dashboard/logs` | 691 | Alta | 1 (maior) |
| `/superadmin/asaas` | 416 | Média | 2 |
| `/superadmin/dashboard/auditoria` | 398 | Média | 3 |
| `/superadmin/dashboard/alertas` | 397 | Média | 4 |
| `/superadmin/dashboard/storage` | 379 | Média | 5 |
| `/superadmin/mercadopago` | 329 | Baixa | 6 |
| **TOTAL** | **2.610** | - | - |

### Padrões Identificados

#### Problemas Comuns
1. ❌ Lógica de estado misturada com UI
2. ❌ Múltiplos `useState` e `useEffect` na mesma página
3. ❌ Funções de API inline
4. ❌ Componentes não reutilizáveis
5. ❌ Código duplicado entre páginas similares

#### Oportunidades
1. ✅ Criar hooks customizados para lógica de negócio
2. ✅ Extrair componentes de UI reutilizáveis
3. ✅ Centralizar chamadas de API
4. ✅ Reduzir duplicação de código
5. ✅ Melhorar tipagem TypeScript

---

## 🎯 Estratégia de Refatoração

### Padrão a Seguir (v770-v775)

```
📁 Estrutura Alvo:
├── hooks/
│   ├── useAsaasConfig.ts       # Lógica de configuração
│   ├── useAsaasStats.ts        # Lógica de estatísticas
│   ├── useMercadoPagoConfig.ts # Lógica Mercado Pago
│   ├── useLogsList.ts          # Lógica de logs
│   ├── useAlertasList.ts       # Lógica de alertas
│   ├── useStorageStats.ts      # Lógica de storage
│   └── useAuditoriaList.ts     # Lógica de auditoria
│
├── components/superadmin/
│   ├── asaas/
│   │   ├── AsaasConfigForm.tsx
│   │   ├── AsaasStatsCards.tsx
│   │   └── index.ts
│   ├── mercadopago/
│   │   ├── MercadoPagoConfigForm.tsx
│   │   ├── MercadoPagoStatusBadges.tsx
│   │   └── index.ts
│   ├── logs/
│   │   ├── LogCard.tsx
│   │   ├── LogFilters.tsx
│   │   └── index.ts
│   ├── alertas/
│   │   ├── AlertaCard.tsx
│   │   ├── AlertaFilters.tsx
│   │   └── index.ts
│   ├── storage/
│   │   ├── StorageChart.tsx
│   │   ├── StorageTable.tsx
│   │   └── index.ts
│   └── auditoria/
│       ├── AuditoriaCard.tsx
│       ├── AuditoriaFilters.tsx
│       └── index.ts
│
└── app/(dashboard)/superadmin/
    ├── asaas/page.tsx              # ~100 linhas (de 416)
    ├── mercadopago/page.tsx        # ~100 linhas (de 329)
    ├── dashboard/
    │   ├── logs/page.tsx           # ~150 linhas (de 691)
    │   ├── alertas/page.tsx        # ~100 linhas (de 397)
    │   ├── storage/page.tsx        # ~100 linhas (de 379)
    │   └── auditoria/page.tsx      # ~100 linhas (de 398)
```

---

## 📝 Plano de Execução

### v777: Refatoração Logs (691 → ~150 linhas)
**Prioridade**: 1 (maior página)

**Hooks a criar:**
- `useLogsList.ts` - Listagem, filtros, paginação
- `useLogActions.ts` - Ações (limpar, exportar)

**Componentes a criar:**
- `LogCard.tsx` - Card individual de log
- `LogFilters.tsx` - Filtros de busca
- `LogStats.tsx` - Estatísticas de logs

**Redução estimada**: 541 linhas (78%)

---

### v778: Refatoração Asaas (416 → ~120 linhas)
**Prioridade**: 2

**Hooks a criar:**
- `useAsaasConfig.ts` - Configuração e salvamento
- `useAsaasStats.ts` - Estatísticas e monitoramento
- `useAsaasActions.ts` - Testar conexão, sincronizar

**Componentes a criar:**
- `AsaasConfigForm.tsx` - Formulário de configuração
- `AsaasStatsCards.tsx` - Cards de estatísticas
- `AsaasSyncPanel.tsx` - Painel de sincronização

**Redução estimada**: 296 linhas (71%)

---

### v779: Refatoração Auditoria (398 → ~100 linhas)
**Prioridade**: 3

**Hooks a criar:**
- `useAuditoriaList.ts` - Listagem e filtros
- `useAuditoriaExport.ts` - Exportação de dados

**Componentes a criar:**
- `AuditoriaCard.tsx` - Card de evento
- `AuditoriaFilters.tsx` - Filtros de busca
- `AuditoriaTimeline.tsx` - Timeline de eventos

**Redução estimada**: 298 linhas (75%)

---

### v780: Refatoração Alertas (397 → ~100 linhas)
**Prioridade**: 4

**Hooks a criar:**
- `useAlertasList.ts` - Listagem e filtros
- `useAlertaActions.ts` - Marcar como lido, resolver

**Componentes a criar:**
- `AlertaCard.tsx` - Card de alerta
- `AlertaFilters.tsx` - Filtros por tipo/status
- `AlertaStats.tsx` - Estatísticas de alertas

**Redução estimada**: 297 linhas (75%)

---

### v781: Refatoração Storage (379 → ~100 linhas)
**Prioridade**: 5

**Hooks a criar:**
- `useStorageStats.ts` - Estatísticas de uso
- `useStorageActions.ts` - Limpeza, otimização

**Componentes a criar:**
- `StorageChart.tsx` - Gráfico de uso
- `StorageTable.tsx` - Tabela de arquivos
- `StorageActions.tsx` - Ações de limpeza

**Redução estimada**: 279 linhas (74%)

---

### v782: Refatoração Mercado Pago (329 → ~100 linhas)
**Prioridade**: 6 (menor página)

**Hooks a criar:**
- `useMercadoPagoConfig.ts` - Configuração e salvamento
- `useMercadoPagoSDK.ts` - Inicialização do SDK

**Componentes a criar:**
- `MercadoPagoConfigForm.tsx` - Formulário de configuração
- `MercadoPagoStatusBadges.tsx` - Badges de status
- `MercadoPagoTestPanel.tsx` - Painel de testes

**Redução estimada**: 229 linhas (70%)

---

## 📊 Resultados Esperados

### Redução de Código

| Versão | Página | Antes | Depois | Redução | % |
|--------|--------|-------|--------|---------|---|
| v777 | Logs | 691 | 150 | 541 | 78% |
| v778 | Asaas | 416 | 120 | 296 | 71% |
| v779 | Auditoria | 398 | 100 | 298 | 75% |
| v780 | Alertas | 397 | 100 | 297 | 75% |
| v781 | Storage | 379 | 100 | 279 | 74% |
| v782 | Mercado Pago | 329 | 100 | 229 | 70% |
| **TOTAL** | - | **2.610** | **670** | **1.940** | **74%** |

### Benefícios

#### Manutenibilidade
- ✅ Código mais organizado e legível
- ✅ Lógica separada da apresentação
- ✅ Componentes reutilizáveis
- ✅ Testes mais fáceis

#### Performance
- ✅ Menos re-renders desnecessários
- ✅ Hooks otimizados com memoization
- ✅ Componentes menores e mais rápidos

#### Desenvolvimento
- ✅ Mais fácil adicionar features
- ✅ Menos bugs por duplicação
- ✅ Onboarding mais rápido
- ✅ Código mais consistente

---

## 🚀 Cronograma

### Fase 1: Preparação (1 dia)
- Análise detalhada de cada página
- Identificação de código duplicado
- Definição de interfaces TypeScript

### Fase 2: Execução (6 dias)
- **Dia 1**: v777 - Logs (maior complexidade)
- **Dia 2**: v778 - Asaas
- **Dia 3**: v779 - Auditoria
- **Dia 4**: v780 - Alertas
- **Dia 5**: v781 - Storage
- **Dia 6**: v782 - Mercado Pago

### Fase 3: Testes e Deploy (1 dia)
- Testes em desenvolvimento
- Deploy incremental no Heroku
- Verificação em produção

**Total**: 8 dias

---

## ✅ Checklist por Versão

### Para cada refatoração:
- [ ] Criar hooks customizados
- [ ] Criar componentes reutilizáveis
- [ ] Atualizar página principal
- [ ] Adicionar tipagem TypeScript
- [ ] Testar funcionalidades
- [ ] Commit com mensagem descritiva
- [ ] Deploy no Heroku
- [ ] Documentar mudanças
- [ ] Atualizar resumo geral

---

## 🔗 Referências

- `RESUMO_REFATORACAO_v770-v775.md` - Padrão estabelecido
- `REFATORACAO_TIPOS_APP_v770.md` - Exemplo de refatoração
- `REFATORACAO_PLANOS_v773.md` - Exemplo de refatoração
- `REFATORACAO_USUARIOS_v774.md` - Exemplo de refatoração
- `REFATORACAO_LOJAS_v775.md` - Exemplo de refatoração

---

## 📌 Notas Importantes

1. **Manter funcionalidades**: Todas as features existentes devem continuar funcionando
2. **Testes manuais**: Testar cada página após refatoração
3. **Deploy incremental**: Um deploy por versão
4. **Documentação**: Criar arquivo MD para cada versão
5. **Consistência**: Seguir exatamente o padrão v770-v775
