# 🧹 Limpar TUDO do Asaas (Sandbox)

## 🎯 Objetivo

Deletar TODOS os pagamentos e clientes que aparecem em:
- https://sandbox.asaas.com/payment/list
- https://sandbox.asaas.com/customer/list

## ⚠️ ATENÇÃO

Este comando vai deletar **TUDO** do Asaas Sandbox. Use apenas se:
- ✅ Está no ambiente SANDBOX (não produção)
- ✅ Quer começar do zero
- ✅ Não tem dados importantes lá

## 🚀 Comando Completo

Execute este comando para limpar TUDO:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig

# Configurar cliente
config = AsaasConfig.get_config()
client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)

print('🔍 Listando todos os pagamentos...')

# 1. Listar TODOS os pagamentos
try:
    payments_response = client.list_payments()
    payments = payments_response.get('data', [])
    print(f'📋 Encontrados {len(payments)} pagamentos')
    
    # Cancelar cada pagamento
    canceled = 0
    skipped = 0
    for payment in payments:
        payment_id = payment.get('id')
        status = payment.get('status')
        customer = payment.get('customer')
        value = payment.get('value')
        
        print(f'\\n💰 Pagamento: {payment_id}')
        print(f'   Cliente: {customer}')
        print(f'   Valor: R$ {value}')
        print(f'   Status: {status}')
        
        # Tentar cancelar
        if status in ['PENDING', 'AWAITING_PAYMENT', 'OVERDUE']:
            try:
                client.delete_payment(payment_id)
                print(f'   ✅ CANCELADO')
                canceled += 1
            except Exception as e:
                print(f'   ❌ Erro: {e}')
                skipped += 1
        else:
            print(f'   ⏭️ Não pode ser cancelado (status: {status})')
            skipped += 1
    
    print(f'\\n📊 Resumo Pagamentos:')
    print(f'   Cancelados: {canceled}')
    print(f'   Não cancelados: {skipped}')
    
except Exception as e:
    print(f'❌ Erro ao listar pagamentos: {e}')

print('\\n' + '='*50)
print('🔍 Listando todos os clientes...')

# 2. Listar TODOS os clientes
try:
    customers_response = client.list_customers()
    customers = customers_response.get('data', [])
    print(f'📋 Encontrados {len(customers)} clientes')
    
    # Deletar cada cliente
    deleted = 0
    failed = 0
    for customer in customers:
        customer_id = customer.get('id')
        name = customer.get('name')
        email = customer.get('email')
        
        print(f'\\n👤 Cliente: {customer_id}')
        print(f'   Nome: {name}')
        print(f'   Email: {email}')
        
        # Tentar deletar
        try:
            client.delete_customer(customer_id)
            print(f'   ✅ DELETADO')
            deleted += 1
        except Exception as e:
            print(f'   ❌ Erro: {e}')
            failed += 1
    
    print(f'\\n📊 Resumo Clientes:')
    print(f'   Deletados: {deleted}')
    print(f'   Não deletados: {failed}')
    
except Exception as e:
    print(f'❌ Erro ao listar clientes: {e}')

print('\\n' + '='*50)
print('✅ LIMPEZA CONCLUÍDA!')
print('Verifique em: https://sandbox.asaas.com/payment/list')
\"" --app lwksistemas
```

## 📋 O que o comando faz:

1. **Lista todos os pagamentos** do Asaas
2. **Cancela pagamentos pendentes** (PENDING, AWAITING_PAYMENT, OVERDUE)
3. **Lista todos os clientes** do Asaas
4. **Deleta todos os clientes** (se possível)

## ⚠️ Limitações do Asaas

### Pagamentos que NÃO podem ser cancelados:
- ✅ PENDING - Pode cancelar
- ✅ AWAITING_PAYMENT - Pode cancelar
- ✅ OVERDUE - Pode cancelar
- ❌ CONFIRMED - NÃO pode cancelar (já confirmado)
- ❌ RECEIVED - NÃO pode cancelar (já recebido)
- ❌ RECEIVED_IN_CASH - NÃO pode cancelar

### Clientes que NÃO podem ser deletados:
- Clientes com pagamentos confirmados/recebidos
- Clientes com histórico financeiro

**Solução:** Asaas mantém histórico. Você pode:
1. Cancelar o que for possível
2. Aceitar que pagamentos confirmados ficam no histórico
3. Ou deletar manualmente no painel do Asaas

## 🎯 Alternativa: Deletar Manualmente no Painel

Se o comando não funcionar 100%, delete manualmente:

### 1. Deletar Pagamentos
1. Acesse: https://sandbox.asaas.com/payment/list
2. Para cada pagamento:
   - Clique no pagamento
   - Clique em "Cancelar" ou "Excluir"
   - Confirme

### 2. Deletar Clientes
1. Acesse: https://sandbox.asaas.com/customer/list
2. Para cada cliente:
   - Clique no cliente
   - Clique em "Excluir"
   - Confirme

## 🔄 Limpar Dados Locais Também

Após limpar o Asaas, limpe os dados locais:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.models import AsaasPayment, AsaasCustomer, LojaAssinatura

# Contar antes
payments_count = AsaasPayment.objects.count()
customers_count = AsaasCustomer.objects.count()
subscriptions_count = LojaAssinatura.objects.count()

print(f'📊 Dados locais ANTES:')
print(f'   Pagamentos: {payments_count}')
print(f'   Clientes: {customers_count}')
print(f'   Assinaturas: {subscriptions_count}')

# Deletar tudo
AsaasPayment.objects.all().delete()
print(f'✅ {payments_count} pagamentos deletados')

AsaasCustomer.objects.all().delete()
print(f'✅ {customers_count} clientes deletados')

LojaAssinatura.objects.all().delete()
print(f'✅ {subscriptions_count} assinaturas deletadas')

print('\\n✅ Dados locais limpos!')
\"" --app lwksistemas
```

## 📊 Verificar Resultado

Após executar, verifique:
1. https://sandbox.asaas.com/payment/list - Deve estar vazio
2. https://sandbox.asaas.com/customer/list - Deve estar vazio

## 🎯 Execute AGORA

Cole o comando completo acima no terminal e me envie o resultado!

Ele vai mostrar:
- Quantos pagamentos foram cancelados
- Quantos clientes foram deletados
- Quais não puderam ser removidos (e por quê)
