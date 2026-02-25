# Checklist de Teste - Criação de Lojas

## 📋 Preparação

- [ ] Excluir loja "Clinica Vida" (Asaas)
- [ ] Excluir loja "Clinica Luiz" (Mercado Pago)
- [ ] Limpar cache do navegador (Ctrl + Shift + R)

## 🧪 Teste 1: Loja com Asaas

### Criação da Loja
- [ ] Criar nova loja com provedor **Asaas**
- [ ] Anotar horário de criação: ___________
- [ ] Anotar slug da loja: ___________
- [ ] Anotar email do admin: ___________

### Verificações Imediatas (Após Criar)
- [ ] Verificar se **apenas 1 cobrança** foi criada no painel do Asaas
- [ ] Anotar Payment ID: ___________
- [ ] Verificar valor: R$ ___________
- [ ] Verificar vencimento: ___________
- [ ] Status inicial: Pendente ✅

### Logs do Sistema
- [ ] Verificar logs do Heroku:
```bash
heroku logs --tail --app lwksistemas | grep -i "SIGNAL DISPARADO\|Cobrança já existe"
```

**Esperado**:
- ✅ Log: "🔔 SIGNAL DISPARADO"
- ✅ Log: "Criando primeira cobrança para loja..."
- ✅ Log: "✅ Cobrança criada para loja..."
- ❌ NÃO deve aparecer: "⚠️ Cobrança já existe"

### Pagamento
- [ ] Pagar boleto/PIX no Asaas
- [ ] Anotar horário do pagamento: ___________
- [ ] Aguardar 1-2 minutos para webhook processar

### Verificações Após Pagamento
- [ ] Status do financeiro mudou para **Ativo** ✅
- [ ] Email com senha provisória foi recebido ✅
- [ ] Anotar horário do email: ___________
- [ ] Senha provisória funciona no login ✅
- [ ] Próxima cobrança foi calculada (próximo mês) ✅

### Verificação de Duplicação
- [ ] Verificar no painel do Asaas se há **apenas 1 cobrança**
- [ ] Executar script de verificação:
```bash
heroku run python backend/check_duplicacao.py --app lwksistemas
```

**Resultado esperado**: 0 duplicações ✅

---

## 🧪 Teste 2: Loja com Mercado Pago

### Criação da Loja
- [ ] Criar nova loja com provedor **Mercado Pago**
- [ ] Anotar horário de criação: ___________
- [ ] Anotar slug da loja: ___________
- [ ] Anotar email do admin: ___________

### Verificações Imediatas (Após Criar)
- [ ] Verificar se **2 transações** foram criadas (boleto + PIX) ✅ Esperado
- [ ] Anotar Boleto Payment ID: ___________
- [ ] Anotar PIX Payment ID: ___________
- [ ] Verificar valor de ambos: R$ ___________
- [ ] Verificar vencimento: ___________
- [ ] Status inicial: Pendente ✅

### Logs do Sistema
- [ ] Verificar logs do Heroku:
```bash
heroku logs --tail --app lwksistemas | grep -i "Mercado Pago\|cobrança"
```

**Esperado**:
- ✅ Log: "Criando cobrança Mercado Pago para loja..."
- ✅ Log: "PIX Mercado Pago criado para loja..."
- ✅ Log: "✅ Cobrança Mercado Pago criada"

### Pagamento
- [ ] Pagar via **PIX** no Mercado Pago
- [ ] Anotar horário do pagamento: ___________
- [ ] Aguardar 1-2 minutos para webhook processar

### Verificações Após Pagamento
- [ ] Status do financeiro mudou para **Ativo** ✅
- [ ] Email com senha provisória foi recebido ✅
- [ ] Anotar horário do email: ___________
- [ ] Senha provisória funciona no login ✅
- [ ] Próxima cobrança foi calculada (próximo mês) ✅
- [ ] Boleto não pago foi cancelado automaticamente? ⏳ (futuro)

### Verificação no Painel
- [ ] Painel financeiro mostra status **Ativo** (não "Pendente")
- [ ] Se mostrar "Pendente", limpar cache (Ctrl + Shift + R)
- [ ] Após limpar cache, status está correto ✅

---

## 🔍 Verificações Finais

