# Correção: Vencimento Incorreto para Planos Anuais

## 🐛 Problema Identificado

Cliente **Dani Pitakos** pagou plano anual em **09/04/2026**, mas o sistema estava mostrando:
- **Próximo Pagamento: 09/04/2026** (mesma data do pagamento!)
- **Deveria mostrar: 09/04/2027** (1 ano depois)

### Causa Raiz

O código estava calculando a próxima data de vencimento SEMPRE adicionando **30 dias**, independente do tipo de assinatura (mensal ou anual).

## ✅ Solução Implementada

### 1. Correção no `sync_service.py`

**Arquivo:** `backend/superadmin/sync_service.py`

**Antes:**
```python
# Calcular próxima data de cobrança: data do pagamento + 30 dias
proxima_data_cobranca = data_pagamento + timedelta(days=30)
```

**Depois:**
```python
# Calcular próxima data de cobrança baseada no tipo de assinatura
if tipo_assinatura == 'anual':
    dias_adicionar = 365
    proxima_data_cobranca = data_pagamento + timedelta(days=dias_adicionar)
else:  # mensal
    dias_adicionar = 30
    proxima_data_cobranca = data_pagamento + timedelta(days=dias_adicionar)
```

### 2. Correção no `financeiro_service.py`

**Arquivo:** `backend/superadmin/services/financeiro_service.py`

**Método:** `calcular_proxima_cobranca()`

**Antes:**
```python
def calcular_proxima_cobranca(dia_vencimento: int) -> date:
    # Sempre calculava para o próximo mês
    if hoje.month == 12:
        proximo_mes = 1
        proximo_ano = hoje.year + 1
    else:
        proximo_mes = hoje.month + 1
        proximo_ano = hoje.year
```

**Depois:**
```python
def calcular_proxima_cobranca(dia_vencimento: int, tipo_assinatura: str = 'mensal') -> date:
    if tipo_assinatura == 'anual':
        # Para assinatura anual, adicionar 1 ano
        proximo_ano = hoje.year + 1
        proximo_mes = hoje.month
    else:
        # Para assinatura mensal, calcular próximo mês
        if hoje.month == 12:
            proximo_mes = 1
            proximo_ano = hoje.year + 1
        else:
            proximo_mes = hoje.month + 1
            proximo_ano = hoje.year
```

### 3. Correção no `cobranca_service.py`

**Arquivo:** `backend/superadmin/cobranca_service.py`

**Método:** `_calcular_proxima_cobranca()`

Mesma lógica aplicada: agora considera o tipo de assinatura (mensal ou anual).

## 🔧 Como Corrigir o Cliente Específico

Execute o script de correção:

```bash
cd backend
python corrigir_vencimento_dani_pitakos.py
```

O script irá:
1. Buscar a loja do cliente pelo email `dani.rfoliveira@gmail.com`
2. Mostrar os dados atuais (incorretos)
3. Calcular a data correta (09/04/2027 para plano anual)
4. Pedir confirmação
5. Atualizar `FinanceiroLoja.data_proxima_cobranca`
6. Atualizar `LojaAssinatura.data_vencimento`

## 📊 Impacto

### Clientes Afetados
- Todos os clientes com **plano anual** que pagaram após a implementação do sistema
- A próxima data de vencimento estava sendo calculada como 30 dias após o pagamento

### Correção Automática
- A partir de agora, todos os novos pagamentos de planos anuais serão calculados corretamente
- Clientes existentes com plano anual precisam ter a data corrigida manualmente usando o script

## 🧪 Como Testar

### Teste 1: Pagamento de Plano Mensal
```python
# Simular pagamento em 09/04/2026
# Próximo vencimento deve ser: 09/05/2026 (30 dias depois)
```

### Teste 2: Pagamento de Plano Anual
```python
# Simular pagamento em 09/04/2026
# Próximo vencimento deve ser: 09/04/2027 (365 dias depois)
```

## 📝 Arquivos Modificados

1. `backend/superadmin/sync_service.py` - Linha ~525-545
2. `backend/superadmin/services/financeiro_service.py` - Linha ~49-85
3. `backend/superadmin/cobranca_service.py` - Linha ~316-350

## 🚀 Deploy

Após fazer o deploy das correções:

1. Execute o script de correção para o cliente Dani Pitakos
2. Identifique outros clientes com plano anual que possam estar afetados
3. Execute o script de correção para cada um deles

## ⚠️ Observações

- A correção só afeta o cálculo da **próxima data de vencimento**
- Não afeta pagamentos já realizados ou histórico
- Clientes com plano mensal não são afetados (já estava correto)
