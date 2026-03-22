# Comandos de Monitoramento - Teste Asaas Produção

## 🔍 Monitoramento em Tempo Real

### 1. Logs Gerais do Heroku
```bash
heroku logs --tail --app lwksistemas
```
**O que mostra:** Todos os logs do sistema em tempo real

**Quando usar:** Durante todo o teste para ver tudo que está acontecendo

---

### 2. Logs de Webhook
```bash
heroku logs --tail --app lwksistemas | grep -i webhook
```
**O que mostra:** Apenas logs relacionados a webhooks

**Quando usar:** Para verificar se o webhook foi recebido após o pagamento

**Exemplo de saída esperada:**
```
2026-03-22T17:30:15.123456+00:00 app[web.1]: Webhook Asaas recebido: {'event': 'PAYMENT_RECEIVED', ...}
2026-03-22T17:30:15.234567+00:00 app[web.1]: Processando webhook para pagamento pay_xxxxx, evento: PAYMENT_RECEIVED
2026-03-22T17:30:15.345678+00:00 app[web.1]: Pagamento pay_xxxxx atualizado via webhook: PENDING -> RECEIVED
```

---

### 3. Logs de Email/Senha
```bash
heroku logs --tail --app lwksistemas | grep -i "senha provisória"
```
**O que mostra:** Logs relacionados ao envio de senha provisória

**Quando usar:** Para verificar se a senha foi enviada após confirmação do pagamento

**Exemplo de saída esperada:**
```
2026-03-22T17:30:16.123456+00:00 app[web.1]: 💰 Pagamento confirmado para loja FELIX REPRESENTACOES. Enviando senha provisória...
2026-03-22T17:30:17.234567+00:00 app[web.1]: ✅ Senha provisória enviada para consultorluizfelix@hotmail.com (loja 41449198000172)
```

---

### 4. Logs de Erro
```bash
heroku logs --tail --app lwksistemas | grep -i error
```
**O que mostra:** Apenas logs de erro

**Quando usar:** Se algo não estiver funcionando como esperado

---

### 5. Logs de Criação de Boleto
```bash
heroku logs --tail --app lwksistemas | grep -i "próximo boleto\|novo boleto"
```
**O que mostra:** Logs relacionados à criação automática do próximo boleto

**Quando usar:** Para verificar se o próximo boleto foi criado após o pagamento

**Exemplo de saída esperada:**
```
2026-03-22T17:30:16.456789+00:00 app[web.1]: 🔍 Verificando cobranças existentes para 2026-04-10...
2026-03-22T17:30:16.567890+00:00 app[web.1]: ✅ Nenhuma cobrança existente, criando novo boleto...
2026-03-22T17:30:17.678901+00:00 app[web.1]: ✅ Cobrança criada no Asaas com sucesso!
2026-03-22T17:30:17.789012+00:00 app[web.1]: ✅ Novo boleto criado no Asaas para FELIX REPRESENTACOES: Vencimento 2026-04-10
```

---

## 🗄️ Consultas no Banco de Dados

### Acessar Shell Django
```bash
heroku run python manage.py shell --app lwksistemas
```

### 1. Verificar Status da Loja
```python
from superadmin.models import Loja

# Buscar loja pelo slug
loja = Loja.objects.get(slug='41449198000172')

# Informações básicas
print(f"Nome: {loja.nome}")
print(f"Owner: {loja.owner.email}")
print(f"Bloqueada: {loja.is_blocked}")
print(f"Dias de atraso: {loja.days_overdue}")

# Informações financeiras
fin = loja.financeiro
print(f"\nStatus Pagamento: {fin.status_pagamento}")
print(f"Último Pagamento: {fin.ultimo_pagamento}")
print(f"Próxima Cobrança: {fin.data_proxima_cobranca}")
print(f"Senha Enviada: {fin.senha_enviada}")
print(f"Data Envio Senha: {fin.data_envio_senha}")
```

---

