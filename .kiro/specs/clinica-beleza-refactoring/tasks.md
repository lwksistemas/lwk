co# Tasks — Clinica da Beleza Refactoring

## Task 1: AgendaDeleteView usar GetObjectMixin
**Req:** 3 | **Risco:** Baixo | **Arquivo:** `backend/clinica_beleza/views_agenda.py`

- [ ] 1.1 Adicionar `GetObjectMixin` ao `AgendaDeleteView` com `model_class = Appointment` e `not_found_message = 'Agendamento não encontrado'`
- [ ] 1.2 Substituir o `try/except` inline por `self.object_or_404(pk)`
- [ ] 1.3 Rodar `python3 manage.py check` — 0 issues

## Task 2: Remover `_get_professional_or_404` redundante
**Req:** 1 | **Risco:** Baixo | **Arquivo:** `backend/clinica_beleza/views_profissionais.py`

- [ ] 2.1 Fazer `HorarioTrabalhoProfissionalView` herdar de `GetObjectMixin` com `model_class = Professional`
- [ ] 2.2 Fazer `ProfessionalCommissionView` herdar de `GetObjectMixin` com `model_class = Professional`
- [ ] 2.3 Substituir todas as chamadas `_get_professional_or_404(pk)` por `self.object_or_404(pk)`
- [ ] 2.4 Remover a função `_get_professional_or_404` do módulo
- [ ] 2.5 Rodar `python3 manage.py check` — 0 issues

## Task 3: Remover aliases deprecated do Patient
**Req:** 6 | **Risco:** Baixo | **Arquivos:** `backend/clinica_beleza/models/patients.py`, management command

- [ ] 3.1 Localizar o management command `popular_loja_clinica_beleza.py` e substituir `patient.name =` por `patient.nome =` e `patient.phone =` por `patient.telefone =`
- [ ] 3.2 Remover as properties `name`, `name.setter`, `phone`, `phone.setter` do model `Patient`
- [ ] 3.3 Rodar `python3 manage.py check` — 0 issues

## Task 4: Rate limiting em views públicas
**Req:** 4 | **Risco:** Médio | **Arquivos:** novo `throttles.py`, 3 views

- [ ] 4.1 Criar `backend/clinica_beleza/throttles.py` com `PublicConfirmacaoThrottle` (30/min), `PublicAssinaturaThrottle` (30/min), `PublicFotoThrottle` (10/min) usando `AnonRateThrottle`
- [ ] 4.2 Aplicar `throttle_classes = [PublicConfirmacaoThrottle]` em `ConfirmarAgendamentoPublicaView`
- [ ] 4.3 Aplicar `throttle_classes = [PublicAssinaturaThrottle]` em `ConsultaAssinaturaPublicaView`
- [ ] 4.4 Aplicar `throttle_classes = [PublicFotoThrottle]` em `EnviarFotoPublicaView`
- [ ] 4.5 Verificar que `DEFAULT_THROTTLE_CLASSES` está configurado no settings (ou configurar se ausente)
- [ ] 4.6 Rodar `python3 manage.py check` — 0 issues

## Task 5: Refatorar DashboardView.get()
**Req:** 5 | **Risco:** Médio | **Arquivo:** `backend/clinica_beleza/views_dashboard.py`

- [ ] 5.1 Extrair `_build_statistics(today, yesterday, period_start, period_end)` como método da classe
- [ ] 5.2 Extrair `_build_next_appointments(period, professional_id, today, current)` como método da classe
- [ ] 5.3 Refatorar `DashboardView.get()` para delegar às funções acima, mantendo a mesma estrutura de resposta JSON e comportamento de cache
- [ ] 5.4 Confirmar que a resposta JSON tem os mesmos campos que antes
- [ ] 5.5 Rodar `python3 manage.py check` — 0 issues

## Task 6: Atualizar docstrings — ClienteSearchMixin e catalog files
**Req:** 10, 11 | **Risco:** Baixo | **Arquivos:** `core/mixins.py`, 3 catalog files

