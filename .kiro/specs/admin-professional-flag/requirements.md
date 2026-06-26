# Requirements Document

## Introduction

No app Clínica da Beleza, o administrador da loja é criado automaticamente como profissional (owner). Porém, nem todos os administradores atendem clientes — alguns apenas fazem gestão financeira/administrativa. Esta feature adiciona um campo `is_profissional` ao model `Professional` para distinguir quem de fato atende pacientes de quem apenas administra a clínica. Profissionais com `is_profissional=False` não devem aparecer na agenda nem receber agendamentos, mas mantêm acesso administrativo ao sistema.

## Glossary

- **Sistema**: O aplicativo Clínica da Beleza (backend Django + frontend Next.js)
- **Professional**: Model que representa um profissional cadastrado na clínica (`clinica_beleza.models.Professional`)
- **Agenda**: Visualização de calendário com colunas por profissional e horários de atendimento
- **Appointment**: Model que representa um agendamento de consulta vinculado a um profissional
- **Select_de_Profissional**: Dropdown de seleção de profissional utilizado ao criar ou editar um agendamento
- **Admin_Não_Profissional**: Usuário com perfil administrador cujo registro Professional possui `is_profissional=False`
- **Campo_is_profissional**: Campo booleano no model Professional que indica se o registro representa um profissional que atende pacientes

## Requirements

### Requirement 1: Campo is_profissional no model

**User Story:** As a administrador da clínica, I want to distinguish professional staff who provide patient care from administrative-only staff, so that the system accurately reflects who should appear on the schedule.

#### Acceptance Criteria

1. THE Professional model SHALL include a boolean field `is_profissional` with default value `True`
2. WHEN a new Professional record is created, THE Sistema SHALL set `is_profissional` to `True` unless explicitly specified otherwise
3. WHEN the database migration runs on existing lojas, THE Sistema SHALL set `is_profissional` to `True` for all existing Professional records to maintain backward compatibility

### Requirement 2: Exclusão da agenda

**User Story:** As a administrador da clínica, I want non-professional admins to not appear on the schedule, so that the agenda only shows staff who actually provide patient care.

#### Acceptance Criteria

1. WHEN the Agenda loads professionals for column display, THE Sistema SHALL filter out Professional records where `is_profissional` is `False`
2. WHILE a Professional has `is_profissional` set to `False`, THE Sistema SHALL exclude that Professional from the Select_de_Profissional dropdown when creating or editing an Appointment
3. WHILE a Professional has `is_profissional` set to `False`, THE Sistema SHALL exclude that Professional from calendar column rendering in the Agenda view

### Requirement 3: Exclusão de agendamentos

**User Story:** As a administrador da clínica, I want to prevent appointments from being scheduled with non-professional admins, so that patients are only booked with staff who provide care.

#### Acceptance Criteria

1. WHEN a user attempts to create an Appointment with a Professional where `is_profissional` is `False`, THE Sistema SHALL reject the request and return a validation error
2. WHILE a Professional has `is_profissional` set to `False`, THE Sistema SHALL not include that Professional in any API response that lists available professionals for scheduling

### Requirement 4: Manutenção do acesso administrativo

**User Story:** As a administrador da clínica, I want to keep full system access even when marked as non-professional, so that I can still manage the clinic without appearing on the schedule.

#### Acceptance Criteria

1. WHILE a Professional has `is_profissional` set to `False`, THE Sistema SHALL maintain all administrative permissions and access for the associated user account
2. WHILE a Professional has `is_profissional` set to `False`, THE Sistema SHALL continue displaying the Professional record in the professionals management list (Cadastro de Profissionais)
3. WHEN `is_profissional` is set to `False` for a Professional, THE Sistema SHALL not modify the `is_active` field or any other existing fields of that Professional record

### Requirement 5: Toggle no frontend

**User Story:** As a administrador da clínica, I want a toggle option in the professionals page to mark someone as non-professional, so that I can easily manage who appears on the schedule.

#### Acceptance Criteria

1. THE Sistema SHALL display a toggle/checkbox labeled "É profissional" in the actions area of each Professional on the professionals management page
2. WHEN the user toggles the "É profissional" control, THE Sistema SHALL send a PATCH request to update the `is_profissional` field of that Professional
3. WHEN the toggle update succeeds, THE Sistema SHALL reflect the new state immediately in the UI without requiring a page reload
4. THE Sistema SHALL display a visual indicator (badge or label) on the professionals list showing which professionals have `is_profissional` set to `False`

### Requirement 6: Endpoint de API para atualizar is_profissional

**User Story:** As a frontend developer, I want an API endpoint to update the is_profissional field, so that the frontend can toggle this flag.

#### Acceptance Criteria

1. THE Sistema SHALL expose a PATCH endpoint that accepts `is_profissional` as a boolean field for a given Professional record
2. WHEN a non-admin user attempts to update `is_profissional`, THE Sistema SHALL reject the request with HTTP 403
3. WHEN a valid PATCH request sets `is_profissional` to `False` for a Professional who has future Appointments, THE Sistema SHALL return a warning in the response indicating that future appointments exist for that Professional

### Requirement 7: Compatibilidade com lojas existentes

**User Story:** As a platform operator, I want the feature to work seamlessly on all existing and new clinics, so that no clinic is broken by the change.

#### Acceptance Criteria

1. WHEN the migration is applied to existing database schemas, THE Sistema SHALL add the `is_profissional` field with default `True` without modifying any other data
2. THE Sistema SHALL apply the migration to all active tenant schemas using the standard `migrate_all_lojas` process
3. WHEN a new loja is created after the migration, THE Sistema SHALL include the `is_profissional` field in the Professional table with default `True`
