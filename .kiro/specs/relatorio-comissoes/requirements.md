# Requirements Document

## Introduction

Relatório de Comissões para o módulo Clínica da Beleza. O sistema fornece uma visão consolidada das comissões devidas aos profissionais com base nos pagamentos realizados (status PAID), permitindo filtros por período e profissional, exibição em tabela com totais, e exportação em CSV e PDF. A estrutura adota um hub de relatórios (`/relatorios`) com sub-rotas, sendo o relatório de comissões o primeiro (`/relatorios/comissoes`). O layout utiliza o ClinicaBelezaShell com sidebar/nav padrão.

## Glossary

- **Sistema_Relatorio**: Módulo de relatórios do frontend (Next.js) integrado ao ClinicaBelezaShell, acessível via rota `/loja/[slug]/relatorios`
- **API_Comissoes**: Endpoint da API Django REST Framework que calcula e retorna dados de comissões dos profissionais
- **Payment**: Model Django que registra pagamentos vinculados a agendamentos, contendo campos `amount`, `status`, `comissao_percentual`, `comissao_valor`, `payment_date` e FK para `Appointment`
- **ProfessionalCommission**: Model Django que define as regras de comissão por profissional — tipo (consulta/procedimento), modo (percentual/fixo) e valor
- **Professional**: Model Django que representa um profissional da clínica
- **Hub_Relatorios**: Página principal de relatórios que serve como ponto de entrada e lista os relatórios disponíveis
- **Periodo**: Intervalo de datas (data_inicio e data_fim) usado para filtrar pagamentos

## Requirements

### Requirement 1: Hub de Relatórios

**User Story:** Como administrador da clínica, eu quero acessar um hub central de relatórios, para que eu possa navegar facilmente entre os diferentes relatórios disponíveis.

#### Acceptance Criteria

1. WHEN o usuário navega para a rota `/loja/[slug]/relatorios`, THE Sistema_Relatorio SHALL exibir a página hub com a lista de relatórios disponíveis dentro do ClinicaBelezaShell
2. THE Hub_Relatorios SHALL exibir um card/link para o relatório de comissões apontando para `/loja/[slug]/relatorios/comissoes`
3. THE Sistema_Relatorio SHALL manter o item "Relatórios" ativo na sidebar do ClinicaBelezaShell quando qualquer sub-rota de relatórios estiver aberta

### Requirement 2: Endpoint de Relatório de Comissões

**User Story:** Como administrador da clínica, eu quero que o backend calcule as comissões em tempo real, para que eu veja dados precisos e atualizados.

#### Acceptance Criteria

1. WHEN uma requisição GET é recebida em `/api/clinica-beleza/relatorios/comissoes/`, THE API_Comissoes SHALL retornar os dados de comissões calculados a partir dos registros Payment com status PAID no período informado
2. WHEN o parâmetro `data_inicio` é fornecido, THE API_Comissoes SHALL filtrar apenas pagamentos com `payment_date` maior ou igual à data informada
3. WHEN o parâmetro `data_fim` é fornecido, THE API_Comissoes SHALL filtrar apenas pagamentos com `payment_date` menor ou igual à data informada
4. WHEN o parâmetro `professional_id` é fornecido, THE API_Comissoes SHALL filtrar apenas pagamentos vinculados ao profissional informado via `appointment__professional_id`
5. THE API_Comissoes SHALL retornar para cada profissional: nome, total de atendimentos pagos, valor total dos pagamentos, comissão percentual aplicada, valor total da comissão
6. THE API_Comissoes SHALL retornar os totais gerais: soma dos valores pagos e soma das comissões de todos os profissionais no período
7. IF nenhum pagamento com status PAID existir no período filtrado, THEN THE API_Comissoes SHALL retornar uma lista vazia com totais zerados

### Requirement 3: Interface do Relatório de Comissões

**User Story:** Como administrador da clínica, eu quero visualizar as comissões dos profissionais em uma tabela clara, para que eu possa conferir e gerenciar os valores devidos.

#### Acceptance Criteria

1. WHEN o usuário navega para `/loja/[slug]/relatorios/comissoes`, THE Sistema_Relatorio SHALL exibir a página de relatório de comissões dentro do ClinicaBelezaShell
2. THE Sistema_Relatorio SHALL exibir filtros de período (data início e data fim) com valor padrão sendo o mês atual
3. THE Sistema_Relatorio SHALL exibir um filtro de profissional com opção "Todos" como padrão
4. WHEN o usuário altera os filtros e aciona a busca, THE Sistema_Relatorio SHALL consultar a API_Comissoes com os parâmetros selecionados e atualizar a tabela
5. THE Sistema_Relatorio SHALL exibir uma tabela com as colunas: Profissional, Atendimentos, Valor Total (R$), Comissão (%), Comissão (R$)
6. THE Sistema_Relatorio SHALL exibir uma linha de totais ao final da tabela com a soma dos atendimentos, valor total e comissão total
7. WHILE os dados estão sendo carregados, THE Sistema_Relatorio SHALL exibir um indicador de carregamento (skeleton ou spinner)
8. IF a API retornar lista vazia, THEN THE Sistema_Relatorio SHALL exibir uma mensagem informativa indicando que não há dados para o período selecionado

### Requirement 4: Exportação CSV

**User Story:** Como administrador da clínica, eu quero exportar o relatório de comissões em CSV, para que eu possa abrir no Excel e realizar análises complementares.

#### Acceptance Criteria

1. WHEN o usuário clica no botão "Exportar CSV", THE Sistema_Relatorio SHALL gerar um arquivo CSV contendo os dados da tabela exibida com os filtros aplicados
2. THE Sistema_Relatorio SHALL incluir no CSV um cabeçalho com as colunas: Profissional, Atendimentos, Valor Total, Comissão (%), Comissão (R$)
3. THE Sistema_Relatorio SHALL incluir no CSV a linha de totais ao final dos dados
4. THE Sistema_Relatorio SHALL nomear o arquivo no formato `comissoes_YYYY-MM-DD_YYYY-MM-DD.csv` usando as datas do filtro aplicado
5. THE Sistema_Relatorio SHALL codificar o CSV em UTF-8 com BOM para compatibilidade com Excel

### Requirement 5: Exportação PDF

**User Story:** Como administrador da clínica, eu quero exportar o relatório de comissões em PDF, para que eu possa imprimir ou enviar como documento formal.

#### Acceptance Criteria

1. WHEN o usuário clica no botão "Exportar PDF", THE Sistema_Relatorio SHALL acionar a funcionalidade de impressão do navegador (`window.print`) com layout otimizado para impressão
2. THE Sistema_Relatorio SHALL aplicar estilos de impressão que ocultam sidebar, filtros e botões de ação, exibindo apenas o cabeçalho do relatório e a tabela de dados
3. THE Sistema_Relatorio SHALL incluir no layout de impressão: nome da clínica, título "Relatório de Comissões", período filtrado e data de geração

### Requirement 6: Isolamento Multi-Tenant

**User Story:** Como administrador de uma clínica específica, eu quero que o relatório mostre apenas dados da minha loja, para que a segurança dos dados seja mantida.

#### Acceptance Criteria

1. THE API_Comissoes SHALL utilizar o LojaIsolationManager para filtrar pagamentos exclusivamente do tenant (loja) do usuário autenticado
2. THE API_Comissoes SHALL exigir autenticação e permissão de acesso ao módulo financeiro antes de retornar dados
