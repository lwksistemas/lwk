# 🧪 Guia de Teste - Webhook v429

## 🎯 OBJETIVO

Testar se:
1. ✅ Apenas 1 cobrança é criada ao criar loja
2. ✅ Webhook atualiza financeiro ao pagar boleto

---

## 📋 PRÉ-REQUISITOS

- [ ] Acesso ao SuperAdmin: https://lwksistemas.com.br/superadmin
- [ ] Acesso ao Asaas Sandbox: https://sandbox.asaas.com
- [ ] Email configurado para receber notificações

---

## 🧪 TESTE 1: Criar Nova Loja

### Passo 1: Acessar SuperAdmin
```
URL: https://lwksistemas.com.br/superadmin/lojas
Usuário: [seu usuário superadmin]
Senha: [sua senha]
```

### Passo 2: Criar Nova Loja
1. Clicar em **"+ Nova Loja"**
2. Preencher dados:
   ```
   Nome: Teste Webhook v429
   Slug: teste-webhook-v429
   Tipo: Cabeleireiro
   Plano: Básico
   Assinatura: Mensal
   
   Admin:
   Nome: Admin Teste
   Username: admin-teste-v429
   Email: [seu email]
   ```
3. Clicar em **"Salvar"**

### Passo 3: Verificar Criação
✅ **Esperado**:
- Loja criada com sucesso
- Mensagem de confirmação
- Email recebido com dados de acesso

### Passo 4: Verificar Cobrança no Asaas
1. Acessar: https://sandbox.asaas.com/payment/list
2. Buscar por: "Teste Webhook v429"

✅ **Esperado**:
- **Apenas 1 cobrança** encontrada
- Status: Aguardando Pagamento
- Valor: R$ 99,90 (ou valor do plano)

❌ **Se encontrar 2 cobranças**:
- Problema não foi resolvido
- Verificar logs do backend

### Passo 5: Verificar Financeiro
1. Acessar: https://lwksistemas.com.br/superadmin/financeiro
2. Buscar loja: "Teste Webhook v429"

✅ **Esperado**:
- Status: Pendente
- Próxima Cobrança: [data]
- Valor: R$ 99,90

---

## 🧪 TESTE 2: Pagar Boleto

### Passo 1: Acessar Asaas Sandbox
```
URL: https://sandbox.asaas.com/payment/list
```

### Passo 2: Localizar Cobrança
1. Buscar por: "Teste Webhook v429"
2. Clicar na cobrança

### Passo 3: Simular Pagamento
1. Clicar em **"Ações"**
2. Selecionar **"Simular Pagamento"**
3. Confirmar

✅ **Esperado**:
- Status mudou para: **Recebido**
- Data de pagamento: Hoje

### Passo 4: Aguardar Webhook (1-2 minutos)
O Asaas enviará webhook automaticamente para:
```
https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/
```

### Passo 5: Verificar Logs (Opcional)
```bash
# Ver logs em tempo real
heroku logs --tail --app lwksistemas

# Filtrar logs do webhook
heroku logs --tail --app lwksistemas | grep "webhook"
```

✅ **Logs Esperados**:
```
🔔 Webhook Asaas recebido
✅ Processando webhook para pagamento pay_xxx
✅ Pagamento atualizado via webhook: PENDING -> RECEIVED
✅ Financeiro da loja atualizado automaticamente
✅ Loja teste-webhook-v429 desbloqueada automaticamente
✅ NF emitida para pagamento pay_xxx
```

### Passo 6: Verificar Financeiro Atualizado
1. Acessar: https://lwksistemas.com.br/superadmin/financeiro
2. Buscar loja: "Teste Webhook v429"

✅ **Esperado**:
- Status: **Ativo** ✅
- Último Pagamento: **Hoje** ✅
- Próxima Cobrança: [próximo mês]

### Passo 7: Verificar Loja Desbloqueada
1. Acessar: https://lwksistemas.com.br/superadmin/lojas
2. Buscar loja: "Teste Webhook v429"

✅ **Esperado**:
- Status: **Ativa** ✅
- Bloqueada: **Não** ✅
- Dias de Atraso: **0** ✅

### Passo 8: Verificar Email de Nota Fiscal
1. Abrir email: [seu email]
2. Buscar por: "Nota Fiscal"

✅ **Esperado**:
- Email recebido com nota fiscal
- Anexo PDF ou link para download

---

## 🧪 TESTE 3: Verificar Banco de Dados (Opcional)

### Via Django Shell
```bash
# Conectar ao Heroku
heroku run python backend/manage.py shell --app lwksistemas

# No shell Python:
from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.models import AsaasPayment

# Buscar loja
loja = Loja.objects.get(slug='teste-webhook-v429')

# Verificar financeiro
print(f"Status: {loja.financeiro.status_pagamento}")
print(f"Último Pagamento: {loja.financeiro.ultimo_pagamento}")
print(f"Bloqueada: {loja.is_blocked}")

# Verificar pagamento
pagamento = AsaasPayment.objects.filter(
    external_reference__contains='teste-webhook-v429'
).first()
print(f"Status Pagamento: {pagamento.status}")
print(f"Data Pagamento: {pagamento.payment_date}")
```

