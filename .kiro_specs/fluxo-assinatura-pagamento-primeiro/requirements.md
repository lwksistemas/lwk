# Requirements Document

## Introduction

Este documento especifica os requisitos para implementar o fluxo correto de assinatura e pagamento de lojas no sistema multi-loja. O fluxo atual envia a senha provisória antes da confirmação do pagamento, o que não está alinhado com as práticas de negócio desejadas. O novo fluxo garante que:

1. O boleto seja criado primeiro ao criar a loja
2. O sistema aguarde a confirmação do pagamento via webhook
3. A senha provisória seja enviada apenas após confirmação do pagamento
4. A renovação de assinatura no dashboard siga o mesmo fluxo unificado para Asaas e Mercado Pago

## Glossary

- **Sistema**: O sistema multi-loja completo (backend Django + frontend React)
- **Loja**: Uma instância de loja criada no sistema com schema PostgreSQL isolado
- **FinanceiroLoja**: Modelo Django que armazena dados financeiros da loja (mensalidade, vencimento, status)
- **Provedor_Pagamento**: Serviço de pagamento (Asaas ou Mercado Pago) escolhido pela loja
- **Boleto**: Cobrança gerada pelo provedor de pagamento para a loja
- **Senha_Provisoria**: Senha temporária gerada automaticamente para o administrador da loja
- **Webhook**: Notificação HTTP enviada pelo provedor de pagamento quando o status do pagamento muda
- **Signal**: Mecanismo Django que dispara automaticamente quando um modelo é criado/atualizado
- **LojaCreateSerializer**: Serializer Django REST Framework responsável pela criação de lojas
- **Dashboard_Assinatura**: Seção do dashboard da loja onde o administrador gerencia sua assinatura

## Requirements

### Requirement 1: Criação de Loja sem Envio Imediato de Senha

**User Story:** Como superadministrador, eu quero que a senha provisória não seja enviada imediatamente ao criar uma loja, para que o acesso só seja liberado após confirmação do pagamento.

#### Acceptance Criteria

1. WHEN LojaCreateSerializer.create() é executado, THE Sistema SHALL criar a loja no banco de dados
2. WHEN LojaCreateSerializer.create() é executado, THE Sistema SHALL criar o schema PostgreSQL isolado
3. WHEN LojaCreateSerializer.create() é executado, THE Sistema SHALL aplicar migrations no schema da loja
4. WHEN LojaCreateSerializer.create() é executado, THE Sistema SHALL criar o usuário owner com senha provisória
5. WHEN LojaCreateSerializer.create() é executado, THE Sistema SHALL armazenar a senha provisória no campo senha_provisoria da Loja
6. WHEN LojaCreateSerializer.create() é executado, THE Sistema SHALL NOT enviar email com senha provisória
7. WHEN LojaCreateSerializer.create() é executado, THE Sistema SHALL criar FinanceiroLoja com data_proxima_cobranca
8. WHEN LojaCreateSerializer.create() é executado, THE Sistema SHALL retornar sucesso com dados da loja criada

### Requirement 2: Criação Automática de Boleto na Criação da Loja

**User Story:** Como superadministrador, eu quero que o boleto seja criado automaticamente ao criar uma loja, para que o administrador da loja possa efetuar o pagamento imediatamente.

#### Acceptance Criteria

1. WHEN FinanceiroLoja é criado, THE Signal create_asaas_subscription_on_financeiro_creation SHALL ser disparado
2. WHEN Signal é disparado, THE Sistema SHALL verificar o campo provedor_boleto_preferido da Loja
3. WHERE provedor_boleto_preferido é 'asaas', THE Sistema SHALL criar cobrança no Asaas
4. WHERE provedor_boleto_preferido é 'mercadopago', THE Sistema SHALL criar cobrança no Mercado Pago
5. WHEN cobrança é criada com sucesso, THE Sistema SHALL atualizar FinanceiroLoja com boleto_url e pix_qr_code
6. WHEN cobrança é criada com sucesso, THE Sistema SHALL criar registro de PagamentoLoja com status 'pendente'
7. IF criação de cobrança falhar, THEN THE Sistema SHALL registrar erro no log sem interromper criação da loja

### Requirement 3: Webhook de Confirmação de Pagamento

**User Story:** Como sistema, eu quero receber notificações de pagamento dos provedores, para que eu possa atualizar o status da assinatura automaticamente.

#### Acceptance Criteria

