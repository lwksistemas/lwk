# Requirements Document

## Introduction

Este documento especifica os requisitos para o Sistema de Monitoramento e Segurança, uma solução abrangente para monitorar atividades, detectar violações de segurança e fornecer auditoria completa em um sistema multi-tenant Django. O sistema será implementado em https://lwksistemas.com.br/superadmin/dashboard e utilizará a infraestrutura existente de histórico de acessos (HistoricoAcessoGlobal) e middleware de captura de ações.

O sistema visa resolver problemas críticos identificados, incluindo a identificação incorreta de usuários nos logs (admin da loja aparecendo como "SuperAdmin") e fornecer ferramentas robustas para análise de segurança, auditoria e detecção de padrões suspeitos.

## Glossary

- **Sistema**: Sistema de Monitoramento e Segurança
- **SuperAdmin**: Administrador global do sistema multi-tenant
- **Loja**: Tenant individual no sistema multi-tenant
- **Admin_Loja**: Administrador de uma loja específica
- **HistoricoAcessoGlobal**: Modelo Django que armazena registros de todas as ações no sistema
- **Middleware_Historico**: Middleware Django que captura automaticamente ações dos usuários
- **Dashboard_Alertas**: Interface para visualização de violações de segurança
- **Dashboard_Auditoria**: Interface para análise de logs com gráficos e estatísticas
- **Violacao_Seguranca**: Evento que indica tentativa de acesso não autorizado ou comportamento suspeito
- **Padrao_Suspeito**: Sequência de ações que indica possível atividade maliciosa
- **Log_Estruturado**: Registro de ação com campos padronizados e indexados
- **Contexto_Loja**: Informação sobre qual loja está sendo acessada em uma requisição
- **TenantMiddleware**: Middleware que gerencia o contexto de loja nas requisições

## Requirements

### Requirement 1: Correção de Identificação de Usuários nos Logs

**User Story:** Como SuperAdmin, eu quero que os logs identifiquem corretamente os usuários e suas lojas, para que eu possa auditar ações com precisão.

#### Acceptance Criteria

1. WHEN um Admin_Loja realiza uma ação, THE Sistema SHALL registrar o nome correto da loja no campo loja_nome
2. WHEN o Middleware_Historico captura uma ação, THE Sistema SHALL preservar o Contexto_Loja antes que o TenantMiddleware limpe o contexto
3. WHEN um registro é criado no HistoricoAcessoGlobal, THE Sistema SHALL incluir loja_id, loja_nome e loja_slug corretos
4. WHEN um SuperAdmin visualiza logs, THE Sistema SHALL distinguir claramente entre ações de SuperAdmin e Admin_Loja
5. IF o Contexto_Loja não estiver disponível, THEN THE Sistema SHALL registrar a ação como ação de SuperAdmin ou sistema

### Requirement 2: Dashboard de Alertas de Violações

**User Story:** Como SuperAdmin, eu quero visualizar alertas de violações de segurança em tempo real, para que eu possa responder rapidamente a ameaças.

#### Acceptance Criteria

1. WHEN uma Violacao_Seguranca é detectada, THE Sistema SHALL criar um alerta visível no Dashboard_Alertas
2. THE Dashboard_Alertas SHALL exibir violações ordenadas por criticidade e data
3. WHEN um SuperAdmin acessa o Dashboard_Alertas, THE Sistema SHALL mostrar violações das últimas 24 horas por padrão
4. THE Dashboard_Alertas SHALL permitir filtrar violações por tipo, loja, usuário e período
5. WHEN um SuperAdmin clica em uma violação, THE Sistema SHALL exibir detalhes completos incluindo contexto e ações relacionadas
6. THE Dashboard_Alertas SHALL destacar visualmente violações críticas não resolvidas
7. WHEN um SuperAdmin marca uma violação como resolvida, THE Sistema SHALL atualizar o status e registrar quem resolveu

