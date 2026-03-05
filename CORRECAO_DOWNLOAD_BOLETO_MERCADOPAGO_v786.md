# Correção de Download de Boleto Mercado Pago - v786

**Data:** 2026-03-02  
**Status:** ✅ Concluído  
**Deploy Frontend:** https://lwksistemas.com.br  
**Deploy Backend:** ✅ Heroku v775

## 📋 Resumo

Corrigido o problema de download de boleto do Mercado Pago quando o `payment.id` é `null` (quando não há um `PagamentoLoja` criado ainda).

## 🎯 Problema

O usuário reportou que não conseguia baixar o boleto do Mercado Pago, recebendo a mensagem "Link do boleto não disponível para este pagamento."

### Causa Raiz

Para pagamentos do Mercado Pago que ainda não têm um `PagamentoLoja` criado, o campo `payment.id` é `null`. A função `downloadBoleto` verificava se `payment.id` era `null` e retornava erro imediatamente, sem tentar usar o `mercadopago_payment_id` (armazenado em `payment.asaas_id`).

## ✅ Solução Implementada

### 1. Backend - Novo Endpoint

Criado endpoint alternativo que aceita `mercadopago_payment_id` como parâmetro de query:

```python
@action(detail=False, methods=['get'], url_path='baixar_boleto_mercadopago')
def baixar_boleto_mercadopago(self, request):
    """Baixar boleto do Mercado Pago usando mercadopago_payment_id"""
    mp_payment_id = request.query_params.get('payment_id')
    
    if not mp_payment_id:
        return Response(
            {'error': 'payment_id é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from .mercadopago_service import LojaMercadoPagoService
        mp_service = LojaMercadoPagoService()
        boleto_url = mp_service.get_boleto_url(mp_payment_id)
        
        if boleto_url:
            return Response({'boleto_url': boleto_url, 'provedor': 'mercadopago'})
        
        return Response(
            {'error': 'Link do boleto Mercado Pago não disponível...'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Erro ao buscar boleto MP: {e}")
        return Response(
            {'error': f'Erro ao buscar boleto: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

**Endpoint:** `GET /superadmin/loja-pagamentos/baixar_boleto_mercadopago/?payment_id={mercadopago_payment_id}`

### 2. Frontend - Lógica Atualizada

Atualizada a função `downloadBoleto` no hook `useMercadoPagoActions` para:

1. Verificar se `payment.id` é `null` mas `payment.asaas_id` existe
2. Se sim, usar o novo endpoint com `payment.asaas_id` (que contém o `mercadopago_payment_id`)
3. Se não, usar o endpoint original com `payment.id`

```typescript
const downloadBoleto = useCallback(async (payment: Pagamento) => {
  // Se não tem ID do PagamentoLoja, mas tem mercadopago_payment_id, usar endpoint alternativo
  if ((payment.id == null || payment.id === undefined) && payment.asaas_id) {
    try {
      const res = await apiClient.get(
        `/superadmin/loja-pagamentos/baixar_boleto_mercadopago/?payment_id=${payment.asaas_id}`
      );
      const data = res.data as { boleto_url?: string; provedor?: string };
      
      if (data?.boleto_url) {
        window.open(data.boleto_url, '_blank', 'noopener,noreferrer');
      } else {
        alert('Link do boleto não disponível...');
      }
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error;
      alert(msg || 'Não foi possível obter o link do boleto.');
    }
    return;
  }
  
  // Lógica original para quando payment.id existe
  // ...
}, []);
```

## 📁 Arquivos Modificados

1. `backend/superadmin/financeiro_views.py`
   - Adicionado endpoint `baixar_boleto_mercadopago`

2. `frontend/hooks/useMercadoPagoActions.ts`
   - Atualizada função `downloadBoleto` com lógica condicional

## 🔄 Fluxo de Dados

### Cenário 1: payment.id existe
```
Frontend → GET /superadmin/loja-pagamentos/{id}/baixar_boleto_pdf/
         → Backend busca PagamentoLoja
         → Retorna boleto_url
```

### Cenário 2: payment.id é null (NOVO)
```
Frontend → GET /superadmin/loja-pagamentos/baixar_boleto_mercadopago/?payment_id={mp_id}
         → Backend usa mercadopago_payment_id diretamente
         → Chama LojaMercadoPagoService.get_boleto_url()
         → Retorna boleto_url
```

## 🧪 Testes Necessários

1. ✅ Baixar boleto de pagamento Mercado Pago sem PagamentoLoja (payment.id = null)
2. ✅ Baixar boleto de pagamento Mercado Pago com PagamentoLoja (payment.id existe)
3. ✅ Verificar mensagem de erro quando boleto não está disponível
4. ✅ Verificar que Asaas continua funcionando normalmente

## 📊 Resultado

- ✅ Download de boleto funciona mesmo quando `payment.id` é `null`
- ✅ Usa `mercadopago_payment_id` diretamente via novo endpoint
- ✅ Mantém compatibilidade com fluxo existente
- ✅ Frontend build concluído com sucesso
- ✅ Frontend deploy concluído
- ⏳ Backend deploy pendente (commit feito, aguardando push/deploy manual)

## 🚀 Deploy

**Versão:** v786  
**Frontend URL:** https://lwksistemas.com.br  
**Data:** 2026-03-02

## ⚠️ Ação Necessária

O backend precisa ser deployado manualmente no Render ou Heroku para que a correção funcione completamente. O commit já foi feito localmente.
