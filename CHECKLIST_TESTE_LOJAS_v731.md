# Checklist de Teste - Lojas Novas v731

## 📋 Objetivo

Testar o fluxo completo de criação de lojas com Asaas e Mercado Pago após implementações v721-v731.

## 🗑️ Passo 1: Excluir Lojas de Teste Antigas

### Lojas para Excluir
- [ ] Clinica Leandro (Asaas)
- [ ] Clinica Felipe (Mercado Pago)
- [ ] Outras lojas de teste que desejar

### Como Excluir
1. Acesse: https://lwksistemas.com.br/superadmin/dashboard
2. Localize a loja na lista
3. Clique em "Excluir"
4. Confirme a exclusão

### ⚠️ Verificar Após Exclusão
- [ ] Loja removida do painel
- [ ] Cobrança cancelada no Asaas/Mercado Pago
- [ ] Sem registros órfãos no banco

---

## 🏪 Passo 2: Criar Nova Loja com ASAAS

### Dados da Loja
- **Nome**: [Seu nome de teste]
- **Slug**: [será gerado automaticamente]
- **Email**: [seu email de teste]
- **Gateway**: Asaas
- **Plano**: Basico Luiz - R$ 5,00
- **Dia de vencimento**: [escolha um dia, ex: 25]

### ✅ Checklist - Criação (Asaas)

#### Imediatamente Após Criar
- [ ] Loja criada com sucesso
- [ ] Redirecionado para página de pagamento
- [ ] **VERIFICAR**: Apenas 1 cobrança criada no painel Asaas (não 2)
- [ ] Boleto disponível para download
- [ ] Código PIX disponível para copiar
- [ ] **VERIFICAR**: Primeiro boleto vence em 3 dias (não no dia escolhido)

#### Calcular Datas Esperadas
- Data de hoje: 25/02/2026
- Primeiro vencimento esperado: **28/02/2026** (hoje + 3 dias)
- Segundo vencimento esperado: **Dia [X] de março** (dia escolhido)

#### No Painel Asaas
- [ ] Apenas 1 cobrança criada ✅
- [ ] Status: Pendente
- [ ] Valor: R$ 5,00
- [ ] Vencimento: 28/02/2026 (3 dias)

#### No Financeiro do Sistema
- [ ] Loja aparece na lista
- [ ] Status da assinatura: "Ativa" ou "Pendente" (antes do pagamento)
- [ ] Próximo pagamento: 28/02/2026
- [ ] Status do pagamento: "Aguardando pagamento"

---

## 💳 Passo 3: Pagar Boleto/PIX (Asaas)

### Opções de Pagamento
- [ ] Pagar via PIX (recomendado - mais rápido)
- [ ] Pagar via Boleto (demora mais)

### ✅ Checklist - Após Pagamento (Asaas)

#### Webhook Recebido (verificar logs)
```bash
heroku logs --tail --app lwksistemas | grep -i "webhook"
```
- [ ] Webhook recebido do Asaas
- [ ] Status atualizado para "RECEIVED" ou "CONFIRMED"
- [ ] Financeiro atualizado automaticamente

#### Email de Senha
- [ ] Email recebido com senha provisória
- [ ] Email contém link de acesso: `https://lwksistemas.com.br/loja/[slug]/login`
- [ ] Senha funciona para login

#### No Financeiro do Sistema
- [ ] Status da assinatura: **"Ativa"** ✅ (não "Aguardando pagamento")
- [ ] Próximo pagamento criado automaticamente
- [ ] Próximo vencimento: Dia [X] de março (dia escolhido)
- [ ] Status do próximo pagamento: "Aguardando pagamento"

#### Testar Login na Loja
- [ ] Acesse: `https://lwksistemas.com.br/loja/[slug]/login`
- [ ] Faça login com email e senha provisória
- [ ] Sistema solicita troca de senha
- [ ] Após trocar senha, acesso liberado ao dashboard

---

## 🏪 Passo 4: Criar Nova Loja com MERCADO PAGO

### Dados da Loja
- **Nome**: [Seu nome de teste 2]
- **Slug**: [será gerado automaticamente]
- **Email**: [seu email de teste]
- **Gateway**: Mercado Pago
- **Plano**: Basico Luiz - R$ 5,00
- **Dia de vencimento**: [escolha um dia, ex: 10]

### ✅ Checklist - Criação (Mercado Pago)

#### Imediatamente Após Criar
- [ ] Loja criada com sucesso
- [ ] Redirecionado para página de pagamento
- [ ] **VERIFICAR**: 2 transações criadas no Mercado Pago (boleto + PIX) - isso é normal
- [ ] Boleto disponível para download
- [ ] Código PIX disponível para copiar
- [ ] **VERIFICAR**: Primeiro boleto vence em 3 dias (não no dia escolhido)

#### Calcular Datas Esperadas
- Data de hoje: 25/02/2026
- Primeiro vencimento esperado: **28/02/2026** (hoje + 3 dias)
- Segundo vencimento esperado: **Dia [X] de março** (dia escolhido)

#### No Painel Mercado Pago
- [ ] 2 transações criadas (boleto + PIX) ✅ Normal!
- [ ] Ambas com status: Pendente
- [ ] Valor: R$ 5,00 cada
- [ ] Vencimento: 28/02/2026 (3 dias)

#### No Financeiro do Sistema
- [ ] Loja aparece na lista
- [ ] Status da assinatura: "Ativa" ou "Pendente" (antes do pagamento)
- [ ] Próximo pagamento: 28/02/2026
- [ ] Status do pagamento: "Aguardando pagamento"

---

