# Análise: Emitir Nota Fiscal e Enviar por Email ao Admin da Loja ao Pagar Boleto da Assinatura

## Objetivo

Quando a loja **paga o boleto da assinatura**, o sistema deve:
1. Solicitar à API do Asaas a **emissão da nota fiscal** vinculada à cobrança.
2. **Enviar por email ao admin da loja** (proprietário) a nota fiscal.

---

## Viabilidade: **Sim, é possível**

A API do Asaas permite:
- Emitir notas fiscais vinculadas a uma **cobrança (payment)**.
- Emissão automática para **assinaturas** (quando cada cobrança é paga).
- Webhooks para notificar quando a NF foi criada/autorizada.

O envio da NF por email pode ser:
- **Pelo Asaas:** se a conta tiver envio automático ao cliente (email do customer = dono da loja).
- **Pelo nosso sistema:** após a NF ser emitida, baixar o PDF (se a API expuser) e enviar por email via Django (SMTP) para o `loja.owner.email`.

---

## Situação atual do sistema

1. **Cobranças:** o sistema cria **payments** (cobranças avulsas) no Asaas via `AsaasPaymentService.create_loja_subscription_payment`, não usa o recurso **Subscriptions** da API Asaas.
2. **Webhook:** em `asaas_integration/views.py` o endpoint `asaas_webhook` processa `PAYMENT_CONFIRMED` e `PAYMENT_RECEIVED` e chama `AsaasSyncService.process_webhook_payment`, que:
   - Atualiza o status do pagamento.
   - Atualiza o financeiro da loja e desbloqueia se estiver bloqueada (`_update_loja_financeiro_from_payment`).
3. **Nota fiscal:** hoje não há nenhuma chamada à API de notas fiscais nem envio de email com NF.

---

## Caminhos para implementar

### Opção A – Emissão por cobrança (recomendada com o fluxo atual)

Quando o webhook receber **PAYMENT_CONFIRMED** ou **PAYMENT_RECEIVED**:

1. **Identificar a loja** pelo pagamento (já feito em `_update_loja_financeiro_from_payment`).
2. **Chamar a API Asaas:**
   - **Agendar a NF:** `POST /v3/invoices` com:
     - `payment`: ID da cobrança no Asaas (`payment_id` do webhook).
     - `serviceDescription`, `value`, `effectiveDate` (ex.: data de hoje).
     - `municipalServiceId` ou `municipalServiceCode` e `municipalServiceName` (conforme configuração municipal da **conta Asaas** da LWK).
     - `taxes`: retenções (ISS, PIS, etc.), se aplicável.
   - **Emitir a NF:** `POST /v3/invoices/{id}/authorize` (permite emissão imediata).
3. **Enviar por email ao admin da loja:**
   - Se a API Asaas tiver endpoint para **baixar PDF da NF** (ex.: `GET /v3/invoices/{id}/pdf` ou similar), usar esse PDF como anexo e enviar para `loja.owner.email` com Django (ex.: `send_mail` + anexo ou EmailMessage).
   - Alternativa: verificar no painel Asaas se há “enviar NF por email ao cliente”; nesse caso o Asaas pode enviar ao email do **customer** (que pode ser o mesmo do dono da loja). Ainda assim é útil ter o passo 1–2 para garantir que a NF seja emitida.

**Requisitos:**
- Conta Asaas (LWK) com **dados fiscais e configurações municipais** preenchidos.
- Permissão da API: **INVOICE:WRITE** (e INVOICE:READ se for baixar PDF).
- **Serviço municipal** definido (código/ID do serviço da prefeitura da LWK) para a descrição do plano (ex.: “Software sob demanda” / “Assinatura de sistema”).

---

### Opção B – Emissão automática por assinatura (Asaas)

Se no futuro o sistema passar a usar **Subscriptions** da API Asaas (um `subscription` por loja, com cobranças recorrentes geradas pelo Asaas):

1. Ao criar a subscription: `POST /v3/subscriptions/{id}/invoiceSettings` com `effectiveDatePeriod: "ON_PAYMENT_CONFIRMATION"`.
2. O Asaas passa a **gerar e emitir a NF automaticamente** quando cada cobrança for paga.
3. O envio por email ao admin pode continuar sendo:
   - pelo Asaas (se o customer for a loja e o email for o do dono), ou
   - pelo nosso sistema, consumindo o webhook de NF (ex.: `INVOICE_AUTHORIZED`) e, se houver endpoint, baixando o PDF e enviando para `loja.owner.email`.

Hoje o sistema **não** usa Subscriptions; usa apenas payments. Por isso a **Opção A** é a que se encaixa sem mudar o modelo de cobrança.

---

## Passos sugeridos para implementar (Opção A)

1. **Configuração no Asaas (conta LWK)**  
   - Completar dados fiscais e configurações municipais.  
   - Obter `municipalServiceId` (ou `municipalServiceCode`) e nome do serviço para “assinatura de software/sistema”.  
   - Garantir que a chave de API tenha permissão **INVOICE:WRITE** (e INVOICE:READ se for usar download de PDF).

