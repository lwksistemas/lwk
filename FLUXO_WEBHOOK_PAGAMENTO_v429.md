# 🔄 Fluxo Webhook Pagamento - v429

## 📊 DIAGRAMA COMPLETO

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRIAR NOVA LOJA                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SuperAdmin → Criar Loja                                        │
│  - Nome, Plano, Tipo Assinatura                                 │
│  - Dados do Admin (email, senha)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  LojaCreateSerializer.create()                                  │
│  - Cria User (admin da loja)                                    │
│  - Cria Loja                                                    │
│  - Cria FinanceiroLoja                                          │
│  - Cria Schema PostgreSQL                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  🎯 SIGNAL: create_asaas_subscription_on_loja_creation          │
│  (asaas_integration/signals.py)                                 │
│                                                                 │
│  ✅ Cria AsaasCustomer                                          │
│  ✅ Cria AsaasPayment (1 cobrança)                              │
│  ✅ Cria LojaAssinatura                                         │
│  ✅ Envia email com boleto                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LOJA CRIADA ✅                               │
│  - 1 cobrança no Asaas                                          │
│  - Email enviado ao admin                                       │
│  - Status: Aguardando Pagamento                                 │
└─────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────┐
│                    CLIENTE PAGA BOLETO                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Asaas processa pagamento                                       │
│  - Status: PENDING → RECEIVED                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  🔔 WEBHOOK: Asaas envia notificação                            │
│  POST /api/asaas/webhook/                                       │
│                                                                 │
│  {                                                              │
│    "event": "PAYMENT_RECEIVED",                                 │
│    "payment": {                                                 │
│      "id": "pay_xxx",                                           │
│      "status": "RECEIVED",                                      │
│      "value": 99.90                                             │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  AsaasWebhookView.post()                                        │
│  (asaas_integration/views.py)                                   │
│                                                                 │
│  - Valida webhook                                               │
│  - Extrai dados do pagamento                                    │
│  - Chama sync_service                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  AsaasSyncService.process_webhook_payment()                     │
│  (superadmin/sync_service.py - linha 276)                       │
│                                                                 │
│  1. Busca pagamento no banco                                    │
│  2. Atualiza status do pagamento                                │
│  3. Verifica se foi confirmado                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  ✅ Pagamento Confirmado?                                       │
│  (RECEIVED, CONFIRMED, RECEIVED_IN_CASH)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ SIM
┌─────────────────────────────────────────────────────────────────┐
│  🎯 _update_loja_financeiro_from_payment()                      │
│  (superadmin/sync_service.py - linha 476)                       │
│                                                                 │
│  ✅ Atualiza AsaasPayment:                                      │
│     - status = 'RECEIVED'                                       │
│     - payment_date = hoje                                       │
│                                                                 │
│  ✅ Atualiza FinanceiroLoja:                                    │
│     - status_pagamento = 'ativo'                                │
│     - ultimo_pagamento = hoje                                   │
│                                                                 │
│  ✅ Atualiza Loja (se bloqueada):                               │
│     - is_blocked = False                                        │
│     - blocked_at = None                                         │
│     - blocked_reason = ''                                       │
│     - days_overdue = 0                                          │
│                                                                 │
│  ✅ Emite Nota Fiscal:                                          │
│     - Gera NF no Asaas                                          │
│     - Envia por email ao admin                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LOJA ATUALIZADA ✅                           │
│  - Status: Ativo                                                │
│  - Último Pagamento: Hoje                                       │
│  - Loja: Desbloqueada                                           │
│  - Nota Fiscal: Enviada                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 DETALHAMENTO POR ETAPA

### 1️⃣ CRIAÇÃO DA LOJA

**Arquivo**: `backend/superadmin/serializers.py`

```python
def create(self, validated_data):
    # 1. Criar usuário admin
    owner = User.objects.create_user(...)
    
    # 2. Criar loja
    loja = Loja.objects.create(owner=owner, ...)
    
    # 3. Criar financeiro
    financeiro = FinanceiroLoja.objects.create(loja=loja, ...)
    
    # 4. Signal cria cobrança automaticamente
    # (não precisa fazer nada aqui)
    
    return loja
```

**Signal Automático**: `backend/asaas_integration/signals.py`

```python
@receiver(post_save, sender='superadmin.Loja')
def create_asaas_subscription_on_loja_creation(sender, instance, created, **kwargs):
    if not created:
        return
    
    # Criar cliente no Asaas
    customer = AsaasCustomer.objects.create(...)
    
    # Criar cobrança no Asaas
    payment = AsaasPayment.objects.create(...)
    
    # Criar assinatura local
    assinatura = LojaAssinatura.objects.create(...)
```

---

### 2️⃣ RECEBIMENTO DO WEBHOOK

**Arquivo**: `backend/asaas_integration/views.py`

```python
class AsaasWebhookView(APIView):
    def post(self, request):
        # 1. Receber dados do webhook
        payment_data = request.data.get('payment', {})
        
        # 2. Processar webhook
        sync_service = AsaasSyncService()
        result = sync_service.process_webhook_payment(payment_data)
        
        # 3. Retornar 200 (sempre)
        return Response({'status': 'ok'}, status=200)
```

---

### 3️⃣ PROCESSAMENTO DO WEBHOOK

**Arquivo**: `backend/superadmin/sync_service.py`

```python
def process_webhook_payment(self, payment_data):
    # 1. Buscar pagamento
    payment_id = payment_data.get('id')
    pagamento = AsaasPayment.objects.get(asaas_id=payment_id)
    
    # 2. Atualizar status
    new_status = payment_data.get('status')
    pagamento.status = new_status
    
    # 3. Se foi pago, atualizar financeiro
    if new_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
        pagamento.payment_date = timezone.now()
        pagamento.save()
        
        # 🎯 ATUALIZAR FINANCEIRO DA LOJA
        self._update_loja_financeiro_from_payment(pagamento)
        
        # 🎯 EMITIR NOTA FISCAL
        emitir_nf_para_pagamento(pagamento)
    
    return {'success': True}
```

---

### 4️⃣ ATUALIZAÇÃO DO FINANCEIRO

**Arquivo**: `backend/superadmin/sync_service.py`

```python
def _update_loja_financeiro_from_payment(self, pagamento):
    # 1. Buscar loja
    loja = self._get_loja_from_payment(pagamento)
    
    # 2. Atualizar financeiro
    financeiro = loja.financeiro
    financeiro.status_pagamento = 'ativo'
    financeiro.ultimo_pagamento = timezone.now()
    financeiro.save()
    
    # 3. Desbloquear loja
    if loja.is_blocked:
        loja.is_blocked = False
        loja.blocked_at = None
        loja.blocked_reason = ''
        loja.days_overdue = 0
        loja.save()
        
        logger.info(f"Loja {loja.nome} desbloqueada automaticamente")
    
    return True
```

---

## 📊 COMPARAÇÃO: ANTES vs DEPOIS

### ANTES (v428) ❌

```
Criar Loja
    ↓
Signal cria cobrança (1)
    ↓
Serializer cria cobrança (2)  ← ❌ DUPLICADO
    ↓
RESULTADO: 2 cobranças no Asaas ❌
```

### DEPOIS (v429) ✅

```
Criar Loja
    ↓
Signal cria cobrança (1)
    ↓
Serializer NÃO cria cobrança  ← ✅ REMOVIDO
    ↓
RESULTADO: 1 cobrança no Asaas ✅
```

---

## 🎯 PONTOS-CHAVE

### ✅ Criação de Cobrança
- **Única fonte**: Signal `create_asaas_subscription_on_loja_creation`
- **Quando**: Ao criar loja (`post_save`)
- **O que cria**: AsaasCustomer + AsaasPayment + LojaAssinatura

### ✅ Webhook
- **URL**: `/api/asaas/webhook/`
- **Método**: POST
- **Retorno**: Sempre 200 (evita reenvio)

### ✅ Atualização Financeiro
- **Quando**: Pagamento confirmado (RECEIVED, CONFIRMED)
- **O que atualiza**: FinanceiroLoja + Loja + AsaasPayment
- **Automático**: Sim, via webhook

### ✅ Nota Fiscal
- **Quando**: Pagamento confirmado
- **O que faz**: Emite NF no Asaas + Envia email
- **Automático**: Sim, via webhook

---

## 🧪 LOGS ESPERADOS

### Criar Loja
```
✅ Loja criada: salao-teste-123
✅ Schema 'salao_teste_123' criado no PostgreSQL
✅ Assinatura Asaas criada com sucesso
   Payment ID: pay_xxx
   Valor: R$ 99.90
   Vencimento: 2026-02-10
✅ Email enviado para admin@teste.com
```

### Webhook Pagamento
```
🔔 Webhook Asaas recebido
   Event: PAYMENT_RECEIVED
   Payment ID: pay_xxx
✅ Processando webhook para pagamento pay_xxx
✅ Pagamento atualizado via webhook: PENDING -> RECEIVED
✅ Financeiro da loja atualizado automaticamente
✅ Loja salao-teste-123 desbloqueada automaticamente
✅ NF emitida para pagamento pay_xxx, e-mail enviado: True
```

---

## 📞 SUPORTE

### Ver Logs em Tempo Real
```bash
heroku logs --tail --app lwksistemas
```

### Filtrar Logs do Webhook
```bash
heroku logs --tail --app lwksistemas | grep "webhook"
```

### Filtrar Logs do Asaas
```bash
heroku logs --tail --app lwksistemas | grep "Asaas"
```

---

**Data**: 7 de janeiro de 2026  
**Versão**: v429  
**Status**: ✅ DOCUMENTADO