### Banco de Dados
Executar para cada loja:
```bash
heroku run python backend/manage.py shell --app lwksistemas
```

```python
from superadmin.models import Loja

# Loja Asaas
loja_asaas = Loja.objects.get(slug='<slug-asaas>')
print(f"Status: {loja_asaas.financeiro.status_pagamento}")
print(f"Senha enviada: {loja_asaas.financeiro.senha_enviada}")

# Loja Mercado Pago
loja_mp = Loja.objects.get(slug='<slug-mercadopago>')
print(f"Status: {loja_mp.financeiro.status_pagamento}")
print(f"Senha enviada: {loja_mp.financeiro.senha_enviada}")
```

**Resultado esperado**:
- ✅ Status: ativo
- ✅ Senha enviada: True

### Verificação de Duplicação (Asaas)
```bash
heroku run python backend/check_duplicacao.py --app lwksistemas
```

**Resultado esperado**:
- ✅ Total de lojas verificadas: 1
- ✅ Lojas com duplicação: 0

### Logs Completos
```bash
heroku logs --num 500 --app lwksistemas | grep -i "signal\|cobrança\|senha"
```

**Verificar**:
- [ ] Signal foi disparado apenas 1 vez por loja
- [ ] Nenhum log de "Cobrança já existe" (exceto se houver retry)
- [ ] Senha foi enviada após pagamento confirmado

---

## 📊 Resultados Esperados

### ✅ Sucesso Total
- Asaas: 1 cobrança criada, pagamento processado, senha enviada
- Mercado Pago: 2 transações criadas (boleto + PIX), pagamento processado, senha enviada
- Nenhuma duplicação detectada
- Sistema funcionando 100%

### ⚠️ Problemas Possíveis

#### Problema 1: Duplicação no Asaas
**Sintoma**: 2 cobranças idênticas criadas
**Causa**: Proteção v721 não funcionou
**Ação**: Verificar logs e reportar

#### Problema 2: Senha não enviada
**Sintoma**: Pagamento confirmado mas email não chegou
**Causa**: Webhook não processou ou signal não disparou
**Ação**: 
1. Verificar status no banco de dados
2. Executar script de correção:
```bash
heroku run python backend/fix_financeiro_mercadopago.py --app lwksistemas
```
3. Ou usar botão "📧 Reenviar senha" no painel

#### Problema 3: Painel mostra "Pendente"
**Sintoma**: Banco mostra "ativo" mas painel mostra "Pendente"
**Causa**: Cache do navegador ou frontend
**Ação**:
1. Limpar cache (Ctrl + Shift + R)
2. Fazer logout e login
3. Clicar em "🔄 Atualizar Status"

#### Problema 4: Webhook não processou
**Sintoma**: Pagamento feito mas status não mudou
**Causa**: Webhook não foi recebido
**Ação**:
1. Verificar configuração do webhook no painel do provedor
2. Executar script de correção manual
3. Verificar logs do Heroku

---

## 📝 Anotações

### Loja Asaas
- Slug: ___________
- Email: ___________
- Payment ID: ___________
- Horário criação: ___________
- Horário pagamento: ___________
- Horário email: ___________
- Status final: ___________

### Loja Mercado Pago
- Slug: ___________
- Email: ___________
- Boleto ID: ___________
- PIX ID: ___________
- Horário criação: ___________
- Horário pagamento: ___________
- Horário email: ___________
- Status final: ___________

### Problemas Encontrados
1. ___________
2. ___________
3. ___________

### Observações
___________
___________
___________

---

## 🎯 Critérios de Sucesso

Para considerar o teste **100% bem-sucedido**:

- [ ] Asaas: Apenas 1 cobrança criada
- [ ] Mercado Pago: 2 transações criadas (esperado)
- [ ] Ambas: Pagamento processado corretamente
- [ ] Ambas: Senha enviada automaticamente
- [ ] Ambas: Status "Ativo" no painel
- [ ] Nenhuma duplicação detectada
- [ ] Logs mostram proteção v721 funcionando

---

**Data do teste**: ___________
**Testado por**: ___________
**Resultado final**: ⬜ Sucesso ⬜ Falha parcial ⬜ Falha total
