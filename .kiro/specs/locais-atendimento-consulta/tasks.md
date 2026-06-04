# Implementation Plan: Locais de Atendimento — Consulta

## Overview

Implementar o modelo `LocalAtendimento`, API CRUD, modal de gerenciamento e integração com o fluxo de criação de consultas no módulo Clínica da Beleza. Backend em Python/Django, frontend em TypeScript/Next.js.

## Tasks

- [x] 1. Criar modelo e migração do LocalAtendimento
  - [x] 1.1 Criar modelo `LocalAtendimento` em `backend/clinica_beleza/models.py`
    - Adicionar classe `LocalAtendimento` com `LojaIsolationMixin`
    - Campos: `nome` (CharField 200), `valor_consulta` (DecimalField 10,2), `is_active` (BooleanField default=True), `created_at`, `updated_at`
    - Configurar `LojaIsolationManager` como manager padrão
    - Meta: `db_table='clinica_beleza_locais_atendimento'`, `ordering=['nome']`
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 1.2 Adicionar FK `local_atendimento` no modelo `Consulta`
    - ForeignKey para `LocalAtendimento`, `on_delete=SET_NULL`, `null=True`, `blank=True`
    - `related_name='consultas'`
    - _Requisitos: 5.1_

  - [x] 1.3 Gerar e aplicar migration
    - Rodar `python3 manage.py makemigrations clinica_beleza`
    - Verificar migration gerada
    - _Requisitos: 1.1, 1.2, 5.1_

- [x] 2. Criar serializer e views da API
  - [x] 2.1 Criar `LocalAtendimentoSerializer` em `backend/clinica_beleza/serializers.py`
    - Fields: `id`, `nome`, `valor_consulta`, `is_active`, `created_at`, `updated_at`
    - Read-only: `id`, `is_active`, `created_at`, `updated_at`
    - Validação de `nome`: não vazio, não apenas whitespace, strip
    - Validação de `valor_consulta`: não nulo, >= 0
    - _Requisitos: 1.3, 1.4, 2.5, 2.6_

  - [x] 2.2 Criar `views_locais_atendimento.py` com `LocalAtendimentoListView` e `LocalAtendimentoDetailView`
    - `LocalAtendimentoListView` (GET: listar ativos da loja; POST: criar novo)
    - `LocalAtendimentoDetailView` (GET: detalhe; PUT: atualizar; DELETE: soft delete via is_active=False)
    - Usar `APIView` + `GetObjectMixin`, `resolve_loja_id_from_request()`
    - Filtrar apenas `is_active=True` no GET de listagem
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.7_

  - [x] 2.3 Registrar URLs em `backend/clinica_beleza/urls.py`
    - `locais-atendimento/` → `LocalAtendimentoListView`
    - `locais-atendimento/<int:pk>/` → `LocalAtendimentoDetailView`
    - _Requisitos: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 2.4 Escrever teste de propriedade — Round-trip de criação
    - **Property 1: Round-trip de criação de Local de Atendimento**
    - Gerar nomes (1-200 chars, não whitespace) e valores (Decimal >= 0), criar via serializer, verificar que dados retornados são idênticos
    - **Valida: Requisitos 1.1, 2.2**

  - [ ]* 2.5 Escrever teste de propriedade — Rejeição de whitespace
    - **Property 3: Rejeição de nome vazio ou whitespace**
    - Gerar strings compostas inteiramente de whitespace, verificar rejeição pelo serializer
    - **Valida: Requisitos 1.3, 2.5**

  - [ ]* 2.6 Escrever teste de propriedade — Rejeição de valor negativo
    - **Property 4: Rejeição de valor negativo**
    - Gerar Decimals negativos, verificar rejeição pelo serializer
    - **Valida: Requisitos 1.4, 2.6**

- [x] 3. Checkpoint — Verificar backend
  - Rodar `python3 manage.py check`, garantir 0 issues
  - Garantir que todos os testes passam, perguntar ao usuário se surgirem dúvidas.

