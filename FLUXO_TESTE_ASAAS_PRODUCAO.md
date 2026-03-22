# Fluxo de Teste - Assinatura Asaas em Produção

## ✅ Configuração Atual

- **URL do Webhook**: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
- **Eventos Recomendados**: 
  - PAYMENT_CREATED
  - PAYMENT_UPDATED
  - PAYMENT_CONFIRMED
  - PAYMENT_RECEIVED
  - PAYMENT_OVERDUE
  - PAYMENT_DELETED
  - PAYMENT_RESTORED

## 📋 Fluxo Esperado (3 Etapas)

### 1️⃣ Cadastro da Loja
**O que acontece:**
- Usuário preenche formulário de cadastro em: `https://lwksistemas.com.br/cadastro`
- Sistema cria:
  - Loja no banco de dados
  - Owner (administrador) da loja
  - Cliente no Asaas (AsaasCustomer)
  - Assinatura (LojaAssinatura)
  - Primeira cobrança (AsaasPayment) com vencimento configurado

**O que verificar:**
- ✅ Loja criada com sucesso
- ✅ Email de boas-vindas recebido (se configurado)
- ✅ Status da loja: `is_blocked=False` (desbloqueada inicialmente)

---

### 2️⃣ Recebimento do Boleto por Email
**O que acontece:**
- Sistema envia email com:
  - Link do boleto
  - Código de barras
  - QR Code PIX (se disponível)
  - Instruções de pagamento

**Arquivo responsável:**
- `backend/asaas_integration/signals.py` (signal `on_loja_created`)
- `backend/superadmin/email_service.py` (método `enviar_senha_provisoria`)

**O que verificar:**
- ✅ Email recebido no endereço do administrador
- ✅ Link do boleto funcionando
- ✅ Dados corretos (valor, vencimento, nome da loja)

**⚠️ IMPORTANTE:** 
- O boleto é enviado IMEDIATAMENTE após o cadastro
- A senha provisória NÃO é enviada neste momento
- A senha só será enviada APÓS confirmação do pagamento

---

### 3️⃣ Confirmação de Pagamento e Envio de Senha
**O que acontece:**

#### A) Webhook recebe notificação do Asaas
- Asaas detecta pagamento (boleto ou PIX)
- Asaas envia webhook para: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
- Sistema processa webhook em: `backend/asaas_integration/views.py` (função `asaas_webhook`)

#### B) Sistema atualiza pagamento
- `AsaasSyncService.process_webhook_payment()` é chamado
- Status do pagamento atualizado: `PENDING` → `RECEIVED/CONFIRMED`
- `AsaasPayment.status` atualizado no banco

#### C) Sistema atualiza financeiro da loja
- `_update_loja_financeiro_from_payment()` é chamado
- `FinanceiroLoja.status_pagamento` → `'ativo'`
- `FinanceiroLoja.ultimo_pagamento` → data/hora atual
- `FinanceiroLoja.data_proxima_cobranca` → próximo mês (baseado no dia de vencimento)
- Loja desbloqueada: `is_blocked=False`

#### D) Próximo boleto é criado automaticamente
- Sistema cria nova cobrança no Asaas para o próximo mês
- Novo `AsaasPayment` criado com vencimento no próximo mês
- `FinanceiroLoja` atualizado com dados do novo boleto

#### E) Signal dispara envio de senha
- Signal `on_payment_confirmed` detecta mudança de status
- Verifica: `status_pagamento == 'ativo'` E `senha_enviada == False`
- `EmailService.enviar_senha_provisoria()` é chamado
- Email enviado para o administrador com:
  - Senha provisória gerada automaticamente
  - Link de acesso ao sistema
  - Instruções de primeiro acesso

#### F) Financeiro marcado como "senha enviada"
- `FinanceiroLoja.senha_enviada` → `True`
- `FinanceiroLoja.data_envio_senha` → data/hora atual

**O que verificar:**
- ✅ Webhook recebido pelo sistema (verificar logs)
- ✅ Status do pagamento atualizado no banco
- ✅ Status da loja: `ativo`
- ✅ Próxima cobrança calculada corretamente (próximo mês)
- ✅ Novo boleto criado automaticamente
- ✅ Email com senha provisória recebido
- ✅ Senha funciona no login
- ✅ Administrador consegue acessar o sistema

---

## 🔍 Como Monitorar o Teste

### 1. Logs do Heroku (Tempo Real)
```bash
heroku logs --tail --app lwksistemas
```

**O que procurar nos logs:**
```
💰 Pagamento confirmado para loja [NOME_LOJA]. Enviando senha provisória...
✅ Senha provisória enviada para [EMAIL] (loja [SLUG])
✅ Financeiro da loja [NOME] atualizado: status=ativo, próxima_cobrança=[DATA]
✅ Novo boleto criado no Asaas para [NOME_LOJA]: Vencimento [DATA]
```

### 2. Verificar no Banco de Dados
```bash
heroku run python manage.py shell --app lwksistemas
```

