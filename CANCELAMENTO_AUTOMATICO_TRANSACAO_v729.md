# Cancelamento Automático de Transação Não Paga - v729

## 📋 Resumo

Implementação de cancelamento automático da transação não paga no Mercado Pago após uma transação ser aprovada.

## 🎯 Problema

Quando uma loja é criada com Mercado Pago, o sistema cria **2 transações**:
1. Boleto bancário
2. PIX

**Objetivo**: Dar flexibilidade ao cliente de pagar por boleto OU PIX.

**Problema identificado**:
- Cliente paga via PIX → Boleto fica "Pendente" no painel do Mercado Pago
- Cliente paga via Boleto → PIX fica "Pendente" no painel do Mercado Pago

**Riscos**:
- Cliente pode pagar a transação pendente por engano (pagamento duplicado)
- Confusão no painel do Mercado Pago
- Possíveis cobranças indevidas

## ✅ Solução Implementada

Cancelamento automático da transação não paga após uma ser aprovada:

```
PIX aprovado → Cancela boleto automaticamente
Boleto aprovado → Cancela PIX automaticamente
```

## 🔧 Implementação

### Arquivo Modificado
`backend/superadmin/sync_service.py` - Função `_update_loja_financeiro_after_mercadopago_payment()`

### Lógica Implementada

```python
# Após atualizar financeiro para 'ativo'
1. Buscar IDs do boleto e PIX no FinanceiroLoja
2. Consultar status de ambas as transações na API do Mercado Pago
3. Identificar qual foi aprovada
4. Cancelar a transação pendente usando API do Mercado Pago
```

### Código Adicionado

```python
# Identificar qual transação foi paga
boleto_id = financeiro.mercadopago_payment_id
pix_id = financeiro.mercadopago_pix_payment_id

# Consultar status na API
boleto_data = client.get_payment(str(boleto_id))
pix_data = client.get_payment(str(pix_id))

# Se PIX foi aprovado, cancelar boleto
if pix_status == 'approved' and boleto_status in ('pending', 'in_process'):
    client.cancel_payment(str(boleto_id))

# Se boleto foi aprovado, cancelar PIX
elif boleto_status == 'approved' and pix_status in ('pending', 'in_process'):
    client.cancel_payment(str(pix_id))
```

## 📊 Fluxo Completo

### Cenário 1: Cliente Paga via PIX

1. **Criação da Loja**
   - Sistema cria boleto (ID: 147732855488)
   - Sistema cria PIX (ID: 147733399216)
   - Ambos com status "pending"

2. **Cliente Paga PIX**
   - Mercado Pago envia webhook
   - Sistema processa pagamento
   - Status do PIX: "approved" ✅

3. **Cancelamento Automático**
   - Sistema detecta PIX aprovado
   - Sistema consulta status do boleto: "pending"
   - Sistema cancela boleto automaticamente
   - Status do boleto: "cancelled" ✅

4. **Resultado Final**
   - PIX: approved ✅
   - Boleto: cancelled ✅
   - Cliente não pode pagar boleto por engano

### Cenário 2: Cliente Paga via Boleto

1. **Criação da Loja**
   - Sistema cria boleto (ID: 147732855488)
   - Sistema cria PIX (ID: 147733399216)
   - Ambos com status "pending"

2. **Cliente Paga Boleto**
   - Mercado Pago envia webhook
   - Sistema processa pagamento
   - Status do boleto: "approved" ✅

3. **Cancelamento Automático**
   - Sistema detecta boleto aprovado
   - Sistema consulta status do PIX: "pending"
   - Sistema cancela PIX automaticamente
   - Status do PIX: "cancelled" ✅

4. **Resultado Final**
   - Boleto: approved ✅
   - PIX: cancelled ✅
   - Cliente não pode pagar PIX por engano

## 🔍 Logs

### Logs de Sucesso

```
INFO: PIX aprovado para loja clinica-felipe-5898. Cancelando boleto 147732855488...
INFO: ✅ Boleto 147732855488 cancelado automaticamente
```

ou

```
INFO: Boleto aprovado para loja clinica-teste-1234. Cancelando PIX 147733399216...
INFO: ✅ PIX 147733399216 cancelado automaticamente
```

### Logs de Aviso

```
WARNING: ⚠️ Não foi possível cancelar boleto 147732855488
```

Possíveis causas:
- Transação já foi cancelada manualmente
- Transação já expirou
- Erro na API do Mercado Pago

## ✅ Benefícios

1. **Evita pagamentos duplicados**: Cliente não pode pagar a transação pendente por engano
2. **Painel limpo**: Apenas transações relevantes aparecem no Mercado Pago
3. **Automático**: Não requer intervenção manual
4. **Seguro**: Só cancela se a outra transação foi aprovada

## 🧪 Como Testar

### Teste 1: Pagar via PIX
1. Criar loja com Mercado Pago
2. Verificar que 2 transações foram criadas (boleto + PIX)
3. Pagar via PIX
4. Aguardar 1-2 minutos
5. Verificar no painel do Mercado Pago:
   - PIX: Aprovado ✅
   - Boleto: Cancelado ✅

### Teste 2: Pagar via Boleto
1. Criar loja com Mercado Pago
2. Verificar que 2 transações foram criadas (boleto + PIX)
3. Pagar via Boleto
4. Aguardar 1-2 minutos
5. Verificar no painel do Mercado Pago:
   - Boleto: Aprovado ✅
   - PIX: Cancelado ✅

### Verificar Logs
```bash
heroku logs --tail --app lwksistemas | grep -i "cancelando\|cancelado"
```

## 📝 Observações

1. **Cancelamento só funciona para transações pendentes**: Se a transação já foi paga, expirou ou cancelada, não será possível cancelar
2. **API do Mercado Pago**: Usa endpoint `PUT /v1/payments/{id}` com `status=cancelled`
3. **Idempotência**: Se o cancelamento falhar, não afeta o processamento do pagamento aprovado
4. **Logs detalhados**: Todos os cancelamentos são registrados nos logs para auditoria

## 🚀 Deploy

```bash
git add backend/superadmin/sync_service.py CANCELAMENTO_AUTOMATICO_TRANSACAO_v729.md
git commit -m "v729: Cancelamento automático de transação não paga no Mercado Pago"
git push heroku master
```

## 📅 Data da Implementação

25 de Fevereiro de 2026

## ✅ Status

Implementado e pronto para teste

---

**Próximos passos**: Testar com nova loja e verificar se transação não paga é cancelada automaticamente.