### 2. Verificar Pagamentos da Loja
```python
from asaas_integration.models import AsaasPayment, LojaAssinatura

# Buscar assinatura
assinatura = LojaAssinatura.objects.get(loja_slug='41449198000172')

# Listar todos os pagamentos
pagamentos = AsaasPayment.objects.filter(
    customer=assinatura.asaas_customer
).order_by('-created_at')

print(f"Total de pagamentos: {pagamentos.count()}\n")

for p in pagamentos:
    print(f"ID: {p.asaas_id}")
    print(f"Status: {p.status}")
    print(f"Valor: R$ {p.value}")
    print(f"Vencimento: {p.due_date}")
    print(f"Criado em: {p.created_at}")
    print(f"Pago em: {p.payment_date}")
    print("-" * 50)
```

---

### 3. Verificar Último Pagamento
```python
from asaas_integration.models import AsaasPayment, LojaAssinatura

assinatura = LojaAssinatura.objects.get(loja_slug='41449198000172')
ultimo = AsaasPayment.objects.filter(
    customer=assinatura.asaas_customer
).order_by('-created_at').first()

if ultimo:
    print(f"Último Pagamento:")
    print(f"  ID: {ultimo.asaas_id}")
    print(f"  Status: {ultimo.status}")
    print(f"  Valor: R$ {ultimo.value}")
    print(f"  Vencimento: {ultimo.due_date}")
    print(f"  Criado: {ultimo.created_at}")
    print(f"  Pago: {ultimo.payment_date or 'Não pago'}")
else:
    print("Nenhum pagamento encontrado")
```

---

### 4. Verificar Histórico de Emails
```python
from superadmin.models import EmailRetry

# Buscar tentativas de email para uma loja
emails = EmailRetry.objects.filter(
    loja_slug='41449198000172'
).order_by('-created_at')

print(f"Total de emails: {emails.count()}\n")

for email in emails[:5]:  # Últimos 5
    print(f"Tipo: {email.email_type}")
    print(f"Para: {email.recipient_email}")
    print(f"Status: {email.status}")
    print(f"Tentativas: {email.retry_count}")
    print(f"Criado: {email.created_at}")
    print(f"Enviado: {email.sent_at or 'Não enviado'}")
    if email.error_message:
        print(f"Erro: {email.error_message}")
    print("-" * 50)
```

---

### 5. Forçar Envio de Senha (Se Necessário)
```python
from superadmin.models import Loja
from superadmin.email_service import EmailService

# Buscar loja
loja = Loja.objects.get(slug='41449198000172')

# Enviar senha
service = EmailService()
success = service.enviar_senha_provisoria(loja, loja.owner)

if success:
    print("✅ Senha enviada com sucesso!")
else:
    print("❌ Erro ao enviar senha. Verifique logs.")
```

---

### 6. Verificar Configuração Asaas
```python
from asaas_integration.models import AsaasConfig

config = AsaasConfig.get_config()

print(f"API Key: {config.api_key_masked}")
print(f"Sandbox: {config.sandbox}")
print(f"Enabled: {config.enabled}")
print(f"Environment: {config.environment_name}")
print(f"Last Sync: {config.last_sync}")
```

---

### 7. Criar Próximo Boleto Manualmente (Se Necessário)
```python
from superadmin.models import Loja
from asaas_integration.models import LojaAssinatura
from asaas_integration.client import AsaasPaymentService
from datetime import date

# Buscar loja
loja = Loja.objects.get(slug='41449198000172')
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

# Data de vencimento
proxima_data = loja.financeiro.data_proxima_cobranca
due_date_str = proxima_data.strftime('%Y-%m-%d')

print(f"Criando boleto para {loja.nome}")
print(f"Vencimento: {due_date_str}")
print(f"Valor: R$ {plano_data['preco']}")

# Criar cobrança
service = AsaasPaymentService()
result = service.create_loja_subscription_payment(loja_data, plano_data, due_date=due_date_str)

if result['success']:
    print(f"\n✅ Boleto criado com sucesso!")
    print(f"Payment ID: {result['payment_id']}")
    print(f"Boleto URL: {result['boleto_url']}")
else:
    print(f"\n❌ Erro ao criar boleto: {result.get('error')}")
```

