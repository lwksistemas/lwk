# 🗑️ Exclusão de Loja e Asaas - v248

## 📊 Situação Atual

Você excluiu lojas mas os boletos ainda aparecem no Asaas:
- https://sandbox.asaas.com/payment/list

**Lojas visíveis no Asaas:**
- vida (R$ 199,90)
- Harmonis (R$ 399,90 - 2x)
- felix (R$ 199,90)
- Linda (R$ 399,90)
- Vendas Felix (R$ 199,90)
- Vida (R$ 399,90)
- felix (R$ 199,90)

## ✅ Código de Exclusão JÁ EXISTE

O sistema **JÁ TEM** código para deletar do Asaas:

### Arquivo: `backend/asaas_integration/deletion_service.py`

```python
class AsaasDeletionService:
    def delete_loja_from_asaas(self, loja_slug: str):
        # 1. Busca assinatura da loja
        # 2. Cancela todos os pagamentos pendentes
        # 3. Exclui cliente do Asaas
        # 4. Remove dados locais
```

### Arquivo: `backend/superadmin/views.py` (linha 295-340)

```python
# 3. Remover dados do Asaas (API e dados locais)
deletion_service = AsaasDeletionService()
if deletion_service.available:
    result = deletion_service.delete_loja_from_asaas(loja_slug)
```

## ❓ Por que não funcionou?

### Possíveis causas:

1. **AsaasConfig não está configurado**
   - API Key não está setada
   - Serviço está desabilitado

2. **Pagamentos já foram processados**
   - Asaas não permite cancelar pagamentos CONFIRMED ou RECEIVED
   - Apenas PENDING, AWAITING_PAYMENT, OVERDUE podem ser cancelados

3. **Erro silencioso**
   - Erro aconteceu mas não foi mostrado ao usuário
   - Logs não foram verificados

## 🔍 Como Verificar

### 1. Verificar configuração do Asaas

Execute no Heroku:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.models import AsaasConfig
config = AsaasConfig.get_config()
print(f'API Key: {config.api_key[:10]}...' if config.api_key else 'Não configurado')
print(f'Enabled: {config.enabled}')
print(f'Sandbox: {config.sandbox}')
\"" --app lwksistemas
```

### 2. Verificar assinaturas existentes

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.models import LojaAssinatura
assinaturas = LojaAssinatura.objects.all()
print(f'Total de assinaturas: {assinaturas.count()}')
for a in assinaturas:
    print(f'  - {a.loja_slug}: Cliente Asaas {a.asaas_customer.asaas_id}')
\"" --app lwksistemas
```

### 3. Ver logs da última exclusão

```bash
heroku logs --tail --app lwksistemas | grep -i "asaas\|exclusão\|delete"
```

## 🔧 Solução: Limpar Manualmente

Se as lojas já foram excluídas mas os boletos ficaram, você precisa limpar manualmente:

### Opção 1: Limpar dados órfãos (RECOMENDADO)

Criei um comando para isso. Execute:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.deletion_service import AsaasDeletionService

service = AsaasDeletionService()
if service.available:
    result = service.cleanup_orphaned_asaas_data()
    print(f'Resultado: {result}')
else:
    print('Serviço Asaas não disponível')
\"" --app lwksistemas
```

### Opção 2: Deletar manualmente cada loja

Para cada loja que ainda aparece no Asaas:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.deletion_service import AsaasDeletionService

service = AsaasDeletionService()
result = service.delete_loja_from_asaas('vida')  # ← Trocar pelo slug
print(f'Resultado: {result}')
\"" --app lwksistemas
```

Repita para cada loja:
- `vida`
- `harmonis`
- `felix`
- `linda`
- `vendas-felix`

### Opção 3: Deletar direto na API do Asaas

Se o serviço não funcionar, delete manualmente no painel do Asaas:

1. Acesse: https://sandbox.asaas.com/payment/list
2. Para cada boleto:
   - Clique no boleto
   - Clique em "Cancelar" ou "Excluir"
3. Depois vá em: https://sandbox.asaas.com/customer/list
4. Delete os clientes órfãos

## 🚀 Prevenir no Futuro

### Garantir que funcione na próxima exclusão:

1. **Verificar configuração do Asaas:**

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.models import AsaasConfig
config = AsaasConfig.get_config()
if not config.api_key:
    print('❌ API Key não configurada!')
elif not config.enabled:
    print('❌ Asaas desabilitado!')
else:
    print('✅ Asaas configurado corretamente')
\"" --app lwksistemas
```

2. **Testar exclusão com uma loja de teste:**

```bash
# Criar loja de teste
# Criar assinatura no Asaas
# Excluir loja
# Verificar se sumiu do Asaas
```

3. **Ver logs durante a exclusão:**

```bash
# Terminal 1: Ver logs
heroku logs --tail --app lwksistemas

# Terminal 2: Excluir loja pelo frontend
# Observar os logs no Terminal 1
```

## 📝 Logs Esperados

Quando funciona corretamente, você deve ver:

```
🗑️ Iniciando exclusão Asaas para loja: vida
📋 Encontrados 2 pagamentos para cliente cus_000123
✅ Pagamento cancelado: pay_000456
✅ Pagamento cancelado: pay_000789
✅ Cliente excluído do Asaas: cus_000123
✅ Exclusão Asaas concluída para loja: vida
```

Se não aparecer, significa que o serviço não está sendo executado.

## 🆘 Troubleshooting

### Erro: "Serviço Asaas não disponível"
**Causa:** AsaasConfig não está configurado
**Solução:** Configurar API Key do Asaas

### Erro: "Pagamento não pode ser removido"
**Causa:** Pagamento já foi confirmado/recebido
**Solução:** Normal, apenas pagamentos pendentes podem ser cancelados

### Erro: "Cliente não pode ser excluído"
**Causa:** Cliente tem histórico de pagamentos confirmados
**Solução:** Normal, Asaas mantém histórico

### Nenhum log aparece
**Causa:** Serviço não está sendo chamado
**Solução:** Verificar se AsaasDeletionService está disponível

## 🎯 Ação Imediata

Execute AGORA para limpar os boletos órfãos:

```bash
heroku run "python backend/manage.py shell -c \"
from asaas_integration.deletion_service import AsaasDeletionService
from asaas_integration.models import LojaAssinatura

# Listar assinaturas
print('📋 Assinaturas no banco:')
for a in LojaAssinatura.objects.all():
    print(f'  - {a.loja_slug}: {a.asaas_customer.asaas_id}')

# Limpar órfãos
service = AsaasDeletionService()
if service.available:
    print('\n🧹 Limpando dados órfãos...')
    result = service.cleanup_orphaned_asaas_data()
    print(f'✅ Resultado: {result}')
else:
    print('❌ Serviço Asaas não disponível')
    print('Verifique a configuração do AsaasConfig')
\"" --app lwksistemas
```

Me envie o resultado desse comando!
