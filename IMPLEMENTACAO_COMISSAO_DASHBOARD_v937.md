# Implementação de Comissão no Dashboard - Deploy v937-v943

## Resumo das Implementações

### ✅ TASK 1: Campos de Comissão no Pipeline (v932-v936)
- Backend: Adicionados campos `data_fechamento_ganho`, `data_fechamento_perdido`, `valor_comissao`
- Frontend: Interface completa para criar/editar oportunidades com comissão
- Status: **COMPLETO**

### ✅ TASK 2: Card de Comissão Total no Dashboard (v935-v939)
- Backend: Endpoint retorna `comissao_total_mes` e `comissao_mes` por vendedor
- Frontend: Card "Comissão do mês" e comissão individual nos top vendedores
- Status: **COMPLETO**

### ✅ TASK 3: Vincular Oportunidades ao Vendedor Logado (v936-v940)
- Backend: Auto-vinculação ao criar/editar oportunidades
- Comando Django: `vincular_oportunidades_vendedor` para dados existentes
- Status: **COMPLETO**

### ✅ TASK 4: Ajustar Pipeline Aberto vs Receita (v938-v941)
- Backend: `pipeline_aberto` agora soma apenas oportunidades em andamento
- Frontend: Card renomeado para "Pipeline em andamento"
- Status: **COMPLETO**

### ✅ TASK 5: Exibição de Atividades no Dashboard (v939-v943)
- Backend: Mudou de "atividades de hoje" para "próximas atividades (7 dias)"
- Frontend: Título atualizado para "Próximas atividades" com link "Criar atividade"
- Status: **COMPLETO**

---

# Correção: Atividades sem Oportunidade/Lead - Deploy v944-v946

## 🐛 Problema Identificado

Usuário reportou: "após salvar não aparece a tarefa no calendário" e "não está aparecendo no dashboard"

### Causa Raiz (Tripla)

**Problema 1 (v944)**: Filtro de vendedor bloqueava atividades órfãs no calendário
- O `VendedorFilterMixin` filtrava apenas por `oportunidade__vendedor_id` e `lead__oportunidades__vendedor_id`
- Atividades sem oportunidade/lead não apareciam na listagem do calendário

**Problema 2 (v945)**: Cache não era invalidado corretamente no calendário
- O decorator `cache_list_response` não verificava a versão do cache
- Mesmo após criar atividade, o cache antigo era retornado
- Usuário via dados desatualizados por até 5 minutos

**Problema 3 (v946)**: Dashboard não mostrava atividades órfãs
- A função `dashboard_data` tinha filtro diferente do calendário
- Não incluía atividades órfãs no resultado
- Cache do dashboard não era invalidado ao criar/atualizar/deletar atividades

### Impacto
- Atividades criadas no calendário não apareciam imediatamente
- Dashboard não mostrava atividades sem oportunidade/lead vinculada
- Usuários pensavam que o sistema não estava salvando
- Confusão sobre necessidade de Google Calendar conectado

---

## ✅ Solução Implementada

### Deploy v944: Permitir Atividades Órfãs no Calendário

Adicionado override do método `filter_by_vendedor` no `AtividadeViewSet`:

```python
def filter_by_vendedor(self, queryset):
    """
    Override para permitir atividades sem oportunidade/lead.
    Atividades órfãs (sem oportunidade/lead) são visíveis para todos da loja.
    """
    vendedor_id = get_current_vendedor_id(self.request)
    if vendedor_id is None:
        # Proprietário: vê tudo
        return queryset
    
    # Vendedor vê:
    # 1. Atividades vinculadas às suas oportunidades
    # 2. Atividades vinculadas aos seus leads
    # 3. Atividades sem oportunidade/lead (órfãs)
    from django.db.models import Q
    filters = (
        Q(oportunidade__vendedor_id=vendedor_id) |
        Q(lead__oportunidades__vendedor_id=vendedor_id) |
        Q(oportunidade__isnull=True, lead__isnull=True)  # Atividades órfãs
    )
    return queryset.filter(filters).distinct()
```

### Deploy v945: Corrigir Invalidação de Cache do Calendário

Atualizado decorator `cache_list_response` para incluir versão na chave de cache:

```python
# Para atividades, incluir versão na chave
if cache_prefix == CRMCacheManager.ATIVIDADES:
    version_key = CRMCacheManager.get_cache_key(
        CRMCacheManager.ATIVIDADES_VERSION,
        loja_id
    )
    version = cache.get(version_key, 0)
    cache_kwargs['v'] = version
```