## 💳 Passo 5: Pagar PIX (Mercado Pago)

### Opções de Pagamento
- [ ] Pagar via PIX (recomendado)
- [ ] Pagar via Boleto

### ✅ Checklist - Após Pagamento (Mercado Pago)

#### Webhook Recebido (verificar logs)
```bash
heroku logs --tail --app lwksistemas | grep -i "webhook\|mercadopago"
```
- [ ] Webhook recebido do Mercado Pago
- [ ] Status atualizado para "approved"
- [ ] Financeiro atualizado automaticamente

#### Cancelamento Automático (v729)
- [ ] **IMPORTANTE**: Transação não paga cancelada automaticamente
- [ ] Se pagou PIX → Boleto cancelado
- [ ] Se pagou Boleto → PIX cancelado
- [ ] Verificar no painel Mercado Pago: apenas 1 transação "Aprovada", outra "Cancelada"

#### Email de Senha
- [ ] Email recebido com senha provisória
- [ ] Email contém link de acesso: `https://lwksistemas.com.br/loja/[slug]/login`
- [ ] Senha funciona para login

#### No Financeiro do Sistema
- [ ] Status da assinatura: **"Ativa"** ✅ (não "Pendente")
- [ ] Próximo pagamento criado automaticamente
- [ ] Próximo vencimento: Dia [X] de março (dia escolhido)
- [ ] Status do próximo pagamento: "Aguardando pagamento"

#### Testar Login na Loja
- [ ] Acesse: `https://lwksistemas.com.br/loja/[slug]/login`
- [ ] Faça login com email e senha provisória
- [ ] Sistema solicita troca de senha
- [ ] Após trocar senha, acesso liberado ao dashboard

---

## 🔍 Passo 6: Verificações Finais

### No Painel Superadmin
- [ ] Acesse: https://lwksistemas.com.br/superadmin/financeiro
- [ ] Ambas as lojas aparecem na lista
- [ ] Status das assinaturas: **"Ativa"** ✅
- [ ] Próximos pagamentos visíveis com datas corretas
- [ ] Não há confusão entre status da assinatura e próximo pagamento

### Verificar Dados Corretos

#### Loja Asaas
- [ ] Status da assinatura: Ativa
- [ ] Primeiro boleto: Pago
- [ ] Próximo boleto: Dia [X] de março
- [ ] Total de pagamentos: 2

#### Loja Mercado Pago
- [ ] Status da assinatura: Ativa
- [ ] Primeiro pagamento: Pago
- [ ] Próximo pagamento: Dia [X] de março
- [ ] Total de pagamentos: 2
- [ ] Transação não paga: Cancelada ✅

### Testar Funcionalidades

#### Botão "Atualizar Status"
- [ ] Clique em "Atualizar Status" (Asaas)
- [ ] Sistema consulta API e confirma status
- [ ] Mensagem de sucesso exibida

#### Botão "Atualizar Status" (Mercado Pago)
- [ ] Clique em "Atualizar Status" (Mercado Pago)
- [ ] Sistema consulta API e confirma status
- [ ] Mensagem de sucesso exibida

#### Botão "Baixar Boleto"
- [ ] Clique em "Baixar Boleto"
- [ ] PDF do boleto abre em nova aba
- [ ] Boleto contém dados corretos

#### Botão "Copiar PIX"
- [ ] Clique em "Copiar PIX"
- [ ] Código copiado para área de transferência
- [ ] Mensagem de confirmação exibida

---

## ✅ Critérios de Sucesso

### Funcionalidades Críticas
- [x] Apenas 1 cobrança criada no Asaas (não 2) - v721
- [x] Primeiro boleto vence em 3 dias - v726
- [x] Próximos boletos no dia escolhido - v726
- [x] Senha enviada automaticamente após pagamento - v728
- [x] Transação não paga cancelada automaticamente (MP) - v729
- [x] Status da assinatura exibido corretamente no frontend - v731

### Experiência do Usuário
- [ ] Processo de criação de loja é claro e simples
- [ ] Pagamento é rápido e funciona
- [ ] Email de senha chega rapidamente
- [ ] Login funciona sem problemas
- [ ] Painel financeiro é claro e compreensível

---

## 📝 Anotações Durante o Teste

### Loja Asaas
**Nome**: _______________
**Slug**: _______________
**Email**: _______________
**Primeiro vencimento**: _______________
**Segundo vencimento**: _______________
**Hora do pagamento**: _______________
**Hora do email**: _______________

**Observações**:
- 
- 
- 

### Loja Mercado Pago
**Nome**: _______________
**Slug**: _______________
**Email**: _______________
**Primeiro vencimento**: _______________
**Segundo vencimento**: _______________
**Hora do pagamento**: _______________
**Hora do email**: _______________
**Transação paga**: _______________ (PIX ou Boleto)
**Transação cancelada**: _______________ (PIX ou Boleto)

**Observações**:
- 
- 
- 

---

## 🐛 Problemas Encontrados

Se encontrar algum problema, anote aqui:

### Problema 1
**Descrição**: 
**Quando ocorreu**: 
**Gravidade**: (Crítico / Alto / Médio / Baixo)

### Problema 2
**Descrição**: 
**Quando ocorreu**: 
**Gravidade**: (Crítico / Alto / Médio / Baixo)

---

## 🎯 Resultado Final

- [ ] Todos os testes passaram ✅
- [ ] Alguns problemas encontrados ⚠️
- [ ] Problemas críticos encontrados ❌

**Conclusão**:


---

**Data do Teste**: 25 de Fevereiro de 2026
**Versão Testada**: v731
**Testado por**: Luiz