### Requirement 3: Dashboard de Auditoria com Gráficos

**User Story:** Como SuperAdmin, eu quero visualizar estatísticas e gráficos de atividades do sistema, para que eu possa identificar tendências e anomalias.

#### Acceptance Criteria

1. THE Dashboard_Auditoria SHALL exibir gráfico de ações por dia nos últimos 30 dias
2. THE Dashboard_Auditoria SHALL exibir gráfico de ações por tipo (criar, editar, excluir, visualizar)
3. THE Dashboard_Auditoria SHALL exibir ranking das lojas mais ativas
4. THE Dashboard_Auditoria SHALL exibir ranking dos usuários mais ativos
5. THE Dashboard_Auditoria SHALL exibir gráfico de horários de pico de atividade
6. WHEN um SuperAdmin seleciona um período customizado, THE Sistema SHALL atualizar todos os gráficos para o período selecionado
7. THE Dashboard_Auditoria SHALL exibir taxa de sucesso vs falha de ações
8. THE Dashboard_Auditoria SHALL permitir drill-down de qualquer métrica para ver logs detalhados

### Requirement 4: Busca e Análise de Logs Estruturados

**User Story:** Como SuperAdmin, eu quero buscar e filtrar logs de forma avançada, para que eu possa investigar incidentes específicos.

#### Acceptance Criteria

1. THE Sistema SHALL permitir busca por texto livre em logs (usuário, ação, recurso, detalhes)
2. THE Sistema SHALL permitir filtros combinados por loja, usuário, ação, recurso, período, sucesso/falha
3. WHEN um SuperAdmin aplica filtros, THE Sistema SHALL retornar resultados em menos de 2 segundos para até 100.000 registros
4. THE Sistema SHALL permitir exportar resultados de busca em formato CSV e JSON
5. THE Sistema SHALL destacar termos de busca nos resultados
6. THE Sistema SHALL exibir contexto temporal (ações antes e depois) de um log selecionado
7. THE Sistema SHALL permitir salvar filtros frequentes como "buscas salvas"
8. WHEN um SuperAdmin visualiza um log, THE Sistema SHALL exibir todos os campos estruturados de forma legível

### Requirement 5: Detecção Automática de Padrões Suspeitos

**User Story:** Como SuperAdmin, eu quero que o sistema detecte automaticamente padrões suspeitos, para que eu possa prevenir ataques e abusos.

#### Acceptance Criteria

1. WHEN um usuário tenta acessar recursos de outra loja, THE Sistema SHALL criar uma Violacao_Seguranca de tipo "acesso_cross_tenant"
2. WHEN um usuário falha login mais de 5 vezes em 10 minutos, THE Sistema SHALL criar uma Violacao_Seguranca de tipo "brute_force"
3. WHEN um usuário realiza mais de 100 ações em 1 minuto, THE Sistema SHALL criar uma Violacao_Seguranca de tipo "rate_limit_exceeded"
4. WHEN um usuário acessa endpoints de SuperAdmin sem ser SuperAdmin, THE Sistema SHALL criar uma Violacao_Seguranca de tipo "privilege_escalation"
5. WHEN um usuário exclui mais de 10 registros em menos de 5 minutos, THE Sistema SHALL criar uma Violacao_Seguranca de tipo "mass_deletion"
6. WHEN um usuário acessa o sistema de um IP diferente do habitual, THE Sistema SHALL criar um alerta de tipo "ip_change"
7. THE Sistema SHALL executar análise de padrões a cada 5 minutos em background
8. THE Sistema SHALL permitir configurar thresholds para cada tipo de detecção

### Requirement 6: Gestão de Violações de Segurança

**User Story:** Como SuperAdmin, eu quero gerenciar violações de segurança, para que eu possa rastrear investigações e resoluções.

#### Acceptance Criteria