### Deploy v946: Incluir Atividades Órfãs no Dashboard

Atualizado filtro de atividades na função `dashboard_data`:

```python
if vendedor_id is not None:
    # Atividades: vendedor vê suas atividades + atividades órfãs (sem oportunidade/lead)
    atividades_qs = atividades_qs.filter(
        Q(oportunidade__vendedor_id=vendedor_id) | 
        Q(lead__oportunidades__vendedor_id=vendedor_id) |
        Q(oportunidade__isnull=True, lead__isnull=True)  # Atividades órfãs
    ).distinct()
```

Adicionada invalidação de cache do dashboard ao criar/atualizar/deletar atividades:

```python
def perform_create(self, serializer):
    # ... código existente ...
    loja_id = get_current_loja_id()
    CRMCacheManager.invalidate_atividades(loja_id)
    CRMCacheManager.invalidate_dashboard(loja_id)  # Invalidar dashboard também
```

### Comportamento Após Correção
- ✅ Atividades sem oportunidade/lead aparecem no calendário
- ✅ Atividades aparecem IMEDIATAMENTE após salvar (sem delay de cache)
- ✅ Dashboard mostra atividades órfãs em "Próximas atividades"
- ✅ Vendedores veem suas atividades + atividades órfãs da loja
- ✅ Proprietários veem todas as atividades
- ✅ Cache do dashboard é invalidado ao criar/atualizar/deletar atividades

---

## 📊 Deploy Status

| Deploy | Status | Descrição |
|---|---|---|
| Backend v944 | ✅ Heroku | Permitir atividades órfãs no calendário |
| Backend v945 | ✅ Heroku | Corrigir invalidação de cache do calendário |
| Backend v946 | ✅ Heroku | Incluir atividades órfãs no dashboard |
| Frontend v947 | ✅ Vercel | Corrigir botão "Ver todas" e formato de data |

---

## 🎨 Melhorias de UX (v947)

### Botão "Ver todas"
- Alterado de `<button>` para `<Link>` funcional
- Agora redireciona para `/loja/{slug}/crm-vendas/calendario`

### Formato de Data/Hora
Antes: `2026-03-12T11:30:00+00:00` (ISO format)

Depois:
- `Hoje às 11:30` (se for hoje)
- `Amanhã às 14:30` (se for amanhã)
- `12/03 às 18:30` (outras datas)

### Tipo de Atividade
Antes: `call`, `meeting`, `email`, `task` (inglês)

Depois: `Ligação`, `Reunião`, `E-mail`, `Tarefa` (português)

---

## 🧪 Teste

1. Ir em https://lwksistemas.com.br/loja/felix-5889/crm-vendas/calendario
2. Clicar no botão "+" flutuante (canto inferior direito)
3. Preencher:
   - Título: "Teste de tarefa"
   - Tipo: Tarefa
   - Data e hora: qualquer data/hora
   - Duração: 1 hora
4. Clicar em "Salvar"
5. ✅ A tarefa deve aparecer imediatamente no calendário
6. Ir em https://lwksistemas.com.br/loja/felix-5889/crm-vendas
7. ✅ A tarefa deve aparecer em "Próximas atividades" com formato legível:
   - "Hoje às 14:30" (se for hoje)
   - "Amanhã às 10:00" (se for amanhã)
   - "13/03 às 16:00" (outras datas)
8. ✅ Clicar em "Ver todas" deve redirecionar para o calendário

---

## 📝 Observações

- Não é necessário conectar Google Calendar para criar tarefas
- Sincronização com Google Calendar é opcional e acontece em background
- Atividades órfãs são úteis para tarefas gerais não vinculadas a vendas específicas

---

## 📊 Status Final

| Funcionalidade | Status | Deploy |
|---|---|---|
| Campos de comissão no pipeline | ✅ Completo | v936 |
| Card de comissão total | ✅ Completo | v939 |
| Vinculação ao vendedor logado | ✅ Completo | v940 |
| Pipeline em andamento | ✅ Completo | v941 |
| Próximas atividades | ✅ Completo | v943 |
| Criação de tarefas sem Google | ✅ CORRIGIDO | v944+v945+v946 |

---

## 🔗 URLs de Teste

- Dashboard: https://lwksistemas.com.br/loja/felix-5889/crm-vendas
- Calendário: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/calendario
- Pipeline: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/pipeline

---

## 📝 Próximos Passos

1. Usuário deve fazer hard refresh no celular
2. Testar criação de atividade no calendário
3. Verificar se aparece no dashboard
4. Se persistir o problema, verificar console do navegador para erros
