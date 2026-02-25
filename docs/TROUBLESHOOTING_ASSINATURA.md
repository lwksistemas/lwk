# Troubleshooting - Assinatura e Pagamento

## Visão Geral

Este guia ajuda a diagnosticar e resolver problemas comuns relacionados ao fluxo de assinatura e pagamento de lojas.

---

## Problemas Comuns

### 1. Senha Provisória Não Foi Enviada

**Sintoma:** Loja foi criada, boleto foi gerado, mas o administrador não recebeu a senha provisória.

**Possíveis Causas:**

1. **Pagamento ainda não foi confirmado**
   - Verifique o status do pagamento no painel do provedor (Asaas ou Mercado Pago)
   - Verifique se o webhook foi recebido pelo sistema

2. **Email falhou no envio**
   - Verifique os logs do sistema para erros de SMTP
   - Consulte a tabela `EmailRetry` para ver tentativas falhadas

3. **Webhook não foi configurado**
   - Verifique se o webhook está configurado no painel do provedor
   - Teste o webhook manualmente

**Solução:**

```bash
# 1. Verificar status do pagamento
python manage.py shell
>>> from superadmin.models import FinanceiroLoja
>>> fin = FinanceiroLoja.objects.get(loja__slug='minha-loja')
>>> print(f"Status: {fin.status_pagamento}")
>>> print(f"Senha enviada: {fin.senha_enviada}")

# 2. Verificar emails falhados
>>> from superadmin.models import EmailRetry
>>> emails = EmailRetry.objects.filter(loja__slug='minha-loja', enviado=False)
>>> for email in emails:
...     print(f"Tentativas: {email.tentativas}/{email.max_tentativas}")
...     print(f"Erro: {email.erro}")

# 3. Reenviar senha manualmente (se pagamento confirmado)
>>> from superadmin.email_service import EmailService
>>> service = EmailService()
>>> loja = fin.loja
>>> success = service.enviar_senha_provisoria(loja, loja.owner)
>>> print(f"Enviado: {success}")
```

**Via API:**

```bash
curl -X POST https://seu-dominio.com/api/superadmin/financeiro/{id}/reenviar-senha/ \
  -H "Authorization: Bearer <token>"
```

---

### 2. Boleto Não Foi Gerado

**Sintoma:** Loja foi criada, mas não há boleto disponível.

**Possíveis Causas:**

1. **Erro na integração com o provedor**
   - Credenciais inválidas (Asaas ou Mercado Pago)
   - API do provedor fora do ar

2. **Dados da loja incompletos**
   - CPF/CNPJ inválido
   - Endereço incompleto (necessário para Mercado Pago)

3. **Signal não foi disparado**
   - Erro no código do signal
   - Signal desabilitado

**Solução:**

```bash
# 1. Verificar logs do sistema
tail -f logs/django.log | grep "Cobrança"

# 2. Verificar dados da loja
python manage.py shell
>>> from superadmin.models import Loja
>>> loja = Loja.objects.get(slug='minha-loja')
>>> print(f"CPF/CNPJ: {loja.cpf_cnpj}")
>>> print(f"Endereço: {loja.logradouro}, {loja.numero}, {loja.cidade}/{loja.uf}")
>>> print(f"Provedor: {loja.provedor_boleto_preferido}")

# 3. Gerar boleto manualmente
>>> from superadmin.cobranca_service import CobrancaService
>>> service = CobrancaService()
>>> result = service.criar_cobranca(loja, loja.financeiro)
>>> print(result)
```

---

### 3. Webhook Não Está Funcionando

**Sintoma:** Pagamento foi confirmado no provedor, mas status da loja não mudou para "ativo".

**Possíveis Causas:**

1. **Webhook não configurado no provedor**
2. **URL do webhook incorreta**
3. **Firewall bloqueando requisições do provedor**
4. **Erro no processamento do webhook**

**Solução:**

```bash
# 1. Verificar configuração do webhook
# Asaas: https://www.asaas.com/webhooks
# Mercado Pago: https://www.mercadopago.com.br/developers/panel/webhooks

# 2. Testar webhook manualmente
curl -X POST https://seu-dominio.com/asaas/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_CONFIRMED",
    "payment": {
      "id": "pay_123456",
      "status": "CONFIRMED"
    }
  }'

# 3. Verificar logs do webhook
tail -f logs/django.log | grep "Webhook"

# 4. Atualizar status manualmente
python manage.py shell
>>> from superadmin.models import FinanceiroLoja
>>> fin = FinanceiroLoja.objects.get(asaas_payment_id='pay_123456')
>>> fin.status_pagamento = 'ativo'
>>> fin.save()  # Isso dispara o signal de envio de senha
```