1. THE Sistema SHALL armazenar violações com campos: tipo, criticidade, usuário, loja, timestamp, detalhes, status
2. WHEN uma Violacao_Seguranca é criada, THE Sistema SHALL definir criticidade automaticamente baseada no tipo
3. THE Sistema SHALL permitir SuperAdmin adicionar notas a uma violação
4. THE Sistema SHALL permitir SuperAdmin alterar status de violação (nova, investigando, resolvida, falso_positivo)
5. WHEN uma violação é resolvida, THE Sistema SHALL registrar quem resolveu e quando
6. THE Sistema SHALL permitir bloquear usuário diretamente de uma violação
7. THE Sistema SHALL manter histórico completo de mudanças de status de violações

### Requirement 7: Notificações de Segurança

**User Story:** Como SuperAdmin, eu quero receber notificações de violações críticas, para que eu possa responder imediatamente.

#### Acceptance Criteria

1. WHEN uma Violacao_Seguranca crítica é detectada, THE Sistema SHALL enviar notificação por email ao SuperAdmin
2. THE Sistema SHALL agrupar notificações similares para evitar spam (máximo 1 email a cada 15 minutos por tipo)
3. THE Sistema SHALL exibir contador de violações não lidas no Dashboard_Alertas
4. THE Sistema SHALL permitir SuperAdmin configurar quais tipos de violação geram notificação
5. WHEN um SuperAdmin está online, THE Sistema SHALL exibir notificação em tempo real no navegador

### Requirement 8: Performance e Escalabilidade

**User Story:** Como desenvolvedor do sistema, eu quero que o monitoramento seja eficiente, para que não impacte a performance do sistema principal.

#### Acceptance Criteria

1. THE Middleware_Historico SHALL processar requisições sem adicionar mais de 50ms de latência
2. THE Sistema SHALL usar índices de banco de dados em campos frequentemente consultados
3. THE Sistema SHALL implementar paginação em todas as listagens de logs
4. THE Sistema SHALL limpar automaticamente logs com mais de 90 dias
5. WHEN o volume de logs excede 1 milhão de registros, THE Sistema SHALL arquivar logs antigos
6. THE Sistema SHALL usar cache para estatísticas do Dashboard_Auditoria (atualização a cada 5 minutos)
7. THE Sistema SHALL executar análise de padrões em processo background separado

### Requirement 9: Integração com Sistema Existente

**User Story:** Como desenvolvedor do sistema, eu quero reutilizar a infraestrutura existente, para que a implementação seja eficiente e consistente.

#### Acceptance Criteria

1. THE Sistema SHALL utilizar o modelo HistoricoAcessoGlobal existente sem modificações estruturais
2. THE Sistema SHALL utilizar o Middleware_Historico existente com correções aplicadas
3. THE Sistema SHALL seguir os padrões de código do projeto (BaseModelViewSet, serializers, etc.)
4. THE Sistema SHALL usar Django REST Framework para APIs
5. THE Sistema SHALL usar Next.js e TypeScript para frontend
6. THE Sistema SHALL seguir o padrão de autenticação JWT existente
7. THE Sistema SHALL integrar-se ao sistema de permissões existente (IsSuperAdmin)

### Requirement 10: Interface de Usuário

**User Story:** Como SuperAdmin, eu quero uma interface intuitiva e responsiva, para que eu possa monitorar o sistema de qualquer dispositivo.

#### Acceptance Criteria

1. THE Sistema SHALL implementar interface responsiva que funciona em desktop, tablet e mobile
2. THE Sistema SHALL usar componentes visuais consistentes com o resto do sistema
3. THE Sistema SHALL exibir loading states durante carregamento de dados
4. THE Sistema SHALL exibir mensagens de erro claras quando operações falham
5. THE Sistema SHALL usar cores para indicar criticidade (vermelho=crítico, amarelo=médio, verde=baixo)
6. THE Sistema SHALL implementar dark mode consistente com o resto do sistema
7. THE Sistema SHALL usar gráficos interativos (hover para detalhes, click para drill-down)
