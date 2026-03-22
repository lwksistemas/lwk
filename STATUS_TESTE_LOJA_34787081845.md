# Status do Teste - Loja 34787081845

## 📊 Informações da Loja de Teste

- **Slug da Loja**: `34787081845`
- **URL de Login**: https://lwksistemas.com.br/loja/34787081845/login
- **Status Atual**: Aguardando compensação do pagamento
- **Data/Hora do Pagamento**: 22/03/2026 às 15:56 (horário de Brasília)

---

## ⏳ Tempo de Compensação Esperado

### Boleto Bancário
- **Compensação normal**: 1 a 3 dias úteis
- **Compensação expressa**: Algumas horas (depende do banco)

### PIX
- **Compensação**: Instantânea (segundos a minutos)
- **Webhook Asaas**: 1 a 5 minutos após confirmação

---

## 🔍 Como Acompanhar o Processo

### 1. Monitorar Logs do Heroku (Recomendado)

Abra um terminal e execute:
```bash
heroku logs --tail --app lwksistemas | grep -E "webhook|34787081845|Pagamento confirmado|senha"
```

**O que você verá quando o pagamento for confirmado:**
```
Webhook Asaas recebido: {'event': 'PAYMENT_RECEIVED', ...}
Processando webhook para pagamento pay_xxxxx
Pagamento pay_xxxxx atualizado via webhook: PENDING -> RECEIVED
💰 Pagamento confirmado para loja [NOME]. Enviando senha provisória...
✅ Senha provisória enviada para [EMAIL]
✅ Novo boleto criado no Asaas: Vencimento [DATA]
```

---

### 2. Verificar no Painel Asaas

1. Acesse: https://www.asaas.com/
2. Login com suas credenciais de produção
3. Menu: **Cobranças** → **Todas as cobranças**
4. Procure pela cobrança da loja `34787081845`
5. Verifique o status:
   - ⏳ **Pendente**: Aguardando pagamento
   - ✅ **Pago/Recebido**: Pagamento confirmado

---

### 3. Verificar Email

Quando o pagamento for confirmado, você receberá um email com:
- ✉️ **Assunto**: "Senha Provisória - LWK Sistemas" (ou similar)
- 📝 **Conteúdo**: 
  - Senha provisória gerada automaticamente
  - Link de acesso ao sistema
  - Instruções de primeiro acesso

**Email esperado**: O email cadastrado no owner da loja

---

### 4. Verificar no Banco de Dados (Avançado)

Se quiser verificar manualmente o status no banco:

```bash
heroku run python manage.py shell --app lwksistemas
```

```python
from superadmin.models import Loja

# Buscar loja
loja = Loja.objects.get(slug='34787081845')

# Verificar status
print(f"Nome: {loja.nome}")
print(f"Owner Email: {loja.owner.email}")
print(f"Status Pagamento: {loja.financeiro.status_pagamento}")
print(f"Bloqueada: {loja.is_blocked}")
print(f"Senha Enviada: {loja.financeiro.senha_enviada}")
print(f"Data Envio Senha: {loja.financeiro.data_envio_senha}")

# Verificar pagamentos
from asaas_integration.models import AsaasPayment, LojaAssinatura
assinatura = LojaAssinatura.objects.get(loja_slug='34787081845')
pagamentos = AsaasPayment.objects.filter(customer=assinatura.asaas_customer).order_by('-created_at')

for p in pagamentos:
    print(f"\nPagamento: {p.asaas_id}")
    print(f"Status: {p.status}")
    print(f"Valor: R$ {p.value}")
    print(f"Vencimento: {p.due_date}")
```

---

## ✅ Checklist de Confirmação

Quando o pagamento for compensado, verifique:

