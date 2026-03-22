# Configuração do Webhook Asaas - Guia Passo a Passo

## 📋 Informações Necessárias

### URL do Webhook
```
https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/
```

### Nome do Webhook (sugestão)
```
LWK Sistemas - Webhook Produção
```

### Eventos a Configurar
Marque os seguintes eventos no painel Asaas:

- ✅ **PAYMENT_CREATED** - Cobrança criada
- ✅ **PAYMENT_UPDATED** - Cobrança atualizada
- ✅ **PAYMENT_CONFIRMED** - Pagamento confirmado
- ✅ **PAYMENT_RECEIVED** - Pagamento recebido
- ✅ **PAYMENT_OVERDUE** - Pagamento vencido
- ✅ **PAYMENT_DELETED** - Cobrança excluída
- ✅ **PAYMENT_RESTORED** - Cobrança restaurada

---

## 🔧 Passo a Passo no Painel Asaas

### 1. Acessar o Painel Asaas
- URL: https://www.asaas.com/
- Faça login com suas credenciais de **PRODUÇÃO**

### 2. Navegar até Webhooks
1. No menu lateral, clique em **"Integrações"**
2. Clique em **"Webhooks"**
3. Clique no botão **"Novo Webhook"** ou **"Adicionar Webhook"**

### 3. Preencher Formulário

#### Campo: Nome do Webhook
```
LWK Sistemas - Webhook Produção
```

#### Campo: URL do Webhook
```
https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/
```

⚠️ **IMPORTANTE:** 
- A URL deve terminar com `/` (barra final)
- Deve começar com `https://` (não `http://`)
- Copie e cole exatamente como está acima

#### Campo: Eventos
Marque os seguintes checkboxes:

```
☑ PAYMENT_CREATED
☑ PAYMENT_UPDATED
☑ PAYMENT_CONFIRMED
☑ PAYMENT_RECEIVED
☑ PAYMENT_OVERDUE
☑ PAYMENT_DELETED
☑ PAYMENT_RESTORED
```

#### Campo: Status
```
☑ Ativo
```

### 4. Salvar Configuração
- Clique no botão **"Salvar"** ou **"Criar Webhook"**
- Aguarde confirmação de sucesso

### 5. Testar Webhook (Opcional)
1. Após salvar, clique no webhook criado
2. Procure por opção **"Testar Webhook"** ou **"Enviar Teste"**
3. Clique para enviar um evento de teste
4. Verifique se o sistema recebeu (ver logs do Heroku)

---

## ✅ Verificação da Configuração

### 1. Verificar no Painel Asaas
Após salvar, você deve ver:
- ✅ Webhook listado na página de Webhooks
- ✅ Status: **Ativo**
- ✅ URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
- ✅ Eventos: 7 eventos configurados

### 2. Verificar Logs do Heroku
Execute o comando:
```bash
heroku logs --tail --app lwksistemas
```

Se o teste foi enviado, você deve ver algo como:
```
Webhook Asaas recebido: {'event': 'PAYMENT_CREATED', ...}
```

### 3. Testar com Pagamento Real
Após configurar, faça um teste completo:
1. Cadastre uma loja de teste
2. Pague o boleto (ou use PIX)
3. Aguarde alguns minutos
4. Verifique se o webhook foi recebido nos logs
5. Verifique se a senha foi enviada por email

---

## 🔍 Monitoramento de Webhooks

### Ver Histórico de Webhooks no Asaas
1. Acesse o painel Asaas
2. Menu: **Integrações** → **Webhooks**
3. Clique no webhook configurado
4. Procure por aba **"Histórico"** ou **"Logs"**
5. Você verá:
   - Data/hora de cada envio
   - Evento enviado
   - Status da resposta (200 OK, 400 Error, etc.)
   - Tempo de resposta

### Ver Logs no Heroku
```bash
# Ver todos os logs
heroku logs --tail --app lwksistemas

# Filtrar apenas webhooks
heroku logs --tail --app lwksistemas | grep -i webhook

# Filtrar apenas erros
heroku logs --tail --app lwksistemas | grep -i error
```

