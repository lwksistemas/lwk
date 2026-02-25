# Configuração do Django-Q para Fluxo de Assinatura

Este documento descreve como configurar as tasks agendadas do Django-Q para o novo fluxo de assinatura e pagamento.

## Tasks Implementadas

### 1. reprocessar_emails_task
**Função:** Reprocessa emails falhados automaticamente  
**Frequência:** A cada 5 minutos  
**Comando:** `python manage.py reprocessar_emails_falhados`

**O que faz:**
- Busca emails em `EmailRetry` com `enviado=False` e `tentativas < max_tentativas`
- Tenta reenviar cada email usando `EmailService`
- Atualiza status e incrementa contador de tentativas
- Registra logs detalhados de sucesso/falha

### 2. verificar_assinaturas_task
**Função:** Verifica e atualiza status de assinaturas vencidas  
**Frequência:** Diariamente às 00:00  
**Comando:** `python manage.py verificar_status_assinaturas`

**O que faz:**
- Marca assinaturas vencidas há 7+ dias como 'atrasado'
- Marca assinaturas vencidas há 30+ dias como 'bloqueado'
- Bloqueia lojas com assinaturas vencidas há 30+ dias
- Registra logs e estatísticas

## Configuração no Django Admin

### Passo 1: Acessar Django-Q Admin

1. Acesse o Django Admin: `https://seu-dominio.com/admin/`
2. Navegue até **Django Q** → **Scheduled tasks**

### Passo 2: Criar Schedule para reprocessar_emails_task

Clique em **Add Scheduled Task** e preencha:

- **Name:** `Reprocessar Emails Falhados`
- **Func:** `superadmin.tasks.reprocessar_emails_task`
- **Schedule type:** `Minutes`
- **Minutes:** `5`
- **Repeats:** `-1` (infinito)
- **Enabled:** ✅ (marcado)

Clique em **Save**.

### Passo 3: Criar Schedule para verificar_assinaturas_task

Clique em **Add Scheduled Task** e preencha:

- **Name:** `Verificar Status Assinaturas`
- **Func:** `superadmin.tasks.verificar_assinaturas_task`
- **Schedule type:** `Cron`
- **Cron:** `0 0 * * *` (diariamente às 00:00)
- **Repeats:** `-1` (infinito)
- **Enabled:** ✅ (marcado)

Clique em **Save**.

## Configuração via Código (Alternativa)

Se preferir configurar via código, adicione ao `settings.py`:

```python
# Django-Q Configuration
Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
    'schedule': [
        {
            'func': 'superadmin.tasks.reprocessar_emails_task',
            'schedule_type': 'I',  # Interval
            'minutes': 5,
            'repeats': -1,  # Infinito
        },
        {
            'func': 'superadmin.tasks.verificar_assinaturas_task',
            'schedule_type': 'C',  # Cron
            'cron': '0 0 * * *',  # Diariamente às 00:00
            'repeats': -1,  # Infinito
        },
    ]
}
```

## Verificação

### Verificar se Django-Q está rodando

```bash
# No servidor (Heroku)
heroku ps -a seu-app

# Deve aparecer algo como:
# worker.1: up 2024/02/25 10:00:00 (~ 1h ago)
```

### Verificar logs das tasks

```bash
# No servidor (Heroku)
heroku logs --tail -a seu-app | grep TASK

# Deve aparecer logs como:
# [TASK] Iniciando reprocessamento de emails falhados...
# [TASK] Reprocessamento concluído em 0.45s
```

### Verificar no Django Admin

1. Acesse **Django Q** → **Successful tasks**
2. Verifique se as tasks estão sendo executadas
3. Clique em uma task para ver detalhes e resultado

## Monitoramento

### Métricas Importantes

1. **Taxa de sucesso de emails:**
   - Acessar `EmailRetry` no admin
   - Filtrar por `enviado=True`
   - Verificar taxa de sucesso vs falha

2. **Assinaturas atrasadas:**
   - Acessar `FinanceiroLoja` no admin
   - Filtrar por `status_pagamento=atrasado`
   - Verificar quantidade e tendência

3. **Assinaturas bloqueadas:**
   - Acessar `FinanceiroLoja` no admin
   - Filtrar por `status_pagamento=bloqueado`
   - Tomar ações corretivas

### Alertas

Configure alertas para:
- Emails com 3+ tentativas falhadas
- Assinaturas atrasadas há mais de 15 dias
- Assinaturas bloqueadas

## Troubleshooting

### Task não está executando

1. Verificar se Django-Q worker está rodando:
   ```bash
   heroku ps -a seu-app
   ```

2. Verificar se a task está habilitada no admin:
   - Django Q → Scheduled tasks
   - Verificar campo **Enabled**

3. Verificar logs de erro:
   ```bash
   heroku logs --tail -a seu-app | grep ERROR
   ```

### Emails não estão sendo reenviados

1. Verificar se existem emails pendentes:
   ```bash
   python manage.py shell
   >>> from superadmin.models import EmailRetry
   >>> EmailRetry.objects.filter(enviado=False).count()
   ```

2. Executar comando manualmente:
   ```bash
   python manage.py reprocessar_emails_falhados --verbose
   ```

3. Verificar configuração de email no `settings.py`:
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.gmail.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'seu-email@gmail.com'
   EMAIL_HOST_PASSWORD = 'sua-senha-app'
   DEFAULT_FROM_EMAIL = 'seu-email@gmail.com'
   ```

### Assinaturas não estão sendo atualizadas

1. Executar comando manualmente:
   ```bash
   python manage.py verificar_status_assinaturas --verbose
   ```

2. Verificar se existem assinaturas vencidas:
   ```bash
   python manage.py shell
   >>> from superadmin.models import FinanceiroLoja
   >>> from django.utils import timezone
   >>> from datetime import timedelta
   >>> hoje = timezone.now().date()
   >>> FinanceiroLoja.objects.filter(
   ...     status_pagamento='ativo',
   ...     data_proxima_cobranca__lt=hoje - timedelta(days=7)
   ... ).count()
   ```

## Comandos Úteis

### Executar tasks manualmente

```bash
# Reprocessar emails
python manage.py reprocessar_emails_falhados

# Reprocessar emails com limite
python manage.py reprocessar_emails_falhados --limit 10

# Reprocessar emails de uma loja específica
python manage.py reprocessar_emails_falhados --loja minha-loja

# Forçar reprocessamento (ignorar proxima_tentativa)
python manage.py reprocessar_emails_falhados --force

# Verificar assinaturas
python manage.py verificar_status_assinaturas

# Verificar assinaturas (dry-run)
python manage.py verificar_status_assinaturas --dry-run

# Verificar assinaturas (verbose)
python manage.py verificar_status_assinaturas --verbose

# Verificar assinaturas com parâmetros customizados
python manage.py verificar_status_assinaturas --dias-atraso 10 --dias-bloqueio 45
```

## Referências

- [Django-Q Documentation](https://django-q.readthedocs.io/)
- [Cron Expression Generator](https://crontab.guru/)
- [Django Email Documentation](https://docs.djangoproject.com/en/4.2/topics/email/)
