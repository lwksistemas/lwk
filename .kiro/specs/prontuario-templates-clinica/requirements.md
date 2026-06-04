# Requirements Document

## Introduction

Sistema de Prontuário Eletrônico e Templates de Documentos para a Clínica da Beleza. Permite que profissionais criem templates reutilizáveis de documentos clínicos (receituários manuais, pedidos de exames, atestados e documentos personalizados), gerem documentos durante consultas (com opção de usar templates ou texto livre), e visualizem/imprimam o prontuário completo do paciente organizado por seções, com geração de PDF timbrado.

## Glossary

- **Sistema_Templates**: Módulo responsável pelo CRUD de templates de documentos clínicos reutilizáveis
- **Sistema_Documentos**: Módulo responsável pela criação e persistência de documentos clínicos vinculados a consultas
- **Prontuario_Viewer**: Módulo responsável pela visualização consolidada do prontuário do paciente
- **Gerador_PDF**: Módulo responsável pela geração de PDFs com timbrado da clínica
- **Template**: Modelo reutilizável de documento clínico com placeholders para dados do paciente
- **Documento_Clinico**: Documento gerado durante uma consulta (receituário, pedido de exame, atestado ou documento personalizado)
- **Timbrado**: Cabeçalho e rodapé com dados da clínica (logo, nome, endereço, CNPJ) aplicado nos PDFs
- **Placeholder**: Marcador no template que é substituído por dados reais do paciente/profissional (ex: {{paciente_nome}}, {{data_atual}})
- **Consulta**: Atendimento clínico com status SCHEDULED, IN_PROGRESS ou COMPLETED
- **Profissional**: Usuário com perfil de profissional de saúde que realiza atendimentos

## Requirements

### Requirement 1: Gerenciamento de Templates

**User Story:** As a Profissional, I want to create and manage reusable document templates, so that I can quickly generate standardized clinical documents during consultations.

#### Acceptance Criteria

1. THE Sistema_Templates SHALL allow creation of templates with the fields: nome, tipo (receituario, pedido_exame, atestado, documento_personalizado), conteudo (rich text with placeholders), and profissional owner
2. WHEN a Profissional creates a template, THE Sistema_Templates SHALL validate that nome is not empty and tipo is one of the allowed values
3. THE Sistema_Templates SHALL support the following placeholders in template content: {{paciente_nome}}, {{paciente_cpf}}, {{paciente_data_nascimento}}, {{profissional_nome}}, {{profissional_registro}}, {{profissional_conselho}}, {{data_atual}}, {{consulta_procedimento}}
4. WHEN a Profissional requests the template list, THE Sistema_Templates SHALL return only templates owned by that Profissional, ordered by most recently updated
5. THE Sistema_Templates SHALL allow updating the nome, tipo, and conteudo of an existing template
6. THE Sistema_Templates SHALL allow soft-deletion of templates by setting is_active to false
7. WHEN a template is marked as inactive, THE Sistema_Templates SHALL exclude the template from listing results but preserve it for historical reference in previously generated documents

### Requirement 2: Criação de Documentos durante Consulta

**User Story:** As a Profissional, I want to create clinical documents during an active consultation using templates or free text, so that I can document prescriptions, exam requests, and certificates for the patient.

#### Acceptance Criteria

1. WHILE a Consulta has status IN_PROGRESS, THE Sistema_Documentos SHALL allow creation of new clinical documents
2. WHEN a Profissional chooses to create a document from a template, THE Sistema_Documentos SHALL replace all placeholders in the template content with actual patient, professional, and consultation data
3. WHEN a Profissional chooses to create a document with free text, THE Sistema_Documentos SHALL accept arbitrary rich text content without requiring a template
4. THE Sistema_Documentos SHALL store each document with: consulta reference, patient reference, professional reference, tipo (receituario, pedido_exame, atestado, documento_personalizado), conteudo (final rendered text), template reference (nullable), and creation timestamp
5. IF a Consulta has status COMPLETED, THEN THE Sistema_Documentos SHALL reject document creation with an appropriate error message
6. IF a Consulta has status SCHEDULED, THEN THE Sistema_Documentos SHALL reject document creation with an appropriate error message
7. WHEN a document is created, THE Sistema_Documentos SHALL associate the document with both the consulta and the patient for historical retrieval
8. THE Sistema_Documentos SHALL allow a Profissional to delete a document from a consulta while the status is IN_PROGRESS

### Requirement 3: Visualização do Prontuário

