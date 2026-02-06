# 📋 Mapeamento: Correções por Tipo de Loja/App

## 🎯 Correções Implementadas

### ✅ App Cabeleireiro (COMPLETO)

**Localização**: `frontend/components/cabeleireiro/modals/`

#### Modais Refatorados (Boas Práticas)
1. ✅ **ModalClientes.tsx** (v408)
   - Código independente (300 linhas)
   - Usa `apiClient` padrão
   - Helpers reutilizáveis
   - Endpoint: `/cabeleireiro/clientes/`

2. ✅ **ModalServicos.tsx** (v411)
   - Código independente (280 linhas)
   - Campo `categoria` adicionado
   - Endpoint: `/cabeleireiro/servicos/`

3. ✅ **ModalFuncionarios.tsx** (v415)
   - Código independente (320 linhas)
   - Campos: cargo, funcao, especialidade
   - Endpoint: `/cabeleireiro/funcionarios/`
   - Badge "Admin" para admin da loja

4. ✅ **ModalAgendamentos.tsx**
   - Usa helpers `extractArrayData`
   - Endpoint: `/cabeleireiro/agendamentos/`

#### Backend
- ✅ Paginação desabilitada (v409)
- ✅ Sincronização Funcionario → Profissional (v416)
- ✅ Modelo Funcionario com campos corretos

---

## ⚠️ Apps que Precisam das Mesmas Correções

### 1. App Clínica Estética

**Localização**: `frontend/components/clinica/modals/`

#### Status Atual
- ❌ **ModalFuncionarios.tsx** - Precisa refatoração
  - Ainda usa estrutura antiga
  - Não tem helpers reutilizáveis
  - Endpoint: `/clinica_estetica/funcionarios/` (?)

#### Correções Necessárias
1. Refatorar ModalFuncionarios (seguir padrão v415)
2. Adicionar helpers `extractArrayData`, `formatApiError`
3. Verificar endpoint correto
4. Adicionar campos: cargo, funcao, especialidade
5. Badge "Admin" para admin da loja

---

### 2. App Serviços

**Localização**: `frontend/components/servicos/modals/`

#### Status Atual
- ❌ **ModalFuncionarios.tsx** - Usa ModalBase (problemático)
  ```typescript
  export function ModalFuncionarios({ loja, onClose }) {
    return (
      <ModalBase  // ❌ Problemático
        loja={loja}
        onClose={onClose}
        ...
      />
    );
  }
  ```

#### Correções Necessárias
1. Remover dependência do ModalBase
2. Criar código independente (seguir padrão v415)
3. Adicionar helpers reutilizáveis
4. Endpoint: `/servicos/funcionarios/`
5. Campos: cargo, funcao, especialidade

---

### 3. App CRM Vendas

**Localização**: `frontend/components/crm-vendas/modals/`

#### Status Atual
- ❌ **ModalFuncionarios.tsx** - Usa `clinicaApiClient` (ERRADO!)
  ```typescript
  import { clinicaApiClient } from '@/lib/api-client';  // ❌ ERRADO
  ```

#### Correções Necessárias
1. Trocar `clinicaApiClient` por `apiClient` padrão
2. Refatorar seguindo padrão v415
3. Adicionar helpers reutilizáveis
4. Endpoint: `/crm_vendas/funcionarios/` (?)
5. Campos: cargo, funcao, especialidade

---

### 4. App Restaurante

**Localização**: `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/restaurante/ModalsAll.tsx`

#### Status Atual
- ❌ **ModalFuncionarios** - Dentro de ModalsAll.tsx
  - Código inline (não componentizado)
  - Não usa helpers reutilizáveis

#### Correções Necessárias
1. Extrair para arquivo separado
2. Refatorar seguindo padrão v415
3. Adicionar helpers reutilizáveis
4. Endpoint: `/restaurante/funcionarios/` (?)
5. Campos: cargo, funcao, especialidade

---

## 📊 Resumo de Status

| App | ModalFuncionarios | Helpers | Endpoint Correto | Badge Admin | Status |
|-----|-------------------|---------|------------------|-------------|--------|
| **Cabeleireiro** | ✅ Refatorado | ✅ Sim | ✅ `/cabeleireiro/funcionarios/` | ✅ Sim | ✅ **COMPLETO** |
| **Clínica** | ❌ Antigo | ❌ Não | ⚠️ Verificar | ❌ Não | ❌ **PENDENTE** |
| **Serviços** | ❌ ModalBase | ❌ Não | ⚠️ Verificar | ❌ Não | ❌ **PENDENTE** |
| **CRM Vendas** | ❌ clinicaApiClient | ❌ Não | ⚠️ Verificar | ❌ Não | ❌ **PENDENTE** |
| **Restaurante** | ❌ Inline | ❌ Não | ⚠️ Verificar | ❌ Não | ❌ **PENDENTE** |

