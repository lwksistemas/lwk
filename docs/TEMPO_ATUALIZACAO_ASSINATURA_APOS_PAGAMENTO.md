# Tempo para atualizar/liberar a loja após pagamento do boleto

## Resumo

| Etapa | Mercado Pago | Asaas |
|-------|--------------|--------|
| **1. Cliente paga o boleto no banco** | Igual (depende do cliente) | Igual |
| **2. Provedor confirma o pagamento** | Minutos a poucas horas* | Minutos a 1–2 dias úteis* |
| **3. Provedor envia webhook para nosso sistema** | Segundos após confirmar | Segundos após confirmar |
| **4. Nosso sistema processa e libera a loja** | **Segundos** | **Segundos** |

\* A confirmação do boleto depende do banco e da política de cada provedor; não controlamos esse tempo.

---

## Como o sistema atualiza a assinatura

### Mercado Pago

- **Mecanismo:** **webhook** + **sync periódico** (opcional, no servidor).
- **URL do webhook:** `https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/`
- **Evento:** `payment` (quando o status do pagamento muda).
- **Fluxo principal:** Cliente paga → MP confirma (status `approved`) → MP envia POST no webhook → backend atualiza `FinanceiroLoja`, `PagamentoLoja` e desbloqueia a loja (segundos).
- **Sync em tempo real no servidor (como Asaas):** execute no Heroku o comando `sync_mercadopago_auto` de tempos em tempos (ex.: a cada 10 min via Heroku Scheduler). O comando consulta a API do MP para todos os pagamentos pendentes e atualiza quem estiver aprovado. Veja a seção *Sincronização periódica no Heroku* abaixo.

### Asaas

- **Mecanismo:** **webhook** + **sync periódico** (comando `sync_asaas_auto` pode ser agendado no Heroku Scheduler para atualização em tempo real no servidor).
- **URL do webhook:** configurada no painel Asaas (deve apontar para o endpoint de webhook do backend).
- **Eventos:** `PAYMENT_CONFIRMED`, `PAYMENT_RECEIVED`, `PAYMENT_UPDATED`, `PAYMENT_CREATED`.
- **Fluxo:** Cliente paga → Asaas confirma → webhook → backend atualiza e desbloqueia (segundos). Opcionalmente, o sync periódico no servidor consulta a API do Asaas e atualiza pagamentos pendentes.

---

## Diferença de tempo entre as duas APIs

- **No nosso sistema:** **não há diferença relevante.** As duas integrações são acionadas por webhook e, ao receber o POST, o backend atualiza e libera a loja em segundos.
- **A diferença que o usuário pode sentir** vem do **tempo que cada provedor leva para confirmar o boleto** (etapa 2):
  - **Mercado Pago:** costuma notificar em minutos a poucas horas após o pagamento, dependendo do banco.
  - **Asaas:** pode variar de minutos a até 1–2 dias úteis, conforme o banco e a data/hora do pagamento.

Ou seja: quem define o atraso é a confirmação do pagamento pelo **Mercado Pago ou pelo Asaas**; depois que o webhook é enviado, nossa atualização é rápida nas duas APIs.

---

## O que conferir se a loja não liberar

