# Requirements Document

## Introduction

Refatoração e limpeza de código do app Clínica da Beleza (backend Django + frontend Next.js) para eliminar redundâncias, unificar padrões, remover código morto e melhorar a manutenibilidade — sem alterar comportamento externo observável.

## Glossary

- **GetObjectMixin**: Mixin base em `views_base.py` que fornece `object_or_404(pk)` para lookup padronizado com tratamento de `DoesNotExist`
- **map_field_names**: Utilitário genérico em `views_base.py` que normaliza nomes de campos (inglês → português) de forma declarativa
- **EntityListTable**: Componente React genérico para renderizar listas tabulares com colunas configuráveis
- **useOfflineSave**: Hook React a ser extraído, encapsulando a lógica de salvamento offline com fallback
- **DashboardView**: View que retorna métricas consolidadas do dashboard da clínica
- **AgendaDeleteView**: View que exclui um agendamento por ID
- **Public_Views**: Views acessíveis sem autenticação (`ConfirmarAgendamentoPublicaView`, `ConsultaAssinaturaPublicaView`, `EnviarFotoPublicaView`)
- **Field_Map_Pattern**: Padrão atual onde cada módulo de views define um `_FIELD_MAP` dict + função `_map_*_data()` para normalização de campos
- **ClienteSearchMixin**: Mixin em `core/mixins.py` para busca de clientes por nome/telefone/email, usado por `clinica_estetica` e `cabeleireiro` mas não por `clinica_beleza`
- **Catalog_Files**: Arquivos `estoque_catalogo.py`, `procedimentos_catalogo.py`, `termos_consentimento_catalogo.py` que definem dados de seed/catálogo

## Requirements

### Requirement 1: Eliminar helper redundante `_get_professional_or_404`

**User Story:** As a developer, I want views de profissionais to use the standard `GetObjectMixin` pattern, so that the codebase has a single consistent way to resolve objects by PK.

#### Acceptance Criteria

1. THE Views_Profissionais module SHALL use `GetObjectMixin.object_or_404()` for all professional lookups instead of the standalone `_get_professional_or_404()` function
2. WHEN a professional lookup by PK fails, THE Views_Profissionais module SHALL return an HTTP 404 response with the message "Profissional não encontrado"
3. WHEN the refactoring is complete, THE `_get_professional_or_404()` function SHALL be removed from the `views_profissionais.py` module
4. THE `HorarioTrabalhoProfissionalView` SHALL use `GetObjectMixin` with `model_class = Professional` for professional existence validation
5. THE `ProfessionalCommissionView` SHALL use `GetObjectMixin` with `model_class = Professional` for professional existence validation

### Requirement 2: Unificar padrão de field-mapping com abordagem declarativa

**User Story:** As a developer, I want a single declarative approach for field mapping across all view modules, so that adding new field mappings requires only configuration changes.

#### Acceptance Criteria

1. THE Views_Pacientes module SHALL use `map_field_names()` from `views_base.py` as the sole mechanism for field name normalization
2. THE Views_Profissionais module SHALL use `map_field_names()` from `views_base.py` as the sole mechanism for field name normalization
3. WHEN a view module performs field mapping, THE View_Module SHALL declare a `_FIELD_MAP` constant and pass it to `map_field_names()` without custom inline logic for name translation
4. THE `_map_professional_data()` function SHALL retain only the post-mapping transformations (type coercion, empty-to-none) that go beyond simple field renaming
5. THE `_map_patient_data()` function SHALL delegate field renaming entirely to `map_field_names()` and retain only null-to-empty transformations

### Requirement 3: AgendaDeleteView deve usar GetObjectMixin

**User Story:** As a developer, I want `AgendaDeleteView` to follow the same object-lookup pattern as other views, so that error handling is consistent across the codebase.

#### Acceptance Criteria

1. THE AgendaDeleteView SHALL inherit from `GetObjectMixin` with `model_class = Appointment` and `not_found_message = 'Agendamento não encontrado'`
2. THE AgendaDeleteView SHALL use `self.object_or_404(pk)` instead of inline `try/except Appointment.DoesNotExist`
3. WHEN the appointment does not exist, THE AgendaDeleteView SHALL return HTTP 404 with `{'error': 'Agendamento não encontrado'}`
4. WHEN the appointment exists, THE AgendaDeleteView SHALL delete it and return HTTP 204

### Requirement 4: Adicionar rate limiting em views públicas

**User Story:** As a developer, I want public-facing views to have rate limiting, so that the system is protected against abuse and denial-of-service attempts.

#### Acceptance Criteria

1. THE ConfirmarAgendamentoPublicaView SHALL enforce a rate limit of no more than 30 requests per minute per IP address
2. THE ConsultaAssinaturaPublicaView SHALL enforce a rate limit of no more than 30 requests per minute per IP address
3. THE EnviarFotoPublicaView SHALL enforce a rate limit of no more than 10 requests per minute per IP address
4. IF a client exceeds the rate limit, THEN THE Public_Views SHALL return HTTP 429 with a descriptive error message indicating retry-after time
5. THE rate limiting mechanism SHALL use Django REST Framework throttle classes or Django's cache-based approach compatible with the existing Redis cache

### Requirement 5: Refatorar DashboardView.get() em métodos menores

**User Story:** As a developer, I want the dashboard handler to be split into focused helper methods, so that each section of data is easy to understand, test, and modify independently.

