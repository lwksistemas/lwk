# Teste: Atualizar Status do Pagamento - v442

## 🎯 Objetivo
Testar se o botão "🔄 Atualizar Status" está atualizando corretamente a data de próxima cobrança e criando o próximo boleto no Asaas.

## 📋 Situação Atual
- **Loja**: Luiz Salao (slug: luiz-salao-5889)
- **Status do Pagamento**: Recebida (PAGO)
- **Data Atual no Sistema**: 09/03/2026
- **Data Esperada**: 10/04/2026 (próximo mês, dia 10)
- **Problema**: Ao clicar em "Atualizar Status", a mensagem aparece mas nada muda

## 🔧 O que foi feito na v442
Adicionei **logs detalhados** em todo o processo de atualização para identificar exatamente onde está o problema:

1. ✅ Logs no botão "Atualizar Status" (`asaas_integration/views.py`)
2. ✅ Logs no método `_update_loja_financeiro_from_payment` (`superadmin/sync_service.py`)
3. ✅ Logs na identificação da loja pelo pagamento
4. ✅ Logs no cálculo da próxima data de cobrança
5. ✅ Logs na criação do novo boleto no Asaas
6. ✅ Logs na verificação de duplicação

## 🧪 Como Testar

### Passo 1: Acessar o SuperAdmin Financeiro
1. Acesse: https://lwksistemas.com.br/superadmin/financeiro
2. Localize a loja "Luiz Salao"
3. Verifique os dados atuais:
   - Status: Recebida
   - Vencimento: 09/03/2026
   - Próxima Cobrança: 09/03/2026

### Passo 2: Clicar em "🔄 Atualizar Status"
1. Clique no botão "🔄 Atualizar Status"
2. Aguarde a mensagem de confirmação
3. **NÃO FECHE A PÁGINA AINDA**

### Passo 3: Verificar os Logs no Heroku
Abra um terminal e execute:

```bash
heroku logs --tail --app lwksistemas
```

Procure por estas mensagens nos logs:

#### ✅ Logs Esperados (Sucesso):
```
🔄 Botão Atualizar Status clicado para pagamento pay_xxxxx
   - Status atual: RECEIVED
   - External Reference: loja_luiz-salao-5889_assinatura
   - Status no Asaas: RECEIVED
   - Pagamento está PAGO, iniciando atualização do financeiro...

🔄 _update_loja_financeiro_from_payment iniciado para pagamento xxx
   - Asaas ID: pay_xxxxx
   - Status: RECEIVED
   - External Reference: loja_luiz-salao-5889_assinatura

✅ Loja identificada: Luiz Salao (slug: luiz-salao-5889)

📊 Financeiro atual:
   - Status: ativo
   - Último Pagamento: 2026-02-07
   - Próxima Cobrança: 2026-03-09
   - Dia Vencimento: 10

📅 Cálculo de próxima cobrança:
   - Hoje: 2026-02-07
   - Dia Vencimento: 10
   - Próximo Mês/Ano: 3/2026
   - Próxima Cobrança Calculada: 2026-04-10
   - Próxima Cobrança Anterior: 2026-03-09

✅ Financeiro salvo com nova data: 2026-04-10

🔍 Buscando LojaAssinatura para slug: luiz-salao-5889
✅ LojaAssinatura encontrada

📝 Atualizando data_vencimento: 2026-03-09 → 2026-04-10
✅ LojaAssinatura.data_vencimento atualizada para 2026-04-10

🔍 Verificando cobranças existentes para 2026-04-10...
✅ Nenhuma cobrança existente, criando novo boleto...

💰 Dados da cobrança:
   - Loja: Luiz Salao
   - Plano: Profissional (Mensal)
   - Valor: R$ 199.90
   - Vencimento: 2026-04-10

🚀 Chamando Asaas API para criar cobrança...

✅ Cobrança criada no Asaas com sucesso!
   - Payment ID: pay_yyyyy
   - Status: PENDING
   - Valor: R$ 199.90
   - Vencimento: 2026-04-10

✅ Pagamento criado no banco local (ID: xxx)
✅ Novo boleto criado no Asaas para Luiz Salao: Vencimento 2026-04-10

✅ Financeiro da loja Luiz Salao atualizado: status=ativo, próxima_cobrança=2026-04-10
   - Resultado da atualização: True
✅ Financeiro da loja atualizado com sucesso via botão Atualizar Status
```