---

## 📊 Comandos de Diagnóstico

### 1. Verificar Status do App
```bash
heroku ps --app lwksistemas
```
**O que mostra:** Status dos dynos (web, worker, etc.)

---

### 2. Verificar Variáveis de Ambiente
```bash
heroku config --app lwksistemas
```
**O que mostra:** Todas as variáveis de ambiente configuradas

---

### 3. Verificar Banco de Dados
```bash
heroku pg:info --app lwksistemas
```
**O que mostra:** Informações sobre o banco de dados PostgreSQL

---

### 4. Executar Comando Django
```bash
heroku run python manage.py [comando] --app lwksistemas
```

**Exemplos:**
```bash
# Verificar migrações
heroku run python manage.py showmigrations --app lwksistemas

# Criar superuser
heroku run python manage.py createsuperuser --app lwksistemas

# Coletar arquivos estáticos
heroku run python manage.py collectstatic --noinput --app lwksistemas
```

---

## 🔄 Sincronização Manual

### Sincronizar Todos os Pagamentos
```bash
heroku run python manage.py shell --app lwksistemas
```
```python
from superadmin.sync_service import AsaasSyncService

service = AsaasSyncService()
result = service.sync_all_payments()

print(f"Total de lojas: {result['total_lojas']}")
print(f"Sucessos: {result['sucessos']}")
print(f"Erros: {result['erros']}")
print(f"Bloqueadas: {result['bloqueadas']}")
print(f"Desbloqueadas: {result['desbloqueadas']}")
```

---

### Sincronizar Loja Específica
```python
from superadmin.models import Loja
from superadmin.sync_service import AsaasSyncService

loja = Loja.objects.get(slug='41449198000172')
service = AsaasSyncService()
result = service.sync_loja_payments(loja)

print(f"Loja: {result['loja']}")
print(f"Pagamentos atualizados: {result['pagamentos_atualizados']}")
print(f"Status: {result['status']}")
print(f"Bloqueada: {result.get('blocked', False)}")
print(f"Desbloqueada: {result.get('unblocked', False)}")
```

---

## 📝 Checklist de Monitoramento Durante o Teste

### Antes do Pagamento
- [ ] Logs do Heroku abertos: `heroku logs --tail --app lwksistemas`
- [ ] Loja cadastrada com sucesso
- [ ] Boleto recebido no email
- [ ] Status da loja: `pendente`

### Durante o Pagamento
- [ ] Pagamento realizado (boleto ou PIX)
- [ ] Aguardar 2-5 minutos para processamento

### Após o Pagamento
- [ ] Verificar logs: webhook recebido
- [ ] Verificar logs: pagamento atualizado
- [ ] Verificar logs: próximo boleto criado
- [ ] Verificar logs: senha enviada
- [ ] Verificar email: senha provisória recebida
- [ ] Testar login com a senha

### Verificação Final
- [ ] Status da loja: `ativo`
- [ ] Loja desbloqueada: `is_blocked=False`
- [ ] Próxima cobrança: próximo mês
- [ ] Senha enviada: `senha_enviada=True`
- [ ] Login funcionando
- [ ] Sistema totalmente funcional

---

## 🚨 Comandos de Emergência

### Reiniciar App (Se Necessário)
```bash
heroku restart --app lwksistemas
```

### Ver Últimos 1000 Logs
```bash
heroku logs -n 1000 --app lwksistemas
```

### Abrir Console do Heroku
```bash
heroku run bash --app lwksistemas
```

### Verificar Processos em Execução
```bash
heroku ps --app lwksistemas
```

---

## 📞 Suporte

Se encontrar problemas:

1. **Copiar logs relevantes**: Use os comandos acima para capturar logs
2. **Verificar banco de dados**: Use as consultas SQL acima
3. **Verificar painel Asaas**: Histórico de webhooks
4. **Reportar problema**: Com logs, screenshots e descrição detalhada

---

**Última atualização:** 22/03/2026
**App Heroku:** lwksistemas
**Ambiente:** Produção
