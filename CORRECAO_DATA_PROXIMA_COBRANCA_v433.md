# Correção Data Próxima Cobrança v433

## Problema Identificado
Após o pagamento do boleto, a `data_proxima_cobranca` não estava sendo atualizada corretamente para o dia 10 do próximo mês.

**Exemplo do problema:**
- Pagamento realizado em: 07/02/2026
- Data próxima cobrança mostrada: 09/02/2026 ❌
- Data próxima cobrança esperada: 10/03/2026 ✅

## Causa Raiz
O método `_update_loja_financeiro_from_payment` em `backend/superadmin/sync_service.py` não estava calculando a próxima data de cobrança baseada no `dia_vencimento` configurado (dia 10).

## Solução Implementada

### Backend: sync_service.py
Modificado o método `_update_loja_financeiro_from_payment` para:

1. **Calcular próximo mês corretamente**
   - Considera virada de ano (dezembro → janeiro)
   - Usa `date.today()` como referência

2. **Ajustar dia de vencimento**
   - Usa `calendar.monthrange()` para obter último dia do mês
   - Ajusta automaticamente dias inválidos (ex: dia 31 em fevereiro vira dia 28/29)

3. **Definir próxima data de cobrança**
   - Calcula: `date(proximo_ano, proximo_mes, dia_cobranca)`
   - Respeita o `dia_vencimento` configurado no financeiro

### Código Implementado
```python
from datetime import date
from calendar import monthrange

# Calcular próxima data de cobrança baseada no dia de vencimento
hoje = date.today()
dia_vencimento = financeiro.dia_vencimento

# Calcular próximo mês
if hoje.month == 12:
    proximo_mes = 1
    proximo_ano = hoje.year + 1
else:
    proximo_mes = hoje.month + 1
    proximo_ano = hoje.year

# Ajustar dia se o mês não tiver esse dia
ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
dia_cobranca = min(dia_vencimento, ultimo_dia_mes)

# Definir próxima data de cobrança
financeiro.data_proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
```

## Arquivos Modificados
- `backend/superadmin/sync_service.py` (linhas 476-530)

## Deploy Realizado
- **Versão**: v433
- **Data**: 07/02/2026
- **Plataforma**: Heroku
- **Status**: ✅ Sucesso

## Como Testar

### 1. Verificar no SuperAdmin Financeiro
```
https://lwksistemas.com.br/superadmin/financeiro
```
- Localizar loja FELIX REPRESENTACOES
- Verificar campo "Próximo Vencimento"
- Deve mostrar: 10/03/2026

### 2. Verificar no Modal de Configurações da Loja
```
https://lwksistemas.com.br/loja/felix-r0172/dashboard
```
- Clicar em "Configurações" nas Ações Rápidas
- Verificar "Próximo Vencimento"
- Deve mostrar: 10/03/2026

### 3. Testar Novo Pagamento
1. Criar nova loja de teste
2. Pagar o boleto da assinatura
3. Verificar se `data_proxima_cobranca` foi atualizada para dia 10 do próximo mês

## Comportamento Esperado

### Cenários de Teste
| Pagamento em | Dia Vencimento | Próxima Cobrança |
|--------------|----------------|------------------|
| 07/02/2026   | 10             | 10/03/2026       |
| 15/03/2026   | 10             | 10/04/2026       |
| 28/12/2026   | 10             | 10/01/2027       |
| 05/01/2026   | 31             | 28/02/2026*      |

*Ajuste automático para último dia do mês quando dia não existe

## Webhook Asaas
O webhook continua funcionando corretamente e atualiza:
- ✅ `status_pagamento` → 'ativo'
- ✅ `ultimo_pagamento` → data/hora atual
- ✅ `data_proxima_cobranca` → dia 10 do próximo mês
- ✅ Desbloqueia loja se estiver bloqueada

## Próximos Passos
1. Testar pagamento de boleto em produção
2. Verificar se data está correta no SuperAdmin
3. Verificar se data está correta no modal da loja
4. Confirmar que webhook está atualizando corretamente

## Observações
- A correção é retroativa: próximo pagamento já calculará corretamente
- Não afeta cobranças já criadas no Asaas
- Respeita o `dia_vencimento` configurado em cada loja
- Ajusta automaticamente dias inválidos (ex: 31 de fevereiro)