```python
from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.models import AsaasPayment

# Buscar loja de teste
loja = Loja.objects.get(slug='[SLUG_DA_LOJA_TESTE]')

# Verificar financeiro
fin = loja.financeiro
print(f"Status: {fin.status_pagamento}")
print(f"Último Pagamento: {fin.ultimo_pagamento}")
print(f"Próxima Cobrança: {fin.data_proxima_cobranca}")
print(f"Senha Enviada: {fin.senha_enviada}")
print(f"Data Envio Senha: {fin.data_envio_senha}")

# Verificar pagamentos
pagamentos = AsaasPayment.objects.filter(
    customer__loja_slug=loja.slug
).order_by('-created_at')

for p in pagamentos:
    print(f"\nPagamento ID: {p.asaas_id}")
    print(f"Status: {p.status}")
    print(f"Valor: R$ {p.value}")
    print(f"Vencimento: {p.due_date}")
    print(f"Criado em: {p.created_at}")
```

### 3. Verificar no Painel Asaas
- Acessar: https://www.asaas.com/
- Login com suas credenciais de produção
- Menu: Cobranças → Todas as cobranças
- Verificar:
  - ✅ Cobrança criada
  - ✅ Status: Pago
  - ✅ Webhook enviado (aba "Histórico")

---

## 🚨 Possíveis Problemas e Soluções

### Problema 1: Boleto não chegou no email
**Causa:** Email não configurado ou erro no envio
**Solução:**
1. Verificar logs: `heroku logs --tail --app lwksistemas | grep -i email`
2. Verificar configuração SMTP no Heroku
3. Reenviar boleto manualmente via painel Asaas

### Problema 2: Webhook não foi recebido
**Causa:** URL do webhook incorreta ou Asaas não conseguiu enviar
**Solução:**
1. Verificar URL configurada no Asaas: `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/`
2. Verificar logs do Asaas (painel → Webhooks → Histórico)
3. Testar webhook manualmente:
```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_RECEIVED",
    "payment": {
      "id": "[ID_DO_PAGAMENTO]",
      "status": "RECEIVED",
      "value": 100.00
    }
  }'
```

### Problema 3: Senha não foi enviada
**Causa:** Signal não disparou ou erro no envio de email
**Solução:**
1. Verificar se `FinanceiroLoja.status_pagamento` está como `'ativo'`
2. Verificar se `FinanceiroLoja.senha_enviada` está como `False`
3. Forçar envio manual:
```bash
heroku run python manage.py shell --app lwksistemas
```
```python
from superadmin.models import Loja
from superadmin.email_service import EmailService

loja = Loja.objects.get(slug='[SLUG_DA_LOJA_TESTE]')
service = EmailService()
success = service.enviar_senha_provisoria(loja, loja.owner)
print(f"Senha enviada: {success}")
```

### Problema 4: Próximo boleto não foi criado
**Causa:** Erro na criação automática do boleto
**Solução:**
1. Verificar logs: `heroku logs --tail --app lwksistemas | grep -i "próximo boleto"`
2. Criar manualmente via comando:
```bash
heroku run python manage.py shell --app lwksistemas
```
```python
from superadmin.models import Loja
from asaas_integration.models import LojaAssinatura
from asaas_integration.client import AsaasPaymentService

loja = Loja.objects.get(slug='[SLUG_DA_LOJA_TESTE]')
assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)

# Preparar dados
loja_data = {
    'nome': loja.nome,
    'slug': loja.slug,
    'email': loja.owner.email,
    'cpf_cnpj': loja.cpf_cnpj,
    'telefone': getattr(loja.owner, 'telefone', ''),
}

valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == 'anual' else loja.plano.preco_mensal
plano_data = {
    'nome': f"{loja.plano.nome} ({loja.get_tipo_assinatura_display()})",
    'preco': valor_plano
}

# Criar cobrança
from datetime import date
proxima_data = loja.financeiro.data_proxima_cobranca
due_date_str = proxima_data.strftime('%Y-%m-%d')

service = AsaasPaymentService()
result = service.create_loja_subscription_payment(loja_data, plano_data, due_date=due_date_str)
print(result)
```

---

## 📊 Checklist de Teste

### Antes do Teste
- [ ] API Asaas de produção configurada
- [ ] Webhook configurado no painel Asaas
- [ ] Eventos do webhook configurados corretamente
- [ ] SMTP configurado no Heroku para envio de emails

### Durante o Teste
- [ ] Cadastro da loja realizado com sucesso
- [ ] Boleto recebido no email
- [ ] Pagamento realizado (boleto ou PIX)
- [ ] Logs do Heroku monitorados em tempo real

### Após o Pagamento
- [ ] Webhook recebido pelo sistema
- [ ] Status do pagamento atualizado
- [ ] Status da loja: `ativo`
- [ ] Próxima cobrança calculada
- [ ] Novo boleto criado automaticamente
- [ ] Email com senha provisória recebido
- [ ] Login funcionando com a senha provisória
- [ ] Administrador consegue acessar todas as funcionalidades

---

## 📞 Suporte

Se encontrar algum problema durante o teste:

1. **Verificar logs primeiro**: `heroku logs --tail --app lwksistemas`
2. **Verificar banco de dados**: Usar comandos Django shell acima
3. **Verificar painel Asaas**: Histórico de webhooks e cobranças
4. **Reportar problema**: Informar exatamente em qual etapa o fluxo parou

---

## 🎯 Resultado Esperado

Ao final do teste bem-sucedido:

✅ Loja cadastrada e ativa
✅ Boleto recebido e pago
✅ Sistema reconheceu o pagamento automaticamente
✅ Próximo boleto criado para o próximo mês
✅ Senha provisória enviada por email
✅ Administrador consegue fazer login
✅ Sistema totalmente funcional para a nova loja

---

**Última atualização:** 22/03/2026
**Versão do sistema:** Heroku v1251, Vercel (frontend)
