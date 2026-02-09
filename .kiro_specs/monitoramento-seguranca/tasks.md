# Implementation Plan: Sistema de Monitoramento e Segurança

## Overview

Este plano de implementação detalha as tarefas necessárias para construir o Sistema de Monitoramento e Segurança, incluindo correção do middleware de histórico, criação de modelos de violação, detector de padrões, APIs REST e dashboards frontend.

A implementação seguirá uma abordagem incremental, começando pela correção crítica do middleware, depois construindo a infraestrutura de detecção de violações, e finalmente implementando os dashboards de visualização.

## Tasks

- [x] 1. Corrigir Middleware de Histórico para Captura Correta de Contexto de Loja
  - [x] 1.1 Modificar HistoricoAcessoMiddleware para capturar loja_id antes de processar resposta
    - Adicionar captura de `loja_id` no início do método `__call__`
    - Armazenar em `request._historico_loja_id` para uso posterior
    - Modificar `_registrar_acao` para usar `request._historico_loja_id`
    - Adicionar logging para debug de captura de contexto
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 1.2 Escrever testes de propriedade para correção de identificação de loja
    - **Property 1: Correção de Identificação de Loja em Logs**
    - **Validates: Requirements 1.1, 1.3**
  
  - [ ]* 1.3 Escrever testes de propriedade para distinção SuperAdmin vs Admin_Loja
    - **Property 2: Distinção entre SuperAdmin e Admin_Loja**
    - **Validates: Requirements 1.4**
  
  - [ ]* 1.4 Escrever testes unitários para edge cases do middleware
    - Testar contexto de loja ausente
    - Testar usuário anônimo
    - Testar falha ao criar registro
    - _Requirements: 1.5_

- [x] 2. Criar Modelo de Violação de Segurança e Infraestrutura Base
  - [x] 2.1 Criar modelo ViolacaoSeguranca em backend/superadmin/models.py
    - Definir campos: tipo, criticidade, status, user, loja, descricao, detalhes_tecnicos, ip_address, logs_relacionados, resolvido_por, resolvido_em, notas, notificado, created_at, updated_at
    - Adicionar choices para tipo, criticidade e status
    - Criar índices em campos frequentemente consultados
    - Implementar métodos auxiliares: `__str__`, `get_criticidade_color`, `get_tipo_display_friendly`
    - _Requirements: 6.1, 6.2_
  
  - [x] 2.2 Criar e executar migrations para ViolacaoSeguranca
    - Gerar migration com `python manage.py makemigrations`
    - Executar migration com `python manage.py migrate`
    - _Requirements: 6.1_
  
  - [ ]* 2.3 Escrever testes de propriedade para campos obrigatórios de violações
    - **Property 24: Campos Obrigatórios de Violações**
    - **Validates: Requirements 6.1**
  
  - [ ]* 2.4 Escrever testes de propriedade para criticidade automática
    - **Property 25: Criticidade Automática**
    - **Validates: Requirements 6.2**

- [x] 3. Implementar Detector de Padrões Suspeitos
  - [x] 3.1 Criar classe SecurityDetector em backend/superadmin/security_detector.py
    - Implementar método `detect_brute_force` (5+ falhas em 10 min)
    - Implementar método `detect_rate_limit` (100+ ações em 1 min)
    - Implementar método `detect_cross_tenant` (acesso a recursos de outra loja)
    - Implementar método `detect_privilege_escalation` (acesso não autorizado a endpoints SuperAdmin)
    - Implementar método `detect_mass_deletion` (10+ exclusões em 5 min)
    - Implementar método `detect_ip_change` (acesso de IP diferente do habitual)
    - Implementar método `run_all_detections` que executa todas as detecções
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 3.2 Escrever testes de propriedade para detecção de cross-tenant access
    - **Property 17: Detecção de Cross-Tenant Access**
    - **Validates: Requirements 5.1**
  
  - [ ]* 3.3 Escrever testes de propriedade para detecção de brute force
    - **Property 18: Detecção de Brute Force**
    - **Validates: Requirements 5.2**
  
  - [ ]* 3.4 Escrever testes de propriedade para detecção de rate limit
    - **Property 19: Detecção de Rate Limit**
    - **Validates: Requirements 5.3**
  
  - [ ]* 3.5 Escrever testes de propriedade para detecção de privilege escalation
    - **Property 20: Detecção de Privilege Escalation**
    - **Validates: Requirements 5.4**
  
  - [ ]* 3.6 Escrever testes de propriedade para detecção de mass deletion
    - **Property 21: Detecção de Mass Deletion**
    - **Validates: Requirements 5.5**
  
  - [ ]* 3.7 Escrever testes de propriedade para detecção de mudança de IP
    - **Property 22: Detecção de Mudança de IP**
    - **Validates: Requirements 5.6**
  
  - [ ]* 3.8 Escrever testes unitários para edge cases do detector
    - Testar threshold exato (5 falhas vs 6 falhas)
    - Testar janela de tempo (9 min vs 11 min)
    - Testar falha ao criar violação
    - _Requirements: 5.2, 5.3, 5.5_

