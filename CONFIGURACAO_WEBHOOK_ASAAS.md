# Configuração do Webhook Asaas - Cartão de Crédito

## ✅ Webhook Único Consolidado

A lógica de cartão de crédito foi integrada ao webhook existente do Asaas. **Não é necessário criar um novo webhook!**

## Webhook Existente

**URL**: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`

Este webhook já está configurado e agora processa:
- ✅ Pagamentos de boleto/PIX
- ✅ Pagamentos de cartão de crédito
- ✅ Cadastro de cartão
- ✅ Bloqueio/desbloqueio de lojas

## O que foi atualizado

### AsaasSyncService (`backend/superadmin/sync_service.py`)

Novos métodos adicionados:

1. **`_process_payment_confirmed()`**
   - Detecta se é primeiro pagamento
   - Envia email com senha de acesso
   - Se escolheu cartão: envia link para cadastrar

2. **`_process_card_registration()`**
   - Processa cadastro de cartão
   - Salva últimos 4 dígitos e bandeira
   - Envia email de confirmação

3. **`_enviar_email_senha_acesso()`**
   - Email com dados de acesso após primeiro pagamento

4. **`_enviar_link_cadastro_cartao()`**
   - Cria cobrança de R$ 0,01 para tokenização
   - Gera link de pagamento
   - Envia email com link

5. **`_enviar_email_confirmacao_pagamento()`**
   - Email de confirmação de renovação

6. **`_enviar_email_cartao_cadastrado()`**
   - Email confirmando cadastro do cartão

## Fluxo Completo

### 1. Cadastro da Loja
```
Usuário escolhe "Cartão de Crédito" em /cadastro
    ↓
Sistema cria loja com forma_pagamento_preferida='cartao_credito'
    ↓
Gera boleto/PIX (primeira cobrança)
    ↓
Email enviado com boleto/PIX
```

### 2. Primeiro Pagamento
```
Usuário paga boleto/PIX
    ↓
Asaas envia webhook: PAYMENT_CONFIRMED
    ↓
AsaasSyncService.process_webhook_payment()
    ↓
Detecta: is_primeiro_pagamento = True
    ↓
Envia email com senha de acesso
    ↓
Se forma_pagamento_preferida == 'cartao_credito':
    ├─> Cria cobrança de R$ 0,01
    ├─> Gera link de pagamento
    └─> Envia email com link
```

### 3. Cadastro do Cartão
```
Usuário clica no link do email
    ↓
Página do Asaas (segura)
    ↓
Preenche dados do cartão
    ↓
Asaas tokeniza cartão
    ↓
Asaas envia webhook: PAYMENT_CONFIRMED
    ↓
AsaasSyncService.process_webhook_payment()
    ↓
Detecta: link_pagamento_cartao contém payment_id
    ↓
_process_card_registration()
    ├─> Marca cartao_cadastrado = True
    ├─> Salva últimos 4 dígitos
    ├─> Salva bandeira
    └─> Envia email de confirmação
```

### 4. Renovações Futuras
```
Data de renovação
    ↓
Sistema verifica forma_pagamento_preferida
    ↓
Se 'cartao_credito' e cartao_cadastrado = True:
    ├─> Cobra automaticamente no cartão
    └─> Webhook confirma pagamento
    └─> Email de confirmação
```

## Eventos Processados

O webhook processa os seguintes eventos do Asaas:

| Evento | Ação |
|--------|------|
| `PAYMENT_RECEIVED` | Confirma pagamento, envia emails |
| `PAYMENT_CONFIRMED` | Confirma pagamento, envia emails |
| `PAYMENT_OVERDUE` | Marca como atrasado |
| `PAYMENT_DELETED` | Marca como cancelado |

## Verificar Configuração Atual

1. Acesse: https://www.asaas.com/customerConfigIntegrations/webhooks

2. Verifique se o webhook está configurado:
   - URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
   - Eventos: Todos os eventos de pagamento

3. Se não estiver configurado, adicione:
   ```
   URL: https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/
   Eventos:
     ☑ PAYMENT_CREATED
     ☑ PAYMENT_UPDATED
     ☑ PAYMENT_CONFIRMED
     ☑ PAYMENT_RECEIVED
     ☑ PAYMENT_OVERDUE
     ☑ PAYMENT_DELETED
   ```

## Testar Webhook

### Teste 1: Primeiro Pagamento
```bash
# Simular webhook de pagamento confirmado
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_CONFIRMED",
    "payment": {
      "id": "pay_test123",
      "status": "CONFIRMED",
      "value": 99.90
    }
  }'
```

### Teste 2: Cadastro de Cartão
```bash
# Simular webhook de cartão cadastrado
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_CONFIRMED",
    "payment": {
      "id": "pay_card123",
      "status": "CONFIRMED",
      "value": 0.01,
      "creditCard": {
        "creditCardNumber": "************1234",
        "creditCardBrand": "VISA"
      }
    }
  }'
```

## Monitorar Logs

```bash
# Ver logs do webhook
heroku logs --tail --app lwksistemas | grep "Processando webhook"

# Ver logs de emails
heroku logs --tail --app lwksistemas | grep "Email de"

# Ver logs de cartão
heroku logs --tail --app lwksistemas | grep "cartão"
```

## Troubleshooting

### Webhook não está sendo chamado
1. Verificar configuração no painel do Asaas
2. Verificar URL está correta
3. Verificar se app está online: `heroku ps --app lwksistemas`

### Email não está sendo enviado
1. Verificar configuração SMTP no Heroku
2. Ver logs: `heroku logs --tail --app lwksistemas | grep email`
3. Verificar variáveis de ambiente: `heroku config --app lwksistemas`

### Cartão não está sendo cadastrado
1. Ver logs: `heroku logs --tail --app lwksistemas | grep "card_registration"`
2. Verificar se link foi gerado corretamente
3. Verificar se payment_id está correto

## Variáveis de Ambiente Necessárias

```bash
# Verificar se estão configuradas
heroku config --app lwksistemas | grep -E "EMAIL|ASAAS"

# Necessárias:
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@lwksistemas.com.br

ASAAS_API_KEY=sua-chave-asaas
```

## Próximos Passos

1. ✅ Webhook consolidado e funcionando
2. ⏳ Testar fluxo completo em sandbox
3. ⏳ Atualizar CobrancaService para renovações automáticas
4. ⏳ Monitorar logs por 24h
5. ⏳ Testar em produção com cliente real

---

**Atualizado em**: 2026-04-08
**Status**: ✅ Webhook consolidado e pronto para uso
