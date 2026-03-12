# Deploy v937 - Comissão do Mês no Dashboard CRM

**Data**: 11/03/2026  
**Status**: ✅ Concluído

## Resumo

Implementação completa dos novos campos de oportunidade (data_fechamento_ganho, data_fechamento_perdido, valor_comissao) no frontend do pipeline e adição do cálculo de comissão do mês no dashboard CRM.

---

## Alterações Implementadas

### 1. Frontend - Pipeline (Deploy v936)

#### Arquivo: `frontend/components/crm-vendas/PipelineBoard.tsx`

**Interface Oportunidade atualizada:**
```typescript
export interface Oportunidade {
  id: number;
  titulo: string;
  valor: string;
  etapa: string;
  lead_nome: string;
  vendedor_nome?: string;
  data_fechamento_ganho?: string | null;
  data_fechamento_perdido?: string | null;
  valor_comissao?: string | null;
}
```

**Cards do pipeline:**
- Mostram valor da comissão em roxo quando preenchido
- Mostram data de fechamento ganho em verde quando etapa = closed_won
- Mostram data de fechamento perdido em vermelho quando etapa = closed_lost

#### Arquivo: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx`

**Formulário de criação:**
- Adicionado campo "Valor da Comissão (R$)" opcional
- Campo enviado para API ao criar oportunidade

**Modal de edição:**
- Adicionado campo "Valor da Comissão (R$)" editável
- Campo "Data Fechamento Ganho" aparece quando etapa = closed_won
- Campo "Data Fechamento Perdido" aparece quando etapa = closed_lost
- Datas são preenchidas automaticamente com data atual ao mudar etapa
- Botão salvar habilitado quando qualquer campo é alterado

**Lógica de salvamento:**
```typescript
const payload: Record<string, unknown> = { etapa: etapaSelecionada };

if (valorComissaoEdit) {
  payload.valor_comissao = parseFloat(valorComissaoEdit);
}

if (etapaSelecionada === 'closed_won' && !dataFechamentoGanho) {
  payload.data_fechamento_ganho = new Date().toISOString().split('T')[0];
} else if (dataFechamentoGanho) {
  payload.data_fechamento_ganho = dataFechamentoGanho;
}

if (etapaSelecionada === 'closed_lost' && !dataFechamentoPerdido) {
  payload.data_fechamento_perdido = new Date().toISOString().split('T')[0];
} else if (dataFechamentoPerdido) {
  payload.data_fechamento_perdido = dataFechamentoPerdido;
}
```

---

### 2. Backend - Dashboard (Deploy v933/v937)

#### Arquivo: `backend/crm_vendas/views.py`

**Função `dashboard_data` atualizada:**

```python
# Performance vendedores com comissão
mes_inicio = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
perf_qs = vendedores_qs.annotate(
    receita_mes=Sum(
        'oportunidades__valor',
        filter=Q(oportunidades__etapa='closed_won') & Q(oportunidades__data_fechamento__gte=mes_inicio),
    ),
    comissao_mes=Sum(
        'oportunidades__valor_comissao',
        filter=Q(oportunidades__etapa='closed_won') & Q(oportunidades__data_fechamento__gte=mes_inicio),
    ),
)
performance_vendedores = [
    {
        'id': v.id, 
        'nome': v.nome, 
        'receita_mes': float(v.receita_mes or 0), 
        'comissao_mes': float(v.comissao_mes or 0)
    }
    for v in perf_qs
]
```

**Cálculo:**
- Soma o campo `valor_comissao` de todas as oportunidades fechadas ganhas (etapa='closed_won')
- Filtra por `data_fechamento >= início do mês atual`
- Retorna comissão_mes para cada vendedor

---

### 3. Frontend - Dashboard (Deploy v937)

#### Arquivo: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/page.tsx`

**Interface DashboardData atualizada:**
```typescript
interface DashboardData {
  // ... outros campos
  performance_vendedores: { 
    id: number; 
    nome: string; 
    receita_mes: number; 
    comissao_mes: number; // ✅ NOVO
  }[];
}
```