1. **Webhook configurado**
   - **Mercado Pago:** em [Suas integrações → Webhooks](https://www.mercadopago.com.br/developers/panel/app), URL do webhook e evento `payment`.
   - **Asaas:** no painel Asaas, URL do webhook apontando para o endpoint de webhook do backend.

2. **Logs no Heroku**
   - Procurar por `Webhook MP` / `Webhook Asaas recebido` e por erros ao processar o pagamento.

3. **Sincronização manual ou periódica (Asaas e Mercado Pago)**
   - **Asaas:** `cd backend && python manage.py sync_asaas_auto` (ou `--loja SLUG` para uma loja).
   - **Mercado Pago:** `cd backend && python manage.py sync_mercadopago_auto` (ou `--loja SLUG`).
   - Para **atualização em tempo real no servidor** (como o Asaas), agende esses comandos no **Heroku Scheduler** (ex.: a cada 10 minutos). Veja a seção abaixo.

---

## Sincronização periódica no Heroku (tempo real no servidor)

Para que o **Mercado Pago** (e o Asaas) atualizem no servidor mesmo se o webhook atrasar ou falhar, agende os comandos de sync no **Heroku Scheduler**:

1. No [Dashboard Heroku](https://dashboard.heroku.com/) → app **lwksistemas** → aba **Resources**.
2. Adicione o add-on **Heroku Scheduler** (se ainda não tiver).
3. Abra o Scheduler e crie **jobs**:

| Provedor      | Comando no Scheduler                          | Frequência sugerida   |
|---------------|------------------------------------------------|------------------------|
| **Asaas**     | `cd backend && python manage.py sync_asaas_auto`     | A cada 10 min ou 1 h   |
| **Mercado Pago** | `cd backend && python manage.py sync_mercadopago_auto` | A cada 10 min ou 1 h   |

Assim, o servidor consulta a API de cada provedor periodicamente e atualiza pagamentos pendentes que já foram aprovados, mantendo o comportamento em tempo real igual ao do Asaas.

---

## Como testar se o webhook Mercado Pago está funcionando

### 1. Testar se a URL está acessível (GET)

Abra no navegador ou use curl:

```
https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/
```

Se estiver tudo certo, a resposta será **200** e um JSON como:

```json
{
  "status": "ok",
  "message": "Endpoint do webhook Mercado Pago ativo.",
  "url": "https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/",
  "test": "Envie POST com JSON: {\"type\": \"payment\", \"data\": {\"id\": \"<payment_id>\"}}. ..."
}
```

Isso confirma que o endpoint existe e está respondendo.

### 2. Testar a confirmação de pagamento (POST com payment_id real)

Quando existe um boleto gerado pelo sistema (loja com Mercado Pago), você pode simular a notificação que o MP enviaria quando o pagamento for aprovado.

**Opção A – Usar um payment_id real (de uma cobrança de teste):**

1. Crie uma loja de teste com provedor Mercado Pago e anote o `mercadopago_payment_id` do `FinanceiroLoja` ou do `PagamentoLoja` (no admin ou no banco).
2. Envie um POST para o webhook com esse ID:

```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/ \
  -H "Content-Type: application/json" \
  -d '{"type": "payment", "data": {"id": "123456789"}}'
```

Substitua `123456789` pelo ID real do pagamento no Mercado Pago.

- Se o pagamento estiver **approved** na API do MP, o sistema atualiza a assinatura e retorna algo como:  
  `{"status": "processed", "payment_id": "...", "loja_slug": "..."}`.
- Se o pagamento ainda não estiver aprovado no MP, a resposta será `{"status": "ok", "processed": false}` (o webhook foi recebido, mas o status no MP não é approved).
- Se o ID não existir no MP ou não estiver vinculado a nenhuma loja, ainda assim o endpoint responde **200** (para o MP não reenviar o webhook).

**Opção B – Teste rápido só do endpoint (qualquer ID):**

```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/mercadopago-webhook/ \
  -H "Content-Type: application/json" \
  -d '{"type": "payment", "data": {"id": "999999999"}}'
```

Resposta esperada: **200** e `{"status": "ok", "processed": false}` (prova que o POST foi aceito e processado; o “processed: false” é esperado com um ID inexistente).

### 3. Conferir nos logs (Heroku)

Após enviar o POST, ver os logs do app:

```bash
heroku logs --tail -a lwksistemas
```

Procure por mensagens como:

- `Webhook MP pagamento <id> status=...`
- `Financeiro da loja ... atualizado via webhook MP`
- Ou erros de configuração (token, pagamento não encontrado, etc.).