---

### 4. Email de Retry Não Está Funcionando

**Sintoma:** Emails falhados não estão sendo reenviados automaticamente.

**Possíveis Causas:**

1. **Django-Q não está rodando**
2. **Task não está agendada**
3. **Configuração de SMTP incorreta**

**Solução:**

```bash
# 1. Verificar se Django-Q está rodando
ps aux | grep qcluster

# Se não estiver rodando, iniciar:
python manage.py qcluster

# 2. Verificar tasks agendadas
python manage.py shell
>>> from django_q.models import Schedule
>>> schedules = Schedule.objects.all()
>>> for s in schedules:
...     print(f"{s.name}: {s.func} - {s.schedule_type}")

# 3. Executar comando manualmente
python manage.py reprocessar_emails_falhados

# 4. Verificar configuração de SMTP
>>> from django.conf import settings
>>> print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
>>> print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
>>> print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")

# 5. Testar envio de email
>>> from django.core.mail import send_mail
>>> send_mail(
...     'Teste',
...     'Mensagem de teste',
...     settings.DEFAULT_FROM_EMAIL,
...     ['seu-email@example.com'],
...     fail_silently=False
... )
```

---

### 5. Loja Bloqueada Indevidamente

**Sintoma:** Loja foi bloqueada mesmo com pagamento em dia.

**Possíveis Causas:**

1. **Task de verificação de status rodou antes do webhook**
2. **Data de próxima cobrança incorreta**
3. **Bug no código de verificação**

**Solução:**

```bash
# 1. Verificar status e datas
python manage.py shell
>>> from superadmin.models import FinanceiroLoja
>>> from django.utils import timezone
>>> fin = FinanceiroLoja.objects.get(loja__slug='minha-loja')
>>> print(f"Status: {fin.status_pagamento}")
>>> print(f"Próxima cobrança: {fin.data_proxima_cobranca}")
>>> print(f"Hoje: {timezone.now().date()}")

# 2. Corrigir status manualmente
>>> fin.status_pagamento = 'ativo'
>>> fin.save()

# 3. Atualizar data de próxima cobrança
>>> from datetime import timedelta
>>> fin.data_proxima_cobranca = timezone.now().date() + timedelta(days=30)
>>> fin.save()
```

---

### 6. Renovação de Assinatura Falha

**Sintoma:** Ao clicar em "Gerar Nova Cobrança", aparece erro.

**Possíveis Causas:**

1. **Dados da loja incompletos**
2. **Erro na API do provedor**
3. **Limite de cobranças atingido**

**Solução:**

```bash
# 1. Verificar dados da loja
python manage.py shell
>>> from superadmin.models import Loja
>>> loja = Loja.objects.get(slug='minha-loja')
>>> print(f"CPF/CNPJ: {loja.cpf_cnpj}")
>>> print(f"Email: {loja.owner.email}")
>>> print(f"Endereço completo: {loja.cep}, {loja.logradouro}, {loja.numero}, {loja.cidade}/{loja.uf}")

# 2. Testar criação de cobrança
>>> from superadmin.cobranca_service import CobrancaService
>>> service = CobrancaService()
>>> result = service.renovar_cobranca(loja, loja.financeiro)
>>> print(result)

# 3. Verificar logs do provedor
# Asaas: https://www.asaas.com/logs
# Mercado Pago: https://www.mercadopago.com.br/developers/panel/logs
```

---

### 7. PIX QR Code Não Aparece

**Sintoma:** Boleto aparece, mas QR Code PIX não é exibido.

**Possíveis Causas:**

1. **Provedor não retornou QR Code**
2. **QR Code não foi salvo no banco**
3. **Erro na renderização da imagem**

**Solução:**

```bash
# 1. Verificar se QR Code está no banco
python manage.py shell
>>> from superadmin.models import FinanceiroLoja
>>> fin = FinanceiroLoja.objects.get(loja__slug='minha-loja')
>>> print(f"PIX QR Code: {fin.pix_qr_code[:50]}...")  # Primeiros 50 caracteres
>>> print(f"PIX Copy/Paste: {fin.pix_copy_paste[:50]}...")

# 2. Se não houver, gerar novamente
>>> from superadmin.cobranca_service import CobrancaService
>>> service = CobrancaService()
>>> result = service.renovar_cobranca(fin.loja, fin)
>>> print(f"PIX QR Code: {result.get('pix_qr_code', 'N/A')[:50]}...")
```

---

## Comandos Úteis

### Verificar Status de Todas as Lojas