---

## 🎯 Estratégia de Replicação

### Opção 1: Replicar Manualmente (Recomendado)
Criar ModalFuncionarios específico para cada app seguindo o padrão do Cabeleireiro.

**Vantagens**:
- ✅ Código adaptado para cada app
- ✅ Endpoints específicos
- ✅ Campos específicos de cada negócio

**Desvantagens**:
- ❌ Mais trabalho inicial
- ❌ Manutenção em múltiplos arquivos

### Opção 2: Componente Genérico Reutilizável
Criar um ModalFuncionariosBase genérico que recebe configurações.

**Vantagens**:
- ✅ DRY (código único)
- ✅ Manutenção centralizada
- ✅ Menos duplicação

**Desvantagens**:
- ❌ Menos flexível
- ❌ Pode ficar complexo

### Opção 3: Híbrida (MELHOR)
Criar helpers e hooks reutilizáveis, mas manter modais específicos.

```typescript
// ✅ Hook reutilizável
export function useFuncionarios(endpoint: string) {
  const [funcionarios, setFuncionarios] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const carregar = async () => {
    const response = await apiClient.get(endpoint);
    setFuncionarios(extractArrayData(response));
  };
  
  return { funcionarios, loading, carregar };
}

// ✅ Uso em cada app
export function ModalFuncionarios({ loja, onClose }) {
  const { funcionarios, loading, carregar } = useFuncionarios('/cabeleireiro/funcionarios/');
  // ... resto do código específico
}
```

---

## 📝 Plano de Ação

### Prioridade 1: Apps Mais Usados
1. ✅ **Cabeleireiro** - COMPLETO
2. ⚠️ **Clínica Estética** - Replicar correções
3. ⚠️ **CRM Vendas** - Replicar correções

### Prioridade 2: Apps Menos Usados
4. ⚠️ **Serviços** - Replicar correções
5. ⚠️ **Restaurante** - Replicar correções

### Passos para Cada App

#### 1. Verificar Backend
```bash
# Verificar se existe endpoint de funcionários
GET /api/{app}/funcionarios/

# Verificar modelo Funcionario
backend/{app}/models.py
```

#### 2. Criar Hook Reutilizável
```typescript
// hooks/useFuncionarios.ts
export function useFuncionarios(endpoint: string) { ... }
```

#### 3. Refatorar Modal
```typescript
// components/{app}/modals/ModalFuncionarios.tsx
// Seguir padrão do Cabeleireiro v415
```

#### 4. Testar
- Modal abre sem travar
- Lista carrega corretamente
- Admin da loja aparece
- CRUD funciona

#### 5. Deploy
```bash
cd frontend
vercel --prod --yes
```

---

## 🎯 Resposta à Pergunta

### As correções foram salvas onde?

**✅ Especificamente no App Cabeleireiro**

**Arquivos Corrigidos**:
1. `frontend/components/cabeleireiro/modals/ModalClientes.tsx`
2. `frontend/components/cabeleireiro/modals/ModalServicos.tsx`
3. `frontend/components/cabeleireiro/modals/ModalFuncionarios.tsx`
4. `frontend/components/cabeleireiro/modals/ModalAgendamentos.tsx`
5. `backend/cabeleireiro/models.py` (sincronização)
6. `backend/cabeleireiro/views.py` (paginação)

**Outros Apps**: ❌ Ainda não foram corrigidos

---

## 💡 Recomendação

### Para Manter Consistência

**Criar helpers reutilizáveis** que todos os apps podem usar:

```typescript
// ✅ lib/api-helpers.ts (já existe)
export function extractArrayData<T>(response: any): T[]
export function formatApiError(error: any): string

// ✅ hooks/useFuncionarios.ts (criar)
export function useFuncionarios(endpoint: string)

// ✅ hooks/useCRUD.ts (criar)
export function useCRUD<T>(endpoint: string)
```

Depois, cada app usa esses helpers mas mantém seu próprio modal específico.

**Benefícios**:
- ✅ DRY (helpers reutilizáveis)
- ✅ Flexibilidade (modais específicos)
- ✅ Manutenção (correções em um lugar)
- ✅ Boas práticas mantidas

---

## 📊 Próximos Passos

1. **Decidir estratégia**: Manual, Genérico ou Híbrida
2. **Criar hooks reutilizáveis** (se híbrida)
3. **Replicar para Clínica** (prioridade alta)
4. **Replicar para CRM** (prioridade alta)
5. **Replicar para outros apps** (prioridade média)

**Quer que eu replique as correções para os outros apps agora?** 🚀
