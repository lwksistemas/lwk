# Problema: Duplicação de Cobranças no Asaas (v720)

## Descrição do Problema

Ao criar uma loja com provedor **Asaas**, o sistema está criando **2 cobranças duplicadas** no painel do Asaas.

**Comportamento esperado**: 1 cobrança por loja
**Comportamento atual**: 2 cobranças idênticas (mesmo valor, mesmo vencimento, mesmo customer)

## Impacto

- ✅ Senha provisória está sendo enviada corretamente após pagamento
- ❌ Cliente vê 2 cobranças duplicadas no painel do Asaas
- ❌ Confusão sobre qual boleto pagar
- ❌ Risco de pagamento duplicado

## Análise Técnica

### Fluxo de Criação de Cobrança

Quando uma loja é criada com provedor Asaas:

1. **Serializer** (`LojaCreateSerializer.create`) cria a loja
2. **Serializer** cria o `FinanceiroLoja`
3. **Signal** (`create_asaas_subscription_on_financeiro_creation`) é disparado
4. **Signal** chama `CobrancaService().criar_cobranca()`
5. **CobrancaService** chama `AsaasPaymentStrategy.criar_cobranca()`
6. **AsaasPaymentStrategy** chama `AsaasPaymentService.create_loja_subscription_payment()`
7. **AsaasPaymentService** cria:
   - `AsaasCustomer`
   - `AsaasPayment`
   - `LojaAssinatura`

### Possíveis Causas da Duplicação

#### Causa 1: Signal Sendo Chamado 2 Vezes

O signal `create_asaas_subscription_on_financeiro_creation` pode estar sendo chamado 2 vezes devido a:

- **Bug no Django**: Em algumas versões, signals podem ser disparados múltiplas vezes
- **Transação rollback**: Se houver erro após criar a cobrança, a transação faz rollback mas a cobrança já foi criada no Asaas
- **Save múltiplo**: Se o `FinanceiroLoja` for salvo 2 vezes durante a criação

**Verificação**:
```python
# Adicionar log no signal
@receiver(post_save, sender='superadmin.FinanceiroLoja')
def create_asaas_subscription_on_financeiro_creation(sender, instance, created, **kwargs):
    if not created:
        return
    
    logger.info(f"🔔 SIGNAL DISPARADO: create_asaas_subscription_on_financeiro_creation")
    logger.info(f"   Loja ID: {instance.loja_id}")
    logger.info(f"   Financeiro ID: {instance.id}")
    logger.info(f"   Created: {created}")
    
    # ... resto do código
```

#### Causa 2: Código Criando Cobrança em 2 Lugares

Pode haver código antigo que também cria cobrança no Asaas:

**Locais que criam cobrança**:
1. ✅ `backend/asaas_integration/signals.py` - Signal (via CobrancaService)
2. ❓ `backend/superadmin/asaas_service.py` - Serviço antigo (pode estar sendo chamado)
3. ❓ `backend/asaas_integration/views.py` - Endpoints manuais
4. ❓ `backend/superadmin/sync_service.py` - Renovação automática

**Verificação**:
```bash
# Procurar por chamadas diretas ao AsaasPaymentService
grep -r "AsaasPaymentService()" backend/ --include="*.py"
```

#### Causa 3: Idempotency Key Não Está Funcionando

O Asaas usa `X-Idempotency-Key` para evitar duplicação, mas pode não estar funcionando se:

- A chave não está sendo enviada
- A chave é diferente nas 2 chamadas
- O Asaas não está respeitando a chave

**Verificação**:
```python
# No AsaasClient, verificar se a chave está sendo enviada
headers = {
    'access_token': self.api_key,
    'Content-Type': 'application/json',
    'X-Idempotency-Key': str(uuid.uuid4())  # ← Verificar se está presente
}
```

#### Causa 4: Retry Automático

Se houver retry automático (ex: Celery, Django-Q), pode estar criando cobrança duplicada.

**Verificação**:
```bash
# Verificar se há tasks agendadas para criar cobrança
heroku run python manage.py shell --app lwksistemas-38ad47519238
>>> from django_q.models import Schedule
>>> schedules = Schedule.objects.filter(func__icontains='asaas')
>>> for s in schedules:
...     print(f"{s.name}: {s.func}")
```

## Soluções

### Solução 1: Adicionar Logs Detalhados (IMEDIATO)

Adicionar logs para identificar onde está a duplicação:

```python
# backend/asaas_integration/signals.py

import traceback

@receiver(post_save, sender='superadmin.FinanceiroLoja')
def create_asaas_subscription_on_financeiro_creation(sender, instance, created, **kwargs):
    if not created:
        return
    
    # Log detalhado
    logger.info(f"{'='*80}")
    logger.info(f"🔔 SIGNAL: create_asaas_subscription_on_financeiro_creation")
    logger.info(f"   Loja ID: {instance.loja_id}")
    logger.info(f"   Financeiro ID: {instance.id}")
    logger.info(f"   Thread: {threading.current_thread().name}")
    logger.info(f"   Stack trace:")
    for line in traceback.format_stack():
        logger.info(f"     {line.strip()}")
    logger.info(f"{'='*80}")
    
    # ... resto do código
```

