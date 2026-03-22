# Diagrama do Fluxo de Assinatura Asaas

## 🔄 Fluxo Completo Visualizado

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         1️⃣ CADASTRO DA LOJA                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Usuário preenche formulário  │
                    │  https://lwksistemas.com.br   │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Sistema cria no banco:      │
                    │   • Loja                      │
                    │   • Owner (admin)             │
                    │   • FinanceiroLoja            │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Signal: on_loja_created     │
                    │   (asaas_integration/signals) │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Asaas API:                  │
                    │   • Criar cliente             │
                    │   • Criar assinatura          │
                    │   • Criar primeira cobrança   │
                    └───────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    2️⃣ ENVIO DO BOLETO POR EMAIL                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Email enviado com:          │
                    │   • Link do boleto            │
                    │   • Código de barras          │
                    │   • QR Code PIX               │
                    │   • Instruções                │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Status da Loja:             │
                    │   • is_blocked = False        │
                    │   • status = 'pendente'       │
                    │   • senha_enviada = False     │
                    └───────────────────────────────┘
                                    │
                                    │
                        ⏳ AGUARDANDO PAGAMENTO ⏳
                                    │
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│              3️⃣ CONFIRMAÇÃO DE PAGAMENTO E ENVIO DE SENHA               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Cliente paga boleto/PIX     │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Asaas detecta pagamento     │
                    │   Status: RECEIVED/CONFIRMED  │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Asaas envia WEBHOOK         │
                    │   POST /api/asaas/webhook/    │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   asaas_webhook()             │
                    │   (asaas_integration/views)   │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   AsaasSyncService            │
                    │   .process_webhook_payment()  │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Atualiza AsaasPayment:      │
                    │   • status = 'RECEIVED'       │
                    │   • payment_date = now()      │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   _update_loja_financeiro     │
                    │   _from_payment()             │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Atualiza FinanceiroLoja:    │
                    │   • status = 'ativo'          │
                    │   • ultimo_pagamento = now()  │
                    │   • proxima_cobranca = +1mês  │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Cria próximo boleto:        │
                    │   • Vencimento: próximo mês   │
                    │   • Novo AsaasPayment         │
                    │   • Status: PENDING           │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Desbloqueia Loja:           │
                    │   • is_blocked = False        │
                    │   • blocked_reason = ''       │
                    │   • days_overdue = 0          │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Signal: on_payment_confirmed│
                    │   (superadmin/signals.py)     │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Verifica condições:         │
                    │   ✓ status = 'ativo'          │
                    │   ✓ senha_enviada = False     │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   EmailService                │
                    │   .enviar_senha_provisoria()  │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Gera senha aleatória        │
                    │   Salva hash no banco         │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Envia email com:            │
                    │   • Senha provisória          │
                    │   • Link de acesso            │
                    │   • Instruções de uso         │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Atualiza FinanceiroLoja:    │
                    │   • senha_enviada = True      │
                    │   • data_envio_senha = now()  │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   ✅ FLUXO COMPLETO!          │
                    │   Admin pode fazer login      │
                    └───────────────────────────────┘
```

---

## 🔑 Pontos Críticos do Fluxo

### 1. Webhook é ESSENCIAL
- Sem webhook, o sistema NÃO detecta o pagamento automaticamente
- URL deve estar correta no painel Asaas
- Eventos devem estar configurados (PAYMENT_RECEIVED, PAYMENT_CONFIRMED)

### 2. Signal on_payment_confirmed
- Dispara AUTOMATICAMENTE quando `status_pagamento` muda para `'ativo'`
- Verifica se senha já foi enviada (`senha_enviada == False`)
- Envia email com senha provisória

### 3. Próximo Boleto Automático
- Criado IMEDIATAMENTE após confirmação do pagamento
- Vencimento: próximo mês (baseado no dia de vencimento configurado)
- Evita que a loja fique sem cobrança ativa

### 4. Desbloqueio Automático
- Loja é desbloqueada automaticamente após pagamento
- `is_blocked = False`
- `days_overdue = 0`

---

## 📊 Estados da Loja

```
┌─────────────────┐
│  CADASTRADA     │  ← Loja criada, aguardando pagamento
│  (pendente)     │    • is_blocked = False
└────────┬────────┘    • senha_enviada = False
         │
         │ Pagamento confirmado
         ▼
┌─────────────────┐
│  ATIVA          │  ← Pagamento confirmado, senha enviada
│  (ativo)        │    • is_blocked = False
└────────┬────────┘    • senha_enviada = True
         │
         │ Vencimento passou (5+ dias)
         ▼
┌─────────────────┐
│  BLOQUEADA      │  ← Inadimplência detectada
│  (suspenso)     │    • is_blocked = True
└────────┬────────┘    • days_overdue > 5
         │
         │ Pagamento confirmado
         ▼
┌─────────────────┐
│  ATIVA          │  ← Desbloqueada automaticamente
│  (ativo)        │    • is_blocked = False
└─────────────────┘    • days_overdue = 0
```

---

## 🎯 Logs Importantes

### Sucesso no Webhook
```
Webhook Asaas recebido: {...}
Pagamento encontrado no AsaasPayment: pay_xxxxx
Processando webhook para pagamento pay_xxxxx, evento: PAYMENT_RECEIVED
Pagamento pay_xxxxx atualizado via webhook: PENDING -> RECEIVED
🔍 Buscando LojaAssinatura para slug: 41449198000172
✅ LojaAssinatura encontrada
📝 Atualizando data_vencimento: 2026-03-10 → 2026-04-10
✅ LojaAssinatura.data_vencimento atualizada para 2026-04-10
🔍 Verificando cobranças existentes para 2026-04-10...
✅ Nenhuma cobrança existente, criando novo boleto...
💰 Dados da cobrança:
   - Loja: FELIX REPRESENTACOES E COMERCIO LTDA
   - Plano: Plano Básico (Mensal)
   - Valor: R$ 100.00
   - Vencimento: 2026-04-10
🚀 Chamando Asaas API para criar cobrança...
✅ Cobrança criada no Asaas com sucesso!
✅ Pagamento criado no banco local (ID: 123)
✅ FinanceiroLoja atualizado com dados do novo boleto
✅ Loja FELIX REPRESENTACOES E COMERCIO LTDA desbloqueada automaticamente após pagamento
💰 Pagamento confirmado para loja FELIX REPRESENTACOES E COMERCIO LTDA. Enviando senha provisória...
✅ Senha provisória enviada para consultorluizfelix@hotmail.com (loja 41449198000172)
```

### Erro no Webhook
```
❌ Erro ao processar webhook: [mensagem de erro]
```

### Erro no Envio de Senha
```
⚠️ Falha ao enviar senha para consultorluizfelix@hotmail.com (loja 41449198000172). Email registrado para retry automático.
```

---

## 🛠️ Comandos Úteis para Debug

### Ver logs em tempo real
```bash
heroku logs --tail --app lwksistemas
```

### Filtrar logs de webhook
```bash
heroku logs --tail --app lwksistemas | grep -i webhook
```

### Filtrar logs de email
```bash
heroku logs --tail --app lwksistemas | grep -i "senha provisória"
```

### Verificar status da loja
```bash
heroku run python manage.py shell --app lwksistemas
```
```python
from superadmin.models import Loja
loja = Loja.objects.get(slug='41449198000172')
print(f"Status: {loja.financeiro.status_pagamento}")
print(f"Bloqueada: {loja.is_blocked}")
print(f"Senha Enviada: {loja.financeiro.senha_enviada}")
```

---

**Última atualização:** 22/03/2026
