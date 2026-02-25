# Verificação: Webhook Mercado Pago

## 🔍 Situação Atual

**Loja**: Clinica Daniel (5889)
**PIX ID**: 147754196204
**Boleto ID**: 147751949750
**Pagamento**: Realizado às 17:40
**Webhook**: Não recebido após 2+ minutos

## ❓ Possíveis Causas

### 1. URL do Webhook Incorreta

Verifique no painel do Mercado Pago se a URL está EXATAMENTE assim:

```
https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/
```

**IMPORTANTE**: 
- Deve ser a URL do Heroku (não lwksistemas.com.br)
- Deve ter a barra final `/`
- Deve ser `https://` (não `http://`)

### 2. Webhook Configurado para Sandbox

Se você configurou o webhook no modo "Sandbox" mas está usando Access Token de "Produção", o webhook não vai funcionar.

**Verifique**:
- Access Token é de produção? → Webhook deve estar em "Produção"
- Access Token é de sandbox? → Webhook deve estar em "Sandbox"

### 3. Eventos Incorretos

O webhook deve estar configurado para o evento:
- ✅ `payment` ou `payment.updated`

**NÃO deve ter**:
- ❌ `merchant_order`
- ❌ Outros eventos

### 4. Webhook Desabilitado

Verifique se o webhook está com status "Ativo" no painel.

## 🔧 Como Verificar

### Passo 1: Acessar Painel

1. Acesse: https://www.mercadopago.com.br/developers/panel/app
2. Selecione sua aplicação
3. Clique em "Webhooks"

### Passo 2: Verificar Configuração

Confirme:
- [ ] URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/`
- [ ] Eventos: `payment`
- [ ] Modo: `Produção` (ou `Sandbox` se estiver testando)
- [ ] Status: `Ativo`

### Passo 3: Ver Histórico de Webhooks

No painel do Mercado Pago, você pode ver o histórico de webhooks enviados:
- Clique em "Webhooks"
- Veja se há tentativas de envio
- Veja se houve erros

## 🧪 Teste Manual

Se o webhook não estiver funcionando, você pode testar manualmente:

### Opção 1: Clicar em "Atualizar Status"

1. Acesse: https://lwksistemas.com.br/superadmin/financeiro
2. Localize "Clinica Daniel"
3. Clique em "🔄 Atualizar Status"
4. Sistema vai processar o pagamento manualmente

### Opção 2: Simular Webhook via cURL

```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "payment",
    "data": {
      "id": "147754196204"
    }
  }'
```

## 📊 URLs Possíveis

O Mercado Pago pode estar tentando enviar para a URL errada. Tente configurar com:

### URL 1 (Heroku - Recomendada)
```
https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/
```

### URL 2 (Domínio Personalizado)
```
https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/
```

**Nota**: A URL 2 pode estar redirecionando (HTTP 308) para a URL 1, o que pode causar problemas.

## ✅ Solução Temporária

Enquanto o webhook não funciona, use o botão "Atualizar Status":

1. Acesse: https://lwksistemas.com.br/superadmin/financeiro
2. Clique em "🔄 Atualizar Status" na Clinica Daniel
3. Sistema vai:
   - Consultar API do Mercado Pago
   - Verificar se PIX foi aprovado
   - Atualizar status para "Ativa"
   - Cancelar boleto
   - Enviar senha

## 📝 Checklist de Verificação

- [ ] Verifiquei URL do webhook no painel MP
- [ ] URL está correta (Heroku, com barra final)
- [ ] Eventos estão corretos (payment)
- [ ] Modo está correto (Produção/Sandbox)
- [ ] Webhook está ativo
- [ ] PIX está aprovado no Mercado Pago
- [ ] Testei manualmente com "Atualizar Status"
- [ ] Webhook funcionou após correção

---

**Data**: 25 de Fevereiro de 2026
**Versão**: v732

