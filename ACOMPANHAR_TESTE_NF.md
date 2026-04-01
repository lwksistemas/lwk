# 🧪 Acompanhamento do Teste de Nota Fiscal

## 📋 Informações do Teste

**Loja:** Master Representações  
**Plano:** Profissional CRM (Mensal)  
**Valor:** R$ 8,00  
**Vencimento:** 01/05/2026  
**Status:** Aguardando pagamento  

## 🔍 Como Acompanhar

### 1. Verificar Status no Heroku

```bash
# Executar script de verificação
heroku run python verificar_nf_master.py -a lwksistemas
```

### 2. Monitorar Logs em Tempo Real

```bash
# Ver logs relacionados a NF e pagamento
heroku logs --tail -a lwksistemas | grep -E "NF|nota|invoice|payment|Master"
```

### 3. Verificar no Dashboard

Acesse: https://lwksistemas.com.br/superadmin/financeiro

## 📊 Fluxo Esperado

### Passo 1: Pagamento Confirmado
⏳ **Status:** Aguardando confirmação do Asaas  
⏱️ **Tempo:** Instantâneo (PIX) ou até 3 dias úteis (boleto)

**O que acontece:**
- Asaas envia webhook de confirmação
- Sistema atualiza status do pagamento para "CONFIRMED"
- Log: `✅ Pagamento confirmado: payment_id=...`

### Passo 2: Emissão da Nota Fiscal
🔄 **Status:** Processamento automático  
⏱️ **Tempo:** Alguns segundos após confirmação

**O que acontece:**
1. Sistema agenda a nota fiscal no Asaas
2. Envia código de serviço: `1401` (4 dígitos)
3. Asaas envia para a Prefeitura de Ribeirão Preto
4. Prefeitura autoriza a nota fiscal

**Logs esperados:**
```
NF agendada no Asaas: invoice_id=..., payment=...
NF emitida no Asaas: invoice_id=...
Configuração municipal NF: code=1401, name=Reparação e manutenção...
```

### Passo 3: Nota Fiscal Autorizada
✅ **Status:** Emitida com sucesso  
⏱️ **Tempo:** Alguns minutos

**O que acontece:**
- Nota fiscal recebe status "AUTHORIZED"
- PDF da nota fica disponível
- Email enviado para o admin da loja

## ✅ Validações a Fazer

### 1. Código de Serviço
- [ ] Código enviado: `1401` (4 dígitos)
- [ ] Sem pontos ou traços
- [ ] Aceito pela prefeitura

### 2. Dados da Nota
- [ ] Valor: R$ 8,00
- [ ] Descrição: "Profissional CRM (Mensal) - Master Representações"
- [ ] Município: Ribeirão Preto-SP

### 3. Status Final
- [ ] Status: AUTHORIZED
- [ ] PDF disponível
- [ ] Email enviado

## 🚨 Possíveis Erros

### Erro 1: "Item da Lista de Serviço deve conter 3 a 4 dígitos"
**Causa:** Código com formato incorreto  
**Solução:** ✅ JÁ CORRIGIDO na v1468

### Erro 2: "Dados cadastrais incompletos"
**Causa:** Falta informações da loja no Asaas  
**Solução:** Completar cadastro no painel Asaas

### Erro 3: "Município não configurado"
**Causa:** Loja não está em Ribeirão Preto  
**Solução:** Verificar endereço da loja

## 📝 Comandos Úteis

### Verificar configuração atual
```bash
heroku config -a lwksistemas | grep ASAAS_INVOICE
```

**Resultado esperado:**
```
ASAAS_INVOICE_SERVICE_CODE:   1401
ASAAS_INVOICE_SERVICE_NAME:   Reparação e manutenção de computadores e de equipamentos periféricos
```

### Ver últimos logs
```bash
heroku logs --tail -a lwksistemas -n 100
```

### Executar verificação manual
```bash
heroku run python verificar_nf_master.py -a lwksistemas
```

## 📞 Checklist Pós-Pagamento

Após realizar o pagamento, aguarde alguns minutos e execute:

1. [ ] Verificar status do pagamento no Asaas
2. [ ] Verificar se a nota fiscal foi agendada
3. [ ] Verificar se a nota fiscal foi autorizada
4. [ ] Verificar se o código `1401` foi aceito
5. [ ] Verificar se o PDF está disponível
6. [ ] Verificar se o email foi enviado
7. [ ] Baixar e conferir o PDF da nota fiscal

## 🎯 Resultado Esperado

Se tudo funcionar corretamente, você verá:

```
✅ Pagamento confirmado
✅ NF agendada no Asaas: invoice_id=inv_...
✅ NF emitida no Asaas: invoice_id=inv_...
✅ Configuração municipal NF: code=1401
✅ Status: AUTHORIZED
✅ PDF disponível
✅ Email enviado para: [email do admin]
```

## 📧 Notificação por Email

O admin da loja receberá um email com:
- Assunto: "Nota Fiscal – Assinatura LWK Sistemas"
- Identificador da NF
- Descrição do serviço
- Valor: R$ 8,00
- Link para download do PDF

---

**Teste iniciado em:** 01/04/2026  
**Status:** ⏳ Aguardando pagamento