### Solução 2: Adicionar Flag de Controle (CURTO PRAZO)

Adicionar um campo no `FinanceiroLoja` para evitar duplicação:

```python
# backend/superadmin/models.py

class FinanceiroLoja(models.Model):
    # ... campos existentes ...
    
    cobranca_criada = models.BooleanField(
        default=False,
        help_text='Indica se a cobrança inicial já foi criada (evita duplicação)'
    )
```

```python
# backend/asaas_integration/signals.py

@receiver(post_save, sender='superadmin.FinanceiroLoja')
def create_asaas_subscription_on_financeiro_creation(sender, instance, created, **kwargs):
    if not created:
        return
    
    # Verificar se já foi criada
    if instance.cobranca_criada:
        logger.warning(f"⚠️ Cobrança já foi criada para loja {instance.loja.nome}, pulando...")
        return
    
    # Marcar como criada ANTES de criar (evita race condition)
    FinanceiroLoja.objects.filter(pk=instance.pk).update(cobranca_criada=True)
    
    # Criar cobrança
    service = CobrancaService()
    result = service.criar_cobranca(loja, instance)
    
    # ... resto do código
```

### Solução 3: Usar Transaction Atomic (MÉDIO PRAZO)

Garantir que a criação da cobrança seja atômica:

```python
# backend/asaas_integration/signals.py

from django.db import transaction

@receiver(post_save, sender='superadmin.FinanceiroLoja')
def create_asaas_subscription_on_financeiro_creation(sender, instance, created, **kwargs):
    if not created:
        return
    
    # Usar transaction.on_commit para garantir que só cria após commit
    def criar_cobranca():
        from superadmin.models import Loja
        from superadmin.cobranca_service import CobrancaService
        
        loja = Loja.objects.get(pk=instance.loja_id)
        provedor = (getattr(loja, 'provedor_boleto_preferido', None) or '').strip() or 'asaas'
        
        logger.info(f"Criando primeira cobrança para loja {loja.nome} (provedor={provedor})")
        
        service = CobrancaService()
        result = service.criar_cobranca(loja, instance)
        
        # ... logs ...
    
    transaction.on_commit(criar_cobranca)
```

### Solução 4: Desabilitar Signal e Criar Manualmente (LONGO PRAZO)

Remover o signal e criar a cobrança explicitamente no serializer:

```python
# backend/superadmin/serializers.py

class LojaCreateSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        # ... código existente ...
        
        # Criar loja
        loja = Loja.objects.create(**validated_data)
        
        # Criar financeiro
        financeiro = FinanceiroLoja.objects.create(
            loja=loja,
            # ... campos ...
        )
        
        # Criar cobrança EXPLICITAMENTE (sem signal)
        from superadmin.cobranca_service import CobrancaService
        service = CobrancaService()
        result = service.criar_cobranca(loja, financeiro)
        
        return loja
```

## Recomendação

**Hoje** (imediato):
1. ✅ Executar `debug_duplicacao_asaas.py` para identificar lojas afetadas
2. ✅ Adicionar logs detalhados no signal
3. ✅ Verificar logs do Heroku para identificar causa

**Esta semana** (curto prazo):
1. Implementar **Solução 2** (flag de controle)
2. Criar migration para adicionar campo `cobranca_criada`
3. Testar com nova loja

**Próxima semana** (médio prazo):
1. Implementar **Solução 3** (transaction atomic)
2. Adicionar testes automatizados
3. Monitorar por 1 semana

**Próximo mês** (longo prazo):
1. Avaliar **Solução 4** (remover signal)
2. Refatorar código para ser mais explícito
3. Documentar fluxo completo

## Comandos Úteis

```bash
# Executar script de debug
heroku run python manage.py shell < debug_duplicacao_asaas.py --app lwksistemas-38ad47519238

# Ver logs em tempo real
heroku logs --tail --app lwksistemas-38ad47519238 | grep -i "asaas\|cobrança"

# Verificar cobranças duplicadas no banco
heroku run python manage.py shell --app lwksistemas-38ad47519238
>>> from asaas_integration.models import AsaasPayment
>>> from django.db.models import Count
>>> duplicates = AsaasPayment.objects.values('external_reference').annotate(count=Count('id')).filter(count__gt=1)
>>> for d in duplicates:
...     print(f"External Ref: {d['external_reference']} - Count: {d['count']}")

# Cancelar cobrança duplicada
>>> from asaas_integration.client import AsaasClient
>>> client = AsaasClient(api_key='SEU_API_KEY')
>>> client.cancel_payment('PAYMENT_ID_DUPLICADO')
```

## Arquivos Relacionados

- `backend/asaas_integration/signals.py` - Signal que cria cobrança
- `backend/superadmin/cobranca_service.py` - Serviço unificado
- `backend/asaas_integration/client.py` - Cliente Asaas
- `backend/superadmin/serializers.py` - Criação de loja
- `backend/debug_duplicacao_asaas.py` - Script de debug
