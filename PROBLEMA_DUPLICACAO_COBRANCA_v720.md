# Problema: Duplicação de Cobranças e Financeiro Não Atualizado (v720)

## Descrição dos Problemas

### Problema 1: Duas Cobranças Criadas (Boleto + PIX)

Ao criar uma loja com provedor Mercado Pago, o sistema cria **2 transações separadas**:
1. **Boleto** (payment_id: 147009653633)
2. **PIX** (payment_id: 147010684823)

Ambas aparecem como transações separadas no painel financeiro, causando confusão.

### Problema 2: Financeiro Não Atualiza Após Pagamento

Após pagar o PIX, o sistema **não atualizou o status do financeiro** para 'ativo' e **não enviou a senha provisória** por email.

## Loja Afetada

- **Nome**: Clinica Luiz
- **Slug**: clinica-luiz-1845
- **Owner**: daniel (danielsouzafelix30@gmail.com)
- **Provedor**: Mercado Pago
- **Boleto ID**: 147009653633
- **PIX ID**: 147010684823
- **Data criação**: 2026-02-25 15:23:35

## Análise Técnica

### Por Que 2 Cobranças São Criadas?

No arquivo `backend/superadmin/mercadopago_service.py`, a função `criar_cobranca_loja` cria:

1. **Boleto** (sempre)
   ```python
   result = client.create_boleto(...)
   payment_id = result.get("id")  # 147009653633
   ```

2. **PIX** (se `criar_pix=True`, que é o padrão)
   ```python
   if criar_pix:
       pix_result = client.create_pix(...)
       pix_payment_id = pix_result.get("id")  # 147010684823
   ```

Isso é **por design** - o objetivo é dar flexibilidade ao cliente de pagar por boleto OU PIX.

### Por Que o Financeiro Não Atualiza?

O webhook do Mercado Pago (`backend/superadmin/views.py`) chama `process_mercadopago_webhook_payment`, que:

1. Busca o pagamento na API do Mercado Pago
2. Verifica se o status é 'approved'
3. Busca o `PagamentoLoja` ou `FinanceiroLoja` pelo payment_id
4. Atualiza o status para 'pago'
5. Chama `_update_loja_financeiro_after_mercadopago_payment` para atualizar o financeiro

**Possíveis causas da falha**:
- Webhook não foi recebido
- Payment ID não foi encontrado no banco
- Erro ao processar o webhook
- Signal `on_payment_confirmed` não foi disparado

## Soluções

### Solução 1: Atualizar Financeiro Manualmente (IMEDIATO)

Execute o script de correção:

```bash
heroku run python manage.py shell < fix_financeiro_clinica_luiz.py --app lwksistemas-38ad47519238
```

Ou no Django shell:

```python
from superadmin.models import Loja, FinanceiroLoja
from django.utils import timezone
from datetime import date
from calendar import monthrange

loja = Loja.objects.get(slug='clinica-luiz-1845')
financeiro = loja.financeiro

# Calcular próxima cobrança
data_vencimento_atual = financeiro.data_proxima_cobranca
dia_vencimento = getattr(financeiro, 'dia_vencimento', 10) or 10

if data_vencimento_atual.month == 12:
    proximo_mes = 1
    proximo_ano = data_vencimento_atual.year + 1
else:
    proximo_mes = data_vencimento_atual.month + 1
    proximo_ano = data_vencimento_atual.year

ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)

# Atualizar financeiro (dispara signal on_payment_confirmed)
financeiro.status_pagamento = 'ativo'
financeiro.ultimo_pagamento = timezone.now()
financeiro.data_proxima_cobranca = proxima_cobranca
financeiro.save(update_fields=['status_pagamento', 'ultimo_pagamento', 'data_proxima_cobranca'])

print("✅ Financeiro atualizado. Senha será enviada automaticamente.")
```

### Solução 2: Verificar e Reprocessar Webhook

Se o webhook foi recebido mas não processou, force o reprocessamento:

```python
from superadmin.sync_service import process_mercadopago_webhook_payment

# Tentar com o PIX ID (que foi pago)
result = process_mercadopago_webhook_payment('147010684823')
print(result)

# Se não funcionar, tentar com o Boleto ID
result = process_mercadopago_webhook_payment('147009653633')
print(result)
```

### Solução 3: Configurar Webhook do Mercado Pago

Verificar se o webhook está configurado corretamente:

1. Acessar: https://www.mercadopago.com.br/developers/panel/webhooks
2. Verificar URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/webhook/mercadopago/`
3. Eventos habilitados: `payment`
4. Testar webhook manualmente com o payment_id: 147010684823

### Solução 4: Corrigir Duplicação de Cobranças (LONGO PRAZO)

#### Opção A: Criar Apenas Boleto (Sem PIX Automático)

Modificar `backend/superadmin/cobranca_service.py`:

```python
class MercadoPagoPaymentStrategy(PaymentProviderStrategy):
    def criar_cobranca(self, loja, financeiro) -> Dict[str, Any]:
        # ...
        # Criar apenas boleto (sem PIX automático)
        result = service.criar_cobranca_loja(loja, financeiro, criar_pix=False)
        # ...
