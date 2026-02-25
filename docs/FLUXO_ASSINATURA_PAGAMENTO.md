# Fluxo de Assinatura e Pagamento

## Visão Geral

Este documento descreve o fluxo completo de assinatura e pagamento de lojas no sistema multi-loja. O fluxo garante que a senha provisória seja enviada apenas após a confirmação do pagamento, proporcionando maior segurança e controle sobre o acesso às lojas.

## Fluxo de Criação de Loja

### 1. Superadmin Cria Nova Loja

O superadministrador acessa o painel de gerenciamento de lojas e preenche o formulário de criação com:

- **Informações Básicas**: Nome, slug, CPF/CNPJ, descrição
- **Endereço**: CEP, logradouro, número, complemento, bairro, cidade, UF
- **Tipo de Loja**: Seleção do tipo (cabeleireiro, clínica de beleza, etc.)
- **Plano e Assinatura**: Plano, tipo de assinatura (mensal/anual), dia de vencimento
- **Provedor de Boleto**: Asaas ou Mercado Pago
- **Usuário Administrador**: Nome completo, username, email, telefone, senha provisória

### 2. Sistema Cria a Loja

Ao submeter o formulário, o sistema:

1. **Cria o usuário owner** com a senha provisória gerada
2. **Cria a loja** no banco de dados principal
3. **Cria o schema PostgreSQL isolado** para a loja
4. **Aplica migrations** no schema da loja
5. **Armazena a senha provisória** no campo `senha_provisoria` da loja
6. **Cria o registro FinanceiroLoja** com data da próxima cobrança

**IMPORTANTE**: Neste momento, a senha provisória **NÃO** é enviada por email.

### 3. Sistema Gera Boleto Automaticamente

Após a criação do FinanceiroLoja, um signal Django é disparado automaticamente:

1. **Signal `create_asaas_subscription_on_financeiro_creation`** é acionado
2. **CobrancaService** verifica o provedor de boleto preferido da loja
3. **Cria a cobrança** no provedor escolhido (Asaas ou Mercado Pago)
4. **Atualiza FinanceiroLoja** com:
   - `boleto_url`: URL do boleto
   - `pix_qr_code`: QR Code PIX em base64
   - `pix_copy_paste`: Código PIX copia e cola
   - `asaas_payment_id` ou `mercadopago_payment_id`: ID do pagamento no provedor

### 4. Resposta ao Superadmin

O sistema retorna ao superadmin:

- **Mensagem de sucesso** informando que a loja foi criada
- **Boleto e PIX** disponíveis para pagamento
- **Mensagem importante**: "A senha será enviada após confirmação do pagamento"
- **URL de acesso** da loja (para referência futura)

### 5. Cliente Efetua o Pagamento

O administrador da loja recebe o boleto/PIX e efetua o pagamento através do banco ou aplicativo de pagamento.

### 6. Webhook Confirma o Pagamento

Quando o pagamento é confirmado, o provedor (Asaas ou Mercado Pago) envia um webhook para o sistema:

**Asaas Webhook:**
- Evento: `PAYMENT_CONFIRMED`
- Sistema busca FinanceiroLoja pelo `asaas_payment_id`
- Atualiza `status_pagamento` para `'ativo'`

**Mercado Pago Webhook:**
- Evento: `payment.updated`
- Sistema consulta API do Mercado Pago para obter status
- Se status = `'approved'`, atualiza `status_pagamento` para `'ativo'`

### 7. Sistema Envia Senha Provisória

Quando o `status_pagamento` muda para `'ativo'`, outro signal é disparado:

1. **Signal `on_payment_confirmed`** é acionado
2. **EmailService** recupera a senha provisória da loja
3. **Envia email** para o administrador com:
   - Senha provisória
   - URL de login da loja
   - Informações da loja (nome, tipo, plano)
   - Próximos passos (login, troca de senha, configuração)
4. **Atualiza FinanceiroLoja**:
   - `senha_enviada = True`
   - `data_envio_senha = timezone.now()`

### 8. Administrador Acessa a Loja

O administrador da loja:

1. Recebe o email com a senha provisória
2. Acessa a URL de login da loja
3. Faz login com username e senha provisória
4. É redirecionado para trocar a senha
5. Começa a configurar sua loja

## Fluxo de Renovação de Assinatura

### 1. Administrador Acessa Dashboard de Assinatura

O administrador da loja acessa a página de assinatura (`/loja/{slug}/assinatura`) e visualiza:

- **Status atual** da assinatura (ativo, pendente, atrasado, bloqueado)
- **Valor da mensalidade**
- **Data do próximo vencimento**
- **Dia de vencimento** configurado
- **Boleto/PIX atual** (se disponível)

### 2. Administrador Gera Nova Cobrança

O administrador clica no botão **"Gerar Nova Cobrança"**:

1. Sistema chama endpoint `POST /api/superadmin/financeiro/{id}/renovar/`
2. **CobrancaService** cria nova cobrança no provedor
3. Sistema retorna:
   - `boleto_url`: URL do novo boleto
   - `pix_qr_code`: QR Code PIX
   - `pix_copy_paste`: Código PIX
   - `due_date`: Data de vencimento
   - `value`: Valor da cobrança

### 3. Modal Exibe Boleto/PIX

Um modal é exibido com:

- **Mensagem de sucesso**
- **Tabs** para escolher entre Boleto e PIX
- **Botão** para abrir boleto em nova aba
- **QR Code PIX** para escanear
- **Código PIX** para copiar e colar

### 4. Administrador Efetua o Pagamento

O administrador:

1. Escolhe a forma de pagamento (boleto ou PIX)
2. Efetua o pagamento
3. Aguarda confirmação (geralmente instantânea para PIX)

### 5. Webhook Confirma Renovação

O webhook do provedor confirma o pagamento e o sistema:

1. Atualiza `status_pagamento` para `'ativo'`
2. Atualiza `data_proxima_cobranca` para o próximo mês
3. Mantém a loja ativa e acessível

## Tratamento de Falhas

### Falha no Envio de Email

Se o envio de email falhar:

1. Sistema registra tentativa no modelo **EmailRetry**
2. Sistema agenda **retry automático** após 5 minutos
3. Sistema tenta até **3 vezes**
4. Se todas as tentativas falharem, superadmin é notificado via log

### Falha na Criação de Cobrança

Se a criação de cobrança falhar:

1. Sistema registra erro no log
2. Loja é criada normalmente (sem interrupção)
3. Superadmin pode gerar cobrança manualmente depois

### Pagamento Não Confirmado

Se o pagamento não for confirmado:

1. Após **7 dias**, status muda para `'atrasado'`
2. Após **30 dias**, status muda para `'bloqueado'`
3. Loja bloqueada impede login de usuários

## Automação via Django-Q

### Task: Reprocessar Emails Falhados

- **Frequência**: A cada 5 minutos
- **Comando**: `reprocessar_emails_falhados`
- **Função**: Tenta reenviar emails que falharam

### Task: Verificar Status de Assinaturas

- **Frequência**: Diariamente às 00:00
- **Comando**: `verificar_status_assinaturas`
- **Função**: Atualiza status de assinaturas vencidas

## Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. Superadmin Cria Loja                       │
│  - Preenche formulário                                           │
│  - Escolhe provedor de boleto (Asaas ou Mercado Pago)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. Sistema Cria Loja                          │
│  - Cria usuário owner                                            │
│  - Cria loja e schema PostgreSQL                                 │
│  - Armazena senha provisória (NÃO envia email)                   │
│  - Cria FinanceiroLoja                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. Signal Gera Boleto                         │
│  - CobrancaService cria cobrança no provedor                     │
│  - Atualiza FinanceiroLoja com boleto_url e pix_qr_code          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. Resposta ao Superadmin                     │
│  - Exibe boleto e PIX                                            │
│  - Mensagem: "Senha será enviada após pagamento"                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5. Cliente Paga Boleto/PIX                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    6. Webhook Confirma Pagamento                 │
│  - Provedor envia webhook                                        │
│  - Sistema atualiza status_pagamento para 'ativo'                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    7. Signal Envia Senha                         │
│  - EmailService envia senha provisória                           │
│  - Atualiza senha_enviada = True                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    8. Administrador Acessa Loja                  │
│  - Faz login com senha provisória                                │
│  - Troca senha                                                   │
│  - Configura loja                                                │
└──────────────────────────────────────────────────────────────────┘
```

## Status de Assinatura

| Status | Descrição | Ação do Sistema |
|--------|-----------|-----------------|
| **ativo** | Pagamento confirmado, loja ativa | Permite acesso normal |
| **pendente** | Aguardando pagamento | Permite acesso, mas exibe aviso |
| **atrasado** | Vencido há mais de 7 dias | Exibe aviso de atraso |
| **bloqueado** | Vencido há mais de 30 dias | Bloqueia login de usuários |

## Provedores de Pagamento

### Asaas

- **Boleto**: PDF para download
- **PIX**: QR Code e código copia e cola
- **Webhook**: `PAYMENT_CONFIRMED`

### Mercado Pago

- **Boleto**: Link para abrir em nova aba
- **PIX**: QR Code e código copia e cola
- **Webhook**: `payment.updated` com status `approved`

## Logs e Auditoria

Todos os eventos importantes são registrados no log:

- Criação de loja
- Criação de cobrança
- Confirmação de pagamento
- Envio de senha
- Falhas e erros

Formato do log:
```
[TIMESTAMP] [LEVEL] [loja_slug] [provedor] Mensagem
```

Exemplo:
```
2026-02-25 10:30:00 INFO minha-loja asaas ✅ Cobrança criada com sucesso (payment_id: pay_123456)
2026-02-25 10:35:00 INFO minha-loja asaas ✅ Pagamento confirmado via webhook
2026-02-25 10:35:05 INFO minha-loja - ✅ Senha enviada para admin@loja.com
```

## Próximos Passos

Após a implementação deste fluxo, considere:

1. **Notificações por SMS**: Enviar SMS além de email
2. **Dashboard de Métricas**: Visualizar taxa de conversão de pagamentos
3. **Renovação Automática**: Gerar cobrança automaticamente antes do vencimento
4. **Descontos e Promoções**: Sistema de cupons de desconto
5. **Múltiplos Planos**: Permitir upgrade/downgrade de planos

## Suporte

Para dúvidas ou problemas, consulte:

- [API de Assinatura](./API_ASSINATURA.md)
- [Troubleshooting](./TROUBLESHOOTING_ASSINATURA.md)
- [Configurar Django-Q](./CONFIGURAR_DJANGO_Q.md)
