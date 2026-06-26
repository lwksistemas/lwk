# Requirements Document

## Introduction

Atualmente, apenas o owner da loja (vinculado via `ProfissionalUsuario`) possui o toggle "É profissional" visível na listagem de profissionais — determinado pelo campo `is_administrador_vinculado` que compara `obj.id == owner_professional_id`. Esta feature estende essa funcionalidade para TODOS os usuários cadastrados com perfil "administrador" na tabela `ProfissionalUsuario`, permitindo que qualquer administrador escolha entre atuar "só como administrador" ou como "administrador + profissional", usando a mesma lógica de checkbox/toggle já existente.

## Glossary

- **Sistema**: O aplicativo Clínica da Beleza (backend Django + frontend Next.js)
- **Professional**: Model que representa um profissional cadastrado na clínica (`clinica_beleza.models.Professional`)
- **ProfissionalUsuario**: Model no schema public que vincula um User Django a um Professional de uma loja, contendo o campo `perfil`
- **Perfil_Administrador**: Valor `'administrador'` no campo `perfil` da tabela `ProfissionalUsuario`, indicando acesso administrativo completo
- **Toggle_Profissional**: Checkbox na coluna de ações da listagem de profissionais que permite alternar o campo `is_profissional` entre `True` e `False`
- **Campo_is_administrador_vinculado**: Campo serializado (read-only) no `ProfessionalSerializer` que indica se aquele Professional é um administrador com toggle disponível
- **Owner**: Usuário proprietário da loja (`Loja.owner`), atualmente o único que recebe `is_administrador_vinculado=True`

## Requirements

### Requirement 1: Identificação de todos os administradores vinculados

**User Story:** As a administrador da clínica, I want all professionals with "administrador" profile to be recognized as admin-linked professionals, so that any admin can toggle between admin-only and admin+professional modes.

#### Acceptance Criteria

1. WHEN the Professional list or detail is serialized, THE Sistema SHALL set `is_administrador_vinculado` to `True` for every Professional whose `ProfissionalUsuario` record (matched by `professional_id`) has `perfil` equal to `'administrador'` in the current loja (resolved from request context)
2. WHEN a Professional has no `ProfissionalUsuario` record with `perfil` equal to `'administrador'` matched by `professional_id` in the current loja, THE Sistema SHALL set `is_administrador_vinculado` to `False` for that Professional
3. IF the owner Professional does not have an explicit `ProfissionalUsuario` record with `perfil` equal to `'administrador'` in the current loja, THEN THE Sistema SHALL still set `is_administrador_vinculado` to `True` for the owner Professional, preserving backward compatibility

### Requirement 2: Backend — obter IDs dos profissionais-administradores

**User Story:** As a backend developer, I want a utility method that returns all admin-linked professional IDs for the current loja, so that the serializer can identify all admins efficiently.

#### Acceptance Criteria

1. THE Sistema SHALL provide a utility method that queries `ProfissionalUsuario` records filtered by `perfil='administrador'` and the current `loja_id` (resolved via `get_current_loja_id()`) and returns a Python `set` of `professional_id` integer values
2. THE Sistema SHALL cache the result of this query using a cache key scoped to the current `loja_id` with a TTL of 3600 seconds (1 hour)
3. WHEN a `ProfissionalUsuario` record with `perfil='administrador'` is created, updated, or deleted for a given `loja_id`, THE Sistema SHALL invalidate the corresponding admin IDs cache entry for that `loja_id`
4. THE Sistema SHALL include the owner's `professional_id` (resolved from `ProfissionalUsuario` where `user_id` equals `Loja.owner_id`) in the returned set, even if the owner's `perfil` is not explicitly `'administrador'`
5. IF `get_current_loja_id()` returns `None`, THEN THE Sistema SHALL return an empty set without querying the database or cache

### Requirement 3: Serializer — lógica expandida de is_administrador_vinculado