- [ ] Webhook recebido nos logs do Heroku
- [ ] Status do pagamento atualizado para `RECEIVED` ou `CONFIRMED`
- [ ] Status da loja atualizado para `ativo`
- [ ] Loja desbloqueada (`is_blocked=False`)
- [ ] Próximo boleto criado automaticamente (vencimento: próximo mês)
- [ ] Email com senha provisória recebido
- [ ] Login funcionando com a senha provisória
- [ ] Sistema totalmente acessível

---

## 🎯 Próximos Passos Após Confirmação

### 1. Testar Login
```
URL: https://lwksistemas.com.br/loja/34787081845/login
Email: [email do owner]
Senha: [senha recebida por email]
```

### 2. Verificar Funcionalidades
- [ ] Dashboard carrega corretamente
- [ ] CRM de vendas acessível
- [ ] Configurações disponíveis
- [ ] Relatórios funcionando

### 3. Verificar Próximo Boleto
- [ ] Novo boleto criado no Asaas
- [ ] Vencimento: próximo mês (mesmo dia do primeiro boleto)
- [ ] Valor correto
- [ ] Status: Pendente

---

## 🚨 Se o Pagamento Não For Reconhecido

### Cenário 1: Pagamento confirmado no banco mas webhook não chegou

**Solução: Sincronização Manual**
```bash
heroku run python manage.py shell --app lwksistemas
```
```python
from superadmin.models import Loja
from superadmin.sync_service import AsaasSyncService

loja = Loja.objects.get(slug='34787081845')
service = AsaasSyncService()
result = service.sync_loja_payments(loja)
print(result)
```

---

### Cenário 2: Webhook chegou mas senha não foi enviada

**Solução: Enviar Senha Manualmente**
```bash
heroku run python manage.py shell --app lwksistemas
```
```python
from superadmin.models import Loja
from superadmin.email_service import EmailService

loja = Loja.objects.get(slug='34787081845')
service = EmailService()
success = service.enviar_senha_provisoria(loja, loja.owner)
print(f"Senha enviada: {success}")
```

---

### Cenário 3: Próximo boleto não foi criado

**Solução: Criar Boleto Manualmente**
```bash
heroku run python manage.py shell --app lwksistemas
```
```python
from superadmin.models import Loja
from asaas_integration.models import LojaAssinatura
from asaas_integration.client import AsaasPaymentService

loja = Loja.objects.get(slug='34787081845')
assinatura = LojaAssinatura.objects.get(loja_slug='34787081845')

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

# Data de vencimento
proxima_data = loja.financeiro.data_proxima_cobranca
due_date_str = proxima_data.strftime('%Y-%m-%d')

# Criar cobrança
service = AsaasPaymentService()
result = service.create_loja_subscription_payment(loja_data, plano_data, due_date=due_date_str)
print(result)
```

---

## 📞 Suporte

Se precisar de ajuda:

1. **Copie os logs**: `heroku logs -n 500 --app lwksistemas > logs.txt`
2. **Verifique o painel Asaas**: Status da cobrança e histórico de webhooks
3. **Verifique o banco de dados**: Use os comandos acima
4. **Reporte o problema**: Com logs, screenshots e descrição detalhada

---

## 📊 Timeline Esperada

```
Agora (15:56)
    │
    │ Pagamento realizado
    │
    ▼
+1 a 3 dias úteis (boleto) ou minutos (PIX)
    │
    │ Banco confirma pagamento
    │
    ▼
+1 a 5 minutos
    │
    │ Asaas detecta pagamento
    │
    ▼
Imediato
    │
    │ Asaas envia webhook
    │
    ▼
Imediato (segundos)
    │
    │ Sistema processa webhook
    │ - Atualiza pagamento
    │ - Atualiza financeiro
    │ - Cria próximo boleto
    │ - Envia senha por email
    │
    ▼
✅ CONCLUÍDO
    │
    │ Administrador pode fazer login
    │
```

---

**Última atualização**: 22/03/2026 às 15:56
**Status**: ⏳ Aguardando compensação do pagamento
**Próxima verificação**: Verificar logs em 5 minutos