- [x] 4. Configurar Task Agendada para Detector de Padrões
  - [x] 4.1 Configurar Django-Q ou Celery para execução de background tasks
    - Instalar e configurar Django-Q (preferência por simplicidade)
    - Criar task agendada para executar `SecurityDetector.run_all_detections()` a cada 5 minutos
    - Adicionar logging para monitorar execução da task
    - _Requirements: 5.7, 8.7_

- [x] 5. Checkpoint - Testar Infraestrutura Base
  - [x] 5.1 Verificar que middleware captura loja_id corretamente
  - [x] 5.2 Verificar que detector cria violações corretamente
  - [x] 5.3 Verificar que task agendada executa sem erros
  - [x] 5.4 Executar todos os testes e garantir que passam
  - [x] 5.5 Perguntar ao usuário se há dúvidas ou ajustes necessários

- [x] 6. Implementar Serializers para APIs
  - [x] 6.1 Criar ViolacaoSegurancaSerializer em backend/superadmin/serializers.py
    - Incluir todos os campos do modelo
    - Adicionar campos calculados: `logs_relacionados_count`, `resolvido_por_nome`
    - _Requirements: 6.1_
  
  - [x] 6.2 Verificar/atualizar HistoricoAcessoGlobalSerializer
    - Garantir que todos os campos necessários estão expostos
    - _Requirements: 1.3, 4.8_

- [x] 7. Implementar ViewSet de Violações de Segurança
  - [x] 7.1 Criar ViolacaoSegurancaViewSet em backend/superadmin/views.py
    - Implementar CRUD básico (list, retrieve, update)
    - Adicionar filtros: status, criticidade, tipo, loja_id
    - Implementar ordenação por criticidade e data
    - Adicionar permissão IsSuperAdmin
    - _Requirements: 2.2, 2.4, 6.3, 6.4_
  
  - [x] 7.2 Implementar action `resolver` para marcar violação como resolvida
    - Atualizar status, resolvido_por, resolvido_em
    - Permitir adicionar notas
    - _Requirements: 2.7, 6.5_
  
  - [x] 7.3 Implementar action `marcar_falso_positivo`
    - Atualizar status para falso_positivo
    - Registrar quem marcou e quando
    - _Requirements: 6.4_
  
  - [x] 7.4 Implementar action `estatisticas` para métricas de violações
    - Retornar total, por_status, por_criticidade, por_tipo
    - _Requirements: 2.2_
  
  - [ ]* 7.5 Escrever testes de propriedade para ordenação de violações
    - **Property 3: Ordenação de Violações**
    - **Validates: Requirements 2.2**
  
  - [ ]* 7.6 Escrever testes de propriedade para filtros de violações
    - **Property 4: Filtros de Violações**
    - **Validates: Requirements 2.4**
  
  - [ ]* 7.7 Escrever testes de propriedade para atualização de status
    - **Property 5: Atualização de Status de Violação**
    - **Validates: Requirements 2.7, 6.5**
  
  - [ ]* 7.8 Escrever testes unitários para actions do ViewSet
    - Testar resolver com notas
    - Testar marcar_falso_positivo
    - Testar estatisticas com dados vazios
    - _Requirements: 2.7, 6.3, 6.4, 6.5_

