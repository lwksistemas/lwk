# Implementation Plan

## Overview

Implementação do sistema de Prontuário Eletrônico e Templates de Documentos para a Clínica da Beleza — backend (models, services, views) e frontend (páginas de templates, documentos na consulta e prontuário viewer).

## Tasks

- [x] 1. Criar models DocumentTemplate e DocumentoClinico com LojaIsolationMixin e gerar migrations
  - [x] 1.1 Criar model DocumentTemplate em models.py (campos: professional, nome, tipo, conteudo, is_active, created_at, updated_at)
    - _Requirements: 1.1, 7.1_
  - [x] 1.2 Criar model DocumentoClinico em models.py (campos: consulta, patient, professional, template, tipo, titulo, conteudo, created_at)
    - _Requirements: 2.4, 7.2_
  - [x] 1.3 Gerar migrations com makemigrations
    - _Requirements: 7.1, 7.2_
  - [x] 1.4 Criar tabelas em todos os schemas de lojas via SQL
    - _Requirements: 7.1, 7.2_

- [x] 2. Criar service layer documento_service.py com render_template, criar_documento e listar_prontuario_paciente
  - [x] 2.1 Implementar render_template(template_content, context) com substituição de placeholders
    - _Requirements: 1.3, 2.2_
  - [x] 2.2 Implementar criar_documento(consulta, professional, tipo, conteudo, template, titulo) com validação de status IN_PROGRESS
    - _Requirements: 2.1, 2.4, 2.5, 2.6, 2.7_
  - [x] 2.3 Implementar listar_prontuario_paciente(patient_id, secao) agregando DocumentoClinico + PrescricaoMemed + ConsultaEvolucao + PatientAnamnese por seção
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Criar service layer prontuario_pdf.py com geração de PDF timbrado
  - [x] 3.1 Implementar _resolver_cabecalho(loja_id) com prioridade MemedTimbrado > Loja.logo > texto
    - _Requirements: 5.1, 5.2, 5.5, 6.1_
  - [x] 3.2 Implementar gerar_pdf_documento(documento) para PDF individual com timbrado
    - _Requirements: 4.3, 5.3, 5.4, 5.6, 5.7_
  - [x] 3.3 Implementar gerar_pdf_secao(patient_id, secao) para PDF de todos os documentos de uma seção
    - _Requirements: 4.4, 5.6_
  - [x] 3.4 Implementar gerar_pdf_prontuario_completo(patient_id) para PDF completo
    - _Requirements: 4.5, 5.6_

- [x] 4. Criar serializers para templates, documentos e prontuário
  - [x] 4.1 Criar DocumentTemplateSerializer para CRUD de templates
    - _Requirements: 1.1, 1.4, 1.5_
  - [x] 4.2 Criar DocumentoClinicoSerializer para documentos da consulta
    - _Requirements: 2.4, 2.7_
  - [x] 4.3 Criar ProntuarioSectionSerializer para prontuário agrupado por seção
    - _Requirements: 3.1, 3.6_

- [x] 5. Checkpoint - Verificar services e serializers
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Criar views e URLs para gerenciamento de templates
  - [x] 6.1 Criar DocumentTemplateListView (GET lista + POST criar) com paginação
    - _Requirements: 1.1, 1.2, 1.4_
  - [x] 6.2 Criar DocumentTemplateDetailView (GET/PUT/DELETE) com GetObjectMixin
    - _Requirements: 1.5, 1.6, 1.7_
  - [x] 6.3 Registrar URLs /templates/ e /templates/<id>/
    - _Requirements: 1.1_

- [x] 7. Criar views e URLs para documentos da consulta
  - [x] 7.1 Criar ConsultaDocumentoListView (GET listar + POST criar) com validação de status IN_PROGRESS e render_template
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 7.2 Criar ConsultaDocumentoDeleteView (DELETE) com validação de status IN_PROGRESS
    - _Requirements: 2.8_
  - [x] 7.3 Registrar URLs /consultas/<id>/documentos/ e /consultas/<id>/documentos/<doc_id>/
    - _Requirements: 2.1_

- [x] 8. Criar views e URLs para prontuário e PDF
  - [x] 8.1 Criar ProntuarioView (GET prontuário agrupado por seção)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [x] 8.2 Criar ProntuarioPDFView (GET PDF por seção ou completo)
    - _Requirements: 4.2, 4.4, 4.5_
  - [x] 8.3 Criar DocumentoPDFView (GET PDF individual)
    - _Requirements: 4.1, 4.3_
  - [x] 8.4 Registrar URLs /patients/<id>/prontuario/, /patients/<id>/prontuario/pdf/, /documentos/<id>/pdf/
    - _Requirements: 3.1, 4.1_