1. WHEN webhook do Asaas é recebido com status 'CONFIRMED', THE Sistema SHALL identificar o pagamento pelo asaas_payment_id
2. WHEN webhook do Mercado Pago é recebido com status 'approved', THE Sistema SHALL identificar o pagamento pelo mercadopago_payment_id
3. WHEN pagamento é identificado, THE Sistema SHALL atualizar status_pagamento do FinanceiroLoja para 'ativo'
4. WHEN pagamento é identificado, THE Sistema SHALL atualizar status do PagamentoLoja para 'pago'
5. WHEN pagamento é identificado, THE Sistema SHALL registrar data_pagamento no PagamentoLoja
6. WHEN status é atualizado para 'ativo', THE Sistema SHALL disparar envio de senha provisória
7. IF pagamento não for identificado, THEN THE Sistema SHALL registrar erro no log e retornar HTTP 400

### Requirement 4: Envio de Senha Provisória Após Confirmação de Pagamento

**User Story:** Como administrador de loja, eu quero receber minha senha provisória apenas após o pagamento ser confirmado, para que eu possa acessar o sistema imediatamente após pagar.

#### Acceptance Criteria

1. WHEN status_pagamento do FinanceiroLoja muda para 'ativo', THE Sistema SHALL recuperar senha_provisoria da Loja
2. WHEN senha_provisoria é recuperada, THE Sistema SHALL recuperar email do owner da Loja
3. WHEN email é recuperado, THE Sistema SHALL enviar email com senha provisória e URL de login
4. WHEN email é enviado, THE Sistema SHALL incluir dados de acesso (usuário e senha)
5. WHEN email é enviado, THE Sistema SHALL incluir informações da loja (nome, tipo, plano)
6. WHEN email é enviado, THE Sistema SHALL incluir próximos passos (login, troca de senha, configuração)
7. IF envio de email falhar, THEN THE Sistema SHALL registrar erro no log e tentar reenvio após 5 minutos
8. WHEN email é enviado com sucesso, THE Sistema SHALL registrar data_envio_senha no FinanceiroLoja

### Requirement 5: Renovação de Assinatura no Dashboard

**User Story:** Como administrador de loja, eu quero renovar minha assinatura diretamente no dashboard, para que eu possa manter minha loja ativa sem intervenção do superadmin.

#### Acceptance Criteria

1. WHEN administrador acessa Dashboard_Assinatura, THE Sistema SHALL exibir status atual da assinatura
2. WHEN administrador acessa Dashboard_Assinatura, THE Sistema SHALL exibir data do próximo vencimento
3. WHEN administrador acessa Dashboard_Assinatura, THE Sistema SHALL exibir valor da mensalidade
4. WHEN administrador acessa Dashboard_Assinatura, THE Sistema SHALL exibir botão "Gerar Nova Cobrança"
5. WHEN administrador clica em "Gerar Nova Cobrança", THE Sistema SHALL verificar provedor_boleto_preferido
6. WHERE provedor_boleto_preferido é 'asaas', THE Sistema SHALL criar nova cobrança no Asaas
7. WHERE provedor_boleto_preferido é 'mercadopago', THE Sistema SHALL criar nova cobrança no Mercado Pago
8. WHEN nova cobrança é criada, THE Sistema SHALL exibir boleto_url e pix_qr_code
9. WHEN nova cobrança é criada, THE Sistema SHALL atualizar data_proxima_cobranca no FinanceiroLoja
10. IF criação de cobrança falhar, THEN THE Sistema SHALL exibir mensagem de erro ao administrador

### Requirement 6: Unificação de Lógica de Cobrança

**User Story:** Como desenvolvedor, eu quero que a lógica de criação de cobrança seja unificada entre Asaas e Mercado Pago, para que o código seja mais fácil de manter e testar.

#### Acceptance Criteria

1. THE Sistema SHALL ter um serviço unificado CobrancaService para criação de cobranças
2. WHEN CobrancaService.criar_cobranca() é chamado, THE Sistema SHALL receber loja e financeiro como parâmetros
3. WHEN CobrancaService.criar_cobranca() é chamado, THE Sistema SHALL verificar provedor_boleto_preferido
4. WHERE provedor_boleto_preferido é 'asaas', THE Sistema SHALL delegar para AsaasPaymentService
5. WHERE provedor_boleto_preferido é 'mercadopago', THE Sistema SHALL delegar para LojaMercadoPagoService
6. WHEN cobrança é criada com sucesso, THE Sistema SHALL retornar dict com success, payment_id, boleto_url, pix_qr_code
7. IF criação falhar, THEN THE Sistema SHALL retornar dict com success=False e error
8. THE Sistema SHALL usar CobrancaService tanto na criação de loja quanto na renovação