- [x] 8. Implementar ViewSet de Estatísticas de Auditoria
  - [x] 8.1 Criar EstatisticasAuditoriaViewSet em backend/superadmin/views.py
    - Implementar action `acoes_por_dia` (últimos N dias)
    - Implementar action `acoes_por_tipo` (distribuição por tipo)
    - Implementar action `lojas_mais_ativas` (ranking top N)
    - Implementar action `usuarios_mais_ativos` (ranking top N)
    - Implementar action `horarios_pico` (distribuição por hora)
    - Implementar action `taxa_sucesso` (sucessos vs falhas)
    - Adicionar permissão IsSuperAdmin
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.7_
  
  - [ ]* 8.2 Escrever testes de propriedade para agrupamento por dia
    - **Property 6: Agrupamento de Ações por Dia**
    - **Validates: Requirements 3.1**
  
  - [ ]* 8.3 Escrever testes de propriedade para agrupamento por tipo
    - **Property 7: Agrupamento de Ações por Tipo**
    - **Validates: Requirements 3.2**
  
  - [ ]* 8.4 Escrever testes de propriedade para ranking de lojas
    - **Property 8: Ranking de Lojas Ativas**
    - **Validates: Requirements 3.3**
  
  - [ ]* 8.5 Escrever testes de propriedade para ranking de usuários
    - **Property 9: Ranking de Usuários Ativos**
    - **Validates: Requirements 3.4**
  
  - [ ]* 8.6 Escrever testes de propriedade para agrupamento por horário
    - **Property 10: Agrupamento por Horário**
    - **Validates: Requirements 3.5**
  
  - [ ]* 8.7 Escrever testes de propriedade para cálculo de taxa de sucesso
    - **Property 11: Cálculo de Taxa de Sucesso**
    - **Validates: Requirements 3.7**

- [x] 9. Implementar Busca Avançada de Logs
  - [x] 9.1 Adicionar filtros avançados ao HistoricoAcessoGlobalViewSet
  - [x] 9.2 Implementar action `exportar` para CSV e JSON
  - [x] 9.3 Implementar action `contexto_temporal` para logs relacionados
  - [ ]* 9.4 Escrever testes de propriedade para busca por texto livre
  - [ ]* 9.5 Escrever testes de propriedade para filtros combinados
  - [ ]* 9.6 Escrever testes de propriedade para exportação de dados
  - [ ]* 9.7 Escrever testes de propriedade para contexto temporal

- [x] 10. Configurar URLs e Rotas de API
  - [x] 10.1 Adicionar rotas em backend/superadmin/urls.py
    - Registrar ViolacaoSegurancaViewSet no router
    - Registrar EstatisticasAuditoriaViewSet no router
    - Verificar que HistoricoAcessoGlobalViewSet está registrado
    - _Requirements: 9.4_

- [ ] 11. Checkpoint - Testar APIs Backend
  - Testar todos os endpoints com Postman ou curl
  - Verificar autenticação JWT
  - Verificar permissões (apenas SuperAdmin)
  - Verificar filtros e ordenação
  - Executar todos os testes e garantir que passam
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

- [x] 12. Implementar Dashboard de Alertas (Frontend)
  - [x] 12.1 Criar página de alertas em frontend/app/superadmin/dashboard/alertas/page.tsx
  - [x] 12.2 Criar modal de detalhes de violação
  - [x] 12.3 Implementar ações de gestão de violações
  - [ ]* 12.4 Escrever testes de integração para dashboard de alertas

- [x] 13. Implementar Dashboard de Auditoria (Frontend)
  - [x] 13.1 Criar página de auditoria em frontend/app/superadmin/dashboard/auditoria/page.tsx
  - [x] 13.2 Implementar seletor de período customizado
  - [x] 13.3 Implementar drill-down de métricas
  - [ ]* 13.4 Escrever testes de integração para dashboard de auditoria

- [x] 14. Implementar Busca de Logs (Frontend)
  - [x] 14.1 Criar página de busca em frontend/app/superadmin/dashboard/logs/page.tsx
    - Implementar componente BuscaAvancada (formulário com múltiplos filtros)
    - Implementar componente ResultadosLogs (tabela paginada)
    - Implementar highlight de termos de busca
    - Adicionar botões de exportação (CSV, JSON)
    - _Requirements: 4.1, 4.2, 4.4, 4.5_
  
  - [x] 14.2 Criar modal de detalhes de log
    - Implementar componente LogDetalhes
    - Exibir todos os campos estruturados
    - Formatar JSON de detalhes de forma legível
    - _Requirements: 4.8_
  
  - [x] 14.3 Implementar contexto temporal de logs
    - Implementar componente ContextoTemporal (timeline)
    - Exibir ações antes e depois do log selecionado
    - _Requirements: 4.6_
  
  - [x] 14.4 Implementar funcionalidade de buscas salvas
    - Adicionar botão "Salvar busca"
    - Armazenar filtros em localStorage
    - Adicionar dropdown de buscas salvas
    - _Requirements: 4.7_
  
  - [ ]* 14.5 Escrever testes de integração para busca de logs
    - Testar busca por texto livre
    - Testar filtros combinados
    - Testar exportação
    - Testar buscas salvas
    - _Requirements: 4.1, 4.2, 4.4, 4.7_

