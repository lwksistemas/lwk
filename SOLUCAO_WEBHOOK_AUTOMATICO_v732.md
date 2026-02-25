# Solução: Webhook Automático Mercado Pago - v732

## 📋 Problema

Após criar loja e pagar via PIX, o sistema não atualiza automaticamente:
- ❌ Status continua "Inativo"
- ❌ Boleto não é cancelado
- ❌ Senha não é enviada

**Causa**: Webhook do Mercado Pago não está configurado.

## ✅ Solução Implementada

### Código Já Está Pronto ✅

O sistema já tem toda a lógica implementada:
- ✅ Endpoint do webhook: `/api/superadmin/mercadopago-webhook/`
- ✅ Processamento automático de pagamentos
- ✅ Cancelamento automático de transação não paga (v729)
- ✅ Envio automático de senha (v728)

### O Que Falta: Configurar no Mercado Pago

Você precisa configurar o webhook no painel do Mercado Pago para que ele envie notificações para o sistema.

## 🔧 Como Configurar (Passo a Passo)

### 1. Acessar Painel do Mercado Pago

1. Acesse: https://www.mercadopago.com.br/developers/panel/app
2. Faça login
3. Selecione sua aplicação

### 2. Configurar Webhook

1. Clique em **"Webhooks"** no menu lateral
2. Clique em **"Adicionar webhook"** ou **"Configurar notificações"**
3. Preencha:

**URL do Webhook**:
```
https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/
```

**OU** (se o domínio personalizado estiver configurado):
```
https://lwksistemas.com.br/api/superadmin/mercadopago-webhook/
```

**Eventos**:
- ✅ Selecione: `payment` ou `payment.updated`

**Modo**:
- ✅ Selecione: `Produção` (se estiver usando Access Token de produção)

4. Clique em **"Salvar"**

### 3. Verificar Configuração

Após salvar, você deve ver:
- ✅ URL configurada
- ✅ Status: Ativo
- ✅ Eventos: payment

## 🧪 Testar

### Teste 1: Verificar Endpoint

Acesse no navegador:
```
https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/
```

Deve retornar:
```json
{
  "status": "ok",
  "message": "Endpoint do webhook Mercado Pago ativo."
}
```

### Teste 2: Criar Nova Loja

1. Crie uma nova loja de teste
2. Pague via PIX
3. Aguarde 1-2 minutos
4. Verifique se:
   - ✅ Status mudou para "Ativa" automaticamente
   - ✅ Boleto foi cancelado automaticamente
   - ✅ Senha foi enviada automaticamente

### Teste 3: Verificar Logs

```bash
heroku logs --tail --app lwksistemas | grep -i "webhook\|mercadopago"
```

Deve aparecer:
```
Webhook MP: pagamento 147748353282 status=approved
Pagamento MP 147748353282 marcado como pago
PIX aprovado para loja clinica-felipe-1845. Cancelando boleto...
✅ Boleto 147748631038 cancelado automaticamente
```

## 📊 Fluxo Após Configurar Webhook

### Antes (Manual) ❌
```
1. Cliente paga PIX
2. Sistema NÃO recebe notificação
3. Admin precisa clicar em "Atualizar Status"
4. Sistema consulta API e atualiza
```

### Depois (Automático) ✅
```
1. Cliente paga PIX
2. Mercado Pago envia webhook → Sistema recebe
3. Sistema processa automaticamente:
   - Atualiza status para "Ativa"
   - Cancela boleto
   - Envia senha por email
4. Cliente recebe email e pode fazer login
```

## 🎯 URLs Importantes

### Webhook Endpoint
```
https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/
```

### Painel Mercado Pago
```
https://www.mercadopago.com.br/developers/panel/app
```

### Financeiro do Sistema
```
https://lwksistemas.com.br/superadmin/financeiro
```

## ✅ Checklist

- [ ] Acessei painel do Mercado Pago
- [ ] Configurei webhook com URL correta
- [ ] Selecionei evento "payment"
- [ ] Selecionei modo "Produção"
- [ ] Salvei configuração
- [ ] Webhook está com status "Ativo"
- [ ] Testei endpoint via navegador
- [ ] Criei loja de teste e paguei
- [ ] Verifiquei que status atualizou automaticamente
- [ ] Verifiquei logs do Heroku

## 📝 Observações

### Por Que Não Está Funcionando Agora?

O webhook não está configurado no painel do Mercado Pago. Por isso:
- Mercado Pago não sabe para onde enviar notificações
- Sistema não recebe avisos de pagamento
- Tudo precisa ser feito manualmente

### Por Que o Botão "Atualizar Status" Funciona?

O botão faz uma consulta manual na API do Mercado Pago:
1. Busca os IDs dos pagamentos no banco de dados
2. Consulta cada pagamento na API do Mercado Pago
3. Verifica se foi aprovado
4. Atualiza o sistema

É a mesma lógica do webhook, mas acionada manualmente.

### Qual a Diferença?

| Aspecto | Webhook (Automático) | Botão (Manual) |
|---------|---------------------|----------------|
| Acionamento | Mercado Pago envia | Admin clica |
| Velocidade | 1-2 minutos | Imediato |
| Experiência | Cliente recebe email automaticamente | Cliente precisa esperar admin |
| Escalabilidade | Funciona para todas as lojas | Admin precisa clicar em cada loja |

## 🚀 Resultado Esperado

Após configurar o webhook:

1. ✅ Cliente cria loja
2. ✅ Cliente paga PIX
3. ✅ Sistema recebe webhook automaticamente (1-2 min)
4. ✅ Status atualiza para "Ativa"
5. ✅ Boleto é cancelado
6. ✅ Senha é enviada por email
7. ✅ Cliente faz login e usa o sistema

**Tudo automático, sem intervenção manual!** 🎉

## 📞 Suporte

Se tiver dúvidas:
1. Leia o guia completo: `GUIA_CONFIGURAR_WEBHOOK_MERCADOPAGO.md`
2. Verifique os logs: `heroku logs --tail --app lwksistemas`
3. Teste o endpoint: acesse a URL no navegador

---

**Data**: 25 de Fevereiro de 2026
**Versão**: v732
**Status**: Aguardando configuração do webhook no Mercado Pago

