# 🧹 Limpar TODAS as Lojas do Asaas

## ✅ Primeira Limpeza Funcionou!

Resultado:
- ✅ harmonis: 1 pagamento cancelado, 1 cliente excluído

## 🔍 Problema Identificado

O comando `cleanup_orphaned_asaas_data()` só limpa assinaturas **órfãs** (sem loja correspondente no banco).

As outras lojas (vida, felix, linda, etc) podem:
1. Ainda existir no banco de lojas
2. Ter assinaturas mas sem registro em `LojaAssinatura`
3. Ter sido criadas diretamente no Asaas sem passar pelo sistema

## 🎯 Solução: Limpar Manualmente Cada Loja

Execute para cada loja que aparece no Asaas:

### 1. Verificar quais lojas existem no banco

```bash
heroku run "python backend/manage.py shell -c \"
from superadmin.models import Loja

print('📦 Lojas no banco:')
for loja in Loja.objects.all():
    print(f'  - {loja.slug} (ID: {loja.id}, Nome: {loja.nome})')
\"" --app lwksistemas
```

### 2. Verificar assinaturas Asaas

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.models import LojaAssinatura

print('💳 Assinaturas Asaas:')
for a in LojaAssinatura.objects.all():
    print(f'  - {a.loja_slug}: Cliente {a.asaas_customer.asaas_id}')
\"" --app lwksistemas
```

### 3. Deletar lojas específicas do Asaas

Para cada loja que aparece no Asaas mas não deveria existir:

```bash
# Para loja "vida"
heroku run "python backend/manage.py shell -c \"
from asaas_integration.deletion_service import AsaasDeletionService

service = AsaasDeletionService()
result = service.delete_loja_from_asaas('vida')
print(f'Resultado: {result}')
\"" --app lwksistemas

# Para loja "felix"
heroku run "python backend/manage.py shell -c \"
from asaas_integration.deletion_service import AsaasDeletionService

service = AsaasDeletionService()
result = service.delete_loja_from_asaas('felix')
print(f'Resultado: {result}')
\"" --app lwksistemas

# Para loja "linda"
heroku run "python backend/manage.py shell -c \"
from asaas_integration.deletion_service import AsaasDeletionService

service = AsaasDeletionService()
result = service.delete_loja_from_asaas('linda')
print(f'Resultado: {result}')
\"" --app lwksistemas
```

### 4. Se não funcionar (loja não tem LojaAssinatura)

Deletar direto pela API do Asaas:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig

# Configurar cliente
config = AsaasConfig.get_config()
client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)

# Listar todos os clientes
customers = client.list_customers()
print('👥 Clientes no Asaas:')
for customer in customers.get('data', []):
    print(f'  - {customer.get(\"name\")}: {customer.get(\"id\")}')

# Listar todos os pagamentos
payments = client.list_payments()
print('\n💰 Pagamentos no Asaas:')
for payment in payments.get('data', []):
    print(f'  - {payment.get(\"customer\")}: {payment.get(\"id\")} - {payment.get(\"status\")}')
\"" --app lwksistemas
```

### 5. Deletar cliente específico do Asaas

Se você souber o ID do cliente:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig

config = AsaasConfig.get_config()
client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)

# Deletar cliente (substitua pelo ID real)
customer_id = 'cus_000007487545'  # ← Trocar pelo ID
result = client.delete_customer(customer_id)
print(f'Cliente deletado: {result}')
\"" --app lwksistemas
```

## 🚀 Comando Completo (Limpar Tudo)

Execute este comando para limpar TODAS as assinaturas órfãs de uma vez:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.deletion_service import AsaasDeletionService
from asaas_integration.models import LojaAssinatura
from superadmin.models import Loja

service = AsaasDeletionService()

# Listar todas as assinaturas
print('📋 Verificando assinaturas...')
all_subscriptions = LojaAssinatura.objects.all()
print(f'Total: {all_subscriptions.count()}')

for subscription in all_subscriptions:
    loja_slug = subscription.loja_slug
    
    # Verificar se loja existe
    try:
        loja = Loja.objects.get(slug=loja_slug)
        print(f'✅ {loja_slug}: Loja existe (manter)')
    except Loja.DoesNotExist:
        print(f'🗑️ {loja_slug}: Loja não existe (deletar)')
        result = service.delete_loja_from_asaas(loja_slug)
        print(f'   Resultado: {result}')
\"" --app lwksistemas
```

## 📊 Verificar Resultado

Após executar, verifique no Asaas:
- https://sandbox.asaas.com/payment/list
- https://sandbox.asaas.com/customer/list

Deve estar vazio ou só com as lojas ativas.

## ⚠️ Importante

**Pagamentos CONFIRMED ou RECEIVED não podem ser cancelados!**

Se aparecer erro tipo:
```
Pagamento não pode ser removido (já processado)
```

É normal! Asaas mantém histórico de pagamentos confirmados. Você só pode:
1. Cancelar pagamentos PENDING
2. Deletar o cliente (mas histórico fica)
3. Aceitar que pagamentos confirmados ficam no histórico

## 🎯 Próximos Passos

1. Execute o comando completo acima
2. Verifique no Asaas se limpou
3. Me diga quantas lojas/pagamentos ainda aparecem
