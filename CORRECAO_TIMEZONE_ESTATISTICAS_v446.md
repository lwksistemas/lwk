# Correção Timezone e Estatísticas - v446

## 📋 Problema Identificado

### 1. Data Incorreta no Frontend
- **Banco de dados**: `2026-04-10` ✅
- **Frontend exibindo**: `09/04/2026` ❌
- **Causa**: Problema de timezone ao converter Date no JavaScript

### 2. Estatísticas Zeradas
- **Dashboard da Loja**: Mostrando 0 cobranças, 0 pagamentos
- **Causa**: Endpoint buscando apenas de `PagamentoLoja`, não do Asaas

### 3. Botão "Ver Boleto" Não Aparecia
- **Causa**: Lógica de exibição dependia de campos que não estavam sendo populados

## 🔧 Correções Implementadas

### Backend (v446)

#### 1. Serialização de Datas sem Timezone
**Arquivo**: `backend/superadmin/financeiro_views.py`

```python
# ANTES
'data_proxima_cobranca': financeiro.data_proxima_cobranca,
'ultimo_pagamento': financeiro.ultimo_pagamento,

# DEPOIS
'data_proxima_cobranca': financeiro.data_proxima_cobranca.strftime('%Y-%m-%d') if financeiro.data_proxima_cobranca else None,
'ultimo_pagamento': financeiro.ultimo_pagamento.strftime('%Y-%m-%d') if financeiro.ultimo_pagamento else None,
```

**Motivo**: Forçar serialização como string no formato ISO sem timezone

#### 2. Estatísticas do Asaas
**Arquivo**: `backend/superadmin/financeiro_views.py`

```python
# Buscar todos os pagamentos do Asaas
todos_pagamentos = AsaasPayment.objects.filter(
    customer=loja_assinatura.asaas_customer
).order_by('-due_date')

# Calcular estatísticas
total_pagamentos_asaas = todos_pagamentos.count()
pagamentos_pagos_asaas = todos_pagamentos.filter(
    status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
).count()
pagamentos_pendentes_asaas = todos_pagamentos.filter(status='PENDING').count()
pagamentos_atrasados_asaas = todos_pagamentos.filter(status='OVERDUE').count()

# Calcular valores
for pag in todos_pagamentos.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']):
    valor_total_pago_asaas += Decimal(str(pag.value))

for pag in todos_pagamentos.filter(status__in=['PENDING', 'OVERDUE']):
    valor_total_pendente_asaas += Decimal(str(pag.value))

# Usar estatísticas do Asaas se disponíveis
total_pagamentos = total_pagamentos_asaas if total_pagamentos_asaas > 0 else total_pagamentos_loja
pagamentos_pagos = pagamentos_pagos_asaas if total_pagamentos_asaas > 0 else pagamentos_pagos_loja
```

**Motivo**: Buscar dados reais do Asaas ao invés de depender apenas de `PagamentoLoja`

### Frontend (v446)

#### 1. Parse Manual de Datas
**Arquivos**: 
- `frontend/components/clinica/modals/ConfiguracoesModal.tsx`
- `frontend/app/(dashboard)/superadmin/financeiro/page.tsx`
- `frontend/app/(dashboard)/loja/[slug]/financeiro/page.tsx`

```typescript
// ANTES
{new Date(dadosFinanceiros.financeiro.data_proxima_cobranca).toLocaleDateString('pt-BR')}

// DEPOIS
{dadosFinanceiros.financeiro.data_proxima_cobranca.split('-').reverse().join('/')}
```

**Motivo**: Evitar conversão de timezone pelo JavaScript

#### 2. Função formatDate Corrigida
```typescript
// ANTES
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('pt-BR');
}

// DEPOIS
const formatDate = (dateString: string) => {
  // Parse manual para evitar problema de timezone
  const [year, month, day] = dateString.split('T')[0].split('-');
  return `${day}/${month}/${year}`;
}
```

## ✅ Resultado

### Datas Corretas
- ✅ SuperAdmin Financeiro: `10/04/2026`
- ✅ Dashboard da Loja: `10/04/2026`
- ✅ Modal Configurações: `10/04/2026`

### Estatísticas Corretas
- ✅ Total de Cobranças: 2 (busca do Asaas)
- ✅ Pagamentos Realizados: 1 (busca do Asaas)
- ✅ Pendentes: 1 (busca do Asaas)
- ✅ Valores corretos de pagamentos

### Botão Ver Boleto
- ✅ Aparece quando há `boleto_url` disponível
- ✅ Busca do próximo boleto pendente no Asaas

## 🔍 Explicação Técnica

### Por que o problema acontecia?

1. **Timezone no JavaScript**:
   - String `"2026-04-10"` é interpretada como UTC 00:00
   - Ao converter para timezone local (Brasil UTC-3), subtrai 3 horas
   - Resultado: `2026-04-09 21:00` → exibido como `09/04/2026`

2. **Solução**:
   - Backend: Serializar como string ISO sem timezone
   - Frontend: Parse manual sem criar objeto Date

### Por que as estatísticas estavam zeradas?

1. **Problema**:
   - Endpoint buscava apenas de `PagamentoLoja`
   - Pagamentos reais estavam no Asaas (`AsaasPayment`)

2. **Solução**:
   - Buscar todos os pagamentos do Asaas
   - Calcular estatísticas baseadas nos dados reais
   - Usar como fallback os dados de `PagamentoLoja` se Asaas não disponível

## 📊 Status Atual

### Loja Luiz Salao
- ✅ Próximo vencimento: 10/04/2026
- ✅ Último pagamento: 07/02/2026
- ✅ Total de cobranças: 2
- ✅ Pagamentos realizados: 1
- ✅ Boleto disponível para próximo pagamento
- ✅ Dia de vencimento: Todo dia 10

### Consistência
- ✅ SuperAdmin Financeiro = Dashboard da Loja
- ✅ Banco de dados = Frontend
- ✅ Estatísticas refletem dados reais do Asaas

## 🚀 Deploy

- **Backend**: v446 - Heroku ✅
- **Frontend**: v446 - Vercel ✅
- **Data**: 07/02/2026

## 📝 Arquivos Modificados

### Backend
- `backend/superadmin/financeiro_views.py`

### Frontend
- `frontend/components/clinica/modals/ConfiguracoesModal.tsx`
- `frontend/app/(dashboard)/superadmin/financeiro/page.tsx`
- `frontend/app/(dashboard)/loja/[slug]/financeiro/page.tsx`

## 🎯 Próximos Passos

1. ✅ Testar em produção
2. ✅ Verificar se data está correta em todos os lugares
3. ✅ Verificar se estatísticas estão corretas
4. ✅ Verificar se botão "Ver Boleto" aparece
5. ⏳ Monitorar próximo pagamento automático