- [x] 9. Checkpoint - Verificar backend completo
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Criar frontend da página de templates
  - [x] 10.1 Criar página /clinica-beleza/templates/ com listagem e filtro por tipo
    - _Requirements: 1.4_
  - [x] 10.2 Criar página /clinica-beleza/templates/novo com formulário (nome, tipo, conteúdo com dica de placeholders)
    - _Requirements: 1.1, 1.3_
  - [x] 10.3 Implementar edição via /templates/novo?id=X
    - _Requirements: 1.5_
  - [x] 10.4 Implementar exclusão (soft-delete) de templates
    - _Requirements: 1.6, 1.7_

- [x] 11. Criar frontend de criação de documentos na consulta
  - [x] 11.1 Adicionar seção Documentos na consulta (tab ou dentro de Atendimento)
    - _Requirements: 2.1_
  - [x] 11.2 Implementar botões Receituário, Exames, Atestado, Documento com opções Usar Memed, Usar Template, Digitar Manual
    - _Requirements: 2.2, 2.3_
  - [x] 11.3 Implementar fluxo Usar Template com select de templates + preview + confirmar
    - _Requirements: 2.2_
  - [x] 11.4 Implementar fluxo Digitar Manual com textarea de texto livre + salvar
    - _Requirements: 2.3_
  - [x] 11.5 Implementar lista de documentos já criados na consulta com opção de excluir
    - _Requirements: 2.8_

- [x] 12. Criar frontend do prontuário viewer
  - [x] 12.1 Criar página /clinica-beleza/pacientes/<id>/prontuario/
    - _Requirements: 3.1_
  - [x] 12.2 Implementar tabs Receitas, Exames, Atestados, Atendimento, Anamnese, Evolução
    - _Requirements: 3.1, 3.4_
  - [x] 12.3 Implementar carregamento de dados da API /patients/<id>/prontuario/?secao=X por tab
    - _Requirements: 3.2, 3.3, 3.5_
  - [x] 12.4 Implementar botão Imprimir por documento (PDF individual em nova aba)
    - _Requirements: 4.1, 4.3_
  - [x] 12.5 Implementar botão Imprimir Seção e Imprimir Prontuário Completo
    - _Requirements: 4.2, 4.4, 4.5_

- [x] 13. Checkpoint final - Deploy e validação
  - [x] 13.1 Rodar python3 manage.py check sem erros
    - _Requirements: 7.1, 7.2_
  - [x] 13.2 Rodar migrations em produção e criar tabelas em todos os schemas
    - _Requirements: 7.1, 7.2_
  - [x] 13.3 Deploy backend (Railway) e frontend (Vercel)
    - _Requirements: 7.1, 7.2_
  - [x] 13.4 Testar fluxo completo: criar template → usar na consulta → finalizar → ver prontuário → imprimir PDF
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1_

## Notes

- Task 1 já está completa (models e migrations criados)
- Tasks 2, 3 e 4 podem ser executadas em paralelo (todas dependem apenas de Task 1)
- Tasks de frontend (10, 11, 12) dependem das respectivas views/APIs do backend
- Task 13 (deploy) só pode ser executada após todas as outras estarem completas
- Tasks marcadas com `*` são opcionais e podem ser puladas para MVP mais rápido
- Cada task referencia requirements específicos para rastreabilidade
- Checkpoints garantem validação incremental

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1", "2.2", "2.3", "3.1", "4.1", "4.2", "4.3"] },
    { "id": 1, "tasks": ["3.2", "3.3", "3.4"] },
    { "id": 2, "tasks": ["6.1", "6.2", "6.3", "7.1", "7.2", "7.3"] },
    { "id": 3, "tasks": ["8.1", "8.2", "8.3", "8.4"] },
    { "id": 4, "tasks": ["10.1", "10.2", "10.3", "10.4", "11.1", "11.2"] },
    { "id": 5, "tasks": ["11.3", "11.4", "11.5", "12.1", "12.2", "12.3"] },
    { "id": 6, "tasks": ["12.4", "12.5"] },
    { "id": 7, "tasks": ["13.1", "13.2", "13.3", "13.4"] }
  ]
}
```
