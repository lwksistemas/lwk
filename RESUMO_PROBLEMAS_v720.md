# Resumo dos Problemas - v720

## 🔴 Problema 1: Duplicação de Cobranças (Boleto + PIX)

**O que acontece**: Ao criar uma loja com Mercado Pago, o sistema cria 2 transações separadas:
- Boleto (payment_id: 147009653633)
- PIX (payment_id: 147010684823)

**Por quê**: O código foi projetado para criar ambos automaticamente, dando flexibilidade ao cliente.

**Impacto**: Confusão no painel financeiro (aparecem 2 cobranças de R$ 15,00).

**Solução imediata**: Nenhuma ação necessária - é comportamento esperado.

**Solução permanente**: Implementar cancelamento automático da transação não paga após uma ser aprovada.

---

## 🔴 Problema 2: Financeiro Não Atualiza Após Pagamento

**O que acontece**: Cliente pagou o PIX, mas:
- Status do financeiro continua "pendente" (deveria ser "ativo")
- Senha provisória não foi enviada por email
- Loja não foi liberada para uso

**Por quê**: Webhook do Mercado Pago não foi recebido OU não processou corretamente.

**Impacto**: Cliente pagou mas não consegue acessar o sistema.

**Solução imediata**: Executar script de correção manual.

---

## ✅ Solução Rápida (Execute Agora)

### Passo 1: Atualizar Financeiro Manualmente

```bash
heroku run python manage.py shell --app lwksistemas-38ad47519238
```

Depois, no shell do Django:

```python
from superadmin.models import Loja, FinanceiroLoja
from django.utils import timezone
from datetime import date
from calendar import monthrange

# Buscar a loja
loja = Loja.objects.get(slug='clinica-luiz-1845')
financeiro = loja.financeiro

# Verificar status atual
print(f"Status atual: {financeiro.status_pagamento}")
print(f"Senha enviada: {financeiro.senha_enviada}")

# Calcular próxima cobrança (próximo mês)
data_vencimento_atual = financeiro.data_proxima_cobranca
dia_vencimento = getattr(financeiro, 'dia_vencimento', 10) or 10

if data_vencimento_atual.month == 12:
    proximo_mes = 1
    proximo_ano = data_vencimento_atual.year + 1
else:
    proximo_mes = data_vencimento_atual.month + 1
    proximo_ano = data_vencimento_atual.year

ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)

# Atualizar financeiro (isso dispara o signal on_payment_confirmed)
financeiro.status_pagamento = 'ativo'
financeiro.ultimo_pagamento = timezone.now()
financeiro.data_proxima_cobranca = proxima_cobranca
financeiro.save(update_fields=['status_pagamento', 'ultimo_pagamento', 'data_proxima_cobranca'])

print("✅ Financeiro atualizado!")

# Aguardar 2 segundos para o signal processar
import time
time.sleep(2)

# Verificar se senha foi enviada
financeiro.refresh_from_db()
print(f"Senha enviada: {financeiro.senha_enviada}")

# Se não foi enviada, enviar manualmente
if not financeiro.senha_enviada:
    from superadmin.email_service import EmailService
    service = EmailService()
    owner = loja.owner
    success = service.enviar_senha_provisoria(loja, owner)
    print(f"Senha enviada manualmente: {success}")
```

### Passo 2: Verificar Resultado

Após executar o script acima:

1. ✅ Status do financeiro deve estar "ativo"
2. ✅ Senha provisória deve ter sido enviada para danielsouzafelix30@gmail.com
3. ✅ Cliente pode fazer login na loja

---

## 📋 Checklist de Verificação

- [ ] Executar script de correção manual
- [ ] Verificar email recebido (danielsouzafelix30@gmail.com)
- [ ] Testar login na loja com a senha provisória
- [ ] Verificar webhook do Mercado Pago está configurado
- [ ] Adicionar logs detalhados no webhook para próximas lojas

---

## 🔧 Correções Permanentes Necessárias

### 1. Cancelamento Automático de Transação Não Paga

Quando uma transação (boleto OU PIX) for paga, cancelar automaticamente a outra.

**Arquivo**: `backend/superadmin/sync_service.py`
**Função**: `_update_loja_financeiro_after_mercadopago_payment`

### 2. Melhorar Logs do Webhook

Adicionar logs detalhados para debugar problemas futuros.

**Arquivo**: `backend/superadmin/views.py`
**Função**: `mercadopago_webhook`

### 3. Unificar Visualização no Painel Financeiro

Mostrar boleto + PIX como uma única cobrança com 2 formas de pagamento.

**Arquivo**: Frontend - `frontend/app/(dashboard)/superadmin/financeiro/page.tsx`

---

## 📞 Próximos Passos

1. **Hoje**: Executar script de correção para Clinica Luiz
2. **Amanhã**: Verificar configuração do webhook no Mercado Pago
3. **Esta semana**: Implementar cancelamento automático
4. **Próxima semana**: Melhorar painel financeiro

---

## 📚 Documentos Relacionados

- `PROBLEMA_DUPLICACAO_COBRANCA_v720.md` - Análise técnica completa
- `PROBLEMA_SENHA_NAO_ENVIADA_v720.md` - Análise do problema de senha
- `backend/fix_financeiro_clinica_luiz.py` - Script de correção
- `backend/test_envio_senha_manual.py` - Script de teste de email