✅ **Resultado Esperado**:
```
Status: ativo
Último Pagamento: 2026-02-07 [hora]
Bloqueada: False
Status Pagamento: RECEIVED
Data Pagamento: 2026-02-07 [hora]
```

---

## 📊 CHECKLIST COMPLETO

### ✅ Teste 1: Criar Loja
- [ ] Loja criada com sucesso
- [ ] Email recebido com dados de acesso
- [ ] **Apenas 1 cobrança** no Asaas
- [ ] Financeiro criado com status "Pendente"

### ✅ Teste 2: Pagar Boleto
- [ ] Pagamento simulado no Asaas
- [ ] Webhook recebido (ver logs)
- [ ] Status financeiro: **Ativo**
- [ ] Último pagamento: **Hoje**
- [ ] Loja: **Desbloqueada**
- [ ] Dias de atraso: **0**
- [ ] Email com nota fiscal recebido

### ✅ Teste 3: Banco de Dados (Opcional)
- [ ] `FinanceiroLoja.status_pagamento = 'ativo'`
- [ ] `FinanceiroLoja.ultimo_pagamento = hoje`
- [ ] `Loja.is_blocked = False`
- [ ] `AsaasPayment.status = 'RECEIVED'`
- [ ] `AsaasPayment.payment_date = hoje`

---

## ❌ PROBLEMAS COMUNS

### Problema 1: 2 Cobranças Criadas
**Sintoma**: Encontrou 2 cobranças no Asaas para a mesma loja

**Causa**: Deploy v429 não foi aplicado corretamente

**Solução**:
```bash
# Verificar versão do backend
heroku releases --app lwksistemas

# Se não for v429, fazer deploy novamente
git push heroku main
```

### Problema 2: Webhook Não Atualiza
**Sintoma**: Pagamento feito mas financeiro não atualiza

**Causa**: Webhook não configurado ou com erro

**Solução**:
```bash
# 1. Verificar configuração do webhook no Asaas
URL: https://sandbox.asaas.com/config/webhook
URL esperada: https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/

# 2. Ver logs de erro
heroku logs --tail --app lwksistemas | grep "ERROR"

# 3. Testar webhook manualmente
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"event":"PAYMENT_RECEIVED","payment":{"id":"pay_test"}}'
```

### Problema 3: Email Não Recebido
**Sintoma**: Não recebeu email com nota fiscal

**Causa**: Email não configurado ou em spam

**Solução**:
```bash
# 1. Verificar configuração de email
heroku config:get EMAIL_HOST --app lwksistemas
heroku config:get EMAIL_HOST_USER --app lwksistemas

# 2. Verificar logs de email
heroku logs --tail --app lwksistemas | grep "email"

# 3. Verificar pasta de spam
```

---

## 🎯 RESULTADO ESPERADO

### ✅ Sucesso Total
```
✅ Apenas 1 cobrança criada
✅ Webhook recebido e processado
✅ Financeiro atualizado automaticamente
✅ Loja desbloqueada automaticamente
✅ Nota fiscal emitida e enviada
✅ Sistema funcionando 100%
```

### ❌ Falha Parcial
Se algum item falhar:
1. Verificar logs: `heroku logs --tail --app lwksistemas`
2. Verificar versão: `heroku releases --app lwksistemas`
3. Reportar problema com logs

---

## 📞 SUPORTE

### Ver Logs
```bash
# Logs gerais
heroku logs --tail --app lwksistemas

# Logs do webhook
heroku logs --tail --app lwksistemas | grep "webhook"

# Logs do Asaas
heroku logs --tail --app lwksistemas | grep "Asaas"

# Últimos 100 logs
heroku logs -n 100 --app lwksistemas
```

### Acessar Shell
```bash
heroku run python backend/manage.py shell --app lwksistemas
```

### Verificar Variáveis
```bash
heroku config --app lwksistemas
```

---

## 📝 RELATÓRIO DE TESTE

Após completar os testes, preencher:

```
Data: ___/___/2026
Testador: _______________

TESTE 1: Criar Loja
[ ] Passou  [ ] Falhou
Observações: _______________________

TESTE 2: Pagar Boleto
[ ] Passou  [ ] Falhou
Observações: _______________________

TESTE 3: Banco de Dados
[ ] Passou  [ ] Falhou  [ ] Não testado
Observações: _______________________

RESULTADO GERAL:
[ ] ✅ Todos os testes passaram
[ ] ⚠️ Alguns testes falharam
[ ] ❌ Maioria dos testes falhou

COMENTÁRIOS:
_________________________________
_________________________________
_________________________________
```

---

**Data**: 7 de janeiro de 2026  
**Versão**: v429  
**Status**: ✅ PRONTO PARA TESTE
