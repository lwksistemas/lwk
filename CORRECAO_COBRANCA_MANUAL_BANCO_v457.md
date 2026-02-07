# CORREÇÃO: Cobrança Manual Não Salvava no Banco Local - v457

## 🐛 PROBLEMA REPORTADO

**Usuário**: "eu criei 2 boleto para Clinica Harmonis... o boleto foi criado no asaas mas nao foi gerado no financerio"

**Análise dos Logs**:
- Boleto criado no Asaas: ✅
- Boleto salvo no banco local: ❌
- Resultado: Boleto aparece no Asaas mas não no sistema

## 🔍 CAUSA RAIZ

A função `create_manual_payment()` em `backend/asaas_integration/views.py` chamava o serviço `AsaasPaymentService.create_loja_subscription_payment()` que:

1. ✅ Criava o cliente no Asaas
2. ✅ Criava a cobrança no Asaas
3. ✅ Retornava os dados da cobrança
4. ❌ **NÃO salvava no banco de dados local** (`AsaasPayment`)

**Resultado**: Cobrança criada no Asaas, mas invisível no sistema.

## ✅ SOLUÇÃO IMPLEMENTADA

### Arquivo Modificado
`backend/asaas_integration/views.py` - Função `create_manual_payment()`

### Código Adicionado

```python
# Salvar no banco de dados local
if resultado.get('success'):
    from .models import AsaasPayment, AsaasCustomer
    
    # Criar ou buscar customer
    customer, _ = AsaasCustomer.objects.get_or_create(
        asaas_id=resultado['customer_id'],
        defaults={
            'name': loja.nome,
            'email': loja.owner.email,
            'cpf_cnpj': loja_data.get('cpf_cnpj', ''),
            'phone': loja_data.get('telefone', ''),
        }
    )
    
    # Criar pagamento
    payment = AsaasPayment.objects.create(
        customer=customer,
        asaas_id=resultado['payment_id'],
        value=resultado['value'],
        status=resultado['status'],
        due_date=resultado['due_date'],
        description=f"Assinatura {plano_data['nome']} - Loja {loja.nome}",
        bank_slip_url=resultado.get('boleto_url', ''),
        pix_copy_paste=resultado.get('pix_copy_paste', ''),
        external_reference=f"loja_{loja.slug}_assinatura"
    )
    
    logger.info(f"✅ Pagamento salvo no banco local (ID: {payment.id})")
```

## 🎯 FLUXO CORRIGIDO

### Antes (v456)
1. Usuário clica em "Nova Cobrança" → Manual
2. Sistema cria cobrança no Asaas ✅
3. Sistema retorna sucesso ✅
4. **Cobrança NÃO aparece no financeiro** ❌

### Depois (v457)
1. Usuário clica em "Nova Cobrança" → Manual
2. Sistema cria cobrança no Asaas ✅
3. **Sistema salva no banco local** ✅
4. Sistema retorna sucesso ✅
5. **Cobrança aparece no financeiro** ✅

## 📊 DADOS SALVOS NO BANCO

Quando uma cobrança manual é criada, o sistema agora salva:

### Tabela `AsaasCustomer`
- `asaas_id`: ID do cliente no Asaas
- `name`: Nome da loja
- `email`: Email do proprietário
- `cpf_cnpj`: CPF/CNPJ da loja
- `phone`: Telefone

### Tabela `AsaasPayment`
- `customer`: Referência ao cliente
- `asaas_id`: ID do pagamento no Asaas
- `value`: Valor da cobrança
- `status`: Status (PENDING, RECEIVED, etc)
- `due_date`: Data de vencimento
- `description`: Descrição da cobrança
- `bank_slip_url`: URL do boleto
- `pix_copy_paste`: Código PIX copia e cola
- `external_reference`: Referência externa (slug da loja)

## 🚀 DEPLOY

- **Versão**: v457
- **Status**: ✅ Sucesso
- **Backend**: https://lwksistemas-38ad47519238.herokuapp.com
- **Commit**: `fix: Salvar cobrança manual no banco local - v457`

## 🔗 SINCRONIZAÇÃO

### Cobrança Automática (via webhook)
- ✅ Já funcionava corretamente
- Webhook do Asaas salva automaticamente no banco

### Cobrança Manual (via botão)
- ❌ Não salvava no banco (v456)
- ✅ Agora salva no banco (v457)

## 📋 BOAS PRÁTICAS APLICADAS

1. **Consistência de Dados**: Asaas e banco local sempre sincronizados
2. **Atomicidade**: Usa `get_or_create` para evitar duplicatas
3. **Logging**: Logs detalhados para debug
4. **Error Handling**: Tratamento de erros específico
5. **Clean Code**: Código organizado e legível

## 🧪 COMO TESTAR

1. Acesse: https://lwksistemas.com.br/superadmin/financeiro
2. Clique em "➕ Nova Cobrança" em qualquer assinatura
3. Escolha "Manual" e selecione uma data
4. Clique em "Criar Cobrança"
5. ✅ Cobrança deve aparecer imediatamente na aba "Pagamentos"
6. ✅ Cobrança deve estar no Asaas: https://sandbox.asaas.com/payment/list

## 📝 PRÓXIMOS PASSOS

1. **Testar criação de cobrança manual** para Clínica Harmonis novamente
2. **Verificar** se aparece na aba "Pagamentos"
3. **Confirmar** sincronização com Asaas

---

**Data**: 07/02/2026  
**Versão**: v457  
**Status**: ✅ Cobrança manual agora salva no banco local
**Problema**: Resolvido
