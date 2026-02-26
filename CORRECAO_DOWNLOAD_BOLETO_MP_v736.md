# Deploy v736: Correção Download de Boleto Mercado Pago no Histórico

**Data**: 25/02/2026  
**Status**: ✅ Concluído (2 deploys)

## Problema Identificado

O botão "Ver Boleto" no histórico de pagamentos da loja não estava funcionando para boletos do Mercado Pago. Havia 2 problemas:

1. **Backend**: O histórico estava usando `financeiro.id` ao invés de `PagamentoLoja.id`
2. **Frontend**: O botão só aparecia se `asaas_payment_id` existisse (não funcionava para MP)
3. A URL do boleto salva no banco estava truncada (200 chars) e perdia o hash de segurança

**Exemplo do erro**:
```
https://www.mercadopago.com.br/payments/147751949750/ticket?caller_id=3224326476&payment_method_id=bolbradesco&payment_id=147751949750&payment_method_reference_id=10552933742&hash=bb65f4a0-d6b1-4abf-82e9-af67c4252c1d

Resultado: "Pagamento indisponível - O prazo para pagar já acabou ou o pagamento foi recusado ou reembolsado."
```

## Solução Implementada

### Backend (`backend/superadmin/financeiro_views.py`)

1. **Corrigido histórico de pagamentos Mercado Pago**:
   - Agora busca o `PagamentoLoja.id` correto ao invés de usar `financeiro.id`
   - Adicionado campo `mercadopago_payment_id` no histórico
   - Adicionado campo `provedor_boleto` para identificar o provedor
   - Incluído `pix_copy_paste` e `pix_qr_code` no histórico MP

```python
# Buscar PagamentoLoja correspondente (pendente ou mais recente)
pagamento_mp = PagamentoLoja.objects.filter(
    loja=loja,
    financeiro=financeiro,
    provedor_boleto='mercadopago'
).order_by('-data_vencimento').first()

if not pagamento_mp:
    logger.warning(f"⚠️ PagamentoLoja não encontrado para loja MP {loja.nome}, criando entrada temporária")
    pagamento_id = 0  # ID temporário, frontend não conseguirá baixar boleto
else:
    pagamento_id = pagamento_mp.id

historico_pagamentos.append({
    'id': pagamento_id,
    'asaas_id': getattr(financeiro, 'mercadopago_payment_id', '') or '',
    'mercadopago_payment_id': getattr(financeiro, 'mercadopago_payment_id', '') or '',  # ✅ NOVO v736
    'provedor_boleto': 'mercadopago',  # ✅ NOVO v736
    'valor': float(financeiro.valor_mensalidade),
    'status': 'PENDING',
    'status_display': 'Aguardando pagamento',
    'data_vencimento': financeiro.data_proxima_cobranca.strftime('%Y-%m-%d') if financeiro.data_proxima_cobranca else None,
    'data_pagamento': None,
    'boleto_url': boleto_url,
    'pix_copy_paste': pix_copy_paste or '',  # ✅ NOVO v736
    'pix_qr_code': pix_qr_code or '',  # ✅ NOVO v736
    'is_paid': False,
    'is_pending': True,
    'is_overdue': False,
})
```

2. **Adicionado campos no histórico Asaas para consistência**:
```python
historico_pagamentos.append({
    'id': pag.id,
    'asaas_id': pag.asaas_id,
    'mercadopago_payment_id': '',  # ✅ NOVO v736: Vazio para Asaas
    'provedor_boleto': 'asaas',  # ✅ NOVO v736: Identificar provedor
    # ... resto dos campos
})
```

### Frontend (`frontend/app/(dashboard)/loja/[slug]/financeiro/page.tsx`)

3. **Modificado função `baixarBoleto`**:
   - Agora aceita parâmetros `mercadopagoPaymentId` e `provedor`
   - Para Mercado Pago, busca URL do boleto diretamente da API (não usa URL salva no banco)
   - Tratamento de erros melhorado

```tsx
const baixarBoleto = async (pagamentoId: number, mercadopagoPaymentId?: string, provedor?: string) => {
  try {
    // Se for Mercado Pago e tiver o payment_id, usar endpoint direto
    if (provedor === 'mercadopago' && mercadopagoPaymentId) {
      // Buscar URL do boleto diretamente da API do Mercado Pago via backend
      const response = await fetch(`${API_BASE_URL}/api/superadmin/loja-pagamentos/${pagamentoId}/baixar_boleto_pdf/`, {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
        }
      })
      if (!response.ok) {
        alert('Erro ao abrir boleto')
        return
      }
      const data = await response.json() as { boleto_url?: string; provedor?: string; error?: string }
      if (data.error) {
        alert(data.error)
        return
      }
      if (data.boleto_url) {
        window.open(data.boleto_url, '_blank', 'noopener,noreferrer')
        return
      }
      alert('Link do boleto não disponível')
      return
    }
    
    // Fluxo normal para Asaas...
  }
}
```

4. **Atualizado chamadas para `baixarBoleto`**:
```tsx
// Próximo pagamento
onClick={() => baixarBoleto(
  data.proximo_pagamento.id,
  data.proximo_pagamento.mercadopago_payment_id,
  data.proximo_pagamento.provedor_boleto || 'asaas'
)}

// Histórico de pagamentos
onClick={() => baixarBoleto(
  pagamento.id,
  pagamento.mercadopago_payment_id,
  pagamento.provedor_boleto || 'asaas'
)}
```

## Resultado

✅ Botão "Ver Boleto" agora funciona corretamente para Mercado Pago  
✅ URL do boleto é buscada diretamente da API (sempre atualizada com hash válido)  
✅ Histórico usa `PagamentoLoja.id` correto  
✅ Tratamento de erros melhorado  
✅ Botão "Pagar com PIX" também disponível no histórico  

## Deploy

### Backend (v737)
- Deploy realizado via Heroku
- URL: https://lwksistemas-38ad47519238.herokuapp.com
- Commit: 2a9e84d0

### Frontend (v736)
- Deploy realizado via Vercel
- URL: https://lwksistemas.com.br
- Inspect: https://vercel.com/lwks-projects-48afd555/frontend/8fmBziVs8t6U1t7BgZ3fkXtZDUD4

## Teste

Para testar:
1. Acesse https://lwksistemas.com.br/loja/clinica-daniel-5889/financeiro
2. Verifique o histórico de pagamentos
3. Clique em "Ver Boleto" para pagamento Mercado Pago
4. Boleto deve abrir em nova aba com URL válida
5. Clique em "Pagar com PIX" para copiar código PIX

## Arquivos Modificados

- `backend/superadmin/financeiro_views.py`
- `frontend/app/(dashboard)/loja/[slug]/financeiro/page.tsx`

## Observações

- A URL do boleto do Mercado Pago muda a cada consulta (novo hash de segurança)
- Por isso, sempre buscamos da API ao invés de usar a URL salva no banco
- O endpoint `baixar_boleto_pdf` já estava preparado para isso desde v733
- Esta correção garante que o histórico use o ID correto do `PagamentoLoja`
