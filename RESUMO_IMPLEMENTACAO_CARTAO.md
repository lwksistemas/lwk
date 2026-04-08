# Resumo: Implementação de Cartão de Crédito

## O que foi feito

### ✅ Frontend Implementado

1. **Formulário de Cadastro Público** (`/cadastro`)
   - Nova seção "Forma de Pagamento" adicionada entre "Plano" e "Dados do Administrador"
   - Duas opções visuais:
     - 🏦 Boleto ou PIX
     - 💳 Cartão de Crédito
   - Aviso claro explicando que:
     - Primeira cobrança é SEMPRE boleto/PIX
     - Se escolher cartão, receberá link após primeiro pagamento
     - Renovações serão automáticas no cartão

2. **Hook do Formulário** (`useLojaForm.ts`)
   - Campo `forma_pagamento_preferida` adicionado
   - Valor padrão: 'boleto'
   - Tipo: 'boleto' | 'pix' | 'cartao_credito'

## Como funciona

### Fluxo do Usuário

```
1. CADASTRO (/cadastro)
   ↓
   Usuário escolhe forma de pagamento
   ↓
   Sistema SEMPRE gera boleto/PIX (primeira cobrança)
   ↓
   Email enviado com boleto/PIX

2. PRIMEIRO PAGAMENTO
   ↓
   Usuário paga boleto/PIX
   ↓
   Webhook confirma pagamento
   ↓
   Email com senha de acesso
   ↓
   Se escolheu CARTÃO: Email com link para cadastrar

3. CADASTRO DO CARTÃO (se escolheu)
   ↓
   Usuário clica no link
   ↓
   Página segura do Asaas
   ↓
   Cadastra dados do cartão
   ↓
   Webhook confirma cadastro
   ↓
   Email de confirmação

4. RENOVAÇÕES
   ↓
   Se CARTÃO: Cobrança automática
   Se BOLETO: Email mensal com boleto/PIX
```

## O que falta implementar (Backend)

### 1. Modelos (Django)

```python
# Loja
forma_pagamento_preferida = models.CharField(
    max_length=20,
    choices=[
        ('boleto', 'Boleto Bancário'),
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão de Crédito'),
    ],
    default='boleto'
)

# FinanceiroLoja
asaas_creditcard_token = models.CharField(max_length=100, blank=True)
cartao_ultimos_digitos = models.CharField(max_length=4, blank=True)
cartao_bandeira = models.CharField(max_length=20, blank=True)
link_pagamento_cartao = models.URLField(blank=True)
cartao_cadastrado = models.BooleanField(default=False)
```

### 2. Cliente Asaas

```python
# Novos métodos necessários
- create_payment_link(payment_id, callback_url)
- tokenize_credit_card(card_data)
- charge_credit_card(customer_id, value, credit_card_token)
```

### 3. Serviço de Cobrança

```python
# Atualizar lógica
def criar_cobranca(loja, financeiro, is_primeira_cobranca=True):
    if is_primeira_cobranca:
        # SEMPRE boleto/PIX
        provedor = 'asaas' ou 'mercadopago'
    else:
        # Usar preferência da loja
        if loja.forma_pagamento_preferida == 'cartao_credito':
            if financeiro.cartao_cadastrado:
                # Cobrar no cartão
                provedor = 'asaas_cartao'
            else:
                # Enviar link para cadastrar
                provedor = 'asaas_cartao_link'
        else:
            # Boleto/PIX
            provedor = 'asaas' ou 'mercadopago'
```

### 4. Webhooks

```python
# Endpoint 1: Confirmação de pagamento
POST /api/superadmin/webhooks/asaas/payment-callback
- Recebe notificação do Asaas
- Atualiza status do pagamento
- Se primeiro pagamento + escolheu cartão: envia link
- Envia emails

# Endpoint 2: Cartão cadastrado
POST /api/superadmin/webhooks/asaas/card-registered
- Recebe notificação de cartão cadastrado
- Marca cartao_cadastrado = True
- Salva token e informações do cartão
- Envia email de confirmação
```

### 5. Emails Automáticos

1. **Após cadastro**: Boleto/PIX
2. **Após primeiro pagamento**: Senha de acesso
3. **Se escolheu cartão**: Link para cadastrar
4. **Após cadastrar cartão**: Confirmação
5. **A cada renovação**: Confirmação de pagamento

## Arquivos Modificados

### Frontend
- ✅ `frontend/components/cadastro/FormularioCadastroLoja.tsx`
- ✅ `frontend/hooks/useLojaForm.ts`

### Backend (Pendente)
- ⏳ `backend/superadmin/models.py`
- ⏳ `backend/superadmin/serializers.py`
- ⏳ `backend/superadmin/cobranca_service.py`
- ⏳ `backend/superadmin/webhooks.py` (novo)
- ⏳ `backend/superadmin/urls.py`
- ⏳ `backend/asaas_integration/client.py`
- ⏳ `backend/superadmin/migrations/XXXX_add_credit_card_fields.py` (novo)

## Testes Necessários

### 1. Fluxo Boleto/PIX
- [ ] Cadastrar loja escolhendo boleto
- [ ] Verificar se boleto foi gerado
- [ ] Simular pagamento via webhook
- [ ] Verificar email com senha

### 2. Fluxo Cartão de Crédito
- [ ] Cadastrar loja escolhendo cartão
- [ ] Verificar se boleto foi gerado (primeira cobrança)
- [ ] Simular pagamento via webhook
- [ ] Verificar email com senha
- [ ] Verificar email com link do cartão
- [ ] Simular cadastro do cartão
- [ ] Verificar email de confirmação
- [ ] Simular renovação automática

### 3. Renovações
- [ ] Testar renovação com boleto
- [ ] Testar renovação com cartão
- [ ] Testar falha de pagamento
- [ ] Testar emails de notificação

## Configuração Asaas

### Webhooks a configurar no painel:
1. **URL**: `https://lwksistemas.com.br/api/superadmin/webhooks/asaas/payment-callback`
   - Eventos: PAYMENT_RECEIVED, PAYMENT_CONFIRMED, PAYMENT_OVERDUE, PAYMENT_DELETED

2. **URL**: `https://lwksistemas.com.br/api/superadmin/webhooks/asaas/card-registered`
   - Eventos: PAYMENT_RECEIVED, PAYMENT_CONFIRMED

## Segurança

### ✅ Boas Práticas Implementadas
- Dados do cartão processados apenas no Asaas (PCI compliant)
- Sistema armazena apenas token e últimos 4 dígitos
- Primeira cobrança sempre manual (boleto/PIX)
- Link de cadastro de cartão expira em 30 dias

### ⏳ A Implementar
- Validação de assinatura HMAC nos webhooks
- Rate limiting nos endpoints de webhook
- Log de todas as tentativas de webhook
- Criptografia adicional para tokens

## Estimativa de Tempo

- ✅ Frontend: 2h (concluído)
- ⏳ Backend - Modelos e Migrations: 1h
- ⏳ Backend - Cliente Asaas: 2h
- ⏳ Backend - Serviço de Cobrança: 2h
- ⏳ Backend - Webhooks: 3h
- ⏳ Backend - Emails: 1h
- ⏳ Testes: 4h
- ⏳ Deploy e Configuração: 1h

**Total estimado**: 16h (2 dias de trabalho)

## Próxima Ação

Começar pela implementação dos modelos e migration:

```bash
# 1. Adicionar campos nos modelos
# 2. Criar migration
python manage.py makemigrations superadmin
# 3. Aplicar migration
python manage.py migrate
# 4. Testar no admin
```
