# API de Assinatura - Documentação

## Visão Geral

Esta documentação descreve os endpoints da API relacionados ao fluxo de assinatura e pagamento de lojas.

## Base URL

```
https://seu-dominio.com/api
```

## Autenticação

Todos os endpoints requerem autenticação via JWT Token:

```
Authorization: Bearer <token>
```

## Endpoints

### 1. Criar Nova Loja

Cria uma nova loja no sistema com geração automática de boleto.

**Endpoint:** `POST /superadmin/lojas/`

**Permissões:** Apenas superadmin

**Request Body:**

```json
{
  "nome": "Minha Loja",
  "slug": "minha-loja",
  "descricao": "Descrição da loja",
  "cpf_cnpj": "12.345.678/0001-90",
  "cep": "12345-678",
  "logradouro": "Rua Exemplo",
  "numero": "123",
  "complemento": "Sala 1",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "uf": "SP",
  "tipo_loja": 1,
  "plano": 2,
  "tipo_assinatura": "mensal",
  "dia_vencimento": 10,
  "provedor_boleto_preferido": "asaas",
  "owner_full_name": "João Silva",
  "owner_username": "joao.silva",
  "owner_password": "SenhaProvisoria123!",
  "owner_email": "joao@example.com",
  "owner_telefone": "(11) 98765-4321"
}
```

**Response (200 OK):**

```json
{
  "id": 123,
  "nome": "Minha Loja",
  "slug": "minha-loja",
  "database_name": "loja_minha_loja",
  "login_page_url": "/loja/minha-loja/login",
  "boleto_url": "https://asaas.com/boleto/abc123",
  "pix_qr_code": "iVBORw0KGgoAAAANSUhEUgAA...",
  "pix_copy_paste": "00020126580014br.gov.bcb.pix...",
  "message": "Loja criada com sucesso. O boleto foi enviado para o email do administrador. A senha será enviada após confirmação do pagamento."
}
```

**Response (400 Bad Request):**

```json
{
  "nome": ["Este campo é obrigatório."],
  "cpf_cnpj": ["CPF/CNPJ inválido."],
  "owner_email": ["Email inválido."]
}
```

---

### 2. Obter Dados Financeiros da Loja

Retorna informações financeiras e de assinatura da loja.

**Endpoint:** `GET /superadmin/loja/{slug}/financeiro/`

**Permissões:** Owner da loja ou superadmin

**Response (200 OK):**

```json
{
  "loja": {
    "id": 123,
    "nome": "Minha Loja",
    "slug": "minha-loja",
    "plano": "Plano Premium",
    "tipo_assinatura": "mensal"
  },
  "financeiro": {
    "status_pagamento": "ativo",
    "valor_mensalidade": 99.90,
    "data_proxima_cobranca": "2026-03-10",
    "dia_vencimento": 10,
    "tem_asaas": true,
    "tem_mercadopago": false,
    "provedor_boleto": "asaas",
    "boleto_url": "https://asaas.com/boleto/abc123",
    "pix_qr_code": "iVBORw0KGgoAAAANSUhEUgAA...",
    "pix_copy_paste": "00020126580014br.gov.bcb.pix..."
  },
  "proximo_pagamento": {
    "id": 456,
    "valor": 99.90,
    "data_vencimento": "2026-03-10",
    "referencia_mes": "2026-03-01",
    "boleto_url": "https://asaas.com/boleto/abc123",
    "asaas_payment_id": "pay_123456"
  }
}
```

**Response (403 Forbidden):**

```json
{
  "error": "Sem permissão para ver assinatura. Apenas o responsável pela loja pode acessar."
}
```

---

### 3. Renovar Assinatura (Gerar Nova Cobrança)

Cria uma nova cobrança para renovação de assinatura.

**Endpoint:** `POST /superadmin/financeiro/{id}/renovar/`

**Permissões:** Owner da loja ou superadmin

**Request Body:**

```json
{
  "dia_vencimento": 10
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "payment_id": "pay_123456",
  "boleto_url": "https://asaas.com/boleto/abc123",
  "pix_qr_code": "iVBORw0KGgoAAAANSUhEUgAA...",
  "pix_copy_paste": "00020126580014br.gov.bcb.pix...",
  "due_date": "2026-03-10",
  "value": 99.90,
  "provedor": "asaas"
}
```

**Response (400 Bad Request):**

```json
{
  "success": false,
  "error": "Dados da loja incompletos. Verifique CPF/CNPJ e endereço."
}
```

**Response (500 Internal Server Error):**

```json
{
  "success": false,
  "error": "Erro ao criar cobrança no provedor: [detalhes do erro]"
}
```

---

### 4. Reenviar Senha Provisória

Reenvia a senha provisória por email (apenas se pagamento já confirmado).

**Endpoint:** `POST /superadmin/financeiro/{id}/reenviar-senha/`

**Permissões:** Apenas superadmin

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Senha reenviada para joao@example.com"
}
```

**Response (400 Bad Request):**

```json
{
  "success": false,
  "error": "Pagamento ainda não confirmado. Aguarde a confirmação do pagamento."
}
```

**Response (404 Not Found):**

```json
{
  "error": "FinanceiroLoja não encontrado."
}
```

---

### 5. Listar Emails com Falha

Lista emails que falharam no envio e estão aguardando retry.

**Endpoint:** `GET /superadmin/emails-retry/`

**Permissões:** Apenas superadmin

**Query Parameters:**

- `page` (opcional): Número da página (padrão: 1)
- `page_size` (opcional): Itens por página (padrão: 20)

**Response (200 OK):**

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "destinatario": "admin@loja.com",
      "assunto": "Acesso à sua loja Minha Loja - Senha Provisória",
      "tentativas": 2,
      "max_tentativas": 3,
      "enviado": false,
      "erro": "SMTP timeout after 30 seconds",
      "loja": "minha-loja",
      "created_at": "2026-02-25T10:30:00Z",
      "updated_at": "2026-02-25T10:40:00Z",
      "proxima_tentativa": "2026-02-25T10:45:00Z"
    },
    {
      "id": 2,
      "destinatario": "outro@loja.com",
      "assunto": "Acesso à sua loja Outra Loja - Senha Provisória",
      "tentativas": 1,
      "max_tentativas": 3,
      "enviado": false,
      "erro": "Connection refused",
      "loja": "outra-loja",
      "created_at": "2026-02-25T11:00:00Z",
      "updated_at": "2026-02-25T11:00:00Z",
      "proxima_tentativa": "2026-02-25T11:05:00Z"
    }
  ]
}
```