```

**Vantagem**: Apenas 1 transação criada
**Desvantagem**: Cliente precisa clicar em "Gerar PIX" manualmente

#### Opção B: Unificar Boleto + PIX em Uma Única Transação

Modificar o painel financeiro para mostrar boleto e PIX como **uma única cobrança** com 2 formas de pagamento:

```
Cobrança #1 - R$ 15,00 - Vencimento: 15/03/2026
├── Boleto: 147009653633 [Ver Boleto]
└── PIX: 147010684823 [Ver QR Code]
```

**Vantagem**: Melhor UX, cliente vê como uma cobrança só
**Desvantagem**: Requer mudanças no frontend

#### Opção C: Cancelar Automaticamente a Outra Transação Após Pagamento

Quando uma das transações (boleto OU PIX) for paga, cancelar automaticamente a outra:

```python
def _update_loja_financeiro_after_mercadopago_payment(loja, financeiro):
    # ... código existente ...
    
    # Cancelar a outra transação pendente
    from superadmin.mercadopago_service import MercadoPagoClient
    from superadmin.models import MercadoPagoConfig
    
    config = MercadoPagoConfig.get_config()
    if config and config.access_token:
        client = MercadoPagoClient(config.access_token)
        
        # Se pagou o boleto, cancelar o PIX
        if financeiro.mercadopago_payment_id and financeiro.mercadopago_pix_payment_id:
            # Verificar qual foi pago
            boleto_data = client.get_payment(financeiro.mercadopago_payment_id)
            pix_data = client.get_payment(financeiro.mercadopago_pix_payment_id)
            
            if boleto_data and boleto_data.get('status') == 'approved':
                # Boleto pago, cancelar PIX
                client.cancel_payment(financeiro.mercadopago_pix_payment_id)
                logger.info(f"PIX {financeiro.mercadopago_pix_payment_id} cancelado (boleto pago)")
            
            elif pix_data and pix_data.get('status') == 'approved':
                # PIX pago, cancelar boleto
                client.cancel_payment(financeiro.mercadopago_payment_id)
                logger.info(f"Boleto {financeiro.mercadopago_payment_id} cancelado (PIX pago)")
```

**Vantagem**: Evita pagamento duplicado
**Desvantagem**: Cliente não pode mudar de ideia depois

## Recomendação

**Curto prazo** (hoje):
1. ✅ Executar `fix_financeiro_clinica_luiz.py` para corrigir a loja atual
2. ✅ Verificar se o webhook está configurado corretamente
3. ✅ Adicionar logs detalhados no webhook e signal

**Médio prazo** (próxima semana):
1. Implementar **Opção C** (cancelar automaticamente a outra transação)
2. Melhorar o painel financeiro para mostrar boleto + PIX como uma cobrança unificada
3. Adicionar testes automatizados para o fluxo de pagamento

**Longo prazo** (próximo mês):
1. Criar dashboard de monitoramento de webhooks
2. Implementar retry automático para webhooks falhados
3. Adicionar alertas para pagamentos não processados

## Comandos Úteis

```bash
# Ver logs do webhook
heroku logs --tail --app lwksistemas-38ad47519238 | grep -i "webhook\|mercadopago"

# Executar script de correção
heroku run python manage.py shell < fix_financeiro_clinica_luiz.py --app lwksistemas-38ad47519238

# Abrir Django shell
heroku run python manage.py shell --app lwksistemas-38ad47519238

# Verificar status do pagamento no Mercado Pago
heroku run python manage.py shell --app lwksistemas-38ad47519238
>>> from superadmin.mercadopago_service import MercadoPagoClient
>>> from superadmin.models import MercadoPagoConfig
>>> config = MercadoPagoConfig.get_config()
>>> client = MercadoPagoClient(config.access_token)
>>> pix_data = client.get_payment('147010684823')
>>> print(f"Status: {pix_data.get('status')}")
>>> print(f"Aprovado em: {pix_data.get('date_approved')}")
```

## Arquivos Relacionados

- `backend/superadmin/mercadopago_service.py` - Criação de cobranças
- `backend/superadmin/cobranca_service.py` - Strategy Pattern
- `backend/superadmin/views.py` - Webhook do Mercado Pago
- `backend/superadmin/sync_service.py` - Processamento de webhooks
- `backend/superadmin/signals.py` - Signal on_payment_confirmed
- `backend/superadmin/email_service.py` - Envio de senha provisória
- `backend/fix_financeiro_clinica_luiz.py` - Script de correção