**User Story:** As a Profissional, I want to view the complete patient medical record organized by sections, so that I can review the full clinical history in one place.

#### Acceptance Criteria

1. THE Prontuario_Viewer SHALL present the patient record organized into the following sections: Receitas (prescriptions), Exames (exam requests), Atestados (certificates), Atendimento (consultation notes), Anamnese (clinical history), Evolução (evolution notes)
2. WHEN a Profissional requests the prontuário of a patient, THE Prontuario_Viewer SHALL aggregate documents from all completed and in-progress consultations for that patient
3. THE Prontuario_Viewer SHALL display documents within each section in reverse chronological order (most recent first)
4. WHEN a Profissional selects a specific section, THE Prontuario_Viewer SHALL display only documents of that section type
5. THE Prontuario_Viewer SHALL include Memed prescriptions (existing PrescricaoMemed records) in the Receitas section alongside manually created prescriptions
6. THE Prontuario_Viewer SHALL display for each document: date, professional name, consultation reference, and document content preview

### Requirement 4: Impressão Individual por Seção

**User Story:** As a Profissional, I want to print individual sections or documents from the patient record, so that I can provide physical copies to the patient as needed.

#### Acceptance Criteria

1. THE Prontuario_Viewer SHALL provide a print action for each individual document within a section
2. THE Prontuario_Viewer SHALL provide a print action for an entire section (all documents of that type for the patient)
3. WHEN a Profissional requests printing of a single document, THE Gerador_PDF SHALL generate a PDF containing only that document with the clinic letterhead
4. WHEN a Profissional requests printing of a full section, THE Gerador_PDF SHALL generate a PDF containing all documents of that section type in chronological order with the clinic letterhead
5. THE Prontuario_Viewer SHALL provide a print action for the complete prontuário (all sections combined)

### Requirement 5: Geração de PDF com Timbrado

**User Story:** As a Profissional, I want generated PDFs to include the clinic's letterhead (from the PDF already configured in Memed settings), so that printed documents have a professional and consistent appearance.

#### Acceptance Criteria

1. THE Gerador_PDF SHALL use the PDF letterhead (MemedTimbrado) already saved in the clinic's Memed configuration (/configuracoes/memed) as background for all generated documents
2. THE Gerador_PDF SHALL extract the header and footer areas from the saved timbrado PDF and apply them to each generated page
3. WHEN the clinic has a timbrado PDF saved (MemedTimbrado.pdf is not empty), THE Gerador_PDF SHALL overlay the document content in the available space between header and footer
4. THE Gerador_PDF SHALL include in the content area: professional name, professional registration (conselho + number), and generation date
5. WHEN a clinic has NOT configured a timbrado PDF, THE Gerador_PDF SHALL generate a text-only PDF with clinic name (from Loja.nome), address, and CNPJ in the header
6. THE Gerador_PDF SHALL produce PDF documents in A4 format with appropriate margins to accommodate the timbrado
7. THE Gerador_PDF SHALL render the document content preserving text formatting (bold, italic, lists, line breaks)

### Requirement 6: Reutilização do Timbrado Existente

**User Story:** As a Profissional (administrador), I want all clinic documents (receituários, exames, atestados) to automatically use the same letterhead configured in Memed settings, so that I don't need to configure the letterhead in multiple places.

#### Acceptance Criteria

1. THE Gerador_PDF SHALL read the timbrado from the existing MemedTimbrado model (table clinica_beleza_memed_timbrado) for the current loja
2. THE configuration page for the timbrado SHALL remain at /configuracoes/memed — no separate configuration is needed for document printing
3. WHEN the timbrado PDF is updated in /configuracoes/memed, THE Gerador_PDF SHALL immediately use the updated version for new document generations
4. THE system SHALL NOT require any additional upload or configuration beyond what is already done in /configuracoes/memed

### Requirement 7: Isolamento Multi-Tenant

**User Story:** As a system administrator, I want templates and documents to be isolated per clinic tenant, so that data from one clinic is never visible to another.

#### Acceptance Criteria

1. THE Sistema_Templates SHALL store templates with loja_id isolation using LojaIsolationMixin
2. THE Sistema_Documentos SHALL store documents with loja_id isolation using LojaIsolationMixin
3. WHEN a Profissional queries templates, THE Sistema_Templates SHALL filter results by the current tenant loja_id
4. WHEN a Profissional queries documents, THE Sistema_Documentos SHALL filter results by the current tenant loja_id
5. THE Gerador_PDF SHALL use the letterhead configuration belonging to the current tenant loja_id
