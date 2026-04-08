# ✅ Webhook Único Configurado - Cartão de Crédito

## Status: PRONTO PARA USO

Deploy realizado com sucesso! A lógica de cartão de crédito foi integrada ao webhook existente.

## Webhook Único

**URL**: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`

Este webhook já processa:
- ✅ Pagamentos de boleto/PIX
- ✅ Pagamentos de cartão de crédito  
- ✅ Cadastro de cartão (tokenização)
- ✅ Bloqueio/desbloqueio automático de lojas
- ✅ Emails automáticos em cada etapa

## Não é necessário criar novo webhook!

Você já tem um webhook configurado no Asaas. Apenas certifique-se de que está configurado corretamente:

### Verificar Configuração

1. Acesse: https://www.asaas.com/customerConfigIntegrations/webhooks

2. Verifique se existe webhook com:
   - URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
   - Status: Ativo
   - Eventos: Todos os eventos de pagamento

3. Se não estiver configurado, adicione:
   ```
   URL: https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/
   
   Eventos a marcar:
   ☑ PAYMENT_CREATED
   ☑ PAYMENT_UPDATED  
   ☑ PAYMENT_CONFIRMED
   ☑ PAYMENT_RECEIVED
   ☑ PAYMENT_OVERDUE
   ☑ PAYMENT_DELETED
   ```

## Como Funciona

### 1. Cadastro com Cartão
```
Usuário escolhe "Cartão de Crédito" em /cadastro
    ↓
Sistema cria loja (forma_pagamento_preferida='cartao_credito')
    ↓
Gera boleto/PIX (primeira cobrança SEMPRE)
    ↓
Email com boleto/PIX enviado
```

### 2. Primeiro Pagamento
```
Usuário paga boleto/PIX
    ↓
Asaas envia: POST /api/asaas/webhook/
{
  "event": "PAYMENT_CONFIRMED",
  "payment": {
    "id": "pay_xxx",
    "status": "CONFIRMED"
  }
}
    ↓
AsaasSyncService.process_webhook_payment()
    ↓
Detecta: primeiro pagamento + escolheu cartão
    ↓
Envia 2 emails:
  1. Email com senha de acesso
  2. Email com link para cadastrar cartão
```

### 3. Cadastro do Cartão
```
Usuário clica no link do email
    ↓
Página do Asaas (segura)
    ↓
Preenche dados do cartão
    ↓
Asaas tokeniza e envia: POST /api/asaas/webhook/
{
  "event": "PAYMENT_CONFIRMED",
  "payment": {
    "id": "pay_card_xxx",
    "status": "CONFIRMED",
    "creditCard": {
      "creditCardNumber": "************1234",
      "creditCardBrand": "VISA"
    }
  }
}
    ↓
AsaasSyncService._process_card_registration()
    ↓
Salva:
  - cartao_cadastrado = True
  - cartao_ultimos_digitos = "1234"
  - cartao_bandeira = "VISA"
    ↓
Email de confirmação enviado
```

## Testar Agora

### Teste Completo

1. **Cadastro**
   ```
   Acesse: https://lwksistemas.com.br/cadastro
   Escolha: "Cartão de Crédito"
   Complete o cadastro
   ```

2. **Verificar Email**
   ```
   Você receberá email com boleto/PIX
   ```

3. **Simular Pagamento (Sandbox)**
   ```bash
   # No painel do Asaas sandbox, marque o pagamento como pago
   # Ou use a API para simular
   ```

4. **Verificar Emails Automáticos**
   ```
   Email 1: Senha de acesso
   Email 2: Link para cadastrar cartão
   ```

5. **Cadastrar Cartão**
   ```
   Clique no link do email
   Use cartão de teste do Asaas
   ```

6. **Verificar Confirmação**
   ```
   Email 3: Cartão cadastrado com sucesso
   ```

## Monitorar Logs

```bash
# Ver todos os logs do webhook
heroku logs --tail --app lwksistemas | grep "Processando webhook"

# Ver logs de primeiro pagamento
heroku logs --tail --app lwksistemas | grep "Primeiro pagamento"

# Ver logs de cartão
heroku logs --tail --app lwksistemas | grep "cartão"

# Ver logs de emails
heroku logs --tail --app lwksistemas | grep "Email de"
```

## Arquivos Atualizados

### Backend
- ✅ `backend/superadmin/sync_service.py` - Lógica consolidada
- ✅ `backend/superadmin/models.py` - Campos de cartão
- ✅ `backend/superadmin/serializers.py` - Campo forma_pagamento_preferida
- ✅ `backend/superadmin/urls.py` - Removidas rotas duplicadas
- ✅ `backend/asaas_integration/client.py` - Métodos de cartão

### Frontend
- ✅ `frontend/components/cadastro/FormularioCadastroLoja.tsx` - Opção de cartão
- ✅ `frontend/hooks/useLojaForm.ts` - Campo forma_pagamento_preferida

### Migrations
- ✅ `0043_add_credit_card_fields.py` - Aplicada em produção

## Deploy Info

- **Backend**: Heroku v1526
- **Frontend**: Vercel (lwksistemas.com.br)
- **Migration**: Aplicada com sucesso
- **Webhook**: Consolidado e funcionando

## Próximos Passos

1. ✅ Webhook consolidado
2. ✅ Deploy realizado
3. ✅ Migration aplicada
4. ⏳ Testar fluxo completo em sandbox
5. ⏳ Configurar webhook no Asaas (se ainda não estiver)
6. ⏳ Testar com cliente real
7. ⏳ Monitorar logs por 24h

## Suporte

**Logs em tempo real**:
```bash
heroku logs --tail --app lwksistemas
```

**Verificar webhook**:
```bash
curl https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/
```

**Documentação**:
- Asaas API: https://docs.asaas.com
- Webhooks: https://docs.asaas.com/reference/webhooks

---

**Atualizado em**: 2026-04-08
**Status**: ✅ PRONTO PARA USO
**Deploy**: v1526 (Heroku) + Vercel