#### ❌ Logs de Erro (Problema):
Se aparecer algum destes logs, significa que há um problema:

```
❌ Não foi possível identificar a loja do pagamento xxx
   - hasattr loja: False
   - hasattr external_reference: True
   - external_reference value: loja_luiz-salao-5889_assinatura
```

```
❌ LojaAssinatura não encontrada para loja luiz-salao-5889
```

```
⚠️ Já existe cobrança para 2026-04-10, pulando criação
```

```
❌ Erro ao criar novo boleto no Asaas: [mensagem de erro]
```

```
⚠️ Financeiro da loja NÃO foi atualizado (retornou False)
```

### Passo 4: Verificar no Frontend
Após clicar em "Atualizar Status", recarregue a página e verifique:

1. **SuperAdmin Financeiro** (https://lwksistemas.com.br/superadmin/financeiro):
   - Vencimento deve mostrar: **10/04/2026**
   - Status deve continuar: **Recebida**
   - Deve aparecer um novo pagamento pendente para 10/04/2026

2. **Dashboard da Loja** (https://lwksistemas.com.br/loja/luiz-salao-5889/dashboard):
   - Próximo Vencimento deve mostrar: **10/04/2026**
   - Status deve mostrar: **Ativo**
   - Último Pagamento deve mostrar: **07/02/2026**

## 📊 Resultados Esperados

### ✅ Sucesso Total:
- Data de próxima cobrança atualizada para 10/04/2026
- Novo boleto criado no Asaas com vencimento 10/04/2026
- Status da loja permanece "Ativo"
- Logs mostram todo o processo executado com sucesso

### ⚠️ Sucesso Parcial:
- Data atualizada mas boleto não criado (verificar logs do Asaas)
- Boleto criado mas data não atualizada (problema no save do financeiro)

### ❌ Falha:
- Nada mudou após clicar no botão
- Logs mostram erro na identificação da loja
- Logs mostram erro na criação do boleto

## 🐛 Possíveis Problemas e Soluções

### Problema 1: Loja não identificada
**Sintoma**: Log mostra "Não foi possível identificar a loja"
**Causa**: `external_reference` do pagamento está incorreto
**Solução**: Verificar e corrigir o `external_reference` no banco de dados

### Problema 2: LojaAssinatura não encontrada
**Sintoma**: Log mostra "LojaAssinatura não encontrada"
**Causa**: Registro de assinatura não existe no banco
**Solução**: Criar manualmente a assinatura ou recriar a loja

### Problema 3: Cobrança já existe
**Sintoma**: Log mostra "Já existe cobrança para 2026-04-10"
**Causa**: Boleto já foi criado anteriormente
**Solução**: Verificar no Asaas se o boleto realmente existe

### Problema 4: Erro na API do Asaas
**Sintoma**: Log mostra "Erro ao criar novo boleto no Asaas"
**Causa**: Problema na comunicação com o Asaas
**Solução**: Verificar credenciais e status da API do Asaas

## 📝 Próximos Passos

Após o teste, me envie:

1. ✅ **Resultado visual**: A data mudou? O boleto foi criado?
2. 📋 **Logs do Heroku**: Copie e cole os logs relevantes
3. 🔍 **Screenshots**: Tire prints do antes e depois

Com essas informações, poderei identificar exatamente onde está o problema e corrigi-lo.

## 🚀 Deploy Realizado
- **Versão**: v442
- **Data**: 07/02/2026
- **Mudanças**: Logs detalhados para debug
- **Status**: ✅ Deploy bem-sucedido

---

**Aguardando seu teste e feedback!** 🎯