- [x] 4. Integrar local de atendimento no fluxo de consulta
  - [x] 4.1 Alterar `ConsultaSerializer` para incluir `local_atendimento` e `local_atendimento_name`
    - Adicionar campo `local_atendimento` (PK, write) e `local_atendimento_name` (read-only, source='local_atendimento.nome')
    - _Requisitos: 5.1, 5.4_

  - [x] 4.2 Alterar `consulta_service.py` — função `criar_consulta_avulsa`
    - Aceitar parâmetro opcional `local_atendimento` (ID)
    - Se `local_atendimento` informado e valor não fornecido manualmente, usar `valor_consulta` do local
    - Se valor fornecido manualmente (override), usar o valor informado
    - Salvar FK `local_atendimento` na consulta criada
    - _Requisitos: 4.5, 5.1, 5.2, 5.3_

  - [ ]* 4.3 Escrever teste de propriedade — Soft delete oculta da listagem
    - **Property 5: Soft delete oculta da listagem ativa**
    - Criar N locais, soft-deletar subconjunto aleatório, verificar que GET retorna apenas ativos
    - **Valida: Requisitos 1.6, 2.1, 2.4**

  - [ ]* 4.4 Escrever teste de propriedade — Valor com override
    - **Property 8: Consulta armazena local e valor com suporte a override**
    - Gerar locais com valores aleatórios + override opcional, criar consulta, verificar valor armazenado correto
    - **Valida: Requisitos 4.5, 5.2, 5.3**

- [x] 5. Checkpoint — Verificar integração backend
  - Garantir que todos os testes passam, perguntar ao usuário se surgirem dúvidas.

- [x] 6. Implementar frontend — Tipos e API
  - [x] 6.1 Adicionar interface `LocalAtendimento` e atualizar tipo `Consulta` em `consultas-types.ts`
    - Interface `LocalAtendimento` com campos: `id`, `nome`, `valor_consulta`, `is_active`, `created_at`, `updated_at`
    - Adicionar `local_atendimento?: number | null` e `local_atendimento_name?: string | null` na interface `Consulta`
    - Arquivo: `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/consultas/components/consultas-types.ts`
    - _Requisitos: 5.1, 5.4_

  - [x] 6.2 Criar funções de API para locais de atendimento
    - Funções: `fetchLocaisAtendimento`, `createLocalAtendimento`, `updateLocalAtendimento`, `deleteLocalAtendimento`
    - Usar `clinicaBelezaFetch` existente do projeto
    - Arquivo: criar em `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/consultas/components/locais-atendimento-api.ts` ou adicionar ao arquivo de API existente
    - _Requisitos: 2.1, 2.2, 2.3, 2.4_

- [x] 7. Implementar frontend — Modal CRUD de Locais
  - [x] 7.1 Criar componente `LocaisAtendimentoModal`
    - Lista de locais com nome e valor formatado (R$ X,XX)
    - Formulário inline para adicionar/editar (campos: nome, valor)
    - Botão excluir com `confirm()` de confirmação
    - Atualização da lista sem reload (estado local)
    - Tratamento de erros com feedback ao usuário
    - Arquivo: `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/consultas/components/LocaisAtendimentoModal.tsx`
    - _Requisitos: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 7.2 Adicionar botão engrenagem na `ConsultasPage` para abrir modal
    - Usar prop `extraActions` do `ClinicaBelezaStandardPageHeader`
    - Ícone de engrenagem (Settings/Cog do lucide-react)
    - Controlar visibilidade do `LocaisAtendimentoModal` via estado
    - Arquivo: `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/consultas/page.tsx`
    - _Requisitos: 3.1, 3.2_

- [ ] 8. Implementar frontend — Integração com NovaConsultaModal
  - [x] 8.1 Adicionar dropdown de local e auto-preenchimento de valor na `NovaConsultaModal`
    - Carregar locais ativos via API ao abrir modal
    - Se existem locais: exibir dropdown de seleção
    - Ao selecionar local: auto-preencher campo `valor_consulta` (campo permanece editável para override)
    - Se não existem locais: ocultar dropdown, manter comportamento atual
    - Enviar `local_atendimento` e `valor_consulta` no payload de criação
    - Arquivo: `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/consultas/components/NovaConsultaModal.tsx`
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.6_

  - [x] 8.2 Exibir nome do local nos detalhes da consulta na listagem
    - Mostrar `local_atendimento_name` quando disponível na tabela/detalhes da consulta
    - Arquivo: `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/consultas/page.tsx`
    - _Requisitos: 5.4_

- [x] 9. Checkpoint final — Verificar tudo
  - Rodar `python3 manage.py check` no backend
  - Verificar `getDiagnostics` nos arquivos frontend alterados
  - Garantir que todos os testes passam, perguntar ao usuário se surgirem dúvidas.

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Testes de propriedade validam propriedades universais de corretude do design
- Após deploy, será necessário rodar o SQL `CREATE TABLE IF NOT EXISTS` da nova tabela em todos os schemas ativos

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "6.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "6.2"] },
    { "id": 4, "tasks": ["2.4", "2.5", "2.6", "4.1"] },
    { "id": 5, "tasks": ["4.2", "7.1"] },
    { "id": 6, "tasks": ["4.3", "4.4", "7.2"] },
    { "id": 7, "tasks": ["8.1"] },
    { "id": 8, "tasks": ["8.2"] }
  ]
}
```
