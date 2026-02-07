# Correção Data Próxima Cobrança v433 e v434

## Problema Identificado
A `data_proxima_cobranca` estava sendo calculada incorretamente em DOIS momentos:

### 1. Na Criação da Loja (v434) ❌
Quando criava uma loja, o sistema calculava a próxima cobrança no MÊS ATUAL se o dia ainda não tivesse passado.

**Exemplo do problema:**
- Criação da loja: 07/02/2026
- Dia de vencimento: 8
- Data próxima cobrança calculada: **08/02/2026** (mês atual) ❌
- Data próxima cobrança esperada: **08/03/2026** (próximo mês) ✅

### 2. Após Pagamento do Boleto (v433) ❌
Após o pagamento, a data não estava sendo atualizada para o próximo mês.

**Exemplo do problema:**
- Pagamento realizado em: 07/02/2026
- Data próxima cobrança mostrada: 09/02/2026 ❌
- Data próxima cobrança esperada: 10/03/2026 ✅

## Causa Raiz

### v433: Webhook após pagamento
O método `_update_loja_financeiro_from_payment` em `backend/superadmin/sync_service.py` não estava calculando a próxima data de cobrança baseada no `dia_vencimento` configurado.

### v434: Criação da loja
O método `create` em `backend/superadmin/serializers.py` tinha lógica incorreta:
```python
# CÓDIGO ANTIGO (ERRADO)
if hoje.day <= dia_vencimento:
    # Próxima cobrança neste mês ❌
    proxima_cobranca = date(hoje.year, hoje.month, dia_vencimento)
else:
    # Próxima cobrança no próximo mês
    proxima_cobranca = date(hoje.year, hoje.month + 1, dia_vencimento)
```

Isso causava cobrança no mês atual quando o dia ainda não tinha passado.

## Solução Implementada

### v433: Backend sync_service.py (Webhook)
Modificado o método `_update_loja_financeiro_from_payment` para calcular corretamente após pagamento.

### v434: Backend serializers.py (Criação da Loja)
Modificado o método `create` para SEMPRE calcular a próxima cobrança no PRÓXIMO MÊS.

### Lógica Implementada (ambos os casos)

1. **Calcular próximo mês corretamente**
   - Considera virada de ano (dezembro → janeiro)
   - Usa `date.today()` como referência

2. **Ajustar dia de vencimento**
   - Usa `calendar.monthrange()` para obter último dia do mês
   - Ajusta automaticamente dias inválidos (ex: dia 31 em fevereiro vira dia 28/29)

3. **Definir próxima data de cobrança**
   - Calcula: `date(proximo_ano, proximo_mes, dia_cobranca)`
   - Respeita o `dia_vencimento` configurado no financeiro
   - **SEMPRE no próximo mês** (nunca no mês atual)

### Código Implementado
```python
from datetime import date
from calendar import monthrange

# Calcular próxima cobrança SEMPRE no próximo mês
hoje = date.today()
dia_vencimento = financeiro.dia_vencimento  # ou variável dia_vencimento

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
proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
```

## Arquivos Modificados
- `backend/superadmin/sync_service.py` (v433 - linhas 476-530)
- `backend/superadmin/serializers.py` (v434 - linhas 315-335)

## Deploy Realizado
- **Versão v433**: Correção webhook após pagamento
- **Versão v434**: Correção criação da loja
- **Data**: 07/02/2026
- **Plataforma**: Heroku
- **Status**: ✅ Sucesso

## Como Testar

### 1. Criar Nova Loja
```
https://lwksistemas.com.br/superadmin/lojas
```
- Criar loja com dia de vencimento 8
- Verificar no modal de Configurações
- Deve mostrar: **08/03/2026** (próximo mês, não mês atual)

### 2. Verificar no SuperAdmin Financeiro
```
https://lwksistemas.com.br/superadmin/financeiro
```
- Localizar a nova loja
- Verificar campo "Próximo Vencimento"
- Deve mostrar: **08/03/2026**

### 3. Pagar Boleto e Verificar Atualização
- Pagar o boleto da assinatura
- Aguardar webhook do Asaas
- Verificar se `data_proxima_cobranca` foi atualizada para dia 8 do próximo mês
- Exemplo: pagamento em 07/02/2026 → próxima cobrança: **08/03/2026**

## Comportamento Esperado

### Cenários de Teste - Criação da Loja
| Criação em   | Dia Vencimento | Próxima Cobrança |
|--------------|----------------|------------------|
| 07/02/2026   | 8              | 08/03/2026       |
| 07/02/2026   | 10             | 10/03/2026       |
| 15/03/2026   | 10             | 10/04/2026       |
| 28/12/2026   | 10             | 10/01/2027       |
| 05/01/2026   | 31             | 28/02/2026*      |

### Cenários de Teste - Após Pagamento
| Pagamento em | Dia Vencimento | Próxima Cobrança |
|--------------|----------------|------------------|
| 07/02/2026   | 8              | 08/03/2026       |
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
1. ✅ Excluir loja de teste antiga (salao-luizao-5889)
2. ✅ Criar nova loja de teste
3. ✅ Verificar se data está correta na criação (próximo mês)
4. ✅ Pagar boleto da nova loja
5. ✅ Verificar se data está correta após pagamento (próximo mês)
6. ✅ Confirmar que webhook está atualizando corretamente

## Observações
- A correção é aplicada em DOIS momentos: criação da loja E após pagamento
- Próxima cobrança SEMPRE será no próximo mês (nunca no mês atual)
- Não afeta cobranças já criadas no Asaas (apenas cálculo interno)
- Respeita o `dia_vencimento` configurado em cada loja
- Ajusta automaticamente dias inválidos (ex: 31 de fevereiro → 28/29)
