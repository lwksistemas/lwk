# Guia: Configurar Webhook do Mercado Pago

## 🎯 Objetivo

Configurar o webhook do Mercado Pago para que o sistema receba notificações automáticas quando um pagamento for aprovado.

## 📋 Pré-requisitos

- Conta no Mercado Pago (produção)
- Acesso ao painel de desenvolvedores
- Aplicação criada no Mercado Pago

## 🔧 Passo a Passo

### 1. Acessar o Painel de Desenvolvedores

1. Acesse: https://www.mercadopago.com.br/developers/panel/app
2. Faça login com sua conta Mercado Pago
3. Selecione sua aplicação (ou crie uma se não tiver)

### 2. Configurar Webhook

1. No menu lateral, clique em **"Webhooks"** ou **"Notificações"**
2. Clique em **"Configurar notificações"** ou **"Adicionar webhook"**

### 3. Preencher Dados do Webhook

#### URL do Webhook
```
https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/
```

**IMPORTANTE**: Use exatamente esta URL, incluindo a barra final `/`

#### Eventos para Notificar

Selecione apenas:
- ✅ **payment** (Pagamento)
- ✅ **payment.updated** (Pagamento atualizado)

**NÃO selecione**:
- ❌ merchant_order
- ❌ chargebacks
- ❌ outros eventos

#### Modo

- **Produção**: Para pagamentos reais
- **Sandbox**: Para testes (se estiver testando)

### 4. Salvar Configuração

1. Clique em **"Salvar"** ou **"Criar"**
2. Mercado Pago vai testar a URL
3. Se tudo estiver correto, webhook será ativado

### 5. Verificar Configuração

Após salvar, você deve ver:
- ✅ URL: `https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/`
- ✅ Status: Ativo
- ✅ Eventos: payment

## 🧪 Testar Webhook

### Teste 1: Verificar Endpoint

Acesse no navegador:
```
https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/
```

Deve retornar:
```json
{
  "status": "ok",
  "message": "Endpoint do webhook Mercado Pago ativo.",
  "url": "https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/",
  "test": "Envie POST com JSON..."
}
```

### Teste 2: Simular Webhook (via cURL)

```bash
curl -X POST https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "payment",
    "data": {
      "id": "147748353282"
    }
  }'
```

Deve retornar:
```json
{
  "status": "processed",
  "payment_id": "147748353282",
  "loja_slug": "clinica-felipe-1845"
}
```

### Teste 3: Criar Nova Loja e Pagar

1. Crie uma nova loja de teste
2. Pague via PIX
3. Aguarde 1-2 minutos
4. Verifique se:
   - Status mudou para "Ativa" automaticamente
   - Boleto foi cancelado automaticamente
   - Senha foi enviada automaticamente

### Teste 4: Verificar Logs

```bash
heroku logs --tail --app lwksistemas | grep -i "webhook\|mercadopago"
```

Deve aparecer:
```
Webhook MP: pagamento 147748353282 status=approved
Pagamento MP 147748353282 marcado como pago
Financeiro da loja clinica-felipe-1845 atualizado via webhook MP
PIX aprovado para loja clinica-felipe-1845. Cancelando boleto...
✅ Boleto 147748631038 cancelado automaticamente
```

## 🔍 Troubleshooting

### Problema: Webhook não está sendo recebido

#### Causa 1: URL Incorreta
- Verifique se a URL está exatamente como: `https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/`
- Não esqueça a barra final `/`
- Não use `http://` (deve ser `https://`)

#### Causa 2: Eventos Incorretos
- Certifique-se de que selecionou apenas `payment`
- Não selecione outros eventos

#### Causa 3: Modo Incorreto
- Se estiver usando Access Token de produção, use modo "Produção"
- Se estiver usando Access Token de sandbox, use modo "Sandbox"

#### Causa 4: Webhook Desabilitado
- Verifique se o webhook está com status "Ativo"
- Se estiver "Inativo", clique em "Ativar"

### Problema: Webhook recebido mas não processa

Verifique os logs:
```bash
heroku logs --tail --app lwksistemas | grep -i "erro\|exception"
```

### Problema: Boleto não é cancelado

Verifique se:
- PIX foi realmente aprovado no Mercado Pago
- Boleto está com status "pending" ou "in_process"
- Access Token tem permissão para cancelar pagamentos

## 📊 Fluxo Completo (Após Configurar Webhook)

### 1. Cliente Cria Loja
```
Cliente preenche formulário
↓
Sistema cria loja
↓
Sistema cria 2 transações no Mercado Pago (boleto + PIX)
↓
Cliente recebe link de pagamento
```

### 2. Cliente Paga PIX
```
Cliente paga PIX
↓
Mercado Pago aprova pagamento
↓
Mercado Pago envia webhook para sistema ✅ AUTOMÁTICO
↓
Sistema recebe webhook
```

### 3. Sistema Processa Webhook
```
Sistema verifica payment_id
↓
Sistema consulta API do Mercado Pago
↓
Sistema confirma que PIX foi aprovado
↓
Sistema atualiza financeiro (status: ativo)
↓
Sistema cancela boleto automaticamente ✅
↓
Sistema envia senha por email ✅
↓
Cliente recebe email e pode fazer login
```

## ✅ Checklist de Configuração

- [ ] Acessei o painel de desenvolvedores do Mercado Pago
- [ ] Selecionei minha aplicação
- [ ] Cliquei em "Webhooks" ou "Notificações"
- [ ] Adicionei novo webhook
- [ ] Configurei URL: `https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/`
- [ ] Selecionei evento: `payment`
- [ ] Selecionei modo: Produção
- [ ] Salvei configuração
- [ ] Webhook está com status "Ativo"
- [ ] Testei endpoint via navegador (GET)
- [ ] Testei webhook via cURL (POST)
- [ ] Criei loja de teste e paguei
- [ ] Verifiquei que status atualizou automaticamente
- [ ] Verifiquei que boleto foi cancelado automaticamente
- [ ] Verifiquei que senha foi enviada automaticamente

## 📝 Informações Importantes

### URL do Webhook
```
https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/
```

### Formato do Webhook (Mercado Pago envia)
```json
{
  "type": "payment",
  "action": "payment.updated",
  "data": {
    "id": "147748353282"
  }
}
```

### Resposta do Sistema
```json
{
  "status": "processed",
  "payment_id": "147748353282",
  "loja_slug": "clinica-felipe-1845"
}
```

## 🎯 Resultado Esperado

Após configurar o webhook:

1. ✅ Pagamentos são processados automaticamente
2. ✅ Status atualiza sem precisar clicar em botão
3. ✅ Boleto é cancelado automaticamente
4. ✅ Senha é enviada automaticamente
5. ✅ Cliente pode fazer login imediatamente

## 📞 Suporte

Se tiver problemas:

1. Verifique os logs: `heroku logs --tail --app lwksistemas`
2. Teste o endpoint: `https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/`
3. Verifique configuração no painel do Mercado Pago
4. Entre em contato com suporte do Mercado Pago se necessário

---

**Data**: 25 de Fevereiro de 2026
**Versão**: v732
**Status**: Aguardando configuração do webhook