### Requirement 7: Tratamento de Falhas no Envio de Email

**User Story:** Como sistema, eu quero ter um mecanismo de retry para envio de emails, para que falhas temporárias não impeçam o administrador de receber sua senha.

#### Acceptance Criteria

1. WHEN envio de email falhar, THE Sistema SHALL registrar tentativa no modelo EmailRetry
2. WHEN EmailRetry é criado, THE Sistema SHALL armazenar destinatário, assunto, mensagem e tentativas
3. WHILE tentativas é menor que 3, THE Sistema SHALL tentar reenviar email após 5 minutos
4. WHEN email é enviado com sucesso, THE Sistema SHALL marcar EmailRetry como enviado
5. IF tentativas atingir 3 sem sucesso, THEN THE Sistema SHALL marcar EmailRetry como falhou
6. IF tentativas atingir 3 sem sucesso, THEN THE Sistema SHALL notificar superadmin via log
7. THE Sistema SHALL ter comando Django management para reprocessar emails falhados

### Requirement 8: Validação de Dados de Pagamento

**User Story:** Como sistema, eu quero validar os dados necessários antes de criar uma cobrança, para que erros sejam detectados antes de chamar a API do provedor.

#### Acceptance Criteria

1. WHEN CobrancaService.criar_cobranca() é chamado, THE Sistema SHALL validar que loja.cpf_cnpj não é vazio
2. WHEN CobrancaService.criar_cobranca() é chamado, THE Sistema SHALL validar que loja.owner.email não é vazio
3. WHERE provedor_boleto_preferido é 'mercadopago', THE Sistema SHALL validar que loja.cep não é vazio
4. WHERE provedor_boleto_preferido é 'mercadopago', THE Sistema SHALL validar que loja.logradouro não é vazio
5. WHERE provedor_boleto_preferido é 'mercadopago', THE Sistema SHALL validar que loja.cidade não é vazio
6. WHERE provedor_boleto_preferido é 'mercadopago', THE Sistema SHALL validar que loja.uf não é vazio
7. IF validação falhar, THEN THE Sistema SHALL retornar erro descritivo sem chamar API do provedor
8. WHEN validação passar, THE Sistema SHALL prosseguir com criação da cobrança

### Requirement 9: Atualização de Status de Assinatura

**User Story:** Como sistema, eu quero atualizar automaticamente o status da assinatura baseado no pagamento, para que lojas inadimplentes sejam bloqueadas e lojas pagas sejam ativadas.

#### Acceptance Criteria

1. WHEN pagamento é confirmado via webhook, THE Sistema SHALL atualizar status_pagamento para 'ativo'
2. WHEN data_proxima_cobranca é atingida sem pagamento, THE Sistema SHALL atualizar status_pagamento para 'pendente'
3. WHEN status_pagamento é 'pendente' por mais de 7 dias, THE Sistema SHALL atualizar status_pagamento para 'atrasado'
4. WHEN status_pagamento é 'atrasado' por mais de 30 dias, THE Sistema SHALL atualizar status_pagamento para 'bloqueado'
5. WHILE status_pagamento é 'bloqueado', THE Sistema SHALL impedir login de usuários da loja
6. WHEN pagamento atrasado é confirmado, THE Sistema SHALL atualizar status_pagamento para 'ativo'
7. THE Sistema SHALL ter task agendada Django-Q para verificar status diariamente

### Requirement 10: Logging e Auditoria de Pagamentos

**User Story:** Como superadministrador, eu quero ter logs detalhados de todas as operações de pagamento, para que eu possa auditar e debugar problemas.

#### Acceptance Criteria

1. WHEN cobrança é criada, THE Sistema SHALL registrar log com loja, provedor, valor e payment_id
2. WHEN webhook é recebido, THE Sistema SHALL registrar log com provedor, payment_id e status
3. WHEN email de senha é enviado, THE Sistema SHALL registrar log com destinatário e timestamp
4. WHEN erro ocorrer em qualquer operação, THE Sistema SHALL registrar log com stack trace completo
5. THE Sistema SHALL incluir loja_slug em todos os logs para facilitar busca
6. THE Sistema SHALL incluir provedor_boleto em todos os logs de pagamento
7. THE Sistema SHALL ter endpoint de API para superadmin consultar logs de pagamento por loja
8. THE Sistema SHALL manter logs de pagamento por no mínimo 12 meses