- [x] 15. Implementar Sistema de Notificações
  - [x] 15.1 Criar serviço de notificações em backend/superadmin/notifications.py
    - Implementar função para enviar email de violação crítica
    - Implementar agrupamento de notificações (máx 1 a cada 15 min por tipo)
    - Adicionar template de email para violações
    - _Requirements: 7.1, 7.2_
  
  - [x] 15.2 Integrar notificações com detector de padrões
    - Chamar serviço de notificações ao criar violação crítica
    - Verificar configuração de tipos que geram notificação
    - _Requirements: 7.1, 7.4_
  
  - [ ] 15.3 Implementar notificações em tempo real no frontend
    - Adicionar WebSocket ou polling para notificações
    - Exibir toast/banner quando violação crítica é detectada
    - _Requirements: 7.5_
  
  - [ ]* 15.4 Escrever testes de propriedade para notificações
    - **Property 30: Notificação de Violações Críticas**
    - **Validates: Requirements 7.1**
    - **Property 31: Agrupamento de Notificações**
    - **Validates: Requirements 7.2**
    - **Property 32: Configuração de Notificações**
    - **Validates: Requirements 7.4**

- [x] 16. Implementar Otimizações de Performance
  - [x] 16.1 Adicionar índices de banco de dados
    - Verificar índices em HistoricoAcessoGlobal
    - Adicionar índices compostos se necessário
    - _Requirements: 8.2_
  
  - [ ] 16.2 Implementar cache para estatísticas
    - Usar Redis para cachear resultados de estatísticas
    - Configurar TTL de 5 minutos
    - _Requirements: 8.6_
  
  - [x] 16.3 Implementar comando de limpeza de logs antigos
    - Criar management command para limpar logs > 90 dias
    - Adicionar logging de quantos registros foram removidos
    - _Requirements: 8.4_
  
  - [x] 16.4 Implementar arquivamento de logs
    - Criar comando para arquivar logs quando total > 1 milhão
    - Exportar logs antigos para arquivo JSON/CSV
    - _Requirements: 8.5_
  
  - [ ]* 16.5 Escrever testes de propriedade para limpeza de logs
    - **Property 34: Limpeza de Logs Antigos**
    - **Validates: Requirements 8.4**
    - **Property 35: Arquivamento de Logs**
    - **Validates: Requirements 8.5**

- [ ] 17. Implementar Testes de Performance
  - [ ]* 17.1 Escrever teste de latência do middleware
    - Usar pytest-benchmark
    - Verificar que latência < 50ms
    - _Requirements: 8.1_
  
  - [ ]* 17.2 Escrever teste de performance de busca
    - Criar 100k registros de teste
    - Verificar que busca retorna em < 2s
    - _Requirements: 4.3_

- [x] 18. Checkpoint Final - Testes End-to-End
  - [x] 18.1 Criar documentação completa da API
    - Documentar todos os 17 endpoints
    - Incluir exemplos de requisições e respostas
    - Documentar códigos de status HTTP
    - Incluir exemplos de uso comuns
    - _Requirements: 9.4_
  
  - [x] 18.2 Criar guia de uso para SuperAdmin
    - Documentar como usar dashboard de alertas
    - Documentar como usar dashboard de auditoria
    - Documentar como usar busca avançada
    - Incluir casos de uso comuns
    - Incluir solução de problemas
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [x] 18.3 Criar checklist de deploy para produção
    - Verificar variáveis de ambiente
    - Executar migrations em produção
    - Configurar task agendada em produção
    - Configurar Redis para cache
    - Validar todos os componentes
    - _Requirements: 8.6, 8.7_

- [x] 19. Documentação e Deploy
  - [x] 19.1 Atualizar documentação de API
    - Documentar endpoints de violações
    - Documentar endpoints de estatísticas
    - Documentar endpoints de busca
    - _Requirements: 9.4_
  
  - [x] 19.2 Criar guia de uso para SuperAdmin
    - Documentar como usar dashboard de alertas
    - Documentar como usar dashboard de auditoria
    - Documentar como usar busca avançada
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [x] 19.3 Preparar deploy
    - Verificar variáveis de ambiente
    - Executar migrations em produção
    - Configurar task agendada em produção
    - Configurar Redis para cache
    - _Requirements: 8.6, 8.7_

## Notes

- Tasks marcadas com `*` são opcionais e podem ser puladas para MVP mais rápido
- Cada task referencia requirements específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Property tests validam propriedades universais de correção
- Unit tests validam exemplos específicos e edge cases
- Implementação segue padrões existentes do projeto (BaseModelViewSet, serializers, JWT auth)