2. **Backend – cliente Asaas (notas fiscais)**  
   - Em `asaas_integration/client.py` (ou novo módulo `invoice_service.py`):
     - Método para **agendar NF:** `POST /v3/invoices` com `payment`, descrição, valor, data efetiva, serviço municipal, impostos.
     - Método para **emitir NF:** `POST /v3/invoices/{id}/authorize`.
     - Se existir na documentação Asaas, método para **obter PDF da NF** (ex.: GET invoice by id e link do PDF, ou endpoint específico de download).

3. **Backend – webhook**  
   - Em `superadmin/sync_service.py`, dentro de `process_webhook_payment`, quando `new_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']`:
     - Após atualizar pagamento e financeiro da loja, chamar um novo serviço (ex.: `emitir_nf_e_enviar_email_para_loja(pagamento, loja)`).
   - Esse serviço:
     - Chama o cliente Asaas para agendar e autorizar a NF da cobrança.
     - Obtém o PDF da NF (se a API permitir).
     - Envia email para `loja.owner.email` com assunto tipo “Nota fiscal – Assinatura LWK Sistemas” e anexo PDF (ou link, se o Asaas enviar link por email e não houver PDF na API).

4. **Configuração de email (Django)**  
   - Configurar `EMAIL_BACKEND`, `EMAIL_HOST`, etc., para envio de emails (ex.: SMTP) e um email “from” adequado (ex.: `noreply@lwksistemas.com.br`).

5. **Tratamento de erros**  
   - Se a emissão da NF ou o envio do email falhar, registrar em log e, se desejado, gravar em uma tabela de “tarefas pendentes” para nova tentativa ou alerta ao suporte.

6. **Documentação Asaas**  
   - Confirmar na documentação oficial:
     - [Agendar nota fiscal](https://docs.asaas.com/reference/agendar-nota-fiscal)  
     - [Emitir uma nota fiscal](https://docs.asaas.com/reference/emitir-uma-nota-fiscal)  
     - Se existe endpoint para **download/PDF da nota fiscal** e qual é a URL.  
   - Se não houver PDF via API, manter pelo menos a emissão (passos 1–2) e combinar com envio automático ao cliente pelo próprio Asaas (se disponível na conta).

---

## Resumo

| Pergunta | Resposta |
|----------|----------|
| É possível emitir NF quando a loja paga o boleto? | **Sim**, via API Asaas (agendar + autorizar NF vinculada ao payment). |
| É possível enviar a NF por email ao admin da loja? | **Sim**, seja pelo Asaas (ao cliente/customer) ou pelo nosso sistema (enviando PDF por email ao `loja.owner.email`), desde que a API permita obter o PDF ou que o Asaas envie o email. |
| O que o sistema precisa fazer? | No webhook de pagamento confirmado: chamar API de NF (agendar + autorizar), depois enviar email ao admin da loja (com PDF se a API expuser). |
| Dependências | Conta Asaas com dados fiscais e municipal configurados, permissão INVOICE:WRITE, serviço municipal definido, envio de email configurado no Django. |

Com isso, quando a loja pagar o boleto da assinatura e o Asaas notificar o webhook, o sistema pode passar a emitir a nota fiscal na API do Asaas e enviar (ou garantir o envio) da nota fiscal por email ao admin da loja.

---

## Implementação realizada

1. **Cliente Asaas** (`backend/asaas_integration/client.py`):
   - `create_invoice()` – agenda NF (POST /v3/invoices) com payment, serviceDescription, value, effectiveDate e opcionais municipais.
   - `authorize_invoice(invoice_id)` – emite a NF (POST /v3/invoices/{id}/authorize).
   - `get_invoice(invoice_id)` – consulta NF (para link do PDF se a API retornar).

2. **Serviço de emissão** (`backend/asaas_integration/invoice_service.py`):
   - `emitir_nf_para_pagamento(asaas_payment_id, loja, value, description, send_email=True)`:
     - agenda e autoriza a NF no Asaas;
     - envia e-mail ao `loja.owner.email` com assunto "Nota Fiscal – Assinatura LWK Sistemas" e, se disponível, link da NF.

3. **Webhook** (`backend/superadmin/sync_service.py`):
   - Em `process_webhook_payment`, quando o evento é pagamento confirmado (`RECEIVED`, `CONFIRMED`, `RECEIVED_IN_CASH`), após atualizar financeiro da loja é chamado `emitir_nf_para_pagamento()` com os dados do webhook.

4. **Configuração** (`backend/config/settings.py` e `.env.example`):
   - `ASAAS_INVOICE_SERVICE_CODE`, `ASAAS_INVOICE_SERVICE_NAME`, `ASAAS_INVOICE_SERVICE_ID` (opcionais), conforme a prefeitura da conta LWK no Asaas.

**Requisitos para funcionar:**
- Chave da API Asaas com permissão **INVOICE:WRITE**.
- Conta Asaas (LWK) com dados fiscais e serviço municipal configurados na prefeitura.
- E-mail do Django configurado (`EMAIL_*`, `DEFAULT_FROM_EMAIL`) para envio ao admin da loja.