---

### 6. Reprocessar Email Falhado

Força o reprocessamento de um email que falhou.

**Endpoint:** `POST /superadmin/emails-retry/{id}/reprocessar/`

**Permissões:** Apenas superadmin

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Email reenviado com sucesso"
}
```

**Response (400 Bad Request):**

```json
{
  "success": false,
  "error": "Email já atingiu o número máximo de tentativas (3)"
}
```

**Response (500 Internal Server Error):**

```json
{
  "success": false,
  "error": "Erro ao reenviar email: SMTP timeout"
}
```

---

### 7. Atualizar Status Asaas

Força atualização do status de pagamento consultando a API do Asaas.

**Endpoint:** `POST /superadmin/loja-financeiro/{id}/atualizar_status_asaas/`

**Permissões:** Owner da loja ou superadmin

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Status atualizado com sucesso",
  "status_pagamento": "ativo"
}
```

**Response (400 Bad Request):**

```json
{
  "error": "Loja não possui integração com Asaas"
}
```

---

### 8. Baixar Boleto PDF

Baixa o boleto em formato PDF (Asaas) ou retorna link (Mercado Pago).

**Endpoint:** `GET /superadmin/loja-pagamentos/{id}/baixar_boleto_pdf/`

**Permissões:** Owner da loja ou superadmin

**Response (200 OK - Asaas):**

Retorna arquivo PDF para download.

**Response (200 OK - Mercado Pago):**

```json
{
  "boleto_url": "https://mercadopago.com.br/boleto/xyz789",
  "provedor": "mercadopago"
}
```

**Response (404 Not Found):**

```json
{
  "error": "Pagamento não encontrado"
}
```

---

## Webhooks

### Webhook Asaas

**Endpoint:** `POST /asaas/webhook/`

**Headers:**

```
Content-Type: application/json
asaas-access-token: <token>
```

**Request Body:**

```json
{
  "event": "PAYMENT_CONFIRMED",
  "payment": {
    "id": "pay_123456",
    "status": "CONFIRMED",
    "value": 99.90,
    "dueDate": "2026-03-10",
    "customer": "cus_123456"
  }
}
```

**Response (200 OK):**

```json
{
  "success": true
}
```

---

### Webhook Mercado Pago

**Endpoint:** `POST /mercadopago/webhook/`

**Headers:**

```
Content-Type: application/json
```

**Request Body:**

```json
{
  "action": "payment.updated",
  "data": {
    "id": "123456789"
  }
}
```

**Response (200 OK):**

```json
{
  "success": true
}
```

---

## Códigos de Status HTTP

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 201 | Criado com sucesso |
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Sem permissão |
| 404 | Não encontrado |
| 500 | Erro interno do servidor |

---

## Exemplos de Uso

### Criar Loja com cURL

```bash
curl -X POST https://seu-dominio.com/api/superadmin/lojas/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Minha Loja",
    "slug": "minha-loja",
    "cpf_cnpj": "12.345.678/0001-90",
    "tipo_loja": 1,
    "plano": 2,
    "tipo_assinatura": "mensal",
    "dia_vencimento": 10,
    "provedor_boleto_preferido": "asaas",
    "owner_full_name": "João Silva",
    "owner_username": "joao.silva",
    "owner_password": "SenhaProvisoria123!",
    "owner_email": "joao@example.com"
  }'
```

### Renovar Assinatura com JavaScript

```javascript
const renovarAssinatura = async (financeiroId) => {
  const response = await fetch(`/api/superadmin/financeiro/${financeiroId}/renovar/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      dia_vencimento: 10
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    console.log('Cobrança gerada:', data.boleto_url);
  } else {
    console.error('Erro:', data.error);
  }
};
```

### Listar Emails Falhados com Python

```python
import requests

url = "https://seu-dominio.com/api/superadmin/emails-retry/"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers)
data = response.json()

for email in data['results']:
    print(f"Email para {email['destinatario']}: {email['tentativas']}/{email['max_tentativas']} tentativas")
```

---

## Notas Importantes

1. **Senha Provisória**: Nunca é retornada pela API após a criação da loja. Apenas enviada por email após confirmação do pagamento.

2. **Webhooks**: Devem ser configurados nos painéis do Asaas e Mercado Pago apontando para os endpoints corretos.

3. **Rate Limiting**: A API possui rate limiting de 100 requisições por minuto por usuário.

4. **Timeout**: Requisições que demoram mais de 30 segundos retornam timeout.

5. **Retry**: Em caso de falha temporária (5xx), recomenda-se retry com backoff exponencial.

---

## Suporte

Para dúvidas ou problemas:

- Consulte [Fluxo de Assinatura](./FLUXO_ASSINATURA_PAGAMENTO.md)
- Consulte [Troubleshooting](./TROUBLESHOOTING_ASSINATURA.md)
- Entre em contato com o suporte técnico