```bash
python manage.py shell
>>> from superadmin.models import FinanceiroLoja
>>> for fin in FinanceiroLoja.objects.all():
...     print(f"{fin.loja.slug}: {fin.status_pagamento} - Próxima: {fin.data_proxima_cobranca}")
```

### Forçar Envio de Senha para Loja Específica

```bash
python manage.py shell
>>> from superadmin.models import Loja
>>> from superadmin.email_service import EmailService
>>> loja = Loja.objects.get(slug='minha-loja')
>>> service = EmailService()
>>> service.enviar_senha_provisoria(loja, loja.owner)
```

### Limpar Emails Falhados Antigos

```bash
python manage.py shell
>>> from superadmin.models import EmailRetry
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> cutoff = timezone.now() - timedelta(days=30)
>>> EmailRetry.objects.filter(created_at__lt=cutoff, enviado=True).delete()
```

### Verificar Logs em Tempo Real

```bash
# Logs gerais
tail -f logs/django.log

# Filtrar por loja específica
tail -f logs/django.log | grep "minha-loja"

# Filtrar por tipo de evento
tail -f logs/django.log | grep "Cobrança"
tail -f logs/django.log | grep "Webhook"
tail -f logs/django.log | grep "Senha"
```

---

## Checklist de Diagnóstico

Ao investigar um problema, siga este checklist:

- [ ] Verificar logs do sistema
- [ ] Verificar status do pagamento no banco de dados
- [ ] Verificar status do pagamento no painel do provedor
- [ ] Verificar configuração do webhook
- [ ] Verificar dados da loja (CPF/CNPJ, endereço, email)
- [ ] Verificar se Django-Q está rodando
- [ ] Verificar configuração de SMTP
- [ ] Testar envio de email manualmente
- [ ] Verificar emails falhados na tabela EmailRetry
- [ ] Verificar se há erros no log do provedor

---

## Logs Importantes

### Criação de Loja

```
[INFO] Criando primeira cobrança para loja Minha Loja
[INFO] ✅ Cobrança criada para loja Minha Loja
[INFO]    Provedor: asaas
[INFO]    Payment ID: pay_123456
```

### Confirmação de Pagamento

```
[INFO] Webhook Asaas: event=PAYMENT_CONFIRMED, payment=pay_123456, status=CONFIRMED
[INFO] ✅ Pagamento confirmado para loja minha-loja
[INFO] Pagamento confirmado para loja Minha Loja. Enviando senha...
[INFO] ✅ Senha enviada para admin@loja.com
```

### Falha no Envio de Email

```
[ERROR] ❌ Erro ao enviar senha para admin@loja.com: SMTP timeout after 30 seconds
[INFO] Email registrado para retry: ID 1
```

### Renovação de Assinatura

```
[INFO] Gerando nova cobrança para loja Minha Loja
[INFO] ✅ Cobrança criada com sucesso (payment_id: pay_789012)
```

---

## Contatos de Suporte

### Suporte Técnico Interno

- Email: suporte@seu-dominio.com
- Slack: #suporte-tecnico

### Suporte dos Provedores

**Asaas:**
- Email: suporte@asaas.com
- Telefone: (11) 4950-2555
- Documentação: https://docs.asaas.com

**Mercado Pago:**
- Email: developers@mercadopago.com
- Telefone: 0800 275 2377
- Documentação: https://www.mercadopago.com.br/developers

---

## Prevenção de Problemas

### Monitoramento Proativo

1. **Configurar alertas** para:
   - Emails falhados > 5 em 1 hora
   - Webhooks não recebidos > 10 minutos após pagamento
   - Lojas bloqueadas > 5 em 1 dia

2. **Verificar diariamente**:
   - Logs de erro
   - Emails pendentes de retry
   - Status de assinaturas

3. **Testar mensalmente**:
   - Criação de loja de teste
   - Fluxo completo de pagamento
   - Webhooks de teste

### Manutenção Regular

```bash
# Executar semanalmente
python manage.py reprocessar_emails_falhados
python manage.py verificar_status_assinaturas

# Executar mensalmente
python manage.py shell
>>> from superadmin.models import EmailRetry
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> cutoff = timezone.now() - timedelta(days=30)
>>> EmailRetry.objects.filter(created_at__lt=cutoff, enviado=True).delete()
```

---

## Recursos Adicionais

- [Fluxo de Assinatura](./FLUXO_ASSINATURA_PAGAMENTO.md)
- [API de Assinatura](./API_ASSINATURA.md)
- [Configurar Django-Q](./CONFIGURAR_DJANGO_Q.md)
- [Documentação do Asaas](https://docs.asaas.com)
- [Documentação do Mercado Pago](https://www.mercadopago.com.br/developers)
