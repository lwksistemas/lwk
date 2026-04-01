# 📝 Resumo de Alterações - v1479

## 🎯 Objetivo

Mudar o momento de criação e envio do boleto de assinatura:
- **ANTES:** Boleto criado imediatamente após pagamento
- **AGORA:** Boleto criado e enviado 10 dias antes do vencimento

## 📋 Arquivos Alterados

### 1. backend/superadmin/sync_service.py
**Função:** `_update_loja_financeiro_from_payment()`

**Mudança:** Removida toda a lógica de criação imediata de boleto após pagamento.

**Comportamento atual:**
- Atualiza status para "ativo"
- Calcula próxima cobrança (+30 dias)
- Atualiza `LojaAssinatura.data_vencimento`
- **NÃO cria boleto** (aguarda comando automático)

### 2. backend/superadmin/management/commands/criar_boletos_proximos.py
**Status:** NOVO ARQUIVO

**Funcionalidade:**
- Busca lojas com vencimento em 10 dias
- Cria boleto no Asaas
- Salva no banco (AsaasPayment, PagamentoLoja, FinanceiroLoja)
- Envia email com boleto e PIX

**Uso:**
```bash
python manage.py criar_boletos_proximos
python manage.py criar_boletos_proximos --dry-run
python manage.py criar_boletos_proximos --dias 7
```

## 🔄 Novo Fluxo de Cobrança

### Dia 0: Cliente Paga
```
1. Webhook Asaas → Sistema recebe confirmação
2. Nota fiscal emitida automaticamente
3. Próxima cobrança calculada (hoje + 30 dias)
4. Loja desbloqueada (se estava bloqueada)
5. Status atualizado para "ativo"
```

### Dia 20: Sistema Aguarda
```
- Nenhum boleto criado ainda
- Cliente não recebe nada
- Sistema apenas mantém data de próxima cobrança
```

### Dia 20: 10 Dias Antes do Vencimento
```
1. Heroku Scheduler executa: criar_boletos_proximos
2. Sistema busca lojas com vencimento em 10 dias
3. Cria boleto no Asaas
4. Salva no banco de dados
5. Envia email com boleto e PIX
```

### Dia 30: Vencimento
```
- Cliente já recebeu boleto há 10 dias
- Tem tempo para organizar pagamento
- Se pagar, ciclo recomeça
```

## ⚙️ Configuração Necessária

### Heroku Scheduler

Adicionar job diário:
```
Comando: python manage.py criar_boletos_proximos
Frequência: Diariamente às 09:00
Dyno: worker ou web
```

## ✅ Vantagens

1. **Cliente recebe boleto apenas quando precisa**
   - Não acumula boletos com vencimento distante
   - Foco no pagamento atual

2. **Menos confusão**
   - Boleto chega próximo ao vencimento
   - Cliente sabe que precisa pagar em breve

3. **Melhor gestão**
   - Menos boletos pendentes no sistema
   - Mais fácil identificar inadimplentes

4. **Economia de recursos**
   - Não cria boletos desnecessários
   - Apenas quando realmente necessário

## 🧪 Como Testar

### 1. Teste com Dry-Run
```bash
python manage.py criar_boletos_proximos --dry-run
```
Mostra quais lojas receberiam boleto sem criar nada.

### 2. Teste Real
```bash
# Ajustar data_proxima_cobranca de uma loja de teste para daqui 10 dias
# Executar comando
python manage.py criar_boletos_proximos

# Verificar:
# - Boleto criado no Asaas
# - Email recebido
# - Dados salvos no banco
```

### 3. Monitorar Logs
```bash
heroku logs --tail -a lwksistemas | grep "criar_boletos_proximos"
heroku logs --tail -a lwksistemas | grep "Boleto criado para"
```

## 📊 Impacto

### Lojas Existentes
- Lojas que já têm boleto criado: **não afetadas**
- Próximo ciclo: **seguirá novo fluxo**

### Novas Lojas
- Primeiro boleto: **criado na ativação**
- Próximos boletos: **10 dias antes do vencimento**

## 🚀 Deploy

```bash
git add .
git commit -m "feat: criar e enviar boletos 10 dias antes do vencimento (v1479)"
git push heroku master

# Configurar Heroku Scheduler
heroku addons:open scheduler -a lwksistemas
```

## 📝 Documentação

- `ALTERACAO_LEMBRETE_BOLETO.md` - Documentação completa
- `ACOMPANHAR_TESTE_NF.md` - Histórico de testes de nota fiscal

---

**Versão:** v1479
**Data:** 01/04/2026
**Status:** ✅ Pronto para deploy
