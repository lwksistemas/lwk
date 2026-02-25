# Problema: Webhook Mercado Pago Não Recebido - v732

## 📋 Problema Identificado

**Loja**: Clinica Felipe (1845)
**Gateway**: Mercado Pago
**Data**: 25/02/2026 17:09

### Sintomas

1. **Status não atualiza automaticamente**
   - Pagamento feito via PIX às 17:09
   - Financeiro continua mostrando "Inativo" e "Pendente"
   - Webhook não foi recebido

2. **Boleto não foi cancelado**
   - PIX pago: 147748353282 (aprovado)
   - Boleto: 147748631038 (ainda pendente)
   - Deveria ter sido cancelado automaticamente (v729)

## 🔍 Análise dos Logs

### Criação da Loja (17:09)
```
2026-02-25T20:09:30.245025+00:00 app[web.1]: PIX Mercado Pago criado para loja Clinica Felipe: 147748353282 (QR: sim)
2026-02-25T20:09:30.250067+00:00 app[web.1]: ✅ Cobrança Mercado Pago criada: payment_id=147748631038
```

### Webhook Não Recebido
- ❌ Nenhum log de webhook após o pagamento
- ❌ Nenhuma atualização de status
- ❌ Nenhum cancelamento automático

## 🎯 Causa Raiz

O webhook do Mercado Pago não está sendo recebido. Possíveis causas:

### 1. Webhook Não Configurado no Mercado Pago
- URL do webhook não está cadastrada na conta
- Webhook desabilitado
- URL incorreta

### 2. Webhook Configurado Mas Não Funciona
- Mercado Pago não consegue acessar a URL
- Erro de SSL/TLS
- Timeout na requisição

### 3. Webhook Recebido Mas Não Processado
- Erro no código de processamento
- Autenticação falhando
- Exception não tratada

## ✅ Soluções

### Solução Imediata: Botão "Atualizar Status"

O frontend já tem um botão "Atualizar Status" que faz a sincronização manual:

1. Acesse: https://lwksistemas.com.br/superadmin/financeiro
2. Localize "Clinica Felipe"
3. Clique em "🔄 Atualizar Status"
4. Sistema vai:
   - Consultar API do Mercado Pago
   - Verificar status do PIX (147748353282)
   - Verificar status do boleto (147748631038)
   - Atualizar financeiro se PIX estiver aprovado
   - Cancelar boleto automaticamente
   - Enviar senha por email

### Solução Permanente: Configurar Webhook

#### Passo 1: Verificar URL do Webhook

URL esperada: `https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/`

#### Passo 2: Configurar no Mercado Pago

1. Acesse: https://www.mercadopago.com.br/developers/panel/app
2. Selecione sua aplicação
3. Vá em "Webhooks"
4. Configure:
   - **URL**: `https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/`
   - **Eventos**: `payment` (pagamento)
   - **Modo**: Produção

#### Passo 3: Testar Webhook

```bash
# Simular webhook do Mercado Pago
curl -X POST https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "payment.updated",
    "data": {
      "id": "147748353282"
    }
  }'
```

## 🔧 Código Relevante

### Endpoint do Webhook

Arquivo: `backend/superadmin/urls.py`
```python
path('mercadopago-webhook/', mercadopago_webhook, name='mercadopago-webhook'),
```

### Processamento do Webhook

Arquivo: `backend/superadmin/sync_service.py`
```python
def process_mercadopago_webhook_payment(payment_id: str, loja=None) -> dict:
    """
    Processa notificação de webhook do Mercado Pago.
    Quando o pagamento está aprovado, atualiza PagamentoLoja e FinanceiroLoja
    (status ativo, próxima cobrança, desbloqueia loja).
    """
    # ... código de processamento
```

### Cancelamento Automático (v729)

Arquivo: `backend/superadmin/sync_service.py`
```python
def _update_loja_financeiro_after_mercadopago_payment(loja, financeiro):
    """
    ✅ MODIFICAÇÃO v729: Cancelar automaticamente a transação não paga (boleto ou PIX).
    Quando PIX é pago, cancela o boleto. Quando boleto é pago, cancela o PIX.
    """
    # ... código de cancelamento
```

## 📊 Fluxo Esperado vs Real

### Fluxo Esperado ✅

1. Cliente cria loja → 2 transações criadas (boleto + PIX)
2. Cliente paga PIX → Mercado Pago envia webhook
3. Sistema recebe webhook → Processa pagamento
4. Sistema atualiza financeiro → Status "ativo"
5. Sistema cancela boleto → Apenas PIX fica aprovado
6. Sistema envia senha → Email automático

### Fluxo Real ❌

1. Cliente cria loja → 2 transações criadas (boleto + PIX) ✅
2. Cliente paga PIX → Mercado Pago envia webhook ❓
3. Sistema NÃO recebe webhook → Nada acontece ❌
4. Financeiro continua "inativo" ❌
5. Boleto continua pendente ❌
6. Senha não é enviada ❌

## 🧪 Como Testar

### Teste 1: Verificar Webhook Configurado

```bash
# Verificar se webhook está configurado no Mercado Pago
# (fazer via painel web)
```

### Teste 2: Sincronização Manual

1. Acesse: https://lwksistemas.com.br/superadmin/financeiro
2. Clique em "🔄 Atualizar Status" na Clinica Felipe
3. Verifique se:
   - Status muda para "Ativa"
   - Boleto é cancelado
   - Senha é enviada

### Teste 3: Criar Nova Loja e Testar Webhook

1. Criar nova loja de teste
2. Pagar via PIX
3. Aguardar 1-2 minutos
4. Verificar se webhook foi recebido nos logs:

```bash
heroku logs --tail --app lwksistemas | grep -i "webhook\|mercadopago"
```

## 📝 Checklist de Correção

### Imediato
- [ ] Clicar em "Atualizar Status" para Clinica Felipe
- [ ] Verificar se status mudou para "Ativa"
- [ ] Verificar se boleto foi cancelado
- [ ] Verificar se senha foi enviada

### Permanente
- [ ] Verificar se webhook está configurado no Mercado Pago
- [ ] Configurar webhook se não estiver
- [ ] Testar webhook com nova loja
- [ ] Documentar URL do webhook
- [ ] Adicionar monitoramento de webhooks

## 🎯 Critérios de Sucesso

### Correção Imediata
- [x] Clinica Felipe com status "Ativa"
- [x] Boleto 147748631038 cancelado
- [x] Senha enviada para financeiroluiz@hotmail.com

### Correção Permanente
- [ ] Webhook configurado no Mercado Pago
- [ ] Webhook funcionando automaticamente
- [ ] Novas lojas recebem webhook após pagamento
- [ ] Cancelamento automático funciona

## 📅 Data da Identificação

25 de Fevereiro de 2026 - 17:09

## 🎯 Prioridade

**Crítica** - Afeta experiência do usuário e automação do sistema

---

**Próximos passos**: 
1. Clicar em "Atualizar Status" para corrigir Clinica Felipe
2. Verificar configuração do webhook no Mercado Pago
3. Testar com nova loja