#### Acceptance Criteria

1. THE DashboardView.get() method SHALL have no more than 40 lines of code in its body (excluding blank lines and comments)
2. THE DashboardView SHALL delegate statistics computation to a `_build_statistics()` helper method
3. THE DashboardView SHALL delegate next-appointments query to a `_build_next_appointments()` helper method
4. THE DashboardView SHALL delegate revenue chart data to the existing `_revenue_by_day()` module-level function
5. THE DashboardView SHALL produce the same JSON response structure as the current implementation for all valid requests
6. THE DashboardView SHALL maintain the existing cache key format and TTL behavior

### Requirement 6: Remover property aliases deprecated do Patient

**User Story:** As a developer, I want to remove deprecated `name`/`phone` property aliases from the Patient model, so that the model interface is clean and developers use the canonical field names.

#### Acceptance Criteria

1. THE Patient model SHALL NOT define `name` property or `name.setter`
2. THE Patient model SHALL NOT define `phone` property or `phone.setter`
3. WHEN the aliases are removed, THE `popular_loja_clinica_beleza` management command SHALL be refactored to use `nome` and `telefone` directly
4. THE removal SHALL NOT affect any view, serializer, or API response since field mapping is handled by `_map_patient_data()`

### Requirement 7: Extrair hook `useOfflineSave` reutilizável

**User Story:** As a developer, I want offline-save logic extracted into a reusable hook, so that all entity pages share a single tested implementation instead of duplicated code.

#### Acceptance Criteria

1. THE Frontend SHALL provide a `useOfflineSave` hook in `hooks/clinica-beleza/useOfflineSave.ts`
2. THE `useOfflineSave` hook SHALL encapsulate: detecting offline state, saving to IndexedDB queue, generating temporary IDs, handling online-save-fallback-to-offline
3. THE `useOfflineSave` hook SHALL accept configuration parameters for: entity type, save-online function, list state updater, offline storage functions
4. WHEN the browser is offline, THE `useOfflineSave` hook SHALL save the entity to the sync queue and return a success result with offline indicator
5. WHEN an online save fails with a network error, THE `useOfflineSave` hook SHALL fall back to offline save and return a success result with offline indicator
6. THE `pacientes/page.tsx` SHALL use `useOfflineSave` instead of inline offline save logic, reducing the save function to under 30 lines

### Requirement 8: Padronizar lista de pacientes com EntityListTable

**User Story:** As a developer, I want the patients list page to use the same `EntityListTable` component as professionals, so that list rendering is consistent and maintainable.

#### Acceptance Criteria

1. THE `pacientes/page.tsx` list view SHALL use the `EntityListTable` component for rendering the patient table
2. THE `EntityListTable` usage SHALL define columns for: foto/avatar, nome, telefone, e-mail, CPF, convênio, ações
3. THE rendered output SHALL preserve the same visual appearance (avatar, offline badge, action buttons) as the current inline table
4. THE `EntityListTable` component SHALL support a custom cell renderer for the avatar column (non-text content)
5. WHEN the list is empty, THE `EntityListTable` SHALL display the existing empty-state message

### Requirement 9: Refatorar pacientes/page.tsx em componentes menores

**User Story:** As a developer, I want the patients page split into smaller focused components and hooks, so that the file is easier to navigate, test, and modify.

#### Acceptance Criteria

1. THE `pacientes/page.tsx` file SHALL contain no more than 150 lines of code (excluding imports and type definitions)
2. THE patient list rendering logic SHALL be extracted into a `PacienteListView` component
3. THE form state management and CEP lookup logic SHALL be handled by the existing `PacienteCadastroForm` component or a new `usePacienteForm` hook
4. THE `patientToForm()` and `montarEnderecoPaciente()` utility functions SHALL be extracted to a separate utility file
5. THE main page component SHALL orchestrate routing (list vs form view) and delegate rendering to child components

### Requirement 10: Avaliar e documentar uso de ClienteSearchMixin

**User Story:** As a developer, I want clarity on whether `ClienteSearchMixin` should remain in `core/mixins.py`, so that shared code is only kept if it serves multiple consumers.

#### Acceptance Criteria

1. THE `ClienteSearchMixin` SHALL remain in `core/mixins.py` since it is actively used by `clinica_estetica` and `cabeleireiro` apps
2. THE `clinica_beleza` app SHALL NOT import or use `ClienteSearchMixin` (it uses `_patient_search_q` in views directly)
3. THE `ClienteSearchMixin` class docstring SHALL be updated to list which apps consume it (`clinica_estetica`, `cabeleireiro`)

### Requirement 11: Documentar e manter catalog files como módulos de seed data

**User Story:** As a developer, I want catalog files properly documented, so that their purpose as seed-data definitions (not runtime logic) is clear.

#### Acceptance Criteria

1. THE `estoque_catalogo.py` SHALL include a module docstring stating it provides seed data consumed by management commands and `estoque_catalogo_service.py`
2. THE `procedimentos_catalogo.py` SHALL include a module docstring stating it provides seed data consumed by `catalogo_service.py` and management commands
3. THE `termos_consentimento_catalogo.py` SHALL include a module docstring stating it provides term templates consumed by `procedimentos_catalogo.py` and management commands
4. THE catalog files SHALL NOT be deleted since they are actively imported by `catalogo_service.py`, `estoque_catalogo_service.py`, and multiple management commands
