# Implementation Plan: Fluxo Assinatura Pagamento Primeiro

## Overview

Implementar novo fluxo onde a senha provisória só é enviada após confirmação do pagamento da assinatura. O sistema inclui retry automático de emails, unificação de lógica de cobrança com Strategy Pattern, e automação via Django-Q.

## Tasks

- [x] 1. Criar modelo EmailRetry e migrations
  - Criar modelo Django para armazenar emails falhados e gerenciar sistema de retry automático
  - Modelo EmailRetry em backend/superadmin/models.py com campos: destinatario, assunto, mensagem, tentativas, max_tentativas, enviado, erro, loja, created_at, updated_at, proxima_tentativa
  - Migration criada e testada
  - Admin Django configurado para visualizar EmailRetry
  - _Requirements: Sistema de retry automático para emails_

- [x] 2. Adicionar campos em FinanceiroLoja
  - Adicionar campo data_envio_senha (DateTimeField, null=True)
  - Adicionar campo senha_enviada (BooleanField, default=False)
  - Migration criada e testada
  - Campos aparecem no admin Django
  - _Requirements: Rastreamento de envio de senha provisória_

- [x] 3. Criar CobrancaService com Strategy Pattern
  - [x] 3.1 Criar estrutura base do CobrancaService
    - Criar arquivo backend/superadmin/cobranca_service.py
    - Implementar classe CobrancaService com métodos criar_cobranca() e renovar_cobranca()
    - Implementar método _validar_dados_loja()
    - _Requirements: Unificação de lógica de cobrança_
  
  - [x] 3.2 Implementar AsaasPaymentStrategy
    - Criar strategy para integração com Asaas
    - _Requirements: Suporte a gateway Asaas_
  
  - [x] 3.3 Implementar MercadoPagoPaymentStrategy
    - Criar strategy para integração com Mercado Pago
    - _Requirements: Suporte a gateway Mercado Pago_
  
  - [ ]* 3.4 Criar testes unitários para CobrancaService
    - Criar backend/superadmin/tests/test_cobranca_service.py
    - Testar ambas as strategies

- [x] 4. Criar EmailService
  - [x] 4.1 Implementar EmailService
    - Criar arquivo backend/superadmin/email_service.py
    - Implementar métodos: enviar_senha_provisoria(), reenviar_email(), _criar_mensagem_senha(), _registrar_retry()
    - _Requirements: Envio de senha após confirmação de pagamento_
  
  - [ ]* 4.2 Criar testes unitários para EmailService
    - Criar backend/superadmin/tests/test_email_service.py

- [x] 5. Modificar LojaCreateSerializer
  - Remover bloco de envio de email do método create() (linhas ~680)
  - Manter geração e salvamento de senha provisória em loja.senha_provisoria
  - Atualizar mensagem de retorno informando que senha será enviada após pagamento
  - _Requirements: Senha enviada apenas após pagamento confirmado_

- [x] 6. Checkpoint - Validar estrutura base
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Modificar signal create_asaas_subscription_on_financeiro_creation
  - Adicionar import de CobrancaService
  - Substituir lógica antiga por service.criar_cobranca()
  - Atualizar logs
  - Remover envio de senha provisória
  - _Requirements: Unificação de lógica de cobrança_

- [x] 8. Criar signal on_payment_confirmed
  - Criar signal que dispara quando status_pagamento muda para 'ativo'
  - Verificar se senha já foi enviada (senha_enviada=False)
  - Chamar EmailService.enviar_senha_provisoria()
  - Adicionar logs detalhados
  - Criar em backend/superadmin/signals.py
  - _Requirements: Envio automático de senha após confirmação_

- [x] 9. Modificar webhook do Asaas
  - [x] 9.1 Atualizar handler de webhook
    - Buscar FinanceiroLoja por asaas_payment_id
    - Atualizar status_pagamento para 'ativo' quando PAYMENT_CONFIRMED
    - Signal on_payment_confirmed é disparado automaticamente
    - Adicionar logs detalhados e tratamento de erros robusto
    - _Requirements: Integração com webhook Asaas_
  
  - [ ]* 9.2 Criar testes para webhook Asaas
    - Criar backend/asaas_integration/tests/test_webhooks.py

- [x] 10. Modificar webhook do Mercado Pago
  - [x] 10.1 Atualizar handler de webhook
    - Buscar FinanceiroLoja por mercadopago_payment_id
    - Consultar API do MP para obter status atualizado
    - Atualizar status_pagamento para 'ativo' quando status='approved'
    - Signal on_payment_confirmed é disparado automaticamente
    - Adicionar logs detalhados e tratamento de erros robusto
    - Modificar backend/superadmin/views.py (função mercadopago_webhook)
    - _Requirements: Integração com webhook Mercado Pago_
  
  - [ ]* 10.2 Criar testes para webhook Mercado Pago
    - Criar backend/superadmin/tests/test_webhooks.py

- [x] 11. Checkpoint - Validar fluxo de pagamento
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Criar endpoint POST /financeiro/{id}/renovar/
  - [x] 12.1 Implementar action renovar em FinanceiroLojaViewSet
    - Receber dia_vencimento opcional
    - Chamar CobrancaService.renovar_cobranca()
    - Retornar boleto_url, pix_qr_code, payment_id
    - Configurar permissões: apenas owner da loja ou superadmin
    - Modificar backend/superadmin/views.py
    - _Requirements: Renovação de assinatura pelo dashboard_
  
  - [ ]* 12.2 Criar testes para endpoint renovar
    - Adicionar em backend/superadmin/tests/test_views.py

