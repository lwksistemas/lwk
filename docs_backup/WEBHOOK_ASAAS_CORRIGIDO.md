# Webhook Asaas - Correção de Erro 400

## 🚨 PROBLEMA IDENTIFICADO

O webhook do Asaas estava retornando erro 400 com a mensagem:
```
"Pagamento não encontrado e não foi possível criar automaticamente"
```

### 📊 Análise do Erro

**Webhook recebido**:
- Event: `PAYMENT_CREATED`
- Payment ID: `pay_cgi67bfre2gdiuby`
- Customer ID: `cus_000007469087`
- External Reference: `loja_loja-final-teste_assinatura`

**Problemas encontrados**:
1. ❌ Cliente `cus_000007469087` não existe no sistema
2. ❌ Loja `loja-final-teste` não existe no sistema
3. ❌ Webhook retornava erro 400, causando reenvios desnecessários

## ✅ CORREÇÕES IMPLEMENTADAS

### 1. Melhor Validação de Loja
```python
# Verificar se a loja existe pelo external_reference
if external_reference and 'loja_' in external_reference:
    loja_slug = external_reference.replace('loja_', '').replace('_assinatura', '')
    try:
        loja = Loja.objects.get(slug=loja_slug, is_active=True)
        logger.info(f"Loja encontrada para webhook: {loja.nome} ({loja_slug})")
    except Loja.DoesNotExist:
        logger.warning(f"Loja {loja_slug} não encontrada - webhook ignorado")
        return None
```

### 2. Tratamento de Cliente Inexistente
```python
try:
    customer = AsaasCustomer.objects.get(asaas_id=customer_id)
    logger.info(f"Cliente encontrado: {customer.name}")
except AsaasCustomer.DoesNotExist:
    logger.warning(f"Cliente {customer_id} não encontrado - tentando criar automaticamente")
    # Por enquanto, ignorar webhook se cliente não existe
    logger.warning(f"Não é possível criar cliente automaticamente - dados insuficientes")
    return None
```

### 3. Retorno 200 para Webhooks Ignorados
```python
# Retornar sucesso para evitar reenvio do webhook
return {
    'success': True,
    'payment_id': payment_id,
    'status': 'ignored',
    'reason': 'Pagamento não encontrado e não foi possível criar automaticamente (loja ou cliente inexistente)'
}
```

### 4. Melhor Logging e Resposta
```python
# Se foi ignorado, adicionar razão
if resultado.get('status') == 'ignored':
    response_data['reason'] = resultado.get('reason')
    logger.info(f"Webhook ignorado: {resultado.get('reason')}")
```

## 🔍 DIAGNÓSTICO REALIZADO

### Lojas Ativas no Sistema
```
• harmonis - Harmonis
• felix - felix
```

### Clientes Asaas Cadastrados
```
• cus_000007472690 - felix (financeiroluiz@hotmail.com)
• cus_000007473535 - Harmonis (nayarass03@hotmail.com)
```

### Webhook Problemático
- **Loja**: `loja-final-teste` ❌ (não existe)
- **Cliente**: `cus_000007469087` ❌ (não existe)
- **Conclusão**: Webhook de loja excluída ou teste

## 🎯 BENEFÍCIOS DA CORREÇÃO

1. **✅ Sem Mais Erros 400**: Webhooks de lojas inexistentes são ignorados graciosamente
2. **✅ Logs Informativos**: Melhor rastreabilidade de webhooks ignorados
3. **✅ Sem Reenvios**: Asaas não reenvia webhooks que retornam 200
4. **✅ Sistema Estável**: Não há mais penalizações por webhooks mal formados

## 🚀 DEPLOY

- **Backend**: ✅ v149 - Correções implementadas
- **Status**: ✅ Webhook funcionando corretamente
- **Teste**: ✅ Webhooks válidos processados, inválidos ignorados

## 🧪 TESTE

Para testar o webhook corrigido:

1. **Webhook Válido** (loja felix):
   - Customer: `cus_000007472690`
   - External Reference: `loja_felix_assinatura`
   - ✅ Deve processar normalmente

2. **Webhook Inválido** (loja inexistente):
   - Customer: `cus_000007469087`
   - External Reference: `loja_loja-final-teste_assinatura`
   - ✅ Deve retornar 200 com status "ignored"

## 📋 LOGS DE EXEMPLO

### Webhook Válido
```
INFO: Webhook processado com sucesso: {'success': True, 'payment_id': 'pay_123', 'status_updated': True}
```

### Webhook Ignorado
```
WARNING: Loja loja-final-teste não encontrada - webhook ignorado
INFO: Webhook ignorado: Pagamento não encontrado e não foi possível criar automaticamente (loja ou cliente inexistente)
```

## 🔧 MONITORAMENTO

O sistema agora monitora:
- ✅ Webhooks processados com sucesso
- ✅ Webhooks ignorados (com razão)
- ✅ Erros reais de processamento
- ✅ Status de sincronização

---

**Data**: 22/01/2026  
**Status**: ✅ Corrigido  
**Deploy**: v149 - Produção  
**Webhook URL**: https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/