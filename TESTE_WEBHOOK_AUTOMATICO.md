# Teste: Webhook Automático Mercado Pago

## 📋 Checklist de Teste

### Passo 1: Criar Loja
- [ ] Acesse: https://lwksistemas.com.br/superadmin/criar-loja
- [ ] Preencha os dados:
  - Nome: **Clinica Teste Webhook**
  - Email: **seu-email@teste.com**
  - Gateway: **Mercado Pago**
  - Plano: **Basico Luiz - R$ 5,00**
  - Dia vencimento: **25**
- [ ] Clique em "Criar Loja"

### Passo 2: Anotar Informações
- [ ] **Nome da loja**: _______________
- [ ] **Slug**: _______________
- [ ] **PIX ID**: _______________
- [ ] **Boleto ID**: _______________
- [ ] **Hora da criação**: _______________

### Passo 3: Verificar Criação
- [ ] 2 transações criadas no Mercado Pago (boleto + PIX)
- [ ] Primeiro vencimento: **28/02/2026** (3 dias)
- [ ] Código PIX disponível para copiar

### Passo 4: Pagar PIX
- [ ] Copie o código PIX
- [ ] Pague via PIX
- [ ] **Hora do pagamento**: _______________

### Passo 5: Aguardar (1-2 minutos)
- [ ] Aguarde 1-2 minutos
- [ ] **NÃO clique em nenhum botão**
- [ ] Deixe o webhook trabalhar automaticamente

### Passo 6: Verificar Automação ✅

#### No Financeiro do Sistema
- [ ] Acesse: https://lwksistemas.com.br/superadmin/financeiro
- [ ] Status da assinatura: **"Ativa"** (não "Inativa")
- [ ] Próximo pagamento: **25/03/2026**
- [ ] Status do pagamento: **"Pendente"** (próximo boleto)

#### No Mercado Pago
- [ ] PIX: **Aprovado** ✅
- [ ] Boleto: **Cancelado** ✅ (não "Pendente")

#### No Email
- [ ] Email recebido com senha provisória
- [ ] Email contém link de login
- [ ] **Hora do email**: _______________

### Passo 7: Testar Login
- [ ] Acesse o link do email
- [ ] Faça login com a senha provisória
- [ ] Sistema solicita troca de senha
- [ ] Após trocar, acesso liberado

## ⏱️ Tempo Esperado

| Ação | Tempo |
|------|-------|
| Criar loja | Imediato |
| Pagar PIX | Imediato |
| Webhook recebido | 30 segundos - 2 minutos |
| Status atualizado | Imediato após webhook |
| Boleto cancelado | Imediato após webhook |
| Email enviado | Imediato após webhook |

## ✅ Critérios de Sucesso

### Webhook Funcionando ✅
- [x] Status atualiza automaticamente (sem clicar em botão)
- [x] Boleto é cancelado automaticamente
- [x] Senha é enviada automaticamente
- [x] Tudo acontece em 1-2 minutos

### Webhook NÃO Funcionando ❌
- [ ] Status continua "Inativo" após 2 minutos
- [ ] Boleto continua "Pendente" no Mercado Pago
- [ ] Email não chega
- [ ] Precisa clicar em "Atualizar Status"

## 🐛 Se Não Funcionar

### Verificar Logs
```bash
heroku logs --tail --app lwksistemas | grep -i "webhook\|mercadopago"
```

### Verificar Webhook no Mercado Pago
1. Acesse: https://www.mercadopago.com.br/developers/panel/app
2. Vá em "Webhooks"
3. Verifique:
   - Status: **Ativo**
   - URL: **https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/**
   - Eventos: **payment**

### Testar Manualmente
Se o webhook não funcionar, clique em "Atualizar Status" para confirmar que a lógica está correta.

## 📝 Anotações

### Observações Durante o Teste
- 
- 
- 

### Problemas Encontrados
- 
- 
- 

### Tempo Real de Execução
- Criação da loja: _______________
- Pagamento: _______________
- Webhook recebido: _______________
- Status atualizado: _______________
- Email recebido: _______________

**Total**: _______________ minutos

---

**Data**: 25 de Fevereiro de 2026
**Versão**: v732
**Testado por**: Luiz