- [ ] 6.1 Atualizar docstring do `ClienteSearchMixin` em `core/mixins.py` indicando que é consumido por `clinica_estetica` e `cabeleireiro`
- [ ] 6.2 Adicionar module docstring em `estoque_catalogo.py`
- [ ] 6.3 Adicionar module docstring em `procedimentos_catalogo.py`
- [ ] 6.4 Adicionar module docstring em `termos_consentimento_catalogo.py`

## Task 7: Hook `useOfflineSave` reutilizável
**Req:** 7 | **Risco:** Médio | **Arquivo:** novo `frontend/hooks/clinica-beleza/useOfflineSave.ts`

- [ ] 7.1 Criar `hooks/clinica-beleza/useOfflineSave.ts` com interface `UseOfflineSaveOptions<T>` e implementação completa do hook
- [ ] 7.2 O hook deve detectar estado offline, salvar na fila de sync, gerar ID temporário, e fazer fallback online → offline
- [ ] 7.3 Verificar `getDiagnostics` no arquivo novo — sem erros TypeScript

## Task 8: Padronizar lista de pacientes com EntityListTable
**Req:** 8 | **Risco:** Médio | **Arquivo:** `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/pacientes/page.tsx`

- [ ] 8.1 Substituir o `<table>` inline da lista de pacientes pelo componente `EntityListTable`
- [ ] 8.2 Definir as 7 colunas: avatar, nome (com badge offline), telefone, e-mail, CPF, convênio, ações
- [ ] 8.3 Preservar `onRowClick={openEdit}`, hover style e `EntityListLoadMore`
- [ ] 8.4 Verificar `getDiagnostics` — sem erros TypeScript

## Task 9: Extrair utilitários de form de pacientes
**Req:** 9 | **Risco:** Médio | **Novos arquivos no módulo de pacientes**

- [ ] 9.1 Criar `pacientes/lib/paciente-form-utils.ts` com funções `patientToForm()` e `montarEnderecoPaciente()`
- [ ] 9.2 Atualizar imports em `pacientes/page.tsx`
- [ ] 9.3 Verificar `getDiagnostics` — sem erros TypeScript

## Task 10: Refatorar pacientes/page.tsx — split de componentes
**Req:** 9 | **Risco:** Alto | **Arquivos:** `pacientes/page.tsx` + novos componentes

- [ ] 10.1 Criar hook `hooks/clinica-beleza/usePacienteForm.ts` para estado do form + CEP lookup + convenios
- [ ] 10.2 Criar componente `pacientes/components/PacienteListView.tsx` com a renderização da lista e paginação
- [ ] 10.3 Refatorar `pacientes/page.tsx` para orquestração apenas: routing (lista vs form), delegates para `PacienteListView` e `PacienteCadastroForm`
- [ ] 10.4 Usar `useOfflineSave` (Task 7) na função `save()` do formulário
- [ ] 10.5 Garantir que `pacientes/page.tsx` fique com ≤ 150 linhas
- [ ] 10.6 Verificar `getDiagnostics` em todos os arquivos modificados — sem erros TypeScript

## Task 11: Deploy e validação
**Risco:** Baixo | **Ambos os ambientes**

- [ ] 11.1 Rodar `python3 manage.py check` no backend — 0 issues
- [ ] 11.2 Rodar `getDiagnostics` nos arquivos frontend modificados — sem erros
- [ ] 11.3 Commit: `refactor(clinica-beleza): unificar padrões, rate limiting, extrair hooks`
- [ ] 11.4 Deploy backend beta: `npx railway up --detach -e staging`
- [ ] 11.5 Deploy frontend beta: `npx vercel --yes` (em `/frontend`, branch `staging`)
- [ ] 11.6 Validar em `https://beta.lwksistemas.com.br` — agenda, pacientes, dashboard funcionando
- [ ] 11.7 Deploy produção backend: `npx railway up --detach`
- [ ] 11.8 Deploy produção frontend: `npx vercel --prod --yes` (em `/frontend`)
