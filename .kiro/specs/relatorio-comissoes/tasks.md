# Implementation Plan: Relatório de Comissões

## Overview

Implementação do módulo de relatório de comissões para a Clínica da Beleza. Inclui um service layer no backend para cálculo de comissões, um endpoint REST, e páginas frontend (hub de relatórios + página de comissões) com filtros, tabela, totais e exportação CSV/PDF.

## Tasks

- [x] 1. Backend — Service layer e endpoint de comissões
  - [x] 1.1 Criar `comissao_relatorio_service.py` com a função `calcular_comissoes()`
    - Implementar a função que filtra Payment por status PAID, período e profissional
    - Agrupar por profissional com Count e Sum (amount, comissao_valor)
    - Calcular percentual médio de comissão por profissional
    - Retornar dict com lista `profissionais` e `totais`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 1.2 Criar `views_relatorios.py` com `RelatorioComissoesView`
    - Criar APIView com `permission_classes = CLINICA_FINANCEIRO`
    - Parsear query params: `data_inicio`, `data_fim`, `professional_id`
    - Delegar ao service e serializar Decimal para float na resposta
    - Tratar parâmetros inválidos (ignorar, não quebrar)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.1, 6.2_

  - [x] 1.3 Registrar a rota em `urls.py` da app `clinica_beleza`
    - Adicionar `path('relatorios/comissoes/', RelatorioComissoesView.as_view(), name='relatorio-comissoes')`
    - Importar `RelatorioComissoesView` de `views_relatorios`
    - _Requirements: 2.1_

  - [ ]* 1.4 Escrever property test — Correção dos filtros (Property 1)
    - **Property 1: Correção dos filtros do serviço de comissões**
    - Gerar pagamentos aleatórios com datas e profissionais variados
    - Verificar que somente pagamentos PAID no intervalo e do profissional são incluídos
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [ ]* 1.5 Escrever property test — Correção da agregação (Property 2)
    - **Property 2: Correção da agregação por profissional**
    - Verificar que total_atendimentos == count, valor_total == sum(amount), comissao_total == sum(comissao_valor)
    - **Validates: Requirements 2.5**

  - [ ]* 1.6 Escrever property test — Invariante dos totais gerais (Property 3)
    - **Property 3: Invariante dos totais gerais**
    - Verificar que totais == soma dos valores de cada profissional
    - **Validates: Requirements 2.6**

  - [ ]* 1.7 Escrever property test — Isolamento multi-tenant (Property 6)
    - **Property 6: Isolamento multi-tenant**
    - Criar pagamentos em dois tenants distintos e verificar que cada um só vê os seus
    - **Validates: Requirements 6.1**

- [x] 2. Checkpoint — Backend validado
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Frontend — Layout e Hub de Relatórios
  - [x] 3.1 Criar layout `relatorios/layout.tsx` com ClinicaBelezaShell
    - Criar `frontend/app/(dashboard)/loja/[slug]/relatorios/layout.tsx`
    - Carregar dados da loja e envolver children no ClinicaBelezaShell
    - Redirecionar para login se não autenticado
    - _Requirements: 1.1, 1.3_

  - [x] 3.2 Reescrever `relatorios/page.tsx` como hub de relatórios
    - Exibir cards com links para os relatórios disponíveis
    - Incluir card de "Comissões dos Profissionais" apontando para `/relatorios/comissoes`
    - Usar ícone e estilo consistente com o design
    - _Requirements: 1.1, 1.2_

  - [x] 3.3 Atualizar navegação do ClinicaBelezaShell para marcar "Relatórios" como ativo em sub-rotas
    - Ajustar a função `isClinicaBelezaNavActive` para que retorne true quando pathname inicia com `/loja/{slug}/relatorios`
    - _Requirements: 1.3_

- [x] 4. Frontend — Página do Relatório de Comissões
  - [x] 4.1 Criar `relatorios/comissoes/page.tsx` com filtros e tabela
    - Implementar filtros de período (data início/fim, padrão = mês atual) e profissional (select com "Todos")
    - Buscar dados da API ao carregar e ao alterar filtros
    - Exibir tabela com colunas: Profissional, Atendimentos, Valor Total (R$), Comissão (%), Comissão (R$)
    - Exibir linha de totais ao final da tabela
    - Exibir loading (skeleton/spinner) durante carregamento
    - Exibir mensagem informativa quando lista vazia
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [x] 4.2 Implementar exportação CSV
    - Gerar CSV com cabeçalho: Profissional, Atendimentos, Valor Total, Comissão (%), Comissão (R$)
    - Incluir linha de totais ao final
    - Nomear arquivo no formato `comissoes_YYYY-MM-DD_YYYY-MM-DD.csv`
    - Codificar em UTF-8 com BOM para compatibilidade com Excel
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 4.3 Implementar exportação PDF via `window.print()`
    - Adicionar botão "Exportar PDF" que aciona `window.print()`
    - Criar estilos de impressão (@media print) que ocultam sidebar, filtros e botões
    - Incluir no layout de impressão: nome da clínica, título, período e data de geração
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 4.4 Escrever property test — Fidelidade da exportação CSV (Property 4)
    - **Property 4: Fidelidade da exportação CSV**
    - Gerar dados aleatórios de comissões e verificar que o CSV contém todas as linhas com valores corretos
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ]* 4.5 Escrever property test — Formato do nome do arquivo CSV (Property 5)
    - **Property 5: Formato do nome do arquivo CSV**
    - Para quaisquer datas, verificar que o nome segue `comissoes_YYYY-MM-DD_YYYY-MM-DD.csv`
    - **Validates: Requirements 4.4**

  - [ ]* 4.6 Escrever property test — Estado ativo da navegação (Property 7)
    - **Property 7: Estado ativo da navegação para sub-rotas**
    - Para qualquer pathname iniciando com `/loja/{slug}/relatorios`, verificar que isClinicaBelezaNavActive retorna true para "Relatórios"
    - **Validates: Requirements 1.3**

- [x] 5. Checkpoint final — Validação completa
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia os requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Property tests validam propriedades universais de correção
- O isolamento multi-tenant é garantido pelo `LojaIsolationManager` já existente nos models

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "3.1", "3.2"] },
    { "id": 2, "tasks": ["1.3", "1.4", "1.5", "1.6", "1.7", "3.3"] },
    { "id": 3, "tasks": ["4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3", "4.4", "4.5", "4.6"] }
  ]
}
```
