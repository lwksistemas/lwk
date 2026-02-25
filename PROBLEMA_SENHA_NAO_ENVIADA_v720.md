# Problema: Senha Provisória Não Enviada Após Pagamento (v720)

## Descrição do Problema

Após pagar o boleto do Mercado Pago via PIX, o sistema não enviou a senha provisória por email para o administrador da loja.

## Loja Afetada

- **Nome**: Clinica Luiz
- **Slug**: clinica-luiz-1845
- **Owner**: daniel (danielsouzafelix30@gmail.com)
- **Payment ID**: 147009653633 (Mercado Pago)
- **Data criação**: 2026-02-25 15:23:35

## Análise do Problema

### Fluxo Esperado (v720)

1. Loja criada → FinanceiroLoja criado com `status_pagamento='pendente'`
2. Signal cria cobrança (boleto + PIX) no Mercado Pago
3. Cliente paga → Webhook recebido
4. Webhook atualiza `status_pagamento='ativo'` no FinanceiroLoja
5. Signal `on_payment_confirmed` é disparado
6. EmailService envia senha provisória
7. FinanceiroLoja atualizado: `senha_enviada=True`, `data_envio_senha=now()`

### O Que Aconteceu

Baseado nos logs fornecidos:

1. ✅ Loja criada com sucesso
2. ✅ Cobrança criada no Mercado Pago (payment_id=147009653633)
3. ✅ Cliente pagou via PIX
4. ❓ Webhook do Mercado Pago foi recebido?
5. ❓ Status do FinanceiroLoja foi atualizado para 'ativo'?
6. ❌ Senha provisória NÃO foi enviada

### Possíveis Causas

1. **Webhook não foi recebido**
   - Mercado Pago não enviou o webhook
   - Webhook foi bloqueado por firewall/proxy
   - URL do webhook está incorreta

2. **Webhook foi recebido mas não processou**
   - Erro na função `process_mercadopago_webhook_payment`
   - Status do pagamento não é 'approved'
   - Payment ID não foi encontrado no banco

3. **Signal não foi disparado**
   - FinanceiroLoja não foi salvo corretamente
   - Signal está desabilitado
   - Erro no signal `on_payment_confirmed`

4. **EmailService falhou**
   - Erro ao enviar email (SMTP)
   - Email foi para spam
   - Credenciais SMTP inválidas

## Verificações Necessárias

### 1. Verificar Status do FinanceiroLoja

```python
from superadmin.models import Loja, FinanceiroLoja

loja = Loja.objects.get(slug='clinica-luiz-1845')
financeiro = loja.financeiro

print(f"Status pagamento: {financeiro.status_pagamento}")
print(f"Senha enviada: {financeiro.senha_enviada}")
print(f"Data envio senha: {financeiro.data_envio_senha}")
print(f"Último pagamento: {financeiro.ultimo_pagamento}")
```

**Resultado esperado**:
- `status_pagamento='ativo'` (se webhook processou)
- `senha_enviada=False` (se email não foi enviado)

### 2. Verificar Logs do Webhook

Procurar nos logs do Heroku por:
- `Webhook MP pagamento 147009653633`
- `process_mercadopago_webhook_payment`
- `Pagamento MP 147009653633 marcado como pago`

### 3. Verificar Logs do Signal

Procurar nos logs por:
- `💰 Pagamento confirmado para loja Clinica Luiz`
- `on_payment_confirmed`
- `Enviando senha provisória`

### 4. Verificar EmailRetry

```python
from superadmin.models import EmailRetry

# Verificar se há tentativas de envio falhadas
retries = EmailRetry.objects.filter(
    loja_slug='clinica-luiz-1845',
    tipo_email='senha_provisoria'
).order_by('-created_at')

for retry in retries:
    print(f"Tentativa: {retry.tentativas}")
    print(f"Status: {retry.status}")
    print(f"Erro: {retry.erro}")
    print(f"Criado em: {retry.created_at}")
    print("---")
```