**User Story:** As a backend developer, I want the ProfessionalSerializer to check against a set of admin professional IDs instead of a single owner ID, so that all admin professionals get the toggle flag.

#### Acceptance Criteria

1. WHEN the serializer context contains `admin_professional_ids` (a Python `set` of integer IDs), THE Sistema SHALL set `is_administrador_vinculado` to `True` if `obj.id` is present in that set, and to `False` otherwise, without consulting `owner_professional_id`
2. WHEN the serializer context does not contain the key `admin_professional_ids`, THE Sistema SHALL fall back to comparing `obj.id` with the context value `owner_professional_id` and return `True` on match, or `False` if `owner_professional_id` is absent or does not match
3. WHEN `ProfessionalSerializer` is instantiated by `ProfessionalListView.get` or `ProfessionalDetailView.get`, THE Sistema SHALL include `admin_professional_ids` in the serializer context as a `set` of integer Professional IDs
4. IF `admin_professional_ids` is present in the context but is an empty set, THEN THE Sistema SHALL set `is_administrador_vinculado` to `False` for every Professional in the response

### Requirement 4: Frontend — toggle visível para todos os administradores

**User Story:** As a administrador da clínica, I want to see the "É profissional" checkbox for every professional marked as `is_administrador_vinculado`, so that I can toggle any admin between admin-only and admin+professional modes.

#### Acceptance Criteria

1. WHEN a Professional has `is_administrador_vinculado` equal to `True`, THE Sistema SHALL display the Toggle_Profissional checkbox in the actions column for that Professional, with checked state reflecting the current value of `is_profissional` (defaulting to `True` if the field is absent)
2. WHEN the user clicks the Toggle_Profissional checkbox, THE Sistema SHALL send a PATCH request to `/professionals/:id/` with `{ is_profissional: <negated current value> }`, where `<negated current value>` is the boolean opposite of that Professional's current `is_profissional` state
3. WHEN the PATCH request succeeds, THE Sistema SHALL re-fetch the professionals list from the API and update the displayed data to reflect the new state without a full page reload
4. THE Sistema SHALL not display the "Desativar" (trash) button for professionals with `is_administrador_vinculado` equal to `True`, preventing accidental deactivation of admin-linked professionals
5. IF the PATCH request for the Toggle_Profissional fails, THEN THE Sistema SHALL display an error message indicating the failure reason to the user and preserve the checkbox in its previous state

### Requirement 5: Proteção contra exclusão de administradores

**User Story:** As a administrador da clínica, I want admin-linked professionals to be protected from deletion, so that no admin accidentally loses their professional record.

#### Acceptance Criteria

1. WHEN a DELETE request is made for a Professional whose ID is in the set of admin professional IDs, THE Sistema SHALL reject the request with HTTP 403 and an error message indicating that the professional is linked to the admin account and cannot be removed
2. WHEN a PUT or PATCH request attempts to set `is_active` to `False` for a Professional whose ID is in the set of admin professional IDs, THE Sistema SHALL reject the request with HTTP 403 and an error message indicating that the admin-linked professional cannot be deactivated
3. IF no admin professional IDs are found for the current loja (empty set), THEN THE Sistema SHALL process DELETE and PUT/PATCH requests for any Professional following standard logic without admin protection

### Requirement 6: Invalidação de cache ao alterar perfil

**User Story:** As a platform operator, I want the admin professional IDs cache to be invalidated when user profiles change, so that the toggle appears or disappears correctly after profile modifications.

#### Acceptance Criteria

1. WHEN a `ProfissionalUsuario` record is created with `perfil='administrador'`, THE Sistema SHALL invalidate the admin professional IDs cache for that loja
2. WHEN a `ProfissionalUsuario` record's `perfil` field is changed from or to `'administrador'`, THE Sistema SHALL invalidate the admin professional IDs cache for that loja
3. WHEN a `ProfissionalUsuario` record with `perfil='administrador'` is deleted, THE Sistema SHALL invalidate the admin professional IDs cache for that loja
