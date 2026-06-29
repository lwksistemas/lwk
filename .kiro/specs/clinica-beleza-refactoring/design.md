# Technical Design — Clinica da Beleza Refactoring

## Overview

Refatoração incremental do app `clinica_beleza` para eliminar redundâncias, unificar padrões e melhorar manutenibilidade sem alterar comportamento externo.

---

## Req 1 — Eliminar `_get_professional_or_404`

### Situação atual
`views_profissionais.py` define uma função standalone:
```python
def _get_professional_or_404(pk):
    try:
        return Professional.objects.get(pk=pk), None
    except Professional.DoesNotExist:
        return None, Response({'error': 'Profissional não encontrado'}, status=404)
```
Usada em `HorarioTrabalhoProfissionalView` e `ProfessionalCommissionView`.

### Solução
Fazer `HorarioTrabalhoProfissionalView` e `ProfessionalCommissionView` herdarem de `GetObjectMixin`:

```python
class HorarioTrabalhoProfissionalView(GetObjectMixin, APIView):
    model_class = Professional
    not_found_message = 'Profissional não encontrado'

    def get(self, request, pk):
        professional, err = self.object_or_404(pk)
        if err: return err
        ...

class ProfessionalCommissionView(GetObjectMixin, APIView):
    model_class = Professional
    not_found_message = 'Profissional não encontrado'
    ...
```

Remover a função `_get_professional_or_404` e os 2 pontos de uso.

---

## Req 2 — Unificar field-mapping

### Situação atual
Cada view define seu próprio mapper:
- `views_pacientes._map_patient_data()` — já usa `map_field_names()` ✅
- `views_profissionais._map_professional_data()` — usa `map_field_names()` mas tem lógica extra de coerção de tipos

### Solução
Manter os mappers existentes pois já usam `map_field_names()`. Apenas garantir que **nenhuma view** faça renaming inline fora dos mappers. `_map_professional_data` pode reter type-coercion (string→bool, empty→None) que é específico de negócio.

Nenhuma mudança estrutural necessária — padrão já está correto.

---

## Req 3 — AgendaDeleteView usar GetObjectMixin

### Situação atual
```python
class AgendaDeleteView(APIView):
    def delete(self, request, pk):
        try:
            Appointment.objects.get(pk=pk).delete()
            return Response(status=204)
        except Appointment.DoesNotExist:
            return Response({'error': '...'}, status=404)
```

### Solução
```python
class AgendaDeleteView(GetObjectMixin, APIView):
    permission_classes = CLINICA_MEMBER
    model_class = Appointment
    not_found_message = 'Agendamento não encontrado'

    def delete(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

---

## Req 4 — Rate limiting em views públicas

### Solução
Criar classes de throttle DRF em `clinica_beleza/throttles.py`:

```python
from rest_framework.throttling import AnonRateThrottle

class PublicConfirmacaoThrottle(AnonRateThrottle):
    rate = '30/min'

class PublicAssinaturaThrottle(AnonRateThrottle):
    rate = '30/min'

class PublicFotoThrottle(AnonRateThrottle):
    rate = '10/min'
```

Aplicar nas views:
```python
class ConfirmarAgendamentoPublicaView(APIView):
    throttle_classes = [PublicConfirmacaoThrottle]
    ...

class ConsultaAssinaturaPublicaView(APIView):
    throttle_classes = [PublicAssinaturaThrottle]
    ...

class EnviarFotoPublicaView(APIView):
    throttle_classes = [PublicFotoThrottle]
    ...
```

Adicionar em `settings_production.py`:
```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
    }
}
```

---

## Req 5 — Refatorar DashboardView.get()

### Situação atual
`DashboardView.get()` tem ~100 linhas com: parse de período, cache, 8 queries, montagem do JSON.

### Solução
Extrair 3 helpers privados na mesma view:

```python
class DashboardView(APIView):

    def get(self, request):
        # ~25 linhas: cache check, build data, cache.set, return
        ...

    def _build_statistics(self, today, yesterday, period_start, period_end):
        # queries de contagem e soma
        ...

    def _build_next_appointments(self, period, professional_id, today, current):
        # queryset próximos agendamentos
        ...
