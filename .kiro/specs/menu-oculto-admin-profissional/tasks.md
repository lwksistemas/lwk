# Implementation Plan: Menu Oculto + Admin como Profissional

## Overview

Implementação em duas frentes paralelas:
1. **Sidebar recolhida por padrão** — Alterar o `ClinicaBelezaShell` para iniciar collapsed, persistindo estado via `sessionStorage`.
2. **Admin como Profissional** — Criar service layer, views e endpoint no backend, e componente toggle no frontend.

## Tasks

- [x] 1. Implementar sidebar recolhida por padrão
  - [x] 1.1 Alterar estado inicial do `ClinicaBelezaShell` para collapsed com persistência em sessionStorage
    - Modificar `frontend/components/clinica-beleza/ClinicaBelezaShell.tsx`
    - Estado inicial: `sidebarCollapsed = true` (default quando sessionStorage vazio)
    - Ler valor de `sessionStorage.getItem('sidebar-collapsed')` no carregamento
    - Persistir mudanças via `useEffect` escrevendo em `sessionStorage`
    - Garantir que no mobile o comportamento existente (menu oculto) não seja afetado
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 1.2 Escrever testes unitários para o estado da sidebar
    - Testar estado inicial collapsed quando sessionStorage vazio
    - Testar que estado persiste em sessionStorage após toggle
    - Testar que valor armazenado é restaurado no re-render
    - _Requisitos: 1.1, 1.4_

- [x] 2. Implementar service layer do admin como profissional (Backend)
  - [x] 2.1 Criar `admin_professional_service.py` com lógica de negócio
    - Criar arquivo `backend/clinica_beleza/admin_professional_service.py`
    - Implementar `habilitar_admin_como_profissional(loja_id, user)` → cria ou reativa Professional
    - Implementar `desabilitar_admin_como_profissional(loja_id, user)` → soft-delete (is_active=False)
    - Implementar `obter_status_admin_profissional(loja_id, user)` → retorna `{ is_enabled, professional_id }`
    - Garantir idempotência: habilitar quando já ativo = noop, desabilitar quando já inativo = noop
    - Usar email do owner como chave de identificação do Professional
    - _Requisitos: 2.2, 2.4, 2.5, 3.1, 3.3_

  - [ ]* 2.2 Escrever teste de propriedade — Criação correta do Professional do admin
    - **Propriedade 1: Para qualquer admin com nome/email válidos, habilitar cria Professional com dados corretos e loja_id correspondente**
    - **Valida: Requisitos 2.2, 3.3**

  - [ ]* 2.3 Escrever teste de propriedade — Desativação preserva registro (soft-delete)
    - **Propriedade 2: Para qualquer Professional ativo do admin, desativar preserva registro com is_active=False**
    - **Valida: Requisitos 2.4**

  - [ ]* 2.4 Escrever teste de propriedade — Lista exclui inativos
    - **Propriedade 3: Para qualquer conjunto de profissionais, a listagem retorna apenas is_active=True**
    - **Valida: Requisitos 2.5**

- [x] 3. Implementar views e URLs do admin como profissional (Backend)
  - [x] 3.1 Criar `views_admin_professional.py` com endpoints de status e toggle
    - Criar arquivo `backend/clinica_beleza/views_admin_professional.py`
    - Implementar `AdminProfessionalStatusView` (GET /professionals/admin-status/)
    - Implementar `AdminProfessionalToggleView` (POST /professionals/toggle-admin/)
    - Usar `resolve_loja_id_from_request()` de `views_base.py`
    - Verificar permissão: somente owner da loja (`loja.owner_id == request.user.id`)
    - Retornar 403 para usuários não-owner
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.8, 3.1_

  - [x] 3.2 Registrar URLs em `clinica_beleza/urls.py`
    - Adicionar `path('professionals/admin-status/', AdminProfessionalStatusView.as_view())`
    - Adicionar `path('professionals/toggle-admin/', AdminProfessionalToggleView.as_view())`
    - _Requisitos: 2.1, 2.2_

  - [ ]* 3.3 Escrever testes unitários para as views
    - Testar GET admin-status retorna estado correto para owner
    - Testar POST toggle-admin habilita/desabilita corretamente
    - Testar 403 para usuário não-owner
    - Testar 403 para usuário anônimo
    - Testar idempotência do toggle
    - _Requisitos: 2.8, 2.2, 2.4_

- [x] 4. Checkpoint — Validar backend
  - Ensure all tests pass, ask the user if questions arise.
  - Rodar `python3 manage.py check` — 0 issues

- [x] 5. Implementar componente toggle no frontend
  - [x] 5.1 Criar componente `AdminProfissionalToggle.tsx`
    - Criar arquivo `frontend/components/clinica-beleza/AdminProfissionalToggle.tsx`
    - Implementar GET /professionals/admin-status/ ao montar para obter estado
    - Implementar POST /professionals/toggle-admin/ ao clicar no switch
    - Exibir switch com label "Habilitar como profissional"
    - Em caso de erro: reverter switch + exibir toast de erro
    - Componente visível apenas quando user é owner da loja
    - _Requisitos: 2.1, 2.3, 2.7, 2.8_

  - [x] 5.2 Integrar `AdminProfissionalToggle` na página de profissionais
    - Modificar `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/profissionais/page.tsx`
    - Renderizar `AdminProfissionalToggle` acima da tabela de profissionais
    - Passar callback `onToggled` para recarregar lista após toggle
    - Condicionar exibição: somente se user é owner (verificar via dados da loja)
    - _Requisitos: 2.1, 2.3, 2.8_

  - [ ]* 5.3 Escrever testes unitários para o componente toggle
    - Testar que toggle não é renderizado para não-owner
    - Testar que toggle exibe estado correto ao carregar
    - Testar que callback onToggled é chamado após toggle bem-sucedido
    - _Requisitos: 2.1, 2.8_

- [x] 6. Garantir listagem filtre inativos corretamente
  - [x] 6.1 Verificar/ajustar filtro `is_active=True` na listagem de profissionais
    - Verificar que `views_profissionais.py` já filtra por `is_active=True` no queryset
    - Se não filtra, adicionar `.filter(is_active=True)` ao queryset da listagem
    - Garantir que Professional desativado não aparece na lista nem na agenda
    - _Requisitos: 2.5, 2.6_

- [x] 7. Checkpoint final — Validação completa
  - Ensure all tests pass, ask the user if questions arise.
  - Rodar `python3 manage.py check` — 0 issues
  - Verificar `getDiagnostics` em todos os arquivos frontend modificados

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Testes de propriedade validam propriedades universais de corretude
- Testes unitários validam exemplos específicos e edge cases
- O service layer segue a convenção do projeto (`*_service.py`)
- As views usam `APIView` com padrões de `views_base.py`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2", "2.2", "2.3", "2.4", "3.1"] },
    { "id": 2, "tasks": ["3.2", "3.3"] },
    { "id": 3, "tasks": ["5.1", "6.1"] },
    { "id": 4, "tasks": ["5.2", "5.3"] }
  ]
}
```