## Soluções

### Solução 1: Enviar Senha Manualmente (Imediato)

Execute o script de teste:

```bash
heroku run python manage.py shell < test_envio_senha_manual.py --app lwksistemas-38ad47519238
```

Ou no Django shell:

```python
from superadmin.models import Loja
from superadmin.email_service import EmailService

loja = Loja.objects.get(slug='clinica-luiz-1845')
owner = loja.owner
service = EmailService()
success = service.enviar_senha_provisoria(loja, owner)
print(f"Senha enviada: {success}")
```

### Solução 2: Atualizar Status Manualmente e Disparar Signal

Se o webhook não foi recebido, atualize manualmente:

```python
from superadmin.models import Loja, FinanceiroLoja
from django.utils import timezone

loja = Loja.objects.get(slug='clinica-luiz-1845')
financeiro = loja.financeiro

# Atualizar status (isso dispara o signal on_payment_confirmed)
financeiro.status_pagamento = 'ativo'
financeiro.ultimo_pagamento = timezone.now()
financeiro.save(update_fields=['status_pagamento', 'ultimo_pagamento'])

print("Status atualizado. Signal disparado.")
```

### Solução 3: Configurar Webhook do Mercado Pago

Verificar se o webhook está configurado corretamente no painel do Mercado Pago:

1. Acessar: https://www.mercadopago.com.br/developers/panel/webhooks
2. Verificar URL: `https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/webhook/mercadopago/`
3. Eventos habilitados: `payment`
4. Testar webhook manualmente

### Solução 4: Adicionar Logs Detalhados

Adicionar logs no signal `on_payment_confirmed` para debugar:

```python
@receiver(post_save, sender='superadmin.FinanceiroLoja')
def on_payment_confirmed(sender, instance, created, **kwargs):
    logger.info(f"[DEBUG] Signal on_payment_confirmed disparado")
    logger.info(f"[DEBUG] created={created}")
    logger.info(f"[DEBUG] status_pagamento={instance.status_pagamento}")
    logger.info(f"[DEBUG] senha_enviada={instance.senha_enviada}")
    
    if created:
        logger.info(f"[DEBUG] Ignorando (created=True)")
        return
    
    if instance.status_pagamento == 'ativo' and not instance.senha_enviada:
        logger.info(f"[DEBUG] Condições atendidas, enviando senha...")
        # ... resto do código
```

## Próximos Passos

1. ✅ Executar script de teste para enviar senha manualmente
2. ⏳ Verificar logs do webhook e signal
3. ⏳ Identificar causa raiz (webhook não recebido ou signal não disparado)
4. ⏳ Implementar correção permanente
5. ⏳ Testar com nova loja para confirmar correção

## Comandos Úteis

```bash
# Ver logs em tempo real
heroku logs --tail --app lwksistemas-38ad47519238

# Filtrar logs do webhook
heroku logs --tail --app lwksistemas-38ad47519238 | grep -i "webhook\|mercadopago"

# Filtrar logs do signal
heroku logs --tail --app lwksistemas-38ad47519238 | grep -i "on_payment_confirmed\|senha"

# Executar script de teste
heroku run python manage.py shell < test_envio_senha_manual.py --app lwksistemas-38ad47519238

# Abrir Django shell
heroku run python manage.py shell --app lwksistemas-38ad47519238
```

## Referências

- Signal: `backend/superadmin/signals.py` (função `on_payment_confirmed`)
- Webhook: `backend/superadmin/views.py` (função `mercadopago_webhook`)
- Sync Service: `backend/superadmin/sync_service.py` (função `process_mercadopago_webhook_payment`)
- Email Service: `backend/superadmin/email_service.py` (função `enviar_senha_provisoria`)
- Modelo: `backend/superadmin/models.py` (classe `FinanceiroLoja`)