- [x] 13. Criar endpoint POST /financeiro/{id}/reenviar-senha/
  - [x] 13.1 Implementar action reenviar_senha em FinanceiroLojaViewSet
    - Verificar se pagamento já foi confirmado (status_pagamento='ativo')
    - Chamar EmailService.enviar_senha_provisoria()
    - Retornar sucesso ou erro
    - Configurar permissões: apenas superadmin
    - Modificar backend/superadmin/views.py
    - _Requirements: Reenvio manual de senha_
  
  - [ ]* 13.2 Criar testes para endpoint reenviar-senha
    - Adicionar em backend/superadmin/tests/test_views.py

- [x] 14. Criar endpoints de EmailRetry
  - [x] 14.1 Criar EmailRetryViewSet
    - Implementar GET /emails-retry/ para listar emails pendentes
    - Implementar POST /emails-retry/{id}/reprocessar/ para forçar reenvio
    - Criar EmailRetrySerializer em backend/superadmin/serializers.py
    - Configurar permissões: apenas superadmin
    - Adicionar rotas em backend/superadmin/urls.py
    - _Requirements: Gerenciamento de emails com falha_
  
  - [ ]* 14.2 Criar testes para EmailRetryViewSet
    - Adicionar em backend/superadmin/tests/test_views.py

- [x] 15. Criar command reprocessar_emails_falhados
  - [x] 15.1 Implementar Django management command
    - Criar backend/superadmin/management/commands/reprocessar_emails_falhados.py
    - Buscar EmailRetry pendentes com proxima_tentativa <= now
    - Chamar EmailService.reenviar_email() para cada um
    - Exibir estatísticas (total, sucesso, falha)
    - Adicionar logs detalhados
    - _Requirements: Automação de retry de emails_
  
  - [ ]* 15.2 Criar testes para command reprocessar_emails_falhados
    - Criar backend/superadmin/tests/test_commands.py

- [x] 16. Criar command verificar_status_assinaturas
  - [x] 16.1 Implementar Django management command
    - Criar backend/superadmin/management/commands/verificar_status_assinaturas.py
    - Marcar como 'atrasado' assinaturas vencidas há 7+ dias
    - Marcar como 'bloqueado' assinaturas vencidas há 30+ dias
    - Exibir estatísticas e logs detalhados
    - _Requirements: Automação de verificação de status_
  
  - [ ]* 16.2 Criar testes para command verificar_status_assinaturas
    - Adicionar em backend/superadmin/tests/test_commands.py

- [x] 17. Configurar Django-Q schedules
  - Criar arquivo backend/superadmin/tasks.py
  - Criar task reprocessar_emails_task (chama command a cada 5 minutos)
  - Criar task verificar_assinaturas_task (chama command diariamente às 00:00)
  - Configurar schedules no admin Django-Q
  - Criar documentação em docs/CONFIGURAR_DJANGO_Q.md
  - _Requirements: Automação via Django-Q_

- [x] 18. Checkpoint - Validar automação
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 19. Criar testes de integração
  - Criar backend/superadmin/tests/integration/test_fluxo_completo.py
  - Implementar test_fluxo_criacao_loja_ate_envio_senha
  - Implementar test_fluxo_renovacao_assinatura
  - Implementar test_fluxo_retry_email_falhado
  - Cobrir Asaas e Mercado Pago com mocks de APIs externas
  - Garantir cobertura > 90%

- [x] 20. Atualizar frontend - Formulário de criação de loja
  - Remover exibição de senha na resposta
  - Adicionar mensagem: "Boleto enviado. Senha será enviada após confirmação do pagamento."
  - Exibir boleto_url e pix_qr_code
  - Modificar frontend/src/pages/superadmin/NovaLoja.jsx (ou similar)
  - _Requirements: Interface refletindo novo fluxo_

- [x] 21. Criar interface de renovação de assinatura
  - Criar página/componente DashboardAssinatura
  - Exibir status atual (ativo, pendente, atrasado, bloqueado)
  - Exibir data do próximo vencimento e valor da mensalidade
  - Adicionar botão "Gerar Nova Cobrança"
  - Criar modal com boleto_url e pix_qr_code após gerar
  - Adicionar tratamento de erros
  - Criar frontend/src/pages/loja/DashboardAssinatura.jsx (ou similar)
  - _Requirements: Interface de renovação no dashboard_

- [x] 22. Criar documentação
  - Atualizar README com novo fluxo
  - Criar docs/FLUXO_ASSINATURA_PAGAMENTO.md com documentação completa
  - Criar docs/API_ASSINATURA.md com documentação de endpoints novos
  - Criar docs/TROUBLESHOOTING_ASSINATURA.md com guia de troubleshooting
  - Adicionar diagramas de fluxo e exemplos de uso
  - _Requirements: Documentação completa_

- [x] 23. Final checkpoint - Preparar para deploy
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marcadas com `*` são opcionais e podem ser puladas para MVP mais rápido
- Cada task referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Tempo estimado total: ~35 horas (~1 semana de trabalho)
- Prioridade: Modelos → Services → Fluxo core → APIs → Automação → Frontend → Docs
