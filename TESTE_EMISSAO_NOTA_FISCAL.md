# Teste de Emissão de Nota Fiscal Automática

**Data:** 25/03/2026  
**Loja de Teste:** Clínica da Beleza (22239255889)  
**Plano:** Enterprise (Mensal) - R$ 8,00  
**Vencimento:** 23/04/2026

---

## ✅ Sistema Configurado

O sistema JÁ ESTÁ IMPLEMENTADO e pronto para emitir notas fiscais automaticamente após o pagamento do boleto.

### Fluxo Automático

1. **Boleto é pago** → Asaas detecta o pagamento
2. **Asaas envia webhook** → `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
3. **Sistema processa webhook** → Atualiza status do pagamento
4. **Sistema emite NF** → Chama API do Asaas para emitir nota fiscal
5. **Sistema envia email** → Email com NF para o administrador da loja

---

## 📋 Checklist de Configuração no Asaas

Para que a emissão funcione, você precisa ter configurado no painel do Asaas:

### 1. Webhook Configurado
- URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
- Eventos: `PAYMENT_RECEIVED`, `PAYMENT_CONFIRMED`
- Status: Ativo

### 2. Chave API com Permissões
- Permissão: `INVOICE:WRITE` (emissão de notas fiscais)
- Chave configurada no Django Admin

### 3. Dados Fiscais da Empresa
- CNPJ cadastrado
- Inscrição Municipal
- Endereço completo
- Regime tributário

### 4. Vinculação com Prefeitura
- Conta Asaas vinculada ao portal da prefeitura
- Certificado digital configurado (se necessário)

### 5. Código de Serviço Municipal
- Variável de ambiente: `ASAAS_INVOICE_SERVICE_CODE`
- Exemplo: "01.07" (Desenvolvimento de programas de computador)

---

## 🔍 Como Verificar se Funcionou

### 1. Verificar Logs do Heroku

Após pagar o boleto, aguarde alguns minutos e verifique os logs:

```bash
heroku logs --tail | grep -i "webhook\|invoice\|nf"
```

**Logs esperados:**
```
Webhook Asaas recebido: {...}
Pagamento XXX atualizado via webhook: PENDING -> RECEIVED
Financeiro da loja atualizado automaticamente via webhook
NF agendada no Asaas: invoice_id=XXX, payment=YYY
NF emitida no Asaas: invoice_id=XXX
NF emitida para pagamento YYY, e-mail enviado: True
```

### 2. Verificar Email

O administrador da loja deve receber um email com:
- Assunto: "Nota Fiscal – Assinatura LWK Sistemas"
- Identificador da NF
- Descrição do serviço
- Valor
- Link para download do PDF (se disponível)

### 3. Verificar no Painel Asaas

Acesse o painel do Asaas:
1. Vá em "Notas Fiscais"
2. Procure pela nota fiscal emitida
3. Verifique o status (deve estar "Autorizada")
4. Baixe o PDF da nota

### 4. Verificar no Banco de Dados

Você pode verificar no Django Admin:
- Modelo: `AsaasPayment`
- Procure pelo pagamento da loja "Clínica da Beleza"
- Status deve estar: `RECEIVED` ou `CONFIRMED`

---

## 🐛 Troubleshooting

### Problema: Webhook não está sendo recebido

**Verificar:**
1. URL do webhook está correta no Asaas?
2. Webhook está ativo no Asaas?
3. Eventos corretos estão selecionados?

**Testar manualmente:**
```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_RECEIVED",
    "payment": {
      "id": "pay_test123",
      "status": "RECEIVED",
      "value": 8.00,
      "description": "Teste"
    }
  }'
```

### Problema: NF não está sendo emitida

**Verificar:**
1. Chave API tem permissão `INVOICE:WRITE`?
2. Dados fiscais estão completos no Asaas?
3. Conta está vinculada à prefeitura?
4. Código de serviço municipal está configurado?

**Ver logs de erro:**
```bash
heroku logs --tail | grep -i "erro.*nf\|falha.*nf"
```

### Problema: Email não está sendo enviado

**Verificar:**
1. Loja tem email do owner cadastrado?
2. Email está válido?
3. Servidor de email está configurado?

**Ver logs de email:**
```bash
heroku logs --tail | grep -i "email.*nf"
```

---

## 📝 Variáveis de Ambiente Necessárias

Certifique-se de que estas variáveis estão configuradas no Heroku:

```bash
# Código do serviço municipal (obrigatório para NF)
ASAAS_INVOICE_SERVICE_CODE=01.07

# Nome do serviço (opcional, tem padrão)
ASAAS_INVOICE_SERVICE_NAME="Software sob demanda / Assinatura de sistema"

# ID do serviço (opcional, se a prefeitura exigir)
ASAAS_INVOICE_SERVICE_ID=

# Email para envio
DEFAULT_FROM_EMAIL=noreply@lwksistemas.com.br
```

**Verificar variáveis:**
```bash
heroku config | grep ASAAS
```

**Adicionar variável (se necessário):**
```bash
heroku config:set ASAAS_INVOICE_SERVICE_CODE="01.07"
```

---

## 🎯 Próximos Passos

1. **Pagar o boleto** da loja "Clínica da Beleza"
2. **Aguardar 5-10 minutos** para o Asaas processar
3. **Verificar logs** do Heroku
4. **Verificar email** do administrador
5. **Verificar painel Asaas** se a NF foi emitida

---

## 📞 Suporte

Se encontrar algum problema:

1. Copie os logs do Heroku
2. Verifique o status no painel do Asaas
3. Verifique se o webhook foi recebido
4. Verifique se há erros de permissão ou configuração

---

## 🔗 Links Úteis

- **Webhook URL:** `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
- **Painel Asaas:** https://www.asaas.com
- **Documentação Asaas NF:** https://docs.asaas.com/reference/criar-nota-fiscal

---

## ✅ Status Atual

- ✅ Código implementado
- ✅ Webhook configurado
- ✅ Serviço de emissão implementado
- ✅ Email automático implementado
- ⏳ Aguardando pagamento do boleto para teste
- ⏳ Aguardando configuração final no Asaas (dados fiscais, vinculação prefeitura, código serviço)

---

**Boa sorte com o teste! 🚀**
