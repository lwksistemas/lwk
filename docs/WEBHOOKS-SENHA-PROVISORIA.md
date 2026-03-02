# Webhooks e envio da senha provisória

Após o pagamento (boleto ou PIX) ser confirmado, o Asaas ou o Mercado Pago envia um **webhook** para a sua API. A API atualiza o status da loja e dispara o envio da **senha provisória** por e-mail para o gerente da loja.

---

## 1. Fluxo resumido

1. Cliente paga (boleto ou PIX) no **Asaas** ou no **Mercado Pago**.
2. O gateway chama a **URL do webhook** que você configurou no painel.
3. A API recebe o webhook, atualiza o **FinanceiroLoja** (ex.: `status_pagamento='ativo'`) e salva.
4. O **signal** `on_payment_confirmed` (em `superadmin/signals.py`) roda no `post_save` do `FinanceiroLoja`.
5. Se `status_pagamento == 'ativo'` e a senha ainda não foi enviada, o **EmailService** envia a senha provisória para o e-mail do dono da loja.

**Se o webhook não for recebido** (URL errada ou servidor parado), o signal não roda e **o e-mail da senha provisória não é enviado**.

---

## 2. URLs dos webhooks

Cada gateway (Asaas e Mercado Pago) permite configurar **uma URL de webhook**. Essa URL deve apontar para o servidor que estiver **no ar** (Heroku ou Render).

### 2.1 Asaas (boleto/PIX Asaas)

| Servidor | URL do webhook |
|----------|----------------|
| **Heroku** (primário) | `https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/` |
| **Render** (backup)    | `https://lwksistemas-backup-ewgo.onrender.com/api/asaas/webhook/` |

**Onde configurar:** Painel Asaas → Sua aplicação → Webhooks / Notificações.

---

### 2.2 Mercado Pago (boleto/PIX MP)

| Servidor | URL do webhook |
|----------|----------------|
| **Heroku** (primário) | `https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/` |
| **Render** (backup)    | `https://lwksistemas-backup-ewgo.onrender.com/api/superadmin/mercadopago-webhook/` |

**Onde configurar:** [Mercado Pago Developers](https://www.mercadopago.com.br/developers/panel) → Sua aplicação → Webhooks / Notificações.

---

## 3. O que fazer em cada cenário

### Cenário A: Heroku sempre no ar (recomendado)

- Deixe as URLs de webhook **apontando para o Heroku** (as da linha “Heroku” na tabela acima).
- Assim, quando o pagamento for confirmado, o Heroku recebe o webhook e envia o e-mail da senha provisória.
- O Render continua como backup só para o **navegador** (failover do frontend).

### Cenário B: Heroku parado e uso só do Render

- Se o Heroku estiver **parado** (ex.: teste de failover), o Asaas e o Mercado Pago **não** vão conseguir chamar a URL do Heroku.
- Para a senha provisória continuar sendo enviada:
  1. Acesse o painel do **Asaas** e altere a URL do webhook para a URL do **Render** (tabela acima).
  2. Acesse o painel do **Mercado Pago** e altere a URL do webhook para a URL do **Render**.
  3. Faça um novo pagamento de teste (ou aguarde o próximo pagamento) para o webhook ser chamado no Render.
- Quando o Heroku voltar a ficar no ar, você pode voltar a configurar as URLs de webhook para o Heroku, se quiser.

### Cenário C: Não quero mudar URL no painel

- Mantenha o **Heroku ligado** (`web=1`) quando houver cobranças (boleto/PIX). Assim os webhooks continuam chegando no Heroku e a senha provisória segue sendo enviada sem alterar nada no Asaas nem no Mercado Pago.

---

## 4. Conferir se o webhook está sendo recebido

- **Heroku:**  
  `heroku logs --tail --app lwksistemas`  
  Procure por: `webhook`, `Pagamento confirmado`, `Senha provisória enviada`.

- **Render:**  
  Dashboard do Render → serviço **lwksistemas-backup-ewgo** → **Logs**.  
  Procure pelas mesmas mensagens.

Se aparecer “Pagamento confirmado para loja … Enviando senha provisória…” e em seguida “Senha provisória enviada para …”, o fluxo até o e-mail está ok. Se o webhook não aparecer nos logs, a URL configurada no Asaas/MP está errada ou o servidor dessa URL está fora do ar.

---

## 5. Resumo

- **Após o pagamento do boleto ou PIX**, o envio da senha provisória depende do **webhook** ser recebido pelo backend (Heroku ou Render).
- As URLs de webhook estão na **seção 2** (Heroku e Render).
- Use a URL do servidor que estiver **recebendo** as requisições (em geral Heroku; se só o Render estiver no ar, use a URL do Render nos painéis Asaas e Mercado Pago).