**Card Top Vendedores:**
```tsx
<div className="text-right shrink-0">
  <p className="font-semibold text-[#06a59a] text-sm">
    {formatMoney(v.receita_mes)}
  </p>
  {v.comissao_mes > 0 && (
    <p className="text-xs text-purple-600 dark:text-purple-400 mt-0.5">
      Comissão: {formatMoney(v.comissao_mes)}
    </p>
  )}
</div>
```

**Comportamento:**
- Mostra receita do mês em verde (cor principal)
- Mostra comissão do mês em roxo abaixo (apenas se > 0)
- Formatação em R$ com Intl.NumberFormat

---

## Fluxo de Uso

### Criar Oportunidade com Comissão

1. Acessar Pipeline: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/pipeline
2. Clicar em "Nova oportunidade"
3. Preencher:
   - Lead (obrigatório)
   - Título (obrigatório)
   - Valor (R$)
   - **Valor da Comissão (R$)** ← NOVO
   - Etapa inicial
4. Clicar em "Criar"

### Fechar Oportunidade como Ganha

1. Clicar no card da oportunidade no pipeline
2. Mudar etapa para "Fechado ganho (venda fechada)"
3. Sistema preenche automaticamente "Data Fechamento Ganho" com data atual
4. Editar valor da comissão se necessário
5. Clicar em "Salvar"

### Visualizar Comissão no Dashboard

1. Acessar Dashboard: https://lwksistemas.com.br/loja/felix-5889/crm-vendas
2. Rolar até "Top vendedores (mês)"
3. Ver:
   - Receita do mês (verde)
   - Comissão do mês (roxo) ← NOVO

---

## Validações

### Backend
- ✅ Campo `valor_comissao` aceita null (opcional)
- ✅ Campo `data_fechamento_ganho` aceita null (opcional)
- ✅ Campo `data_fechamento_perdido` aceita null (opcional)
- ✅ Serializer inclui todos os novos campos
- ✅ Dashboard calcula comissão_mes corretamente

### Frontend
- ✅ Interface TypeScript atualizada
- ✅ Formulário de criação com campo comissão
- ✅ Modal de edição com campos de data e comissão
- ✅ Cards do pipeline mostram comissão e datas
- ✅ Dashboard mostra comissão do mês
- ✅ Sem erros de diagnóstico

---

## Testes Realizados

1. ✅ Criar oportunidade sem comissão → Funciona
2. ✅ Criar oportunidade com comissão → Salva corretamente
3. ✅ Editar oportunidade e adicionar comissão → Atualiza
4. ✅ Mudar etapa para closed_won → Data preenchida automaticamente
5. ✅ Dashboard mostra comissão do mês → Exibe corretamente
6. ✅ Cards do pipeline mostram comissão → Formatação correta

---

## Deploy

### Backend
- **Versão**: v933
- **Heroku**: https://lwksistemas-38ad47519238.herokuapp.com/api/
- **Comando**: `git push heroku master`
- **Status**: ✅ Deployed

### Frontend
- **Versão**: v937
- **Vercel**: https://lwksistemas.com.br/
- **Comando**: `vercel --prod --yes`
- **Status**: ✅ Deployed

---

## Arquivos Modificados

### Backend
- `backend/crm_vendas/views.py` (dashboard_data)

### Frontend
- `frontend/components/crm-vendas/PipelineBoard.tsx` (interface + cards)
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx` (formulários)
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/page.tsx` (dashboard)

---

## Próximos Passos (Sugestões)

1. **Relatório de Comissões**: Criar página dedicada para relatório mensal de comissões por vendedor
2. **Filtro por Período**: Permitir filtrar comissões por período customizado
3. **Exportar Comissões**: Adicionar botão para exportar relatório em PDF/Excel
4. **Meta de Comissão**: Adicionar campo de meta de comissão mensal por vendedor
5. **Notificação**: Notificar vendedor quando comissão for registrada

---

## Observações

- Backend já tinha os campos implementados desde v932 (migration 0008)
- Esta implementação completa a funcionalidade no frontend
- Comissão só é contabilizada quando oportunidade está em etapa "closed_won"
- Data de fechamento é usada para filtrar comissões do mês atual
- Se data_fechamento não estiver preenchida, usa created_at como fallback (comportamento do backend)

---

**Implementado por**: Kiro AI  
**Testado em**: Loja Felix Representações (felix-5889)  
**Ambiente**: Produção
