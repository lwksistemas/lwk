# Relatório de Refatoração e Otimização - Frontend

**Data:** 2026-03-14

## Resumo Executivo

O frontend apresenta oportunidades de refatoração e otimização em **5 áreas**: templates duplicados, componentes grandes, performance, padrões de código e Tailwind/CSS. A prioridade geral é **alta** para templates e componentes, **média** para performance e padrões.

---

## 1. TEMPLATES DO DASHBOARD

### 1.1 Arquivo Órfão

| Arquivo | Status | Ação |
|---------|--------|------|
| `app/(dashboard)/loja/[slug]/dashboard/templates/servicos-modals.tsx` | ✅ Removido (2026-03-14) | Era duplicata; `servicos.tsx` usa `@/components/servicos/modals`. |

### 1.2 Duplicação Entre Templates

| Padrão | clinica-estetica | clinica-beleza | cabeleireiro | servicos | restaurante |
|--------|------------------|----------------|--------------|----------|-------------|
| ActionButton/Shortcut | `@/components/dashboard` | inline | `ShortcutCard` | inline local | `restaurante-shared` |
| StatCard | `@/components/dashboard` | inline | `@/components/cabeleireiro` | inline local | `restaurante-shared` |
| EmptyState | `@/components/dashboard` | não usa | não usa | inline local | `restaurante-shared` |
| Loading | `DashboardSkeleton` | spinner inline | spinner inline | `DashboardSkeleton` | `DashboardSkeleton` |

### 1.3 Recomendações

| Prioridade | Ação |
|------------|------|
| **Alta** | Remover ou integrar `servicos-modals.tsx` (código morto) |
| **Alta** | Padronizar uso de `@/components/dashboard` em `servicos.tsx` e `restaurante.tsx` |
| **Média** | Extrair componentes de `clinica-beleza.tsx` (~560 linhas) para `@/components/dashboard` |
| **Média** | Criar `DashboardLayoutBase` com header, ações rápidas e estatísticas |

---

## 2. COMPONENTES GRANDES

### 2.1 Componentes com Mais de 200 Linhas

| Arquivo | Linhas | Prioridade |
|---------|--------|------------|
| `CalendarioAgendamentos.tsx` | **1701** | Alta |
| `GerenciadorConsultas.tsx` | **1203** | Alta |
| `ModalNovaLoja.tsx` | 924 | Média |
| `SidebarCrm.tsx` | 496 | Média |
| `ModalAnamnese.tsx` | 619 | Média |
| `clinica-beleza.tsx` | 560 | Média |
| `ModalFinanceiro.tsx` | 463 | Baixa |
| `ModalAgendamentos.tsx` (cabeleireiro) | 441 | Baixa |

### 2.2 Violações de SRP (Single Responsibility)

1. **CalendarioAgendamentos.tsx** – Mistura: calendário, menu de status, formulário, lista, lógica de API  
   - Extrair: `AgendamentoForm`, `AgendamentoList`, `StatusMenu`, `useCalendarioData`

2. **GerenciadorConsultas.tsx** – Muitas responsabilidades em um único componente

3. **clinica-beleza.tsx** – Mistura: layout, modal WhatsApp, dashboard  
   - Extrair: `ClinicaBelezaHeader`, `ClinicaBelezaSidebar`, `ModalConfigWhatsApp`

### 2.3 Duplicação de Modais CRUD

- Padrão repetido: `loadDados` → `useEffect` → `handleNovo` → `handleEditar` → `handleExcluir` → `handleSubmit`
- `CrudModal` e `useCrudForm` existem em `clinica/shared` mas não são usados em todos os modais
- Recomendação: padronizar modais CRUD com `CrudModal`/`useCrudForm`

---

## 3. PERFORMANCE

### 3.1 Lazy Loading

| Local | Status |
|-------|--------|
| `dashboard/page.tsx` | OK – `dynamic()` para templates |
| `clinica-estetica.tsx` | OK – `lazy()` para modais |
| `restaurante.tsx` | OK – `dynamic()` para modais |
| `servicos.tsx` | ✅ Corrigido – `lazy()` + Suspense para modais |
| `cabeleireiro` | ✅ Corrigido – `lazy()` + Suspense para modais |
| `crm-vendas` | OK – `dynamic()` para SalesChart e FullCalendar |

### 3.2 Recomendações

| Prioridade | Ação |
|------------|------|
| **Alta** | Aplicar `dynamic()` ou `lazy()` aos modais em `servicos.tsx` e `dashboard-cabeleireiro-novo.tsx` |
| **Média** | Adicionar `@next/bundle-analyzer` para identificar chunks grandes |
| **Média** | Otimizar estado em `clinica-beleza` (muitos `useState` → considerar `useReducer` ou Zustand) |
| **Baixa** | Ampliar `remotePatterns` para imagens da API e usar `next/image` |

---

## 4. PADRÕES E ORGANIZAÇÃO

### 4.1 API Client

| Cliente | Uso |
|---------|-----|
| `apiClient` | superadmin, auth, loja info |
| `clinicaApiClient` | clinica-estetica, servicos, restaurante, cabeleireiro |
| `fetch` + `getClinicaBelezaHeadersWithLoja` | clinica-beleza |

- **Problema:** `clinica-beleza` usa API própria (`lib/clinica-beleza-api.ts`) em vez de `clinicaApiClient`
- **Recomendação:** Unificar com `clinicaApiClient` ou abstrair em um único cliente

### 4.2 Hooks

- Hooks em `hooks/` e em `components/clinica/hooks/`
- `useCrudForm` pouco reutilizado
- Recomendação: centralizar em `hooks/` e documentar

### 4.3 Estado: Context vs Zustand

- **Context:** ThemeProvider, Toast, CRMConfigContext
- **Zustand:** `store/crm-ui.ts`, `lib/tenant.ts`
- Recomendação: documentar critério (Context para UI global, Zustand para domínio)

---

## 5. TAILWIND / CSS

### 5.1 Classes Repetidas

| Padrão | Sugestão |
|--------|----------|
| `bg-white dark:bg-gray-800` | Componente `Card` |
| `rounded-xl shadow-lg` | `Card` |
| `px-3 py-2 border border-gray-300 dark:border-gray-600` | `Input` em `@/components/ui` |
| `hover:bg-gray-50 dark:hover:bg-gray-700` | `Button` variant |

### 5.2 Recomendações

| Prioridade | Ação |
|------------|------|
| **Média** | Criar `DashboardCard`, `DashboardButton` com variantes |
| **Média** | Usar `@/components/ui/button` e `@/components/ui/input` nos formulários |
| **Baixa** | Revisar `card-hover` e `btn-press` em `globals.css` |

---

## Ordem Sugerida de Refatoração

1. **Remover** `servicos-modals.tsx` (órfão)
2. **Padronizar** uso de `@/components/dashboard` em servicos e restaurante
3. **Aplicar** lazy loading aos modais de servicos e cabeleireiro
4. **Dividir** `CalendarioAgendamentos.tsx` em subcomponentes e hooks
5. **Dividir** `GerenciadorConsultas.tsx` em subcomponentes
6. **Unificar** API da clínica beleza com o restante do app
7. **Extrair** modal de WhatsApp de `clinica-beleza.tsx`
8. **Adicionar** bundle analyzer e revisar chunks