---

## 🚨 Problemas Comuns e Soluções

### Problema 1: Webhook não está sendo recebido
**Sintomas:**
- Pagamento confirmado no Asaas
- Nada aparece nos logs do Heroku
- Senha não é enviada

**Soluções:**
1. Verificar se URL está correta (com `/` no final)
2. Verificar se webhook está **Ativo** no painel Asaas
3. Verificar histórico de webhooks no Asaas (pode mostrar erro de conexão)
4. Testar URL manualmente:
```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"event":"PAYMENT_RECEIVED","payment":{"id":"test123","status":"RECEIVED"}}'
```

### Problema 2: Webhook retorna erro 500
**Sintomas:**
- Webhook é recebido
- Asaas mostra erro 500 no histórico
- Logs do Heroku mostram erro

**Soluções:**
1. Verificar logs completos: `heroku logs --tail --app lwksistemas`
2. Procurar por stack trace do erro
3. Verificar se banco de dados está acessível
4. Verificar se todas as dependências estão instaladas

### Problema 3: Webhook recebido mas senha não enviada
**Sintomas:**
- Webhook aparece nos logs
- Pagamento atualizado no banco
- Senha não é enviada

**Soluções:**
1. Verificar se `FinanceiroLoja.status_pagamento` está como `'ativo'`
2. Verificar se `FinanceiroLoja.senha_enviada` está como `False`
3. Verificar configuração SMTP no Heroku
4. Forçar envio manual (ver FLUXO_TESTE_ASAAS_PRODUCAO.md)

### Problema 4: Múltiplos webhooks duplicados
**Sintomas:**
- Mesmo evento recebido várias vezes
- Logs mostram processamento duplicado

**Soluções:**
1. Verificar se há múltiplos webhooks configurados no Asaas
2. Desativar webhooks duplicados
3. Sistema já tem proteção contra duplicação (verifica se já foi processado)

---

## 📊 Exemplo de Payload do Webhook

Quando o Asaas envia um webhook, o payload tem este formato:

```json
{
  "event": "PAYMENT_RECEIVED",
  "payment": {
    "id": "pay_1234567890abcdef",
    "customer": "cus_0987654321fedcba",
    "billingType": "BOLETO",
    "value": 100.00,
    "netValue": 97.50,
    "status": "RECEIVED",
    "dueDate": "2026-03-10",
    "paymentDate": "2026-03-08",
    "invoiceUrl": "https://www.asaas.com/i/1234567890",
    "bankSlipUrl": "https://www.asaas.com/b/pdf/1234567890",
    "externalReference": "loja_41449198000172_assinatura_202603",
    "description": "Assinatura Plano Básico - FELIX REPRESENTACOES"
  }
}
```

### Campos Importantes:
- **event**: Tipo do evento (PAYMENT_RECEIVED, PAYMENT_CONFIRMED, etc.)
- **payment.id**: ID único do pagamento no Asaas
- **payment.status**: Status atual do pagamento
- **payment.externalReference**: Referência da loja no nosso sistema
- **payment.value**: Valor do pagamento

---

## 🎯 Checklist de Configuração

Antes de fazer o teste em produção, verifique:

- [ ] Webhook criado no painel Asaas
- [ ] URL correta: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
- [ ] 7 eventos configurados (PAYMENT_CREATED, UPDATED, CONFIRMED, RECEIVED, OVERDUE, DELETED, RESTORED)
- [ ] Status: Ativo
- [ ] Teste enviado com sucesso (opcional)
- [ ] Logs do Heroku monitorados
- [ ] SMTP configurado para envio de emails

---

## 📞 Suporte Asaas

Se tiver problemas com a configuração do webhook:

- **Email**: suporte@asaas.com
- **Telefone**: (16) 3509-2000
- **Chat**: Disponível no painel Asaas (canto inferior direito)
- **Documentação**: https://docs.asaas.com/reference/webhooks

---

**Última atualização:** 22/03/2026
**Ambiente:** Produção
**App Heroku:** lwksistemas