```

`_revenue_by_day`, `_top_procedures_realizados_periodo`, `_top_soroterapia_periodo` já são module-level — manter como estão.

---

## Req 6 — Remover aliases deprecated do Patient

### Arquivo: `models/patients.py`
Remover as properties `name`/`name.setter`/`phone`/`phone.setter`.

### Arquivo: `management/commands/popular_loja_clinica_beleza.py`
Substituir `patient.name =` por `patient.nome =` e `patient.phone =` por `patient.telefone =`.

---

## Req 7 — Hook `useOfflineSave`

### Novo arquivo: `frontend/hooks/clinica-beleza/useOfflineSave.ts`

```typescript
interface UseOfflineSaveOptions<T> {
  entityType: string;
  saveOnline: (body: unknown) => Promise<void>;
  onSuccess: () => void;
  list: T[];
  setList: (list: T[]) => void;
  saveOffline: (list: T[]) => Promise<void>;
  buildNewEntity: (body: unknown, tempId: number) => T;
  getEntityId: (entity: T) => number;
}

export function useOfflineSave<T>(options: UseOfflineSaveOptions<T>) {
  const save = async (body: unknown, editing: T | null) => {
    // 1. Se offline → salva direto na fila
    // 2. Tenta online → se falhar com network error → salva na fila
    // 3. Retorna { ok: true, offline: boolean }
  };
  return { save };
}
```

### Refatoração de `pacientes/page.tsx`
A função `save()` que tem ~100 linhas passa a:
```typescript
const { save: offlineSave } = useOfflineSave({...});

const save = async () => {
  if (!form.name.trim()) { setError('Nome é obrigatório.'); return; }
  setSaving(true);
  const body = buildBody(form);
  const result = await offlineSave(body, editing);
  if (result.offline) alert('Salvo offline...');
  if (result.ok) { voltarLista(); load(); }
  else setError(result.error);
  setSaving(false);
};
```

---

## Req 8 — Padronizar lista de pacientes com EntityListTable

### Situação atual
`pacientes/page.tsx` usa `<table>` inline de ~80 linhas.

### Solução
Substituir pelo `EntityListTable` com colunas declarativas:
```typescript
<EntityListTable
  rows={activeList}
  rowKey={(p) => p.id}
  onRowClick={openEdit}
  columns={[
    { key: 'avatar', header: '', render: (p) => <PacienteAvatar ... /> },
    { key: 'nome', header: 'Nome', render: (p) => <NomeCell p={p} /> },
    { key: 'telefone', header: 'Telefone', render: (p) => formatTelefone(entityPhone(p)) || '—' },
    { key: 'email', header: 'E-mail', className: 'hidden sm:table-cell', render: (p) => entityEmail(p) || '—' },
    { key: 'cpf', header: 'CPF', className: 'hidden lg:table-cell', render: (p) => formatCpf(patientCpf(p)) || '—' },
    { key: 'convenio', header: 'Convênio', className: 'hidden md:table-cell', render: (p) => p.convenio_name || CONVENIO_PARTICULAR_LABEL },
    { key: 'acoes', header: 'Ações', render: (p) => <AcoesCell p={p} /> },
  ]}
/>
```

---

## Req 9 — Refatorar pacientes/page.tsx

### Estrutura alvo

```
frontend/app/(dashboard)/loja/[slug]/clinica-beleza/pacientes/
  page.tsx                          ← orquestração, ~120 linhas
  components/
    PacienteCadastroForm.tsx        ← já existe
    PacienteListView.tsx            ← novo: renderização da lista
  lib/
    paciente-form-utils.ts          ← novo: patientToForm(), montarEnderecoPaciente()
hooks/clinica-beleza/
  useOfflineSave.ts                 ← novo (Req 7)
  usePacienteForm.ts                ← novo: estado do form + CEP lookup
```

---

## Req 10 — ClienteSearchMixin — manter, documentar

Atualizar docstring em `core/mixins.py` para listar apps consumidoras.

---

## Req 11 — Catalog files — manter, documentar

Adicionar module docstrings nos 3 arquivos de catálogo.

---

## Ordem de implementação (por risco/impacto)

| # | Item | Risco | Esforço |
|---|------|-------|---------|
| 1 | Req 3 — AgendaDeleteView GetObjectMixin | Baixo | 15 min |
| 2 | Req 1 — Remover `_get_professional_or_404` | Baixo | 20 min |
| 3 | Req 6 — Remover aliases deprecated Patient | Baixo | 15 min |
| 4 | Req 4 — Rate limiting views públicas | Médio | 30 min |
| 5 | Req 5 — Refatorar DashboardView | Médio | 45 min |
| 6 | Req 10/11 — Docstrings | Baixo | 15 min |
| 7 | Req 7 — Hook useOfflineSave | Médio | 60 min |
| 8 | Req 8 — EntityListTable em pacientes | Médio | 45 min |
| 9 | Req 9 — Split pacientes/page.tsx | Alto | 90 min |
