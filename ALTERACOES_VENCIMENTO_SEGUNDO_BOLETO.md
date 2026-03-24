# Alteração: Vencimento do Segundo Boleto - 30 Dias Após Pagamento

## Resumo
Modificado o cálculo do vencimento do segundo boleto (e subsequentes) para ser 30 dias após a data do pagamento do boleto anterior, ao invés de ser baseado na data de criação da loja.

## Problema Anterior
- O sistema calculava o vencimento do próximo boleto baseado na data de vencimento atual + 1 mês
- Exemplo: Se a loja foi criada dia 15/03 e o primeiro boleto vencia dia 15/04, o segundo vencia dia 15/05
- Isso não considerava quando o cliente efetivamente pagou o boleto

## Solução Implementada
- Agora o vencimento do próximo boleto é calculado como: **data do pagamento + 30 dias**
- Exemplo: Se o cliente pagar o primeiro boleto dia 20/04, o segundo boleto vencerá dia 20/05
- Isso garante que o cliente sempre tenha 30 dias após pagar para o próximo vencimento

## Arquivos Modificados

### backend/superadmin/sync_service.py
**Método:** `_update_loja_financeiro_from_payment`

**Alteração:**
```python
# ANTES: Calculava baseado na data de vencimento atual + 1 mês
data_vencimento_atual = financeiro.data_proxima_cobranca
if data_vencimento_atual.month == 12:
    proximo_mes = 1
    proximo_ano = data_vencimento_atual.year + 1
else:
    proximo_mes = data_vencimento_atual.month + 1
    proximo_ano = data_vencimento_atual.year
proxima_data_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)

# DEPOIS: Calcula baseado na data do pagamento + 30 dias
data_pagamento = timezone.now().date()
proxima_data_cobranca = data_pagamento + timedelta(days=30)
```

## Fluxo Completo

1. **Cliente cria loja** → Primeiro boleto é gerado com vencimento baseado no dia configurado
2. **Cliente paga primeiro boleto** → Webhook do Asaas notifica o sistema
3. **Sistema processa pagamento** → Método `process_webhook_payment` é chamado
4. **Atualiza financeiro** → Método `_update_loja_financeiro_from_payment` calcula próxima cobrança
5. **Novo boleto é gerado** → Vencimento = data do pagamento + 30 dias
6. **Cliente recebe senha provisória** → Email enviado automaticamente após confirmação do pagamento

## Exemplo Prático

### Cenário 1: Pagamento no Vencimento
- Loja criada: 01/03/2026
- Primeiro boleto vence: 10/04/2026
- Cliente paga: 10/04/2026
- Segundo boleto vence: **10/05/2026** (10/04 + 30 dias)

### Cenário 2: Pagamento Antecipado
- Loja criada: 01/03/2026
- Primeiro boleto vence: 10/04/2026
- Cliente paga: 05/04/2026 (5 dias antes)
- Segundo boleto vence: **05/05/2026** (05/04 + 30 dias)

### Cenário 3: Pagamento Atrasado
- Loja criada: 01/03/2026
- Primeiro boleto vence: 10/04/2026
- Cliente paga: 20/04/2026 (10 dias depois)
- Segundo boleto vence: **20/05/2026** (20/04 + 30 dias)

## Benefícios

1. **Flexibilidade para o cliente**: Se pagar antecipado, ganha mais tempo até o próximo vencimento
2. **Justiça no atraso**: Se pagar atrasado, não perde dias do próximo período
3. **Simplicidade**: Sempre 30 dias após o pagamento, fácil de entender
4. **Previsibilidade**: Cliente sabe exatamente quando vence o próximo boleto

## Deploy

- **Versão:** v1297
- **Data:** 24/03/2026
- **Ambiente:** Heroku (Produção)
- **Branch:** master

## Testes Recomendados

1. Criar uma loja de teste
2. Pagar o primeiro boleto via sandbox do Asaas
3. Verificar se o segundo boleto foi gerado com vencimento 30 dias após o pagamento
4. Verificar se o email com senha provisória foi enviado
5. Verificar se a loja foi desbloqueada (se estava bloqueada)

## Observações

- A alteração afeta apenas boletos gerados **após o primeiro pagamento**
- O primeiro boleto continua sendo gerado com base no dia de vencimento configurado na loja
- Lojas existentes não são afetadas retroativamente
- O campo `dia_vencimento` no FinanceiroLoja ainda é usado para referência, mas não mais para cálculo do próximo vencimento

## Logs

O sistema registra logs detalhados do processo:
```
📅 Cálculo de próxima cobrança:
   - Data do Pagamento: 2026-04-20
   - Dia Vencimento Configurado: 10
   - Próxima Cobrança Calculada (30 dias após pagamento): 2026-05-20
   - Diferença: 2026-04-20 → 2026-05-20 (30 dias)
```

## Contato

Para dúvidas ou problemas relacionados a esta alteração, contate o desenvolvedor.
